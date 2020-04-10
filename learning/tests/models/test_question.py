#
# Copyright (C) 2020 Guillaume Bernard <guillaume.bernard@koala-lms.org>
#
# Copyright (C) 2020 Loris Le Bris <loris.le_bris@etudiant.univ-lr.fr>
# Copyright (C) 2020 Arthur Baribeaud <arthur.baribeaud@etudiant.univ-lr.fr>
# Copyright (C) 2020 Alexis Delabarre <alexis.delabarre@etudiant.univ-lr.fr>
# Copyright (C) 2020 Célian Rolland <celian.rolland@etudiant.univ-lr.fr>
#
# This file is part of Koala LMS (Learning Management system)

# Koala LMS is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# We make an extensive use of the Django framework, https://www.djangoproject.com/
#

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.crypto import get_random_string

from learning.models import Course, CourseAccess, CourseState, QuestionCourse


class QuestionTestCase(TestCase):
    def setUp(self) -> None:
        get_user_model().objects.create_user(id=1, username="isaac-newton")
        get_user_model().objects.create_user(id=2, username="antoine-lavoisier")
        get_user_model().objects.create_user(id=3, username="marie-curie")
        get_user_model().objects.create_user(id=4, username="thomas-edison")
        get_user_model().objects.create_user(id=5, username="martin-luther")

        self.private_course = Course.objects.create(
            id=1,
            name="A simple private course",
            description="A simple description",
            author=get_user_model().objects.get(pk=1),
            tags="simple, course",
            access=CourseAccess.PRIVATE.name,
            state=CourseState.PUBLISHED.name,
            registration_enabled=True
        )

        self.public_course = Course.objects.create(
            id=2,
            name="A simple public course",
            description="A simple description",
            author=get_user_model().objects.get(pk=1),
            tags="simple, course",
            access=CourseAccess.PUBLIC.name,
            state=CourseState.PUBLISHED.name,
            registration_enabled=True
        )


class QuestionsUserPermsTest(QuestionTestCase):

    def test_no_permission_to_post_a_question_on_a_course(self):
        user2 = get_user_model().objects.get(pk=2)
        self.assertNotIn('submit_question_course', self.private_course.get_user_perms(user2))

    def test_allow_to_change_my_question_on_a_course(self):
        user1 = get_user_model().objects.get(pk=1)
        question = QuestionCourse.objects.create(course=self.public_course, author=user1, title="my question", body="this is the question's body")
        self.assertIn('change_questioncourse', question.get_user_perms(user1))

    def test_allow_to_delete_my_question_on_a_course(self):
        user1 = get_user_model().objects.get(pk=1)
        question = QuestionCourse.objects.create(course=self.public_course, author=user1, title="my question", body="this is the question's body")
        self.assertIn('delete_questioncourse', question.get_user_perms(user1))

    def test_allow_to_reply_to_my_question_on_a_course(self):
        user1 = get_user_model().objects.get(pk=1)
        question = QuestionCourse.objects.create(course=self.public_course, author=user1, title="my question", body="this is the question's body")
        self.assertIn('reply_questioncourse', question.get_user_perms(user1))

    def test_allow_to_view_my_question_on_a_course(self):
        user1 = get_user_model().objects.get(pk=1)
        question = QuestionCourse.objects.create(course=self.public_course, author=user1, title="my question", body="this is the question's body")
        self.assertIn('view_questioncourse', question.get_user_perms(user1))


class QuestionTest(QuestionTestCase):

    def test_default_values_for_attributes(self):
        question = QuestionCourse.objects.create(course=self.public_course, author=get_user_model().objects.get(pk=1), title="my question", body="this is the question's body")
        self.assertEqual(question.course, self.public_course)
        self.assertEqual(question.slug, "my-question")
        self.assertEqual(question.title, "my question")
        self.assertEqual(question.body, "this is the question's body")
        self.assertEqual(question.author, get_user_model().objects.get(pk=1))

    def test_generate_slug_field_for_new_question(self):
        q1 = QuestionCourse.objects.create(course=self.public_course, author=get_user_model().objects.get(pk=1), title="Question slug")
        q2 = QuestionCourse.objects.create(course=self.public_course, author=get_user_model().objects.get(pk=2), title="Question slug")
        q3 = QuestionCourse.objects.create(course=self.public_course, author=get_user_model().objects.get(pk=2), title="Question slug")
        self.assertEqual(q1.slug, "question-slug")
        self.assertEqual(q2.slug, "question-slug-1")
        self.assertEqual(q3.slug, "question-slug-2")

    def test_question_slug_max(self):
        long_name = get_random_string(length=60)
        q1 = QuestionCourse.objects.create(course=self.public_course, author=get_user_model().objects.get(pk=1), title=long_name)
        self.assertEqual(50,len(q1.slug))
        self.assertEqual(50, QuestionCourse._meta.get_field('slug').max_length)


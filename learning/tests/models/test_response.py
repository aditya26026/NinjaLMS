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

from learning.models import Course, CourseAccess, CourseState, QuestionCourse, Response


class ResponseTestCase(TestCase):
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


class QuestionsUserPermsTest(ResponseTestCase):

    def test_user_allow_to_reply_its_question(self):
        user = get_user_model().objects.get(pk=1)
        question = QuestionCourse.objects.create(course=self.private_course, author=user, title="question", body="this is the body")
        self.assertIn('reply_questioncourse', question.get_user_perms(user))

    def test_user_not_registered_on_private_course_dont_have_permission_on_responses(self):
        user = get_user_model().objects.get(pk=1)
        user2 = get_user_model().objects.get(pk=2)
        question = QuestionCourse.objects.create(course=self.private_course, author=user, title="question", body="this is the body")
        response = Response.objects.create(question=question, author=user, body="this is the response's body")
        self.assertEqual([], response.get_user_perms(user2))

    def test_user_can_delete_its_response(self):
        user = get_user_model().objects.get(pk=1)
        question = QuestionCourse.objects.create(course=self.private_course, author=user, title="question", body="this is the body")
        response = Response.objects.create(question=question, author=user, body="this is the response's body")
        self.assertIn('delete_response', response.get_user_perms(user))

    def test_user_can_update_its_response(self):
        user = get_user_model().objects.get(pk=1)
        question = QuestionCourse.objects.create(course=self.private_course, author=user, title="question", body="this is the body")
        response = Response.objects.create(question=question, author=user, body="this is the response's body")
        self.assertIn('change_response', response.get_user_perms(user))

    def test_user_is_able_see_its_response(self):
        user = get_user_model().objects.get(pk=1)
        question = QuestionCourse.objects.create(course=self.private_course, author=user, title="question", body="this is the body")
        response = Response.objects.create(question=question, author=user, body="this is the response's body")
        self.assertIn('view_response', response.get_user_perms(user))


class ResponseTest(ResponseTestCase):

    def test_default_values_for_attributes(self):
        user = get_user_model().objects.get(pk=1)
        question = QuestionCourse.objects.create(course=self.public_course, author=user, title="my question", body="this is the question's body")
        response = Response.objects.create(question=question, author= get_user_model().objects.get(pk=1), body="this is the body")
        self.assertEqual(user, response.author)
        self.assertEqual(question, response.question)
        self.assertEqual("this is the body", response.body)
        self.assertEqual(0, response.score)



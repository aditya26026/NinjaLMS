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
from django.urls import reverse

from learning.models import Course, CourseAccess, CourseState, QuestionCourse, Response
from learning.tests.views.helpers import ClientFactory


class AgoraViewsTest(TestCase):
    user_class = get_user_model()

    def setUp(self):
        for initials in ["ws", "acd", "lt", "ed"]:
            setattr(self, initials, get_user_model().objects.create_user(username=initials, password="pwd"))

        self.private_course = Course.objects.create(
            id=1,
            name="A simple course",
            description="A simple description",
            author=self.user_class.objects.get(pk=1),
            tags="simple, course",
            access=CourseAccess.PRIVATE.name,
            state=CourseState.PUBLISHED.name,
            registration_enabled=True
        )

        self.public_course = Course.objects.create(
            id=2,
            name="A simple course",
            description="A simple description",
            author=self.user_class.objects.get(pk=1),
            tags="simple, course",
            access=CourseAccess.PUBLIC.name,
            state=CourseState.PUBLISHED.name,
            registration_enabled=True
        )

        self.students_only_course = Course.objects.create(
            id=3,
            name="A simple course",
            description="A simple description",
            author=get_user_model().objects.get(pk=1),
            tags="simple, course",
            access=CourseAccess.STUDENTS_ONLY.name,
            state=CourseState.PUBLISHED.name,
            registration_enabled=True
        )


class TestAgoraViews(AgoraViewsTest):

    def test_agora_field_in_course_detail(self):
        for course in (self.public_course, self.private_course):
            response = ClientFactory.get_client_for_user("ws").get(reverse("learning:course/detail", kwargs={'slug': course.slug}))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "learning/course/detail.html")

            content = response.content.decode("utf-8")
            self.assertIn("agora-acces", content)

    def test_btn_new_question_in_agora_page(self):
        response = ClientFactory.get_client_for_user("ws").get(reverse("learning:course/detail/agora", kwargs={'slug': self.public_course.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "learning/course/details/agora/agora.html")
        content = response.content.decode("utf-8")
        self.assertIn("btn-new-question", content)

    def test_no_question_in_agora_page(self):
        response = ClientFactory.get_client_for_user("ws").get(reverse("learning:course/detail/agora", kwargs={'slug': self.public_course.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "learning/course/details/agora/agora.html")

        content = response.content.decode("utf-8")
        self.assertNotIn("agora-question", content)

    def test_a_question_in_agora_page(self):
        QuestionCourse.objects.create(course=self.public_course, author=get_user_model().objects.get(pk=1), title="my question", body="this is the question's body")
        response = ClientFactory.get_client_for_user("ws").get(reverse("learning:course/detail/agora", kwargs={'slug': self.public_course.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "learning/course/details/agora/agora.html")

        content = response.content.decode("utf-8")
        self.assertIn("btn-new-question", content)

    def test_breadcrumb_in_agora_page(self):
        response = ClientFactory.get_client_for_user("ws").get(reverse("learning:course/detail/agora", kwargs={'slug': self.public_course.slug}))
        content = response.content.decode("utf-8")
        self.assertIn("/course/detail/"+ self.public_course.slug +"/", content)

    def test_see_more_when_question_agora_exist(self):
        QuestionCourse.objects.create(course=self.public_course, author=get_user_model().objects.get(pk=1),title="my question", body="this is the question's body")
        response = ClientFactory.get_client_for_user("ws").get(reverse("learning:course/detail/agora", kwargs={'slug': self.public_course.slug}))
        content = response.content.decode("utf-8")
        self.assertIn("link-towards-question", content)

    def test_informations_about_a_question_agora(self):
        question = QuestionCourse.objects.create(course=self.public_course, author=get_user_model().objects.get(pk=1), title="my question", body="this is the question's body")
        response = ClientFactory.get_client_for_user("ws").get(reverse("learning:course/detail/agora", kwargs={'slug': self.public_course.slug}))
        content = response.content.decode("utf-8")
        self.assertIn(question.title.__str__(), content)

    def test_page_answer_question_agora(self):
        question = QuestionCourse.objects.create(course=self.public_course, author=get_user_model().objects.get(pk=1), title="my question", body="this is the question body")
        response = ClientFactory.get_client_for_user("ws").get(reverse("learning:course/detail/question", kwargs={'slug': self.public_course.slug, 'question_slug': question.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "learning/course/details/agora/question_detail.html")

        content = response.content.decode("utf-8")
        self.assertIn("0 Answers", content)
        self.assertIn(question.title.__str__(), content)
        self.assertIn(question.body.__str__(), content)

    def test_page_question_with_a_response(self):
        user2 = get_user_model().objects.get(pk=2)
        question = QuestionCourse.objects.create(course=self.public_course, author=get_user_model().objects.get(pk=1), title="my question", body="this is the question body")
        answer = Response.objects.create(question=question, author=user2, body="this is the response body")
        response = ClientFactory.get_client_for_user("ws").get(reverse("learning:course/detail/question", kwargs={'slug': self.public_course.slug,'question_slug': question.slug}))
        content = response.content.decode("utf-8")
        self.assertIn(answer.body, content)
        self.assertIn("1 Answers", content)
        self.assertIn("btn-score", content)

    def test_page_question_without_response(self):
        question = QuestionCourse.objects.create(course=self.public_course,author=get_user_model().objects.get(pk=1), title="my question",body="this is the question body")
        response = ClientFactory.get_client_for_user("ws").get(reverse("learning:course/detail/question", kwargs={'slug': self.public_course.slug,'question_slug': question.slug}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("0 Answers", content)

    def test_page_question_have_field_to_answer(self):
        question = QuestionCourse.objects.create(course=self.public_course, author=get_user_model().objects.get(pk=1), title="my question", body="this is the question body")
        response = ClientFactory.get_client_for_user("ws").get(reverse("learning:course/detail/question", kwargs={'slug': self.public_course.slug, 'question_slug': question.slug}))
        content = response.content.decode("utf-8")
        self.assertIn("id_body", content)

    def test_page_add_question_to_course(self):
        QuestionCourse.objects.create(course=self.public_course, author=get_user_model().objects.get(pk=1), title="my question", body="this is the question body")
        response = ClientFactory.get_client_for_user("ws").get(reverse("learning:course/detail/question/add", kwargs={'slug': self.public_course.slug}))
        content = response.content.decode("utf-8")
        self.assertIn("id_title", content)
        self.assertIn("id_body", content)
        self.assertIn("btn-submit", content)

    def test_btn_new_question_on_course(self):
        response = ClientFactory.get_client_for_user("ws").get(reverse("learning:course/detail", kwargs={'slug': self.public_course.slug}))
        content = response.content.decode("utf-8")
        self.assertTemplateUsed(response, "learning/course/detail.html")
        self.assertIn("btn-new-question", content)






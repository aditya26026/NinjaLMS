#
# Copyright (C) 2019 Guillaume Bernard <guillaume.bernard@koala-lms.org>
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

import json

from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import Person, Notification


class MarkNotificationAsReadTestView(TestCase):

    def setUp(self) -> None:
        self.user = Person.objects.create_user(id=1, username="william-shakespeare", password="pwd")
        self.client = Client()
        self.client.login(username="william-shakespeare", password="pwd")
        Notification.objects.create(id=1, recipient=self.user, message="A test", target="https://google.com")
        Notification.objects.create(id=2, recipient=self.user, message="A test", target="https://google.com")
        Notification.objects.create(id=3, recipient=self.user, message="A test 2", target="https://google.com")
        Notification.objects.create(id=4, recipient=self.user, message="A test 3")
        Notification.objects.create(id=5, recipient=self.user, message="A test 4", target="https://google.com")
        Notification.objects.create(id=6, recipient=self.user, message="A test 5")
        Notification.objects.create(id=7, recipient=self.user, message="A test 6", target="https://google.com")

    def test_get_mark_notification_as_read(self):
        self.assertEqual(7, self.user.unread_notifications.count())
        response = self.client.get(
            reverse("accounts:ajax/notification/read", kwargs={'notification_id': 1})
        )
        self.assertEqual(200, response.status_code)
        json_object = json.loads(response.content)
        self.assertEqual(7, self.user.unread_notifications.count())
        self.assertEqual(7, json_object.get('unread'))

    def test_post_mark_notification_as_read(self):
        self.assertEqual(7, self.user.unread_notifications.count())
        response = self.client.post(
            reverse("accounts:ajax/notification/read", kwargs={'notification_id': 1})
        )
        self.assertEqual(200, response.status_code)
        json_object = json.loads(response.content)
        self.assertEqual(6, self.user.unread_notifications.count())
        self.assertEqual(6, json_object.get('unread'))

    def test_get_delete_notification(self):
        self.assertEqual(7, self.user.unread_notifications.count())
        response = self.client.get(
            reverse("accounts:ajax/notification/delete", kwargs={'notification_id': 1})
        )
        self.assertEqual(200, response.status_code)
        json_object = json.loads(response.content)
        self.assertEqual(7, self.user.unread_notifications.count())
        self.assertEqual(7, json_object.get('unread'))

    def test_post_delete_notification(self):
        self.assertEqual(7, self.user.unread_notifications.count())
        response = self.client.post(
            reverse("accounts:ajax/notification/delete", kwargs={'notification_id': 1})
        )
        self.assertEqual(200, response.status_code)
        json_object = json.loads(response.content)
        self.assertEqual(6, self.user.unread_notifications.count())
        self.assertEqual(6, json_object.get('unread'))

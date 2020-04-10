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

from datetime import datetime

from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.test import TestCase

from accounts.models import Notification, Person, GroupOfPeople


class PersonTest(TestCase):

    def setUp(self) -> None:
        self.user = Person.objects.create_user(id=1, username="william-shakespeare")
        Notification.objects.create(
            recipient=self.user,
            message="A test",
            target="https://google.com"
        )

    def test_display_name_first_name_only(self):
        user = Person.objects.create_user(username="leo-tolstoi", first_name="Leo")
        self.assertEqual("leo-tolstoi", user.display_name)

    def test_display_name_last_name_only(self):
        user = Person.objects.create_user(username="leo-tolstoi", last_name="Tolstoi")
        self.assertEqual("leo-tolstoi", user.display_name)

    def test_display_name_username_only(self):
        user = Person.objects.create_user(username="leo-tolstoi")
        self.assertEqual("leo-tolstoi", user.display_name)

    def test_display_name_first_and_last_names(self):
        user = Person.objects.create_user(username="leo-tolstoi", first_name="Leo", last_name="Tolstoi")
        self.assertEqual("Leo Tolstoi", user.display_name)

    def test_notify_user_with_target(self):
        self.assertEqual(1, self.user.notifications.count())
        self.user.notify("A new message", "https://www.koala-lms.org")
        self.assertEqual(2, self.user.notifications.count())

        n = Notification.objects.get(id=2)
        self.assertEqual(self.user, n.recipient)
        self.assertEqual("A new message", n.message)
        self.assertEqual("https://www.koala-lms.org", n.target)
        self.assertFalse(n.is_read)
        self.assertAlmostEqual(n.timestamp.timestamp(), datetime.now().timestamp(), delta=0.1)

    def test_notify_user_with_target_in_french(self):
        self.assertEqual(1, self.user.notifications.count())
        self.user.preferred_language = 'fr'
        self.user.save()
        self.user.notify("User", "https://www.koala-lms.org")
        self.assertEqual(2, self.user.notifications.count())

        n = Notification.objects.get(id=2)
        self.assertEqual(self.user, n.recipient)
        self.assertEqual("Utilisateur", n.message)
        self.assertEqual("https://www.koala-lms.org", n.target)
        self.assertFalse(n.is_read)
        self.assertAlmostEqual(n.timestamp.timestamp(), datetime.now().timestamp(), delta=0.1)

    def test_notify_user_with_target_not_supported_language(self):
        self.assertEqual(1, self.user.notifications.count())
        self.user.preferred_language = 'abcd'
        self.user.save()
        self.user.notify("User", "https://www.koala-lms.org")
        self.assertEqual(2, self.user.notifications.count())

        n = Notification.objects.get(id=2)
        self.assertEqual(self.user, n.recipient)
        self.assertEqual("User", n.message)
        self.assertEqual("https://www.koala-lms.org", n.target)
        self.assertFalse(n.is_read)
        self.assertAlmostEqual(n.timestamp.timestamp(), datetime.now().timestamp(), delta=0.1)

    def test_notify_user_without_target(self):
        self.assertEqual(1, self.user.notifications.count())
        self.user.notify("A new message")
        self.assertEqual(2, self.user.notifications.count())

        n = Notification.objects.get(id=2)
        self.assertEqual(self.user, n.recipient)
        self.assertEqual("A new message", n.message)
        self.assertIsNone(n.target)
        self.assertFalse(n.is_read)
        self.assertAlmostEqual(n.timestamp.timestamp(), datetime.now().timestamp(), delta=0.1)

    def test_get_unread_notifications(self):
        Notification.objects.create(id=2, recipient=self.user, message="A test", target="https://google.com")
        Notification.objects.create(id=3, recipient=self.user, message="A test 2", target="https://google.com")
        Notification.objects.create(id=4, recipient=self.user, message="A test 3")
        Notification.objects.create(id=5, recipient=self.user, message="A test 4", target="https://google.com")
        Notification.objects.create(id=6, recipient=self.user, message="A test 5")
        Notification.objects.create(id=7, recipient=self.user, message="A test 6", target="https://google.com")

        self.assertEqual(7, self.user.unread_notifications.count())
        self.assertIsInstance(self.user.unread_notifications, QuerySet)
        for notification in self.user.unread_notifications.all():
            self.assertFalse(notification.is_read)

        n = Notification.objects.get(id=5)
        n.is_read = True
        n.save()

        self.assertEqual(6, self.user.unread_notifications.count())
        for notification in self.user.unread_notifications.all():
            self.assertFalse(notification.is_read)


class NotificationTest(TestCase):

    def setUp(self) -> None:
        self.user = Person.objects.create_user(id=1, username="william-shakespeare")
        Notification.objects.create(recipient=self.user, message="A test", target="https://google.com")

    def test_default_values(self):
        n = Notification.objects.create(recipient=self.user)
        self.assertEqual(self.user, n.recipient)
        self.assertEqual(str(), n.message)
        self.assertIsNone(n.target)
        self.assertFalse(n.is_read)
        self.assertAlmostEqual(n.timestamp.timestamp(), datetime.now().timestamp(), delta=0.1)

    def test_clean_escape_message(self):
        n = Notification.objects.create(recipient=self.user, message="<script>alert('Hello');</script>")
        n.clean()
        self.assertEqual("&lt;script&gt;alert(&#39;Hello&#39;);&lt;/script&gt;", n.message)


class GroupOfPeopleTest(TestCase):

    def setUp(self) -> None:
        self.user = Person.objects.create_user(id=1, username="william-shakespeare")
        self.group1 = GroupOfPeople.objects.create(name="group1")
        self.sub_group1 = GroupOfPeople.objects.create(name="sub_group1")
        self.sub_group2 = GroupOfPeople.objects.create(name="sub_group2")
        self.sub_sub_group1 = GroupOfPeople.objects.create(name="sub_sub_group1")

        self.sub_group1.parent_group = self.group1
        self.sub_group1.save()

        self.sub_group2.parent_group = self.group1
        self.sub_group2.save()

        self.sub_sub_group1.parent_group = self.sub_group1
        self.sub_sub_group1.save()

    def test_has_subgroups(self):
        self.assertEquals(2, self.group1.subgroups.count())

    def test_no_subgroup(self):
        self.assertEquals(0, self.sub_sub_group1.subgroups.count())

    def test_has_parent(self):
        self.assertEqual(self.group1, self.sub_group2.parent_group)
        self.assertEqual(self.group1, self.sub_group1.parent_group)

    def test_user_in(self):
        self.sub_sub_group1.user_set.add(self.user)
        self.assertTrue(self.group1.is_user_in(self.user))
        self.assertTrue(self.sub_group1.is_user_in(self.user))
        self.assertTrue(self.sub_sub_group1.is_user_in(self.user))

    def test_group_in(self):
        self.assertTrue(self.group1.is_group_in(self.sub_group1))
        self.assertTrue(self.group1.is_group_in(self.sub_group2))

    def test_sub_sub_group_in(self):
        self.assertTrue(self.group1.is_group_in(self.sub_sub_group1))

    def test_clean_cannot_add_self_as_parent(self):
        self.group1.parent_group = self.group1
        with self.assertRaises(ValidationError):
            self.group1.clean()

    def test_clean_cannot_add_direct_children_as_parent(self):
        self.group1.parent_group = self.group1.subgroups.first()
        with self.assertRaises(ValidationError):
            self.group1.clean()

    def test_clean_cannot_add_children_as_parent(self):
        self.group1.parent_group = self.sub_sub_group1
        with self.assertRaises(ValidationError):
            self.group1.clean()

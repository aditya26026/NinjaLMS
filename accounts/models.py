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


from django.conf import global_settings
from django.contrib.auth.models import AbstractUser, Group as AbstractGroup
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import translation
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _, pgettext_lazy


def get_translated_languages():
    """
    Get the list of languages supported by Django, translated in the current locale.

    .. note:: Languages are wrapped around the “noop_gettext” function which does not translate them at runtime.

    :return: a list of tuples containing the language code and the translated version of the language name
    :rtype: list of tuples
    """
    languages = []
    for code, language in global_settings.LANGUAGES:
        languages.append((code, _(language)))
    return languages


class Person(AbstractUser):
    preferred_language = models.CharField(
        max_length=20,
        choices=get_translated_languages(),
        verbose_name=_("Preferred language"),
        default='en',
        help_text=_("This parameter is used to let you define in which language you want us to talk with you. Because "
                    "of translation status, it may happen that no translation is available for you language.")
    )
    email = models.EmailField(_('email address'), blank=False)

    class Meta:
        verbose_name = _('User')
        db_table = 'users'
        ordering = ('username',)

    def notify(self, message, target=None):
        current_language = translation.get_language()
        try:
            translation.activate(self.preferred_language)
            self.notifications.create(message=translation.gettext(message), target=target)
        finally:
            translation.activate(current_language)

    @property
    def unread_notifications(self):
        return self.notifications.filter(is_read=False)

    @property
    def display_name(self):
        if self.first_name and self.last_name:
            return "{} {}".format(self.first_name, self.last_name)
        return self.username

    def __str__(self):
        return self.display_name


class Notification(models.Model):
    recipient = models.ForeignKey(
        Person,
        verbose_name=_("Recipient"),
        related_name="notifications",
        on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        auto_now=False,
        verbose_name=_("Date and time")
    )
    message = models.TextField(
        verbose_name=_("Message"),
    )
    target = models.CharField(
        max_length=500,
        verbose_name=_("Target"),
        blank=True,
        null=True
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name=pgettext_lazy("State of a notification", "Is read")
    )

    def clean(self):
        self.message = escape(self.message)

    def __str__(self):
        return "To %(recipient)s: “%(message)s”" % {'recipient': self.recipient, 'message': self.message}

    class Meta:
        ordering = ['recipient', 'timestamp']
        verbose_name = pgettext_lazy("Notification verbose name (singular form)", "notification")
        verbose_name_plural = pgettext_lazy("Notification verbose name (plural form)", "notifications")


class GroupOfPeople(AbstractGroup):
    parent_group = models.ForeignKey(
        'self',
        related_name="subgroups",
        verbose_name=_("Parent group"),
        on_delete=models.CASCADE,
        blank=True, null=True
    )

    def is_user_in(self, user: Person) -> bool:
        """
        Check if a user is in the group or in its subgroups

        :param user: the user to query in the group hierarchy
        :type user: Person
        :return: True is the user is in the hierarchy
        :rtype: bool
        """
        user_in_group = user in self.user_set.all()
        user_in_subgroup = False
        for subgroup in self.subgroups.all():
            user_in_subgroup = subgroup.is_user_in(user)
            if user_in_subgroup:
                break
        return user_in_group or user_in_subgroup

    def is_group_in(self, group: 'GroupOfPeople') -> bool:
        """
        Check if a group is in the current subgroups or deeper in the hierarchy

        :param group: the group to query in the hierarchy
        :type group: GroupOfPeople
        :return: True if the group is in the hierarchy
        :rtype: bool
        """
        is_in_subgroups = group in self.subgroups.all()
        if not is_in_subgroups:  # It may be in the subgroups of the subgroups
            is_group_in_subgroups = False
            for subgroup in self.subgroups.all():
                is_group_in_subgroups = subgroup.is_group_in(group)
                if is_group_in_subgroups:
                    break
            return is_group_in_subgroups
        return is_in_subgroups

    def clean(self):
        if self == self.parent_group:
            raise ValidationError(
                {'parent_group': _("“%(group)s” cannot be its own parent group.") % {'group': self.name}}
            )
        if self.parent_group in self.subgroups.all():
            raise ValidationError(
                {
                    'parent_group': _("“%(parent_group)s” cannot be set as the parent group because it appears in the "
                                      "“%(group)s” subgroups.") % {'group': self.name,
                                                                   'parent_group': self.parent_group.name}
                }
            )
        if self.is_group_in(self.parent_group):
            raise ValidationError(
                {
                    'parent_group': _("If “%(parent_group)s” becomes the parent of “%(group)s”, “%(group)s” will have "
                                      "itself as an ancestor because “%(group)s” is already the ancestor of "
                                      "“%(parent_group)s”. It is forbidden in order to prevent cycles in the "
                                      "hierarchy.") % {'group': self.name, 'parent_group': self.parent_group.name}
                }
            )

    def __str__(self):
        parent, children = None, None
        if self.parent_group:
            parent = self.parent_group.name
        if self.subgroups.count() > 0:
            children = ', '.join([group.name for group in self.subgroups.all()])
        if parent and children:
            return _("%(group)s (children of “%(parent)s“, parent of [%(children)s])") % \
                   {'group': self.name, 'parent': parent, 'children': children}
        if parent and not children:
            return _("%(group)s (children of “%(parent)s“)") % {'group': self.name, 'parent': parent}
        if children and not parent:
            return _("%(group)s (parent of [%(children)s])") % {'group': self.name, 'children': children}
        return _("%(group)s") % {'group': self.name}

    class Meta:
        verbose_name = pgettext_lazy("Group of people (singular form)", "group of people")
        verbose_name_plural = pgettext_lazy("Group of people (plural form)", "groups of people")
        ordering = ('name',)

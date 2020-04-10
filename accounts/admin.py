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

from datetime import datetime, timedelta

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext as _

from accounts.forms import UserCreationForm, UserAdminChangeForm
from accounts.models import Person, Notification, GroupOfPeople, Preferences


# noinspection PyUnusedLocal
# pylint: disable=unused-argument
def delete_inactive_account_since_30_days(modeladmin, request, queryset):
    """
    Delete account's which are have not been activated since 30 days.
    """
    date_boundary = datetime.now() - timedelta(days=30)
    queryset.filter(date_joined__lt=date_boundary, is_active=False).delete()


delete_inactive_account_since_30_days.short_description = _(
    "Delete accounts that are inactive since at least 30 days")


class AccountsAdmin(UserAdmin):
    model = Person
    form = UserAdminChangeForm
    add_form = UserCreationForm

    prepopulated_fields = {'username': ('first_name', 'last_name',)}

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'username', 'email', 'password1', 'password2',),
        }),
    )
    actions = [delete_inactive_account_since_30_days]


class GroupAdminForm(forms.ModelForm):
    class Meta:
        model = GroupOfPeople
        fields = ('name', 'parent_group', 'users',)

    users = forms.ModelMultipleChoiceField(
        queryset=Person.objects.all(),
        required=False,
        widget=FilteredSelectMultiple(_('Users'), False)
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['users'].initial = self.instance.user_set.all()

    def _save_m2m(self):
        self.instance.user_set.set(self.cleaned_data['users'])


class GroupOfPeopleAdmin(GroupAdmin):
    model = GroupOfPeople
    form = GroupAdminForm


# Register person
admin.site.register(Person, AccountsAdmin)

# Register group
admin.site.unregister(Group)
admin.site.register(GroupOfPeople, GroupOfPeopleAdmin)

# Register notifications
admin.site.register(Notification)


admin.site.register(Preferences)

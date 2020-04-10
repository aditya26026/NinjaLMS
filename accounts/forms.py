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

import django.contrib.auth.forms as auth_forms
from django.contrib.auth import authenticate
from django.forms import Form

from .models import Person


class CustomClassesOnFormMixin(Form):
    custom_classes = ["form-control"]

    def __init__(self, *args, **kwargs):
        super(CustomClassesOnFormMixin, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': ' '.join(self.custom_classes)})


class UserLoginForm(CustomClassesOnFormMixin, auth_forms.AuthenticationForm):

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                try:
                    self.user_cache = Person.objects.get(username=username)
                except Person.DoesNotExist:
                    self.user_cache = None

                if self.user_cache is not None and self.user_cache.check_password(password):
                    self.confirm_login_allowed(self.user_cache)
                else:
                    self.get_invalid_login_error()

        return self.cleaned_data


class UserPasswordResetForm(CustomClassesOnFormMixin, auth_forms.PasswordResetForm):
    pass


class UserCreationForm(CustomClassesOnFormMixin, auth_forms.UserCreationForm):
    class Meta:
        model = Person
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')


class UserChangeForm(CustomClassesOnFormMixin, auth_forms.UserChangeForm):
    class Meta:
        model = Person
        fields = ('first_name', 'last_name', 'email', 'preferred_language')


class UserAdminChangeForm(CustomClassesOnFormMixin, auth_forms.UserChangeForm):
    class Meta:
        model = Person
        fields = ('first_name', 'last_name', 'email', 'preferred_language')

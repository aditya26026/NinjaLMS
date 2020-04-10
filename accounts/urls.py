#
# Copyright (C) 2019 Guillaume Bernard <guillaume.bernard@koala-lms.org>
# Copyright (C) 2020 Louis Barbier <louis.barbier41@outlook.fr>
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
from django.contrib.auth.views import PasswordResetView
from django.urls import path, include, re_path

from accounts import views
from accounts.forms import UserPasswordResetForm

app_name = 'accounts'

ajax_api_urlpatterns = [
    path('search/', views.search_user, name='ajax/search'),
    path('notification/read/<int:notification_id>',
         views.notification_mark_as_read, name="ajax/notification/read"),
    path('notification/delete/<int:notification_id>',
         views.notification_delete, name="ajax/notification/delete"),
]

urlpatterns = [
    path('', views.LoginView.as_view(), name='index'),

    path('login/', views.LoginView.as_view(), name='login'),
    path('login_success/', views.loginSuccess, name='login_success'),
    path('details/', views.AccountsDetailsView.as_view(), name='details'),

    #  Password update and reset
    path('password_change/', views.PasswordChange.as_view(), name='password_change'),
    path('password_reset/', PasswordResetView.as_view(
        form_class=UserPasswordResetForm), name="password_reset"),

    path('preferences/', views.preferences, name='preferences'),

    #  Account registration and activation
    path('register/', views.AccountsRegisterView.as_view(), name='register'),
    re_path(
        r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.activate, name='activate'
    ),
    re_path(
        r'send_activation_mail/(?P<uidb64_username>[0-9A-Za-z_\-]+)/$', views.resend_activation_mail,
        name='resend_email_confirmation'
    ),

    #  Ajax views
    path('ajax/', include(ajax_api_urlpatterns))
]

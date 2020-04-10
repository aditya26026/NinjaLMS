#
# Copyright (C) 2019 Guillaume Bernard <guillaume.bernard@koala-lms.org>
#
# This file is part of Koala LMS (Learning Management system)

import urllib
from django import template
from accounts.tokens import account_activation_token
from accounts.models import Person, Notification, Preferences
from accounts.forms import UserLoginForm, UserCreationForm, UserChangeForm
from django.views.generic import CreateView, UpdateView
from django.contrib import messages
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
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as AuthLoginView, PasswordChangeView
from django.core.mail import EmailMessage
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import ugettext_lazy as _
from django.core import serializers

pref_dict = {
    'Development': ['Web Development', 'Data Science', 'Mobile Apps', 'Programming Languages', 'Game Development', 'Databases', 'Software Testing', 'Software Engineering', 'Development Tools', 'E Commerce'],
    'Business': ['Finance Courses', 'Entrepreneurship', 'Communications', 'Management', 'Sales', 'Strategy', 'Operations', 'Project Management', 'Business Law', 'Data And Analytics', 'Home Business', 'Human Resources', 'Industry', 'Media', 'Real Estate', 'Other Business'],
    'Finance And Accounting': ['Accounting Bookkeeping', 'Compliance', 'Cryptocurrency And Blockchain', 'Economics', 'Finance Management', 'Finance Certification And Exam Prep', 'Financial Modeling And Analysis', 'Investing And Trading', 'Money Management Tools', 'Taxes', 'Other Finance And Accounting'],
    'It And Software': ['It Certification', 'Network And Security', 'Hardware', 'Operating Systems', 'Other It And Software'],
    'Office Productivity': ['Microsoft', 'Apple', 'Google', 'Sap', 'Oracle', 'Other Productivity'],
    'Personal Development': ['Personal Transformation', 'Productivity', 'Leadership', 'Personal Finance', 'Career Development', 'Parenting And Relationships', 'Happiness', 'Religion And Spirituality', 'Personal Brand Building', 'Creativity', 'Influence', 'Self Esteem', 'Stress Management', 'Memory', 'Motivation', 'Other Personal Development'],
    'Design': ['Web Design', 'Graphic Design', 'Design Tools', 'User Experience', 'Game Design', 'Design Thinking', '3D And Animation', 'Fashion', 'Architectural Design', 'Interior Design', 'Other Design'],
    'Marketing': ['Digital Marketing', 'Search Engine Optimization', 'Social Media Marketing', 'Branding', 'Marketing Fundamentals', 'Analytics And Automation', 'Public Relations', 'Advertising', 'Video And Mobile Marketing', 'Content Marketing', 'Growth Hacking', 'Affiliate Marketing', 'Product Marketing', 'Other Marketing'],
    'Lifestyle': ['Arts And Crafts', 'Food And Beverage', 'Beauty And Makeup', 'Travel', 'Gaming', 'Home Improvement', 'Pet Care And Training', 'Other Lifestyle'],
    'Photography': ['Digital Photography', 'Photography Fundamentals', 'Portraits', 'Photography Tools', 'Commercial Photography', 'Video Design', 'Other Photography'],
    'Health And Fitness': ['Fitness', 'General Health', 'Sports', 'Nutrition', 'Yoga', 'Mental Health', 'Dieting', 'Self Defense', 'Safety And First Aid', 'Dance', 'Meditation', 'Other Health And Fitness'],
    'Music': ['Instruments', 'Production', 'Music Fundamentals', 'Vocal', 'Music Techniques', 'Music Software', 'Other Music'],
    'Teaching And Academics': ['Engineering', 'Humanities', 'Math', 'Science', 'Online Education', 'Social Science', 'Language', 'Teacher Training', 'Test Prep', 'Other Teaching Academics']
}

pref_values = tuple(pref_dict.keys())


def _update_valid_or_invalid_form_fields(form):
    for field in form.fields:
        try:
            current_class = form.fields[field].widget.attrs['class']
        except KeyError:
            current_class = str()

        if field in form.errors:
            form.fields[field].widget.attrs.update(
                {'class': current_class + ' ' + 'is-invalid'})
        elif field in form.changed_data:
            form.fields[field].widget.attrs.update(
                {'class': current_class + ' ' + 'is-valid'})
    return form


def loginSuccess(request):
    if request.method == 'GET':
        current_user = request.user
        if current_user.is_first_login:
            return redirect("accounts:preferences")
    return redirect("home")


def send_activation_mail(user: get_user_model(), domain: str) -> bool:
    """
    This function sends an activation email. It can be used to send the first confirmation email or to send a new one

    :param user: This contains the user who wants activate his account
    :type user: get_user_model()
    :param domain: the domain on which the current instance is running. This is, for instance: demo.koala-lms.org
    :type domain: str
    :return True if the mail has been send
    :rtype bool
    """
    message = render_to_string('registration/account_activation_mail.html', {
        'user': user,
        'domain': domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    })
    return EmailMessage(_("Activate your Koala LMS account"), message, to=[user.email]).send() == 1


def resend_activation_mail(request, uidb64_username: str):
    """
    This view is used to resent the confirmation email to the user that requested it.

    :param request: the request to handle
    :type request: django.http.HttpRequest
    :param uidb64_username: the user’s username to send the confirmation email. username is encoded using urlsafe_base64_encode
    :type uidb64_username: str
    """
    try:
        decoded_user = get_object_or_404(get_user_model(), username=force_text(
            urlsafe_base64_decode(uidb64_username)))
    except(TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        messages.error(
            request,
            _("Something went wrong when trying to find your account in the database. Aborting.")
        )
    else:
        if send_activation_mail(decoded_user, request.get_host()):
            messages.info(
                request, _(
                    "%(user)s, we send you a new confirmation email to %(email)s."
                ) % {'user': decoded_user.get_full_name(), 'email': decoded_user.email}
            )
        else:
            messages.error(
                request, _("The component used to send the confirmation mails is broken. Please contact your "
                           "system administrator to let him fix this issue.")
            )
    return redirect("accounts:login")


class LoginView(AuthLoginView):
    form_class = UserLoginForm
    redirect_authenticated_user = True

    def form_invalid(self, form):
        if not self.request.user.is_active:
            # If the error code is 'inactive' we propose to the user sending a new confirmation's email
            user = urlsafe_base64_encode(force_bytes(form.user_cache.username))
            messages.warning(
                self.request,
                _("%(name)s, is seems your account has not been activated yet. If you did not received any "
                  "confirmation email, click <a href=\"%(resend_link)s\">here</a>. Another one will be resend "
                  "to you.")
                % {
                    'name': form.user_cache.get_full_name(),
                    'resend_link': reverse_lazy('accounts:resend_email_confirmation', kwargs={'uidb64_username': user})
                }
            )
        return super().form_invalid(form)


class PasswordChange(PasswordChangeView):
    success_url = reverse_lazy('accounts:details')
    title = _("My account − Change password")

    def form_valid(self, form):
        messages.success(self.request, _("Password updated!"))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _(
            "Error when updating password. You should fix the issues and try again."))
        form = _update_valid_or_invalid_form_fields(form)
        return super().form_invalid(form)


class AccountsRegisterView(CreateView):
    template_name = "accounts/register.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("accounts:details")
    extra_context = {
        "title": _("Create a new account")
    }

    def form_valid(self, form):
        user = form.save()
        user.is_active = False
        if send_activation_mail(user, self.request.get_host()):
            messages.success(
                self.request, _(
                    "%(user)s (%(username)s), your registration is complete now. In order to access your account, you "
                    "have to activate it first. We just sent you an email to confirm your registration."
                ) % {'user': user.get_full_name(), 'username': user.username}
            )
        else:
            messages.error(
                self.request, _("The component used to send the confirmation mails is broken. Please contact your "
                                "system administrator to let him fix this issue.")
            )
        return super().form_valid(form)

    def form_invalid(self, form):
        for error in form.errors:
            messages.error(self.request, form.errors[error])
        return super().form_invalid(form)


class AccountsDetailsView(LoginRequiredMixin, UpdateView):
    template_name = "accounts/details.html"
    form_class = UserChangeForm
    success_url = reverse_lazy("accounts:details")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        form.save()
        if form.has_changed():
            messages.success(self.request, _(
                "Your personal details have been updated!"))
        return super().form_valid(form)

    def form_invalid(self, form):
        form = _update_valid_or_invalid_form_fields(form)
        messages.error(self.request, _(
            "Error when changing personal details. Check errors and retry."))
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("My account − %(username)s") % {
            'username': self.request.user.display_name}
        return context


@login_required
def search_user(request):
    """
    Searching for a user is limited to − obviously − registered user.
    It seems that this may be a personal data leak, but as any registered
    user can create a course and add collaborator or students, up to now
    there is not other solution.

    :param request:
    :return:
    """
    response = JsonResponse({})
    if request.method == 'GET':
        search_string = request.GET.get('user', None)
        if search_string and len(search_string) > 1:
            persons = Person.objects.filter(
                Q(username__icontains=search_string) |
                Q(first_name__icontains=search_string) |
                Q(last_name__icontains=search_string)
            )
            response = JsonResponse(
                list(persons.values('username', 'first_name', 'last_name')),
                safe=False
            )
    return response


@login_required
def notification_mark_as_read(request, notification_id):
    if request.method == 'POST':
        notification = get_object_or_404(
            Notification, recipient=request.user, pk=notification_id)
        notification.is_read = True
        notification.save()
    # noinspection PyUnresolvedReferences
    return JsonResponse({'unread': request.user.unread_notifications.count()})


@login_required
def preferences(request):
    if request.method == 'POST':
        choice_list = request.POST["choices"].split(",")
        inst_arr = []
        for choice in choice_list:
            p1 = Preferences(name=choice)
            p1.save()
            inst_arr.append(p1)
        user = request.user
        user.save()
        user.preferences.add(*inst_arr)
        return redirect("home")
    return render(request, 'accounts/preferences.html', {'pref_list': pref_dict})


@login_required
def notification_delete(request, notification_id):
    if request.method == 'POST':
        notification = get_object_or_404(
            Notification, recipient=request.user, pk=notification_id)
        notification.delete()
    # noinspection PyUnresolvedReferences
    return JsonResponse({'unread': request.user.unread_notifications.count()})


def activate(request, uidb64, token):
    """
    This method enable user's account
    """
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = get_object_or_404(get_user_model(), pk=uid)
    except(TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        messages.error(
            request,
            _("Something went wrong when trying to find your account in the database. Aborting.")
        )
    else:
        #  Check the token itself
        if account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(
                request,
                _("%(user)s (%(username)s), your account has been confirmed. You can now log in using the password "
                  "you previously chose.") % {'user': user.get_full_name(), 'username': user.username}
            )
        else:
            messages.error(
                request,
                _("The activation link you provided is broken, or does not correspond to something expected. Please check "
                  "your email in order to find your activation link.")
            )

    #  Anyway, get back to login page
    return redirect("accounts:login")

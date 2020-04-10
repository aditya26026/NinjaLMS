#
# Copyright (C) 2019 Guillaume Bernard <guillaume.bernard@koala-lms.org>
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
import os

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.forms import Form, Select, TextInput
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, gettext
from markdownx.fields import MarkdownxFormField

from learning import logger
from learning.models import Course, Activity, CourseState, CourseAccess, Resource, CollaboratorRole, QuestionCourse, \
    ActivityCollaborator, ResourceCollaborator, Response, CourseCollaborator, RegistrationOnCourse


class UserPKForm(Form):
    """
    A form to process and validate the “user_pk” POST value, referencing a PK.
    """
    user_pk = forms.IntegerField(min_value=1, required=True)


class ActivityPKForm(Form):
    """
    A form to process and validate the “activity” POST value, referencing a PK.
    """
    activity = forms.IntegerField(min_value=1, required=True)


class ResponsePKForm(Form):
    """
        A form to process and validate the “activity” POST value, referencing a PK.
        """
    response = forms.IntegerField(min_value=1, required=True)


class CustomClassesOnFormMixin(Form):
    custom_classes = ["form-control"]

    def __init__(self, *args, **kwargs):
        super(CustomClassesOnFormMixin, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, Select):
                field.widget.attrs.update({'class': 'custom-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        if not self.has_error(NON_FIELD_ERRORS):
            for field_name, field in self.fields.items():
                current_class = field.widget.attrs.get('class', str())
                if field_name in self.errors.as_data():
                    field.widget.attrs.update({'class': current_class + ' ' + 'is-invalid'})
                elif field_name in self.changed_data:
                    field.widget.attrs.update({'class': current_class + ' ' + 'is-valid'})


class FormWithMarkdownFieldMixin(forms.ModelForm):
    description = MarkdownxFormField(
        help_text=_(
            'Write a good description that helps understanding the entity you are describing. Try not to write too '
            'much and express clearly what you mean. Try to avoid ambiguities. You can use the'
            ' <a href="https://www.markdownguide.org/basic-syntax/" target="_blank">Markdown</a>'
            ' syntax here.')
    )

################
# Course forms #
################


course_fields_for_author = ['name', 'description', 'state', 'access', 'language', 'registration_enabled', 'tags']


class CourseFormMixin(CustomClassesOnFormMixin, FormWithMarkdownFieldMixin, forms.ModelForm):
    def clean(self):
        # Check is registration is enabled on a draft course
        registration_enabled = self.cleaned_data.get('registration_enabled', None)
        state = self.cleaned_data.get('state', None)
        if state and registration_enabled:
            if registration_enabled and CourseState[state] == CourseState.DRAFT:
                raise ValidationError(
                    gettext("Registration is not possible on draft course.") + ' ' +
                    gettext("Change the status of the course if you wish to enable registration.")
                )
            if registration_enabled and CourseState[state] == CourseState.ARCHIVED:
                raise ValidationError(
                    gettext("Registration is no longer possible on an archived course.") + ' ' +
                    gettext("Change the status of the course if you wish to enable registration.")
                )

        # Having something published but without access does not have any purpose
        access = self.cleaned_data.get("access", None)
        if access and state:
            if CourseAccess[access] >= CourseAccess.COLLABORATORS_ONLY and CourseState[state] == CourseState.PUBLISHED:
                raise ValidationError(
                    gettext("Level access is collaborators only but course is published. It seems inconsistent.")
                )

        super().clean()

    class Meta:
        model = Course
        fields = ['name', 'description', 'state', 'author', 'access', 'registration_enabled', 'tags']


class CourseCreateForm(CourseFormMixin, forms.ModelForm):

    class Meta:
        model = Course
        fields = course_fields_for_author
        widgets = {
            'name': TextInput(attrs={'placeholder': _("Introduction to Ancient Egypt and Its Civilization")}),
            'tags': TextInput(attrs={'placeholder': _("History, Ancient Egypt, Civilization, Pharaoh ")})
        }


class CourseUpdateFormForOwner(CourseFormMixin, forms.ModelForm):
    """
    Update a course as owner
    """

    class Meta:
        model = Course
        fields = course_fields_for_author


class CourseUpdateForm(CourseFormMixin, forms.ModelForm):
    """
    Update a course without being owner
    """

    class Meta:
        model = Course
        fields = ['name', 'description', 'state', 'tags']


class CourseCollaboratorUpdateRoleForm(CustomClassesOnFormMixin, forms.ModelForm):
    """
    Change the role of a collaborator on a course
    """

    class Meta:
        model = CourseCollaborator
        fields = ['role']


class ActivityCollaboratorUpdateRoleForm(CustomClassesOnFormMixin, forms.ModelForm):
    """
    Change the role of a collaborator on an activity
    """

    class Meta:
        model = ActivityCollaborator
        fields = ['role']


class ResourceCollaboratorUpdateRoleForm(CustomClassesOnFormMixin, forms.ModelForm):
    """
    Change the role of a collaborator on a resource
    """

    class Meta:
        model = ResourceCollaborator
        fields = ['role']


class CourseStudentRegistrationUpdateForm(CustomClassesOnFormMixin, forms.ModelForm):
    class Meta:
        model = RegistrationOnCourse
        fields = ['registration_locked']


class CourseUpdateAdminForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = course_fields_for_author + ['author']


##################
# Activity forms #
##################
activity_fields_for_author = ['name', 'description', 'language', 'access', 'reuse', 'tags']


class ActivityFormMixin(CustomClassesOnFormMixin, FormWithMarkdownFieldMixin, forms.ModelForm):
    pass


class ActivityCreateForm(ActivityFormMixin):

    class Meta:
        model = Activity
        fields = activity_fields_for_author
        widgets = {
            'name': TextInput(attrs={'placeholder': _("Building the Pyramids: hypothesis")}),
            'tags': TextInput(attrs={'placeholder': _("Pyramids, Ancient Egypt, Science, Building")})
        }


class ActivityUpdateForm(ActivityFormMixin):
    class Meta:
        model = Activity
        fields = activity_fields_for_author


class ActivityAdminUpdateForm(forms.ModelForm):
    """
    The admin form allows to change the activity author and collaborators
    """
    class Meta:
        model = Resource
        fields = activity_fields_for_author + ['author']


##################
# Resource forms #
##################
resource_fields_for_author = ['name', 'description', 'type', 'tags', 'language', 'licence', 'access', 'reuse', 'duration', 'media']


def delete_resource_media(resource, form_initial, form_changed_data, cleaned_data):

    def _delete(media_name: str):
        os_path = os.path.join(settings.MEDIA_ROOT, media_name)
        if os.path.isfile(os_path):
            os.remove(os_path)

    #  Delete the media file manually, as Django does not do this automatically.
    if not cleaned_data.get('media'):  # Field is False, media should be removed
        _delete(resource.media.name)

    if 'media' in form_changed_data and form_initial.get('media') and Resource.acceptable_media(cleaned_data.get('media')):
        try:
            _delete(form_initial.get('media').name)
        except OSError as ex:
            logger.error("Deleting media for resource %(resource)s failed (%(cause)s)", {'resource': resource, 'cause': str(ex)})


class ResourceUpdateFormMixin(forms.ModelForm):
    pass


class ResourceCreateForm(CustomClassesOnFormMixin, FormWithMarkdownFieldMixin, forms.ModelForm):

    class Meta:
        model = Resource
        fields = resource_fields_for_author
        widgets = {
            'name': TextInput(attrs={'placeholder': _("BBC Documentary: How the Pyramids?")}),
            'tags': TextInput(attrs={'placeholder': _("BBC, Documentary, Pyramids, Ancient Egypt, Building")})
        }


class ResourceUpdateForm(CustomClassesOnFormMixin, FormWithMarkdownFieldMixin, ResourceUpdateFormMixin):
    class Meta:
        model = Resource
        fields = resource_fields_for_author

    def clean(self):
        delete_resource_media(self.instance, self.initial, self.changed_data, self.cleaned_data)


class ResourceAdminUpdateForm(forms.ModelForm):
    """
    The admin form allows to change the resource author
    """
    class Meta:
        model = Resource
        fields = resource_fields_for_author + ['author']

    def clean(self):
        delete_resource_media(self.instance, self.initial, self.changed_data, self.cleaned_data)


######################################
# Forms to link users with resources #
######################################

class AddUserOn(CustomClassesOnFormMixin, forms.Form):
    """
    Add a user on an object. The available users are shown in the linked user_list element.
    """
    username = forms.CharField(
        label=_('Username'),
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'list': 'user_list', 'placeholder': _("Login, surname, firstname or user email…")})
    )


class AddStudentOnCourseForm(AddUserOn):
    """
    Adding a user on a course only requires the username.
    """
    registration_locked = forms.BooleanField(
        label=_("Locked"),
        help_text=_("Lock registration for the user. This means he will not be able to self-unregister."),
        initial=True,
        required=False
    )


class AddCollaboratorOnBasicModelMixin(AddUserOn):
    """
    When adding a collaborator on a course, the collaborator role is required.
    """
    roles = forms.ChoiceField(
        label=_('Role'),
        choices=[(role.name, role.value) for role in CollaboratorRole]
    )
    propagate = forms.BooleanField(
        label=_("Propagate"),
        help_text=_("Whether to also add the collaborator on all related objects (activities and resources)"),
        required=False
    )


###############
# Search form #
###############


class BasicSearchForm(CustomClassesOnFormMixin):
    query = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _("A title, keywords, tags, topics…")})
    )

#################
# Question form #
#################


question_fields = ['title', 'body']
admin_question_fields = ['course', 'author', 'title', 'body']


class QuestionCourseCreateForm(CustomClassesOnFormMixin, forms.ModelForm):
    """
    When posting a question on a course.
    """
    class Meta:
        model = QuestionCourse
        fields = question_fields


class QuestionCourseAdminCreateForm(CustomClassesOnFormMixin, forms.ModelForm):
    """
    When posting a question on a course.
    """

    class Meta:
        model = QuestionCourse
        fields = admin_question_fields


###############
# Answer form #
###############


response_fields = ['body']
admin_response_fields = ['question', 'author', 'body', 'question']


class ResponseCreateForm(CustomClassesOnFormMixin, forms.ModelForm):
    class Meta:
        model = Response
        fields = response_fields


class ResponseAdminCreateForm(CustomClassesOnFormMixin, forms.ModelForm):
    class Meta:
        model = Response
        fields = admin_response_fields

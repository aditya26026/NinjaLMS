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
from gettext import dgettext

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q
from django.forms import Form
from django.http import HttpResponseNotAllowed, HttpResponseNotFound
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.translation.trans_null import gettext_noop
from django.views.generic import CreateView, UpdateView, DetailView, DeleteView, TemplateView, ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import ProcessFormView, FormView

from learning.exc import LearningError, ChangeActivityOnCourseError, UserIsAlreadyCollaborator, UserIsAlreadyAuthor, \
    UserIsAlreadyStudent
from learning.forms import CourseCreateForm, CourseUpdateFormForOwner, CourseUpdateForm, \
    ActivityCreateForm, AddStudentOnCourseForm, BasicSearchForm, \
    CourseStudentRegistrationUpdateForm, UserPKForm, ActivityPKForm, \
    QuestionCourseCreateForm, ResponseCreateForm, ResponsePKForm
from learning.models import CourseCollaborator, Course, Activity, ActivityReuse, Resource, \
    CourseActivity, RegistrationOnCourse, QuestionCourse, Response
from learning.views.helpers import PaginatorFactory, SearchQuery, InvalidFormHandlerMixin
from learning.views.includes.collaborators import BasicModelDetailCollaboratorsListView, \
    BasicModelDetailCollaboratorsAddView, BasicModelDetailCollaboratorsDeleteView, \
    BasicModelDetailCollaboratorsChangeView


class CourseDetailMixin(PermissionRequiredMixin, SingleObjectMixin):
    """
    Simple Course Mixin to enrich the course detail context with boolean that indicate the role of the current
    user for instance.
    """
    model = Course
    template_name = "learning/course/detail.html"

    # noinspection PyAttributeOutsideInit
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    # noinspection PyUnresolvedReferences
    def has_permission(self) -> bool:
        return self.object.user_can_view(self.request.user)

    # noinspection PyUnresolvedReferences
    def __user_can_register(self) -> bool:
        return self.request.user != self.object.author and \
            self.request.user not in self.object.collaborators.all() and \
            self.object.can_register

    # noinspection PyUnresolvedReferences
    def __user_is_teacher(self) -> bool:
        return self.request.user == self.object.author or \
            self.request.user in self.object.collaborators.all()

    # noinspection PyUnresolvedReferences
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_can_register'] = self.__user_can_register()

        if self.request.user.is_authenticated:
            if self.request.user in self.object.collaborators.all():
                context["contribution"] = CourseCollaborator.objects \
                    .get(collaborator=self.request.user, course=self.object)
            registration = self.object.registrations.filter(
                student=self.request.user)
            context['user_is_student'] = registration.exists()
            if context.get('user_is_student', False):
                context['registration'] = registration.get()
            context['user_is_teacher'] = self.__user_is_teacher()
        return context


class CourseDetailView(CourseDetailMixin, PermissionRequiredMixin, DetailView):
    def handle_no_permission(self):
        messages.error(self.request, _(
            "You do not have the required permissions to view this course."))
        return super().handle_no_permission()


class CourseCreateView(LoginRequiredMixin, InvalidFormHandlerMixin, CreateView):
    model = Course
    form_class = CourseCreateForm
    template_name = "learning/course/add.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, _('Course “%(course)s” created.') % {
                         'course': form.instance.name})
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("learning:course/detail", kwargs={'slug': self.object.slug})


class CourseUpdateViewMixin(LoginRequiredMixin, CourseDetailMixin):
    """
       Mixin to update a course.

       .. caution:: Updating a course requires the **change_course** permission.
    """

    # noinspection PyUnresolvedReferences
    def has_permission(self):
        return self.object.user_can_change(self.request.user)

    # noinspection PyUnresolvedReferences
    def handle_no_permission(self):
        messages.error(self.request, _(
            "You do not have the required permissions to change this course."))
        return super().handle_no_permission()


class CourseUpdateView(CourseUpdateViewMixin, InvalidFormHandlerMixin, UpdateView):
    """
    Update a course in a HTML page. The form shown to the user depends on its role on the course. Standard editors
    will not be able to perform administration tasks (like changing privacy) whereas the owner will have this
    possibility.
    """
    form_class = CourseUpdateForm
    template_name = "learning/course/details/change.html"

    def get_form_class(self):
        if self.object.user_can("change_privacy", self.request.user):
            self.form_class = CourseUpdateFormForOwner
        return self.form_class

    def form_valid(self, form):
        if form.has_changed():
            messages.success(
                self.request, _('The course “%(course)s” has been updated.') % {
                    'course': self.object.name}
            )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('learning:course/detail', kwargs={'slug': self.object.slug})


class CourseDeleteViewMixin(LoginRequiredMixin, CourseDetailMixin, DeleteView):
    """
    Mixin to delete a course

    .. caution:: Deleting a course requires the **delete_course** permission.
    """

    # noinspection PyAttributeOutsideInit
    def has_permission(self):
        return self.object.user_can_delete(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, _(
            "You do not have the required permissions to delete this course."))
        super().handle_no_permission()


class CourseDeleteView(LoginRequiredMixin, CourseDetailMixin, DeleteView):
    """
    Delete a course in a HTML page.
    """
    success_url = reverse_lazy('learning:course/teaching')
    template_name = 'learning/course/delete.html'

    def get_success_url(self):
        messages.success(
            self.request, _('The course ”%(course)s” has been deleted') % {
                'course': self.object.name}
        )
        return super().get_success_url()


class CourseAsTeacherListView(LoginRequiredMixin, FormView):
    """
    List courses as a teacher. Thus, it includes courses the user manages as their author, and courses on
    which the user collaborates.
    """
    template_name = 'learning/course/teaching.html'
    form_class = BasicSearchForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add the paginator on courses where user is author
        context.update(PaginatorFactory.get_paginator_as_context(
            Course.objects.written_by(self.request.user), self.request.GET, prefix="author", nb_per_page=6)
        )

        # Add the paginator on courses where user is a collaborator
        context.update(PaginatorFactory.get_paginator_as_context(
            CourseCollaborator.objects.filter(collaborator=self.request.user), self.request.GET, prefix="contributor", nb_per_page=6)
        )

        # Execute the user query and add the paginator on query
        form = BasicSearchForm(data=self.request.GET)
        if form.is_valid() and form.cleaned_data.get('query', str()):
            context.update(PaginatorFactory.get_paginator_as_context(Course.objects.taught_by(
                self.request.user, query=form.cleaned_data.get('query', str())
            ).all(), self.request.GET, prefix="search"))

        # Add the query form in the view
        context['form'] = form
        return context


class CourseAsStudentListView(LoginRequiredMixin, ListView):
    """
    List courses on which the user is registered has a student
    """
    template_name = "learning/course/student.html"
    paginate_by = 6

    def get_queryset(self):
        return Course.objects.followed_by(self.request.user)


class CourseDetailActivitiesView(CourseDetailView):
    """
    View activities presented for students. This is a paginator for which a page contains only one activity.
    """
    template_name = "learning/course/details/activities.html"

    # noinspection PyAttributeOutsideInit
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.course_activities.count() > 0:
            return super().dispatch(request, *args, **kwargs)
        messages.warning(request, _(
            "This course does not have any activity yet."))
        return redirect('learning:course/detail', slug=self.object.slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the activity into the context
        if 'activity_slug' in self.kwargs.keys():
            course_activity = get_object_or_404(
                CourseActivity, activity__slug=self.kwargs.get('activity_slug'), course=self.object
            )
        else:
            course_activity = self.object.course_activities.first()
        context['current_course_activity'] = course_activity

        # Add previous and next activities in the context
        context['next_course_activity'] = CourseActivity.objects.filter(
            course=self.object, rank=course_activity.rank + 1
        ).first()
        context['previous_course_activity'] = CourseActivity.objects.filter(
            course=self.object, rank=course_activity.rank - 1
        ).first()
        return context


class CourseDetailActivityResourceView(CourseDetailView):
    """
    View a specific resource on an activity.
    """
    template_name = "learning/course/details/activity_resource.html"

    # noinspection PyAttributeOutsideInit
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.activity = get_object_or_404(
            Activity, slug=self.kwargs.get('activity_slug'))
        self.resource = get_object_or_404(
            Resource, slug=self.kwargs.get('resource_slug'))
        if self.object.course_activities.filter(activity=self.activity).exists() and \
                self.activity.resources.filter(id=self.resource.id).exists():
            return self.get(request, args, kwargs)
        return HttpResponseNotFound()

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['activity'] = self.activity
        context['resource'] = self.resource
        return context


class CourseDetailCollaboratorsListView(BasicModelDetailCollaboratorsListView, CourseDetailMixin):
    """
    View collaborators on a course in a HTML page.
    """
    template_name = "learning/course/details/collaborators.html"


class CourseDetailCollaboratorsAddView(BasicModelDetailCollaboratorsAddView, CourseDetailMixin):
    """
    Add a collaborator on a course in a HTML page.
    """
    success_url = "learning:course/detail/collaborators"


class CourseDetailCollaboratorsChangeView(BasicModelDetailCollaboratorsChangeView, CourseDetailMixin):
    """
    Change a collaborator on a course in a HTML page.
    """
    success_url = "learning:course/detail/collaborators"


class CourseDetailCollaboratorsDeleteView(BasicModelDetailCollaboratorsDeleteView, CourseDetailMixin):
    """
    Delete a collaborator from a course in a HTML page.
    """
    success_url = "learning:course/detail/collaborators"


class CourseDetailStudentViewMixin(LoginRequiredMixin, CourseDetailView):
    """
    Mixin to view students registered on a course.

    .. note:: Viewing students registered on a course requires the **view_students** permission.
    """

    def has_permission(self):
        return self.object.user_can("view_students", self.request.user) and super().has_permission()

    def handle_no_permission(self):
        messages.error(self.request, _(
            "You do not have the required permissions to view students of this course."))
        return super().handle_no_permission()


class CourseDetailStudentsView(CourseDetailStudentViewMixin, FormView):
    """
    View students registered on a course in a HTML page.
    """
    form_class = AddStudentOnCourseForm
    template_name = "learning/course/details/students.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            PaginatorFactory.get_paginator_as_context(
                self.object.registrations.order_by(
                    'student__last_login').all(),
                self.request.GET, nb_per_page=10)
        )
        return context


class CourseDetailStudentsAddViewMixin(LoginRequiredMixin, CourseDetailMixin):
    """
    Mixin to register a student on a course.

    .. note:: Adding a student on a course requires the **add_student** permission..
    """

    # noinspection PyUnresolvedReferences
    def has_permission(self):
        return self.object.user_can("add_student", self.request.user) and super().has_permission()

    # noinspection PyUnresolvedReferences
    def handle_no_permission(self):
        messages.error(self.request, _(
            "You do not have the required permissions to add a student on this course."))
        return super().handle_no_permission()


class CourseDetailStudentsAddView(CourseDetailStudentsAddViewMixin, InvalidFormHandlerMixin, FormView):
    """
    Register a student on a course in a HTML page.
    """
    form_class = AddStudentOnCourseForm

    # noinspection PyAttributeOutsideInit
    def form_valid(self, form):
        self.object = self.get_object()
        username = form.cleaned_data.get('username', None)
        locked = form.cleaned_data.get('registration_locked', True)
        try:
            user = get_user_model().objects.filter(username=username).get()
            self.object.register_student(user, locked)
            messages.success(self.request, _(
                '%(user)s is now registered on this course.') % {'user': user})
        except ObjectDoesNotExist:
            messages.error(self.request,
                           _("The user identified by %(username)s does not exists.") % {'username': username})
        except (UserIsAlreadyStudent, UserIsAlreadyCollaborator, UserIsAlreadyAuthor) as ex:
            messages.warning(self.request, ex)
        except LearningError as ex:
            messages.error(self.request, ex)
        return redirect("learning:course/detail/students", slug=self.object.slug)

    def form_invalid(self, form):
        super().form_invalid(form)
        return redirect("learning:course/detail/students", slug=self.object.slug)


class CourseDetailStudentChangeViewMixin(LoginRequiredMixin, CourseDetailMixin):
    """
    Mixin to change a student on a course

    .. caution:: Changing a student on a course requires the **change_student** permission.
    """

    # noinspection PyUnresolvedReferences
    def has_permission(self):
        return self.object.user_can("change_student", self.request.user) and super().has_permission()

    # noinspection PyUnresolvedReferences
    def handle_no_permission(self):
        messages.error(self.request, _(
            "You do not have the required permissions to change a student on this course."))
        return super().handle_no_permission()


class CourseDetailStudentChangeView(CourseDetailStudentChangeViewMixin, InvalidFormHandlerMixin, ProcessFormView):
    """
    Change a student on a course in a HTML page.
    """

    class RegistrationPKForm(Form):
        registration_pk = forms.IntegerField(min_value=1, required=True)

    def post(self, request, *args, **kwargs):
        registration_pk_form = self.RegistrationPKForm(
            self.request.POST or None)
        if registration_pk_form.is_valid():
            registration = get_object_or_404(
                RegistrationOnCourse, pk=registration_pk_form.cleaned_data.get('registration_pk'))
            form = CourseStudentRegistrationUpdateForm(
                self.request.POST, instance=registration)
            if form.is_valid():
                self.form_valid(form)
            else:
                self.form_invalid(form)
            return self.get_success_url()
        return HttpResponseNotFound(_("The given registration primary key is invalid. It this intentional?"))

    def form_valid(self, form):
        form.instance.save()
        if form.instance.registration_locked:
            messages.success(
                self.request,
                _('Registration is now locked for %(user)s. This user will not be able to unregister.')
                % {'user': form.instance.student}
            )
        else:
            messages.success(
                self.request,
                _('%(user)s now can unregister by itself from this course.')
                % {'user': form.instance.student}
            )

    def get_success_url(self):
        return redirect("learning:course/detail/students", slug=self.object.slug)


class CourseDetailStudentsDeleteViewMixin(LoginRequiredMixin, CourseDetailMixin):
    """
    Mixin to unregister a student on a course

    .. caution:: Unregistering a student on a course requires the **delete_student** permission.
    """

    # noinspection PyUnresolvedReferences
    def has_permission(self):
        return self.object.user_can("delete_student", self.request.user) and super().has_permission()

    # noinspection PyUnresolvedReferences
    def handle_no_permission(self):
        messages.error(
            self.request, _(
                "You do not have the required permissions to unregister a student from this course.")
        )
        return super().handle_no_permission()


class CourseDetailStudentsDeleteView(CourseDetailStudentsDeleteViewMixin, ProcessFormView):
    """
    Unregister a student from a course.
    """

    def post(self, request, *args, **kwargs):
        user_pk_form = UserPKForm(self.request.POST or None)
        if user_pk_form.is_valid():
            student = get_object_or_404(
                get_user_model(), pk=user_pk_form.cleaned_data.get('user_pk'))
            self.object.unsubscribe_student(student)
            messages.success(
                self.request,
                _("The student “%(student)s” has been unregistered from the course “%(course)s”.")
                % {'course': self.object, 'student': student}
            )
            return redirect("learning:course/detail/students", slug=self.object.slug)
        return HttpResponseNotFound(user_pk_form.errors.get('user_pk'))

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(['POST'])


class CourseDetailSimilarViewMixin(LoginRequiredMixin, CourseDetailView):
    """
    Mixin to view courses that are similar to the current one.

    .. caution:: Viewing similar courses requires the **view_similar** permission.
    """

    def has_permission(self):
        return self.object.user_can("view_similar", self.request.user) and super().has_permission()

    def handle_no_permission(self):  # pragma: no cover
        messages.error(self.request, _(
            "You do not have the required permissions to view similar courses."))
        return super().handle_no_permission()


class CourseDetailSimilarView(CourseDetailSimilarViewMixin):
    """
    View courses that are similar to the current one.

    .. note:: This requires the permission to view similar courses and to view the course itself.
    """
    template_name = "learning/course/details/similar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # noinspection PyBroadException
        try:
            similar_list = [
                similar for similar in self.object.tags.similar_objects()
                if isinstance(similar, Course) and similar.user_can_view(self.request.user)
            ]
            context.update(PaginatorFactory.get_paginator_as_context(
                similar_list, self.request.GET, nb_per_page=9))
        # django-taggit similar tags can have weird behaviour sometimes: https://github.com/jazzband/django-taggit/issues/80
        except Exception:
            messages.error(self.request, _(
                "The component used to detect similar courses crashed. We try to fix this as soon as possible."))
        return context


class CourseRegisterView(LoginRequiredMixin, CourseDetailView, FormView):
    """
    Register the current user on the course.
    """

    # noinspection PyUnusedLocal
    def post(self, request, *args, **kwargs):
        try:
            self.object.register(request.user)
            messages.success(
                request, _("You have been registered on the course “%(course)s”") % {
                    'course': self.object}
            )
        except LearningError as ex:
            messages.error(request, ex)
        return redirect("learning:course/detail", slug=self.object.slug)

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(['POST'])


class CourseUnregisterView(LoginRequiredMixin, CourseDetailView, FormView):
    """
    Unsubscribe the current user from the course.
    """

    # noinspection PyUnusedLocal
    def post(self, request, *args, **kwargs):
        try:
            self.object.unsubscribe(request.user)
            messages.success(
                request, _("You have been unregistered from the course “%(course)s”") % {
                    'course': self.object}
            )
        except LearningError as ex:
            messages.error(request, ex)
        return redirect("learning:course/detail", slug=self.object.slug)

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(['POST'])


class CourseSearchView(TemplateView):
    """
    Search for a specific course.
    """
    template_name = "learning/course/search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Show the user some recommended courses, based on its profile
        if self.request.user.is_anonymous:
            queryset = Course.objects.all()
        else:
            queryset = Course.objects.recommendations_for(
                self.request.user).all()

        context.update(PaginatorFactory.get_paginator_as_context(
            queryset, self.request.GET, prefix="recommended", nb_per_page=9)
        )

        context.update(SearchQuery.search_query_as_context(
            Course, self.request.GET))
        return context


class ActivityCreateOnCourseViewMixin(LoginRequiredMixin, CourseDetailMixin):
    """
    Mixin to create an activity on a course.

    .. caution:: Adding an activity on a course implies you have the **change** permission and it’s not read-only.
    """

    # noinspection PyUnresolvedReferences
    def has_permission(self):
        return self.object.user_can_change(self.request.user) and not self.object.read_only

    # noinspection PyUnresolvedReferences
    def handle_no_permission(self):
        messages.error(
            self.request,
            _("You do not have the required permissions to change this course. "
              "It may be read-only because archived or you may not have the rights to edit the course.")
        )
        return super().handle_no_permission()


class ActivityAttachOnCourseViewMixin(ActivityCreateOnCourseViewMixin):
    """
    Mixin to attach an activity on a course.

    .. caution:: Adding an activity on a course implies you have the **change** permission and it’s not read-only.
    """

    # noinspection PyUnresolvedReferences
    def handle_no_permission(self):
        messages.warning(
            self.request, _(
                "You do not have the required permission to attach an activity on this course.")
        )
        return super().handle_no_permission()


class ActivityCreateOnCourseView(ActivityCreateOnCourseViewMixin, InvalidFormHandlerMixin, UpdateView):
    """
    View to create a new activity and automatically link it with the current course.

    .. note:: This requires the right to change the course, and implies the course is not read-only (can be edited)
    .. note:: This implies that data from the CourseActivity and Activity models are presented in two separated forms.
    """
    template_name = "learning/course/details/add_activity_on_course.html"

    def get_form(self, form_class=None):
        if self.request.POST:
            return ActivityCreateForm(self.request.POST)
        return ActivityCreateForm()

    def form_valid(self, form):
        activity = form.instance  # Extract form instances
        # Manually set the activity author to the current user
        activity.author = self.request.user
        try:
            self.object.add_activity(activity)
            messages.success(
                self.request,
                _('The activity “%(activity)s” has been added to this course.') % {
                    'activity': activity.name}
            )
            return redirect("learning:course/detail", slug=self.object.slug)
        except LearningError as ex:
            messages.error(self.request, ex)
            return self.form_invalid(form)

    def form_invalid(self, form):
        super().form_invalid(form)
        context = super().get_context_data()
        context.update({'course': self.object, 'form': self.get_form()})
        return render(self.request, self.template_name, context)


class ActivityAttachOnCourseView(ActivityAttachOnCourseViewMixin, FormView):
    template_name = "learning/course/details/attach_activity.html"
    form_class = BasicSearchForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        basic_queryset = Activity.objects.exclude(
            # activities already linked with the course
            course_activities__course=self.object
        ).exclude(
            # activities that are not reusable
            reuse=ActivityReuse.NON_REUSABLE.name,
        ).exclude(
            # activities that can only be reused by their respective authors
            Q(reuse=ActivityReuse.ONLY_AUTHOR.name) & ~Q(
                author=self.object.author)
        )

        # Suggestion for new activities
        context.update(PaginatorFactory.get_paginator_as_context(
            basic_queryset.all(), self.request.GET, prefix="suggested", nb_per_page=6)
        )

        # User may query some words using the search filter
        form = BasicSearchForm(data=self.request.GET)
        if form.is_valid() and form.cleaned_data.get('query', str()):
            query = form.cleaned_data.get('query', str())
            context.update(PaginatorFactory.get_paginator_as_context(
                basic_queryset.filter(
                    Q(name__icontains=query) | Q(description__icontains=query)
                ).all(), self.request.GET, prefix="search", nb_per_page=6)
            )

        # Add the query form in the view
        context['form'] = form
        return context

    # noinspection PyAttributeOutsideInit
    def post(self, request, *args, **kwargs):
        activity_pk_form = ActivityPKForm(self.request.POST or None)
        if activity_pk_form.is_valid():
            activity = get_object_or_404(
                Activity, pk=activity_pk_form.cleaned_data.get('activity'))
            try:
                self.object.add_activity(activity)
                messages.success(
                    self.request,
                    _('Activity “%(activity)s” added to the course “%(course)s”')
                    % {'activity': activity, 'course': self.object}
                )
            except LearningError as ex:
                messages.error(self.request, ex)
            return redirect("learning:course/detail/activity/attach", slug=self.object.slug)
        return HttpResponseNotFound(activity_pk_form.errors.get('activity'))


@login_required
def activity_on_course_up_view(request, slug):
    """
    Increase by 1 point the rank of the activity on the course.

    .. caution:: Changing the order or activities in a course requires the **change_course** permission.
    .. important:: The activity to change is given as a POST parameter called **activity** and contains the resource
    primary key.

    :param request: django request object
    :type request: django.http.HttpRequest
    :param slug: course slug
    :type slug: str
    :return: the course detail view
    """
    if request.method == "POST":
        # Retrieve objects : course, activity, the current course activity
        course = get_object_or_404(Course, slug=slug)

        if course.user_can_change(request.user):
            activity_pk_form = ActivityPKForm(request.POST or None)
            if activity_pk_form.is_valid():
                activity = get_object_or_404(
                    Activity, pk=activity_pk_form.cleaned_data.get('activity'))
                course_activity = get_object_or_404(
                    CourseActivity, course=course, activity=activity)
                previous_course_activity = get_object_or_404(CourseActivity, course=course,
                                                             rank=course_activity.rank - 1)

                # Switch course activity ranks
                course_activity.rank = previous_course_activity.rank
                previous_course_activity.rank += 1

                # Save objects
                course_activity.save()
                previous_course_activity.save()

                messages.success(
                    request,
                    _("Activity “%(activity)s” was repositioned and is now the activity n°%(rank)d on this course.")
                    % {'activity': activity, 'rank': course_activity.rank}
                )
                return redirect("learning:course/detail", slug=course.slug)
            return HttpResponseNotFound(activity_pk_form.errors.get('activity'))

        # User cannot change the course
        messages.error(request, _(
            "You do not have the required permission to change activities of this course."))
        raise PermissionDenied()

    # Method used is not POST, so it’s not allowed
    return HttpResponseNotAllowed(['POST'])


# noinspection PyUnresolvedReferences
@login_required
def activity_on_course_unlink_view(request, slug):
    """
    Unlink an activity from a course. This means the activity will no longer be attached to the course. The activity
    is not removed.

    .. caution:: Changing the activities in a course requires the **change_course** permission.
    .. important:: The activity to change is given as a POST parameter called **activity** and contains the resource primary key.

    :param request: django request object
    :type request: django.http.HttpRequest
    :param slug: course slug
    :type slug: str
    :return: the course detail view
    """
    if request.method == "POST":
        course = get_object_or_404(Course, slug=slug)
        if course.user_can_change(request.user):
            # noinspection PyCallByClass
            activity_pk_form = ActivityPKForm(request.POST or None)
            if activity_pk_form.is_valid():
                activity = get_object_or_404(
                    Activity, pk=activity_pk_form.cleaned_data.get('activity'))
                try:
                    course.remove_activity(activity)
                    messages.success(request, _("The activity “%(activity)s” has been removed from this course. "
                                                "The activity itself has not been removed.") % {'activity': activity})
                except ChangeActivityOnCourseError as ex:
                    messages.error(request, ex)
                return redirect("learning:course/detail", slug=course.slug)
            return HttpResponseNotFound(activity_pk_form.errors.get('activity'))

        # Not permission to change the course
        messages.error(
            request,
            _("You do not have the required permissions to unlink this activity from this course.")
        )
        raise PermissionDenied()

    # Method is not allowed
    return HttpResponseNotAllowed(['POST'])


# noinspection PyUnresolvedReferences
@login_required
def activity_on_course_delete_view(request, slug):
    """
    Delete an activity which is currently attached to a course. The link between the activity and the course
    will be removed, as well as the activity itself.

    .. caution:: Changing the activities in a course requires the **change_course** permission.
    .. important:: The activity to change is given as a POST parameter called **activity** and contains the resource primary key.

    :param request: django request object
    :type request: django.http.HttpRequest
    :param slug: course slug
    :type slug: str
    :return: the course detail view
    """
    if request.method == "POST":
        course = get_object_or_404(Course, slug=slug)
        activity_pk_form = ActivityPKForm(request.POST or None)
        if activity_pk_form.is_valid():
            activity = get_object_or_404(
                Activity, pk=activity_pk_form.cleaned_data.get('activity'))
            if course.user_can_change(request.user) and activity.user_can_delete(request.user):
                try:
                    course.remove_activity(activity)
                    activity.delete()
                    messages.success(request, _("The activity “%(activity)s” has been removed from this course. "
                                                "The activity has also been removed.") % {'activity': activity})
                except ChangeActivityOnCourseError as ex:
                    messages.error(request, ex)
                return redirect("learning:course/detail", slug=course.slug)
            # Not permission to change delete the activity
            messages.error(request, _(
                "You do not have the required permissions to delete this activity."))
            raise PermissionDenied()

        return HttpResponseNotFound(activity_pk_form.errors.get('activity'))

    # Method is not allowed
    return HttpResponseNotAllowed(['POST'])


class CourseDetailAgoraAddView(LoginRequiredMixin, CourseDetailMixin, InvalidFormHandlerMixin, FormView):
    """
    View to add a new question in the Agora and automatically link it with the current course.

    .. note:: This requires the right to view the course
    """
    template_name = "learning/course/details/agora/add_question_on_course.html"
    form_class = QuestionCourseCreateForm

    # noinspection PyAttributeOutsideInit
    def form_valid(self, form):
        question = form.instance
        question.author = self.request.user
        question.course = self.object
        question.save()
        messages.success(
            self.request,
            _('The question “%(question)s” has been added to the agora.') % {
                'question': question.title}
        )
        self.question = question
        #  Notify the course owner that a question has been add to the couse agora
        print("bla")
        self.object.author.notify(
            gettext_noop("A question has just been asked in the agora for your course “%(course)s”.") % {
                'course': self.object},
            target=self.get_success_url()
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "learning:course/detail/question",
            kwargs={'slug': self.object.slug,
                    'question_slug': self.question.slug}
        )


class CourseDetailAgoraQuestionAnswerView(LoginRequiredMixin, CourseDetailMixin, InvalidFormHandlerMixin, FormView):
    """
    View to add a new answer in a question page and automatically link it with the current question.
    :param request: django request object
    :type request: django.http.HttpRequest
    .. note:: This requires the right to view the course

    """
    template_name = "learning/course/details/agora/question_detail.html"
    form_class = ResponseCreateForm

    # noinspection PyAttributeOutsideInit
    def dispatch(self, request, *args, **kwargs):
        self.question = get_object_or_404(
            QuestionCourse, slug=self.kwargs.get('question_slug', None))
        return super().dispatch(request, *args, **kwargs)

    def has_permission(self) -> bool:
        return super().has_permission() and \
            self.object.user_can_view(self.request.user) and self.question.user_can(
                "reply", self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['question'] = get_object_or_404(
            QuestionCourse, slug=self.kwargs.get('question_slug', None))
        return context

    def form_valid(self, form):
        response = form.instance
        response.author = self.request.user
        response.question = self.question
        response.save()
        self.object.author.notify(
            dgettext(
                self.object.author.preferred_language,
                "Someone has just replied to your question “%(question)s” on “%(course)s”.") % {
                'question': self.question, 'course': self.object
            },
            target=self.get_success_url()
        )
        messages.success(self.request, _(
            'The answer has been added in the agora.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "learning:course/detail/question", kwargs={'slug': self.object.slug, 'question_slug': self.question.slug}
        )


class CourseDetailAgoraView(LoginRequiredMixin, CourseDetailMixin, FormView):
    """
    View question who are related with the current course.

    .. note:: This requires the right to view the course
    """
    form_class = QuestionCourseCreateForm
    template_name = "learning/course/details/agora/agora.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            PaginatorFactory.get_paginator_as_context(
                self.object.registrations.order_by(
                    'student__last_login').all(),
                self.request.GET, nb_per_page=10)
        )
        return context


class CourseDetailAgoraQuestionAnswerVote(InvalidFormHandlerMixin, CourseDetailMixin, FormView):
    """
       Vote for a response to a question, the behave depends on whether the user already voted for that question. Is so
       the vote is removed. Otherwise, vote is added.

       .. note:: This requires the right to view the question
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['response'] = get_object_or_404(
            Response, slug=self.kwargs.get('response', None))
        context['question'] = get_object_or_404(
            QuestionCourse, slug=self.kwargs.get('question_slug', None))
        return context

    def post(self, request, *args, **kwargs):
        response_pk_form = ResponsePKForm(request.POST or None)
        question_course = get_object_or_404(
            QuestionCourse, slug=self.kwargs.get('question_slug', None))
        response = get_object_or_404(
            Response, pk=response_pk_form.data.get('response'))
        response.handle_vote(self.request.user)
        return redirect(reverse_lazy(
            "learning:course/detail/question", kwargs={'slug': self.object.slug, 'question_slug': question_course.slug}
        ))

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(['POST'])

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

from django.contrib import admin
from django.contrib.admin import TabularInline, ModelAdmin

from learning.forms import CourseUpdateAdminForm, ActivityAdminUpdateForm, ResourceAdminUpdateForm, \
    QuestionCourseAdminCreateForm
from learning.models import Course, Activity, CourseActivity, CourseCollaborator, Resource, RegistrationOnCourse, \
    ActivityCollaborator, ResourceCollaborator, QuestionCourse, Response


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    """
     Inheriting from GuardedModelAdmin just adds access to per-object
     permission management tools. This can be replaced by ModelAdmin at any
     time.
    """

    class CourseActivityInline(TabularInline):
        model = CourseActivity
        extra = 0

    class CourseCollaboratorsInline(TabularInline):
        model = CourseCollaborator
        readonly_fields = ('created', 'updated',)
        extra = 0

    class RegistrationOnCourseInline(TabularInline):
        model = RegistrationOnCourse
        readonly_fields = ('created', 'updated', 'self_registration')
        extra = 0

    form = CourseUpdateAdminForm
    list_display = ('id', 'name', 'state', 'author', 'published', 'updated')
    list_display_links = ('id', 'name')
    list_filter = ('published', 'state')
    readonly_fields = ('slug',)

    inlines = [
        RegistrationOnCourseInline,
        CourseCollaboratorsInline,
        CourseActivityInline,
    ]

    def save_formset(self, request, form, formset, change):
        super(CourseAdmin, self).save_formset(request, form, formset, change)
        # When CourseActivity objects are added, they may not be in proper order, or with gaps
        # between ranks. Calling save again will ensure they are ordered properly
        form.instance.reorder_course_activities()


@admin.register(Activity)
class ActivityAdmin(ModelAdmin):
    form = ActivityAdminUpdateForm
    list_display = ('id', 'name', 'author', 'published', 'updated')
    list_display_links = ('id', 'name')
    readonly_fields = ('slug',)

    class ActivityCollaboratorsInline(TabularInline):
        model = ActivityCollaborator
        readonly_fields = ('created', 'updated',)
        extra = 0

    inlines = [
        ActivityCollaboratorsInline,
    ]


@admin.register(Resource)
class ResourceAdmin(ModelAdmin):
    form = ResourceAdminUpdateForm
    list_display = ('id', 'name', 'type', 'author', 'published', 'updated')
    list_display_links = ('id', 'name')
    list_filter = ('type', 'published')
    readonly_fields = ('slug',)

    class ResourceCollaboratorsInline(TabularInline):
        model = ResourceCollaborator
        readonly_fields = ('created', 'updated',)
        extra = 0

    inlines = [
        ResourceCollaboratorsInline,
    ]


@admin.register(QuestionCourse)
class QuestionCourseAdmin(ModelAdmin):
    form = QuestionCourseAdminCreateForm
    list_display = ('id', 'title', 'course', 'author', 'created')
    list_display_links = ('id', 'title')

    class ResponseOnQuestionCourseInline(TabularInline):
        model = Response
        readonly_fields = ('created', 'updated')
        extra = 0

    inlines = [
        ResponseOnQuestionCourseInline
    ]

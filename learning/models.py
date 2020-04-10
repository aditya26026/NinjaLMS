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
import abc
import itertools
import os
from enum import Enum
from typing import Generator

from django.conf import global_settings, settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max, QuerySet, Q
from django.template.defaultfilters import filesizeformat
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _, gettext_noop
from django.utils.translation import pgettext_lazy
from taggit.managers import TaggableManager

import learning.exc
from learning import logger
from learning.permissions import ObjectPermissionManagerMixin

# Translate course, activity or resource in order to use them dynamically
gettext_noop('course')
gettext_noop('resource')
gettext_noop('activity')


def get_max_upload_size():
    try:
        upload_size = settings.LEARNING_UPLOAD_SIZE
    except AttributeError:
        upload_size = 2**20  # 1Mio
    return upload_size


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


def generate_slug_for_model(model, instance):
    """
    Generate a slug value for a specific instance. It is made to avoid duplicates, as slugs are unique. \
    In case of two instance having the same slug_value, hence the same slug, a counter is added at the end \
    of the slug.

    :param model: the concrete model of the instance
    :type model: class
    :param instance: an instance of a ObjectWithSlugMixin
    :type instance: ObjectWithSlugMixin
    :return: a slug made from the instance
    :rtype: str
    """
    max_length = model._meta.get_field('slug').max_length
    slug = instance.slug = original_slug = slugify(instance.slug_generator())[:max_length]

    # If necessary, add an index (1, 2, etc.) to the slug field if another Resource exists
    # with the same slug
    for counter in itertools.count(1):
        # noinspection PyUnresolvedReferences
        if not model.objects.filter(slug=slug).exclude(pk=instance.id).exists():
            break  # The slug is not used by another resource
        slug = "{slug}-{counter}".format(slug=original_slug[:max_length - len(str(counter)) - 1], counter=counter)
    return slug


class OrderedEnum(Enum):
    """
    Special enumeration which can has ordered elements. Each literal has a weight which is used to compare with others.

    .. warning:: Literals are tuples with a value and a weight, like:
        A = ('A', 0)
        B = ('B', 1
    """

    # pylint: disable=unused-argument
    # noinspection PyUnusedLocal
    def __init__(self, token, weight):
        self.__weight = weight

    @property
    def weight(self):
        return self.__weight

    @property
    def value(self):
        return super().value[0]

    def __eq__(self, other):
        return self.weight == other.weight

    def __lt__(self, other):
        return self.weight < other.weight

    def __gt__(self, other):
        return self.weight > other.weight

    def __le__(self, other):
        return self.weight <= other.weight

    def __ge__(self, other):
        return self.weight >= other.weight


class Licences(OrderedEnum):
    CC_0 = (_("Creative Commons 0 (Public domain)"), 0)
    CC_BY = (_("Creative Commons Attribution"), 1)
    CC_BY_SA = (_("Creative Commons Attribution, Share Alike"), 2)
    CC_BY_NC = (_("Creative Commons Attribution, Non Commercial"), 3)
    CC_BY_NC_SA = (_("Creative Commons Attribution, Non Commercial, Share Alike"), 4)
    CC_BY_ND = (_("Creative Commons Attribution, No Derivatives"), 5)
    CC_BY_NC_ND = (_("Creative Commons Attribution, No Commercial, No Derivatives"), 6)
    NA = (_("Not appropriate"), 7)
    ALL_RIGHTS_RESERVED = (_("All rights reserved"), 8)


class Duration(OrderedEnum):
    FIVE_OR_LESS = (_("Less than 5 minutes"), 0)
    TEN_OR_LESS = (_("Less than 10 minutes"), 0)
    FIFTEEN_OR_LESS = (_("Less than 15 minutes"), 1)
    TWENTY_OR_LESS = (_("Less than 20 minutes"), 1)
    TWENTY_FIVE_OR_LESS = (_("Less than 25 minutes"), 2)
    THIRTY_OR_MORE = (_("30 minutes or more"), 2)
    NOT_SPECIFIED = (_("Not specified"), 3)


class ResourceAccess(OrderedEnum):
    PUBLIC = (_("Public"), 0)
    EXISTING_ACTIVITIES = (_("Only in activities"), 1)
    COLLABORATORS_ONLY = (_("Collaborators only"), 2)
    PRIVATE = (_("Private"), 3)


class ResourceReuse(OrderedEnum):
    NO_RESTRICTION = (_("Reusable"), 0)
    ONLY_AUTHOR = (_("Author only"), 1)
    NON_REUSABLE = (_("Non reusable"), 2)


class ResourceType(Enum):
    FILE = (_("File"), "fa-file-alt")
    VIDEO = (_("Video"), "fa-video")
    AUDIO = (_("Audio"), "fa-broadcast-tower")

    # noinspection PyUnusedLocal
    # pylint: disable=unused-argument
    def __init__(self, i18n_str, fa_icon):
        self.__icon = fa_icon

    @property
    def icon(self):  # pragma: no cover
        return self.__icon

    @property
    def value(self):
        return super().value[0]


class ObjectWithSlugMixin:
    """
    This class is obsolete but required because referenced in migrations.
    """


class CollaboratorRole(Enum):
    TEACHER = _("Teacher")
    NON_EDITOR_TEACHER = _("Non-editor Teacher")
    OWNER = _("Owner")


PERMISSIONS_FOR_ROLE = {
    "students": ["view", "view_similar"],
    CollaboratorRole.TEACHER.name: [
        "view", "view_hidden", "view_similar", "add", "change", "view_collaborators", "view_students", "add_student",
        "change_student", "delete_student",
    ],
    CollaboratorRole.NON_EDITOR_TEACHER.name: [
        "view", "view_hidden", "view_similar", "view_collaborators", "view_students",
    ],
    CollaboratorRole.OWNER.name: [
        "view", "view_hidden", "view_similar", "add", "change", "delete",
        "change_privacy",
        "view_students", "add_student", "change_student", "delete_student",
        "view_collaborators", "add_collaborator", "change_collaborator", "delete_collaborator",
    ]
}


# noinspection PyAbstractClass
class BasicModelMixin(ObjectPermissionManagerMixin, models.Model):
    """
    This is the basic model used in Course, Resource and Activity. This groups fields in common.
    """
    @property
    @abc.abstractmethod
    def author(self):
        pass

    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("A title that clearly indicates the content of this entity")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    language = models.CharField(
        max_length=20,
        choices=get_translated_languages(),
        verbose_name=_("Language"),
        help_text=_("The language in which you are currently writing")
    )
    tags = TaggableManager(
        help_text=_("A set of coma separated keywords that describe the entity and allows it to be found by "
                    "browsing or searching. You can write multi-token keywords by surrounding them with \" "
                    "(double quote) symbols.")
    )

    """
    Auto-generated fields
    """
    slug = models.SlugField(unique=True)
    published = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name=_("Published the"))
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name=_("Last updated the"))

    def slug_generator(self):
        return self.name

    @property
    @abc.abstractmethod
    def object_collaborators(self):
        """
        The collaborators related name (as declared in Course, Activity or Resource)

        :return: The RelatedManager that references the object collaborators
        :rtype: RelatedManager
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def linked_objects(self) -> Generator['BasicModelMixin', None, None]:
        """
        The included objects in this object. For instance, a course has activities, while an activity has resources.

        :return: The Generator that references the included objects
        :rtype: Generator
        """
        raise NotImplementedError()

    def add_collaborator(self, collaborator: get_user_model(), role: CollaboratorRole):
        """
        Add a collaborator on the object

        :raises UserIsAlreadyAuthor: when the user is already the author on the object
        :raises UserIsAlreadyCollaborator: when the user is already a collaborator on the object

        :param collaborator: the collaborator to add on the object
        :type collaborator: get_user_model()
        :param role: the role of the collaborator on the object
        :type role: CollaboratorRole
        """
        user_is_collaborator = collaborator in self.collaborators.all()
        user_is_author = collaborator == self.author
        if user_is_author:
            raise learning.exc.UserIsAlreadyAuthor(
                _("The user “%(user)s” is already the author of this %(object)s. "
                  "The user %(user)s cannot be added as a collaborator.")
                % {'object': _(self.__class__.__name__.lower()), 'user': collaborator}
            )
        if user_is_collaborator:
            raise learning.exc.UserIsAlreadyCollaborator(
                _("The user “%(user)s” already collaborates on this %(object)s. "
                  "Maybe you just want to change its role?")
                % {'object': _(self.__class__.__name__.lower()), 'user': collaborator}
            )
        self.object_collaborators.create(collaborator=collaborator, role=role.name)

    def remove_collaborator(self, collaborator: get_user_model()):
        """
        Remove a collaborator from the object

        :raises UserNotCollaboratorError: when the user is not a collaborator on the object

        :param collaborator: the collaborator to remove from the object
        :type collaborator: get_user_model()
        :param propagate: whether to propagate the deletion of a collaborator on included objects
        :type propagate: bool
        """
        user_is_collaborator = collaborator in self.collaborators.all()
        if not user_is_collaborator:
            raise learning.exc.UserNotCollaboratorError(
                _("The user “%(user)s” is not already a collaborator on this %(object)s.")
                % {'object': _(self.__class__.__name__.lower()), 'user': collaborator}
            )
        self.object_collaborators.filter(collaborator=collaborator).delete()

    def change_collaborator_role(self, collaborator: get_user_model(), role: CollaboratorRole):
        """
        Change the role of a collaborator on the object

        :raises UserNotCollaboratorError: when the user is not a collaborator on the object

        :param collaborator: the collaborator for which to change his role
        :type collaborator: get_user_model()
        :param role: the new role for the collaborator
        :type role: CollaboratorRole
        """
        user_is_collaborator = collaborator in self.collaborators.all()
        if not user_is_collaborator:
            raise learning.exc.UserNotCollaboratorError(
                _("The user “%(user)s” does not collaborates on this %(object)s. "
                  "Maybe you just want to add it as a collaborator?")
                % {'object': _(self.__class__.__name__.lower()), 'user': collaborator}
            )
        self.object_collaborators.filter(collaborator=collaborator).update(role=role.name)

    def _get_user_perms(self, user: get_user_model()) -> set:
        permissions = set()
        if user == self.author:
            permissions.update([
                # Basic CRUD actions
                "view", "delete", "add", "change",
                # Extra access for objects
                "view_similar",
                # Collaborators permissions
                "add_collaborator", "delete_collaborator", "change_collaborator", "view_collaborators"
            ])
        return permissions

    class Meta:
        abstract = True


def extract_all_included_objects(base_object: BasicModelMixin) -> Generator[BasicModelMixin, None, None]:
    """
    This generator return iteratively every included objects, whatever the depth is.

    :param base_object: the object that has included dependencies
    :type base_object: BasicModelMixin
    :return: a generator of included objects
    :rtype: Generator[BasicModelMixin, None, None]
    """
    for an_object in base_object.linked_objects:
        for linked_object in extract_all_included_objects(an_object):
            yield linked_object
        yield an_object


class Resource(BasicModelMixin):
    type = models.CharField(
        max_length=10,
        choices=[(rtype.name, rtype.value) for rtype in ResourceType],
        verbose_name=_("Type"),
        help_text=_("Whether this resource is a common file, a video file or an audio")
    )
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="resources",
        verbose_name=_("Author"),
        help_text=_("The user that created this resource, or that is considered as the current owner")

    )
    collaborators = models.ManyToManyField(
        get_user_model(),
        through="ResourceCollaborator",
        related_name="collaborates_on_resource",
        verbose_name=_("Collaborators"),
        help_text=_("The users that collaborate on this resource alongside the author")
    )
    duration = models.CharField(
        max_length=30,
        choices=[(duration.name, duration.value) for duration in Duration],
        default=Duration.NOT_SPECIFIED.name,
        verbose_name=_("Duration"),
        help_text=_("The estimated, required duration to consult and understand the resource")
    )
    licence = models.CharField(
        max_length=20,
        choices=[(licence.name, licence.value) for licence in Licences],
        default=Licences.CC_BY.name,
        verbose_name=_("Licence"),
        help_text=("The licence under which the content is provided. If you want to share your work with the community"
                   "a Creative Commons Licence is a bit more adapted. Anyway you can choose to keep your rights on "
                   "your resource")
    )
    access = models.CharField(
        max_length=20,
        choices=[(access.name, access.value) for access in ResourceAccess],
        default=ResourceAccess.PUBLIC.name,
        verbose_name=_("Access"),
        help_text=_("Whether the resource should remain private (for you only), visible only in activities that use it"
                    ", restricted to your collaborators or public")
    )
    reuse = models.CharField(
        max_length=20,
        choices=[(reuse.name, reuse.value) for reuse in ResourceReuse],
        default=ResourceReuse.ONLY_AUTHOR.name,
        verbose_name=_("Reuse"),
        help_text=_("Whether you want the resource to be reusable in an activity. Resources can be fully reusable, "
                    "only by you or not reusable")
    )
    media = models.FileField(
        blank=True, null=True,
        verbose_name=_("File")
    )

    @property
    def object_collaborators(self):
        return self.resource_collaborators

    @property
    def linked_objects(self):
        yield

    def is_reusable(self, for_activity=None) -> bool:
        """
        Check if it is possible to use the resource in an activity. Resource linking depends on a few conditions, based on
        access and reuse Resource attributes.

        :raises ResourceNotReusableError: when reuse condition do not allow the Resource to be reused by any Activity
        :raises ResourceNotReusableOnlyAuthorError: when reuse condition is set to “Only author” and the Resource \
            author and the author of the activity given in parameter do not match.
        :raises RuntimeError: when reuse condition is set to “Only author” but no activity is given in parameter

        :param for_activity: in case the reuse attribute is set to “Only author”, this argument must be provided. \
            It indicates for which activity to link the resource.
        :type for_activity: Activity
        :return: True if reusing resource is possible
        :rtype: bool
        """
        reuse = ResourceReuse[self.reuse]
        # Reuse is stricter than “Only Author”, means no one has access
        if reuse > ResourceReuse.ONLY_AUTHOR:
            raise learning.exc.ResourceNotReusableError(_("Reuse conditions for this resource prevent it from being added to an activity."))
        if reuse == ResourceReuse.ONLY_AUTHOR:
            if for_activity is None:
                raise RuntimeError("If resource reuse condition is set to “Only author”, you must provide the corresponding activity.")
            if reuse == ActivityReuse.ONLY_AUTHOR and for_activity.author != self.author:
                raise learning.exc.ResourceNotReusableOnlyAuthorError(
                    _("The author of this resource is the only one allowed to add it an activity that it owns.")
                )
        return True

    @staticmethod
    def acceptable_media(media):
        return media and media.size <= get_max_upload_size()

    def clean(self):
        # Check upload size
        upload_size = get_max_upload_size()
        if self.media and not Resource.acceptable_media(self.media):
            raise ValidationError(
                _("The file you tried to upload to the application is too big: you sent %(media_size)s "
                  "(maximum is %(upload_size)s).")
                % {'media_size': filesizeformat(self.media.size), 'upload_size': filesizeformat(upload_size)}
            )
        if self.access == ResourceAccess.PRIVATE.name and self.reuse == ResourceReuse.NO_RESTRICTION.name:
            raise ValidationError(_("The resource is private but also reusable. This is inconsistent."))
        if Licences[self.licence] > Licences.CC_BY_NC_ND and self.reuse == ResourceReuse.NO_RESTRICTION.name:
            raise ValidationError(_("The resource can be reused by anyone but the licence is too restrictive. Choose a "
                                    "Creative Commons licence if you wish to share your content."))

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        save() method is overridden to generate the slug field.
        :return:
        """
        self.slug = generate_slug_for_model(Resource, self)
        super().save(force_insert, force_update, using, update_fields)

    def delete(self, using=None, keep_parents=False):
        """
        delete() method is overridden to ensure the associated file is deleted at \
        the same time as the object.
        """
        if self.media:
            try:
                os.remove(os.path.join(settings.MEDIA_ROOT, self.media.name))
            except OSError as ex:
                logger.error("Deleting media for resource %(resource)s failed (%(cause)s)", resource=self, cause=str(ex))
        return super().delete()

    def _get_user_perms(self, user: get_user_model()) -> set:
        permissions = super()._get_user_perms(user)
        if self.author == user:
            permissions.update(['view_usage'])
        if self.access == ResourceAccess.PUBLIC.name:
            permissions.update(['view'])
        if self.access == ResourceAccess.EXISTING_ACTIVITIES.name:
            activities_with_this_resource = Activity.objects.filter(resources=self).all()
            for activity in activities_with_this_resource:
                # If able to see one of the linked course, it’s ok to view the activity
                if "view_activity" in activity.get_user_perms(user):
                    permissions.update(['view'])
                    break
        if user in self.collaborators.all() and ResourceAccess[self.access] <= ResourceAccess.COLLABORATORS_ONLY:
            permissions.update(PERMISSIONS_FOR_ROLE.get(self.object_collaborators.get(collaborator=user).role, set()))
        return permissions

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-updated', 'name']
        verbose_name = pgettext_lazy("Resource verbose name (singular form)", "resource")
        verbose_name_plural = pgettext_lazy("Resource verbose name (plural form)", "resources")


class ActivityAccess(OrderedEnum):
    PUBLIC = (_("Public"), 0)
    EXISTING_COURSES = (_("Only in courses"), 1)
    COLLABORATORS_ONLY = (_("Collaborators only"), 2)
    PRIVATE = (_("Private"), 3)


class ActivityReuse(OrderedEnum):
    NO_RESTRICTION = (_("Reusable"), 0)
    ONLY_AUTHOR = (_("Author only"), 1)
    NON_REUSABLE = (_("Non reusable"), 2)


class Activity(BasicModelMixin):
    access = models.CharField(
        max_length=20,
        choices=[(access.name, access.value) for access in ActivityAccess],
        default=ActivityAccess.PUBLIC.name,
        verbose_name=_("Access"),
        help_text=_("Whether the activity should remain private (for you only), visible only in courses that use it, "
                    "restricted to your collaborators or public")
    )
    reuse = models.CharField(
        max_length=20,
        choices=[(reuse.name, reuse.value) for reuse in ActivityReuse],
        default=ActivityReuse.ONLY_AUTHOR.name,
        verbose_name=_("Reuse"),
        help_text=_("Whether you want the activity to be reusable in courses. Activities can be fully reusable, only by "
                    "you or not reusable")
    )
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="activities",
        verbose_name=_("Author"),
        help_text=_("The user that created this activity, or that is considered as the current owner")
    )
    collaborators = models.ManyToManyField(
        get_user_model(),
        through="ActivityCollaborator",
        related_name="collaborates_on_activity",
        verbose_name=_("Collaborators"),
        help_text=_("The users that collaborate on this activity alongside the author")
    )
    resources = models.ManyToManyField(Resource, related_name="activities", verbose_name=_("Resources"))

    @property
    def object_collaborators(self):
        return self.activity_collaborators

    @property
    def linked_objects(self) -> Generator[Resource, None, None]:
        return Resource.objects.filter(activities=self).all()

    def __str__(self):
        return self.name

    def is_reusable(self, for_course=None) -> bool:
        """
        Check if it is possible to use the activity in a course. Activity linking depends on a few conditions, based \
            on access and reuse Activity attributes.

        :raises ActivityNotReusableError: when reuse condition do not allow the activity to be reused by any course
        :raises ActivityNotReusableOnlyAuthorError: when reuse condition is set to “Only author” and the activity \
            author and the author of the course given in parameter do not match.
        :raises RuntimeError: when reuse condition is set to “Only author” but no course is given in parameter

        :param for_course: in case the reuse attribute is set to “Only author”, this argument must be provided. \
            It indicates for which course to link the activity.
        :type for_course: Course
        :return: True if reusing activity is possible
        :rtype: bool
        """
        reuse = ActivityReuse[self.reuse]
        # Reuse is stricter than “Only Author”, means no one has access
        if reuse > ActivityReuse.ONLY_AUTHOR:
            raise learning.exc.ActivityNotReusableError(_("Reuse conditions for this activity prevent it from being added to a course."))
        if reuse == ActivityReuse.ONLY_AUTHOR:
            if for_course is None:
                raise RuntimeError("If activity reuse condition is set to “Only author”, you must provide the corresponding course.")
            if reuse == ActivityReuse.ONLY_AUTHOR and for_course.author != self.author:
                raise learning.exc.ActivityNotReusableOnlyAuthorError(
                    _("The author of this activity is the only one allowed to add it a course that it owns.")
                )
        return True

    def add_resource(self, resource: Resource):
        """
        Add a resource on an activity.

        .. note:: You do not need to save the resource before calling this method. It the resource can be added, it will be saved anyway.

        :raises ResourceAlreadyOnActivityError: when the Resource is already linked with the Activity
        :raises ResourceNotReusableError: when reuse condition do not allow the Resource to be reused by any Activity
        :raises ResourceNotReusableOnlyAuthorError: when reuse condition is set to “Only author” and the Resource \
            author and the author of the activity given in parameter do not match.

        :param resource: the resource to add on the activity
        :type resource: Resource
        """
        if resource in self.resources.all():
            raise learning.exc.ResourceAlreadyOnActivityError(
                _("%(resource)s is already linked with this activity. Operation cancelled.") % {'resource': resource}
            )
        if resource.is_reusable(for_activity=self):
            resource.save()
            self.resources.add(resource)

    def remove_resource(self, resource: Resource):
        """
        Remove the resource from the activity. This means the link between the resource and the activity is removed.

        :raises ResourceIsNotLinkedWithThisActivityError: when the resource is not already linked with the activity

        :param resource: the resource to remove from the activity
        :type resource: Resource
        """
        if resource not in self.resources.all():
            raise learning.exc.ResourceIsNotLinkedWithThisActivityError(
                _("%(resource)s is not linked with this activity. Hence, it cannot be removed from the activity.") % {'resource': resource}
            )
        self.resources.remove(resource)

    def clean(self):
        if self.access == ActivityAccess.PRIVATE.name and self.reuse == ActivityReuse.NO_RESTRICTION.name:
            raise ValidationError(
                _("The activity is private and also reusable. This is inconsistent. "
                  "If you wish to share the activity, it should be visible by users.")
            )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        save() method is overridden to generate the slug field.
        :return:
        """
        self.slug = generate_slug_for_model(Activity, self)
        super().save(force_insert, force_update, using, update_fields)

    def _get_user_perms(self, user: get_user_model()) -> set:
        permissions = super()._get_user_perms(user)
        if self.author == user:
            permissions.update(['view_usage'])
        if self.access == ActivityAccess.PUBLIC.name:
            permissions.update(['view'])
        if self.access == ActivityAccess.EXISTING_COURSES.name:
            courses_with_this_activity = Course.objects.filter(course_activities__activity=self).all()
            for course in courses_with_this_activity:
                # If able to see one of the linked course, it’s ok to view the activity
                if "view_course" in course.get_user_perms(user):
                    permissions.update(['view'])
                    break
        if user in self.collaborators.all() and ActivityAccess[self.access] <= ActivityAccess.COLLABORATORS_ONLY:
            permissions.update(PERMISSIONS_FOR_ROLE.get(self.object_collaborators.get(collaborator=user).role, set()))
        return permissions

    class Meta:
        ordering = ['-updated', 'name']
        verbose_name = pgettext_lazy("Activity verbose name (singular form)", "activity")
        verbose_name_plural = pgettext_lazy("Activity verbose name (plural form)", "activities")


class CourseState(Enum):
    """
    State of a course
    """
    DRAFT = _("Draft")
    PUBLISHED = _("Published")
    ARCHIVED = _("Archived")


class CourseAccess(OrderedEnum):
    """
    Access permissions on a course
    """
    PUBLIC = (_("Public"), 0)
    STUDENTS_ONLY = (_("Students only"), 1)
    COLLABORATORS_ONLY = (_("Collaborators only"), 2)
    PRIVATE = (_("Private"), 3)


class CourseManager(models.Manager):

    # noinspection PyMethodMayBeStatic
    def __filter_with_query(self, queryset: QuerySet, query: str) -> QuerySet:
        """
        Filter a Course queryset with a query string. This filters name and description.

        :param queryset: the original queryset to filter
        :type queryset: QuerySet
        :param query: the query string
        :type query: str
        :return: a new queryset based on the original but filtered using the query parameter
        :rtype: QuerySet
        """
        if queryset and query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))
        return queryset

    def public(self, **kwargs) -> QuerySet:
        """
        Get all public courses

        :param kwargs: kwargs that can contain a key “query” to filter name and description
        :type kwargs: dict
        :return: public courses
        :rtype: QuerySet
        """
        qs = super().get_queryset().filter(access=CourseAccess.PUBLIC.name)
        return self.__filter_with_query(qs, kwargs.get('query', ""))

    def written_by(self, author: get_user_model(), **kwargs) -> QuerySet:
        """
        Get all Course objects written by the author.

        :param author: a user that wrote courses
        :type author: get_user_model()
        :param kwargs: kwargs that can contain a key “query” to filter name and description
        :type kwargs: dict
        :return: all courses written by the author given in parameter
        :rtype: QuerySet
        """
        qs = super().get_queryset().filter(author=author)
        return self.__filter_with_query(qs, kwargs.get('query', "")).order_by('-updated')

    def taught_by(self, teacher: get_user_model(), **kwargs) -> QuerySet:
        """
        Get all courses taught by (as author or collaborator) a teacher.

        :param teacher: a user that teachers in courses
        :type teacher: get_user_model()
        :param kwargs: kwargs that can contain a key “query” to filter name and description
        :type kwargs: dict
        :return: all courses taught by the teacher
        :rtype: QuerySet
        """
        qs = super().get_queryset().filter(Q(author=teacher) | Q(collaborators=teacher))
        return self.__filter_with_query(qs, kwargs.get('query', ""))

    def followed_by(self, student: get_user_model(), **kwargs) -> QuerySet:
        """
        Get all courses followed by the student

        :param student: a user that is registered in courses
        :type: get_user_model()
        :param kwargs: kwargs that can contain a key “query” to filter name and description
        :type kwargs: dict
        :return: all courses followed by the student
        :rtype: QuerySet
        """
        qs = super().get_queryset().filter(students=student)
        return self.__filter_with_query(qs, kwargs.get('query', ""))

    def recommendations_for(self, user: get_user_model(), **kwargs) -> QuerySet:
        """
        Get all courses opened for registration and recommended for a user

        .. note:: A recommendation concerns courses the user is not registered as a \
        student or as a teacher and is public and published.

        :param user: the user for which to query recommendations
        :type user: get_user_model()
        :param kwargs: kwargs that can contain a key “query” to filter name and description
        :type kwargs: dict
        :return: Courses recommended for the user
        :rtype: QuerySet
        """
        qs = super().get_queryset() \
            .exclude(Q(students=user) | Q(author=user) | Q(collaborators=user)) \
            .filter(Q(state=CourseState.PUBLISHED.name) & Q(access=CourseAccess.PUBLIC.name))
        return self.__filter_with_query(qs, kwargs.get('query', ""))


class Course(BasicModelMixin):
    state = models.CharField(
        max_length=20,
        choices=[(state.name, state.value) for state in CourseState],
        default=CourseState.DRAFT.name,
        verbose_name=_("State"),
        help_text=_("Whether the course should be considered as a draft, published or archived. Archived means "
                    "read-only"),
        blank=False,
        null=False
    )
    access = models.CharField(
        max_length=20,
        choices=[(access.name, access.value) for access in CourseAccess],
        default=CourseAccess.PUBLIC.name,
        verbose_name=_("Access"),
        help_text=_("Whether the course should remain private (for you only), restricted to your collaborators, "
                    "your students or public"),
        blank=False,
        null=False
    )
    registration_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Registration enabled"),
        help_text=_("Whether users are authorised to register or unregister from this course")
    )
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="courses",
        verbose_name=_("Author"),
        help_text=_("The user that created this course, or that is considered as the current owner")
    )
    collaborators = models.ManyToManyField(
        get_user_model(),
        through="CourseCollaborator",
        related_name="collaborates_on_course",
        verbose_name=_("Collaborators"),
        help_text=_("The users that collaborate on this course alongside the author")
    )
    students = models.ManyToManyField(
        get_user_model(),
        through="RegistrationOnCourse",
        related_name="registered_on",
        verbose_name=_("Students"),
        help_text=_("The users that registered on this course, that are hence considered as students")
    )

    objects = CourseManager()

    @property
    def object_collaborators(self):
        return self.course_collaborators

    @property
    def linked_objects(self) -> Generator[Activity, None, None]:
        return Activity.objects.filter(course_activities__course=self).all()

    def clean(self):
        if self.id:
            if self.author in self.students.all():
                raise ValidationError(
                    _("%(user)s is already the author of the course. The user %(user)s cannot be added as a "
                      "student.") % {'user': self.author}
                )
            if self.author in self.collaborators.all():
                raise ValidationError(
                    _("%(user)s is already the author of the course. The user %(user)s cannot be added as a "
                      "collaborator.") % {'user': self.author}
                )
        if self.registration_enabled and (self.state == CourseState.ARCHIVED.name or self.state == CourseState.DRAFT.name):
            raise ValidationError(
            _("You cannot enable registration on a course that is %(state)s.") % {'state': CourseState[self.state].value}
        )
        if CourseAccess[self.access] >= CourseAccess.COLLABORATORS_ONLY and CourseState[self.state] == CourseState.PUBLISHED:
            raise ValidationError(
                _("Access is collaborators only but course is published. It seems inconsistent. "
                  "If you wish to publish the course, you should at least let it accessible to students.")
            )

    @property
    def can_register(self) -> bool:
        """
        Indicates if it is possible to register on the course.

        :return: True if registration is possible
        :rtype: bool
        """
        return self.registration_enabled and CourseState[self.state] == CourseState.PUBLISHED

    def __check_student_registration(self, user: get_user_model()) -> bool:
        """
        Check is the user given in parameter can be added as a student on the course.
        Being a student on a course implies you’re not already a collaborator, you’re not the author of the course
        and you’re not already a student.

        :raises learning.exc.UserIsAlreadyCollaborator: when the user is a collaborator on the course
        :raises learning.exc.UserIsAlreadyAuthor when: the user is the author of the course
        :raises UserIsAlreadyStudent when: the user is already a student

        :param user: the user that is to be added as a student
        :type user: get_user_model()
        :return: True if registration is possible
        :rtype bool
        """
        user_is_collaborator = user in self.collaborators.all()
        user_is_author = user == self.author
        user_is_student = user in self.students.all()
        if user_is_collaborator:
            raise learning.exc.UserIsAlreadyCollaborator(
                _("%(user)s cannot register on this course. %(user)s is already "
                  "a collaborator on this course, a user cannot be both.") % {'user': user}
            )
        if user_is_author:
            raise learning.exc.UserIsAlreadyAuthor(
                _("%(user)s is already the author of this course. %(user)s cannot "
                  "register as a student.") % {'user': user}
            )
        if user_is_student:
            raise learning.exc.UserIsAlreadyStudent(
                _("%(user)s is already registered on this course.") % {'user': user}
            )
        return True

    def register(self, student: get_user_model()):
        """
        Register, as a student, on the course.

        :raises RegistrationDisabledError: when registration is disabled on the course
        :raises UserIsAlreadyCollaborator: when the user is a collaborator on the course
        :raises UserIsAlreadyAuthor: when the user is the author of the course
        :raises UserIsAlreadyStudent: when the user is already a student

        :param student: The student that wants to register on the course.
        :type student: get_user_model()
        """
        if not self.can_register:
            raise learning.exc.RegistrationDisabledError(
                _("Nobody can register on this course. Registration is disabled or the course is not published yet.")
            )
        if self.__check_student_registration(student):
            # noinspection PyUnresolvedReferences
            self.registrations.create(student=student, self_registration=True)

    def register_student(self, student: get_user_model(), registration_locked=True):
        """
        Register a student on the course

        :raises UserIsAlreadyCollaborator: when the user is a collaborator on the course
        :raises UserIsAlreadyAuthor: when the user is the author of the course
        :raises UserIsAlreadyStudent: when the user is already a student

        :param student: The student will be registered on the course.
        :type student: get_user_model()
        :param registration_locked: Indicates whether the registration is locked, meaning the user
                                    cannot self-unregister.
        :type registration_locked: bool
        """
        if self.__check_student_registration(student):
            # noinspection PyUnresolvedReferences
            self.registrations.create(student=student, registration_locked=registration_locked)

    def __check_student_unsubscription(self, user: get_user_model()) -> bool:
        """
        Check is the user given in parameter can be removed from students of this course.
        Unsubscription is possible when registration is not disabled and when the user is already a student on this
        course.

        :raises UserIsNotStudent: when the user to unsubscribe is not a student

        :param user: the user that is to be added as a student
        :type user: get_user_model()
        :return: True if registration is possible
        :rtype bool
        """
        user_is_student = user in self.students.all()
        if not user_is_student:
            raise learning.exc.UserIsNotStudent(
                _("User “%(user)s is not a student registered on this course. Thus %(user)s cannot be unregistered.")
                % {'user': user}
            )
        return True

    def unsubscribe(self, student: get_user_model()):
        """
        Unsubscribe, as a student, from the course

        :raises RegistrationDisabledError: when registration is disabled on the course
        :raises UserIsNotStudent: when the user to unsubscribe is not a student

        :param student: The student that wants to unsubscribe from the course.
        :type student: get_user_model()
        """
        if not self.can_register:
            raise learning.exc.RegistrationDisabledError(
                _("Nobody can unregister from this course. Registration is disabled or the course is no longer "
                  "published.")
            )
        if student in self.students.all() and self.registrations.get(student=student).registration_locked:
            raise learning.exc.RegistrationDisabledError(
                _("You cannot unregister from this course. Registration is locked for you.")
            )
        if self.__check_student_unsubscription(student):
            # noinspection PyUnresolvedReferences
            self.registrations.get(student=student).delete()

    def unsubscribe_student(self, user: get_user_model()):
        """
        Unsubscribe a student from the course

        :raises UserIsNotStudent: when the user to unsubscribe is not a student

        :param user:The student that has to be unsubscribed from the course.
        :type user: get_user_model()
        """
        if self.__check_student_unsubscription(user):
            # noinspection PyUnresolvedReferences
            self.registrations.get(student=user).delete()

    def add_collaborator(self, collaborator: get_user_model(), role: CollaboratorRole):
        """
        Add a collaborator on a course.

        :raises UserIsAlreadyAuthor: when the user is already the author of the course
        :raises UserIsAlreadyCollaborator: when the user is already a collaborator on the course
        :raises UserIsAlreadyStudent: when the user is already a student

        :param collaborator: the collaborator to add on the course
        :type collaborator: get_user_model()
        :param role: the role of the collaborator on the course
        :type role: CollaboratorRole
        :param propagate: whether to propagate the addition of a collaborator on activities
        :type propagate: bool
        """
        user_is_student = collaborator in self.students.all()
        if user_is_student:
            raise learning.exc.UserIsAlreadyStudent(
                _("%(user)s is already registered on this course.") % {'user': collaborator}
            )
        super().add_collaborator(collaborator=collaborator, role=role)

    @property
    def activities(self) -> Generator['CourseActivity', None, None]:
        """
        Get activities of this course, sorted by their rank.

        :return: the list of activities linked on this course.
        :rtype: list
        """
        for course_activity in self.course_activities.all():
            yield course_activity.activity

    def reorder_course_activities(self):
        ranked_activities = self.course_activities.all()

        in_order, rank_counter = True, 1
        for ranked_course_activity in ranked_activities:
            if not in_order:
                break
            if not ranked_course_activity.rank == rank_counter:
                in_order = False
            else:
                rank_counter += 1

        if not in_order:
            new_rank = 1
            for course_activity in ranked_activities:
                course_activity.rank = new_rank
                course_activity.save()
                new_rank += 1

    def add_activity(self, activity):
        """
        Add an activity on this course.

        .. note:: You do not need to save the activity before calling this method. It the resource can be added, it will be saved anyway.

        :raises ChangeActivityOnCourseError: when changing activity on the course is not possible
        :raises ActivityAlreadyOnCourseError: when activity is already linked with the course
        :raises ActivityNotReusableError: when reuse condition do not allow the resource to be reused by any activity
        :raises ActivityNotReusableOnlyAuthorError: when reuse condition is set to “Only author” and the activity \
            author and the author of the course do not match.

        :param activity: the activity to add on the course
        :type activity: Activity
        """
        if self.read_only:
            raise learning.exc.ChangeActivityOnCourseError(_("This course is read only. It is not possible to add activities."))
        if activity in self.activities:
            raise learning.exc.ActivityAlreadyOnCourseError(
                _("“%(activity)s is already linked with this course. Operation cancelled.")
                % {'activity': activity}
            )
        if activity.is_reusable(for_course=self):
            # TODO: rewrite this block. This is not well written and understanding is quite hard
            last_rank = CourseActivity.objects.filter(course=self).aggregate(Max('rank')).get('rank__max', 0)
            activity.save()
            CourseActivity.objects.create(
                course=self, activity=activity, rank=1 if last_rank is None else last_rank + 1
            )
            self.reorder_course_activities()

    def remove_activity(self, activity: Activity):
        """
        Remove the activity from the course. This means the link between the activity and the course is removed.

        :raises ChangeActivityOnCourseError: when changing activity on the course is not possible
        :raises ActivityIsNotLinkedWithThisCourseError: when activity is not linked with the course yet

        :param activity: the activity to remove on this course
        :type activity: Activity
        """
        if self.read_only:
            raise learning.exc.ChangeActivityOnCourseError(_("This course is read only. It is not possible to remove activities."))
        if activity not in self.activities:
            raise learning.exc.ActivityIsNotLinkedWithThisCourseError(
                _("“%(activity)s is not linked with this course. Hence, it cannot be removed from the course.")
                % {'activity': activity}
            )
        CourseActivity.objects.filter(course=self, activity=activity).get().delete()
        self.reorder_course_activities()

    @property
    def read_only(self) -> bool:
        """
        Indicates whether the course is read only or not

        :return: True if the course a read-only
        :rtype: bool
        """
        return CourseState[self.state] == CourseState.ARCHIVED

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        save() method is overridden to generate the slug field.
        :return:
        """
        self.slug = generate_slug_for_model(Course, self)
        super().save(force_insert, force_update, using, update_fields)

    def _get_user_perms(self, user: get_user_model()) -> set:
        permissions = super()._get_user_perms(user)
        # Public access means everyone can view it
        if self.access == CourseAccess.PUBLIC.name:
            permissions.update(["view"])
        # Being author of a course implies you have the owner permissions
        if user == self.author:
            permissions.update(PERMISSIONS_FOR_ROLE.get(CollaboratorRole.OWNER.name, set()))
        # Being a student with students only access or lower implies you have the students permissions
        if user in self.students.all() and CourseAccess[self.access] <= CourseAccess.STUDENTS_ONLY:
            permissions.update(PERMISSIONS_FOR_ROLE.get("students", set()))
        # Being a collaborator with collaborators only access or lower implies you have the collaborators permissions
        if user in self.collaborators.all() and CourseAccess[self.access] <= CourseAccess.COLLABORATORS_ONLY:
            permissions.update(PERMISSIONS_FOR_ROLE.get(self.object_collaborators.get(collaborator=user).role, set()))
        return permissions

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-updated', 'name']
        verbose_name = pgettext_lazy("Course verbose name (singular form)", "course")
        verbose_name_plural = pgettext_lazy("Course verbose name (plural form)", "courses")


class RegistrationOnCourse(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name=_("Cours"),
        related_name="registrations"
    )
    student = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        verbose_name=_("Student"),
        related_name="registrations"
    )
    self_registration = models.BooleanField(
        default=False,
        verbose_name=_("User registered by itself"),
        help_text=_("Indicates the user decided to register to the course by itself, the user was not registered "
                    "manually by a teacher in the course or as a member of a group.")
    )
    registration_locked = models.BooleanField(
        default=False,
        verbose_name=_("Registration locked"),
        help_text=_("Locking a registration means the user will not be able to unregister by itself.")
    )

    """
    Auto-generated fields
    """
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name=_("Registered the"))
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name=_("Last updated the"))

    def __str__(self):
        return _("%(student)s, student in course “%(course)s”") % {
            'student': self.student,
            'course': self.course
        }

    def clean(self):
        if self.course.author == self.student:
            raise ValidationError(
                _("%(user)s is already the author of this course. %(user)s cannot be "
                  "registered as a student.") % {'user': self.student}
            )
        if self.student in self.course.collaborators.all():
            raise ValidationError(
                _("%(user)s cannot register on this course. %(user)s is already "
                  "a collaborator on this course, a user cannot be both.") % {'user': self.student}
            )

    class Meta:
        ordering = ['course', 'student']
        unique_together = ('course', 'student')
        verbose_name = pgettext_lazy("Course registration verbose name (singular form)", "course registration")
        verbose_name_plural = pgettext_lazy("Course registration verbose name (plural form)", "course registrations")


class ObjectCollaboratorMixin(models.Model):
    role = models.CharField(
        max_length=20,
        choices=[(role.name, role.value) for role in CollaboratorRole],
        default=CollaboratorRole.NON_EDITOR_TEACHER.name,
        verbose_name=_("Role")
    )

    @property
    @abc.abstractmethod
    def related_object(self) -> BasicModelMixin:
        raise NotImplementedError

    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name=_("Since the"))
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name=_("Last updated the"))

    def clean(self):
        if self.collaborator == self.related_object.author:
            raise ValidationError(
                _("%(user)s is already author of the course. It cannot be added as a collaborator.")
                % {'user': self.collaborator}
            )

    def __str__(self):
        return _("%(user)s is ”%(role)s” in the %(object_name)s “%(object)s”") % {
            'user': self.collaborator,
            'role': CollaboratorRole[self.role].value,
            'object_name': _(self.related_object.__class__.__name__.lower()),
            'object': self.related_object
        }

    class Meta:
        abstract = True


class CourseCollaborator(ObjectCollaboratorMixin):
    collaborator = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="course_collaborators",
        verbose_name=_("Collaborator")
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="course_collaborators",
        verbose_name=_("Course")
    )

    @property
    def related_object(self) -> BasicModelMixin:
        return self.course

    def clean(self):
        super().clean()
        if self.collaborator in self.course.students.all():
            raise ValidationError(
                _("%(user)s cannot be added as a collaborator on this course. %(user)s is already "
                  "a student, a user cannot be both.") % {'user': self.collaborator}
            )

    class Meta:
        ordering = ['course__updated', 'role']
        unique_together = ('collaborator', 'course')
        verbose_name = pgettext_lazy("Course collaborators verbose name (singular form)", "course collaborator")
        verbose_name_plural = pgettext_lazy("Course collaborators verbose name (plural form)", "course collaborators")


class ActivityCollaborator(ObjectCollaboratorMixin):
    collaborator = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="activity_collaborators",
        verbose_name=_("Collaborator")
    )
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="activity_collaborators",
        verbose_name=_("Course")
    )

    @property
    def related_object(self) -> BasicModelMixin:
        return self.activity

    class Meta:
        ordering = ['activity__updated', 'role']
        unique_together = ('collaborator', 'activity')
        verbose_name = pgettext_lazy("Activity collaborators verbose name (singular form)", "activity collaborator")
        verbose_name_plural = pgettext_lazy("Activity collaborators verbose name (plural form)", "activity collaborators")


class ResourceCollaborator(ObjectCollaboratorMixin):
    collaborator = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="resource_collaborators",
        verbose_name=_("Collaborator")
    )
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="resource_collaborators",
        verbose_name=_("Course")
    )

    @property
    def related_object(self) -> BasicModelMixin:
        return self.resource

    class Meta:
        ordering = ['resource__updated', 'role']
        unique_together = ('collaborator', 'resource')
        verbose_name = pgettext_lazy("Resource collaborators verbose name (singular form)", "resource collaborator")
        verbose_name_plural = pgettext_lazy("Resource collaborators verbose name (plural form)", "resource collaborators")


class CourseActivity(models.Model):
    rank = models.PositiveIntegerField(verbose_name=_("Rank"))
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="course_activities",
        verbose_name=_("Course")
    )
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="course_activities",
        verbose_name=_("Activity")
    )

    def __str__(self):
        return _('“%(activity)s”, n°%(rank)d on “%(course)s”') % {'activity': self.activity, 'rank': self.rank, 'course': self.course}

    class Meta:
        unique_together = ('activity', 'course')
        ordering = ['rank']
        verbose_name = pgettext_lazy("Course activity verbose name (singular form)", "course activity")
        verbose_name_plural = pgettext_lazy("Course activity verbose name (plural form)", "course activities")


class QuestionMixin(ObjectPermissionManagerMixin, models.Model):
    title = models.CharField(
        max_length=50,
        verbose_name=_("Title"),
        blank=False,
        null=False,
    )
    body = models.TextField(
        verbose_name=_("Question body"),
        blank=False,
        null=False
    )
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_("Author")
    )

    """
    Auto-generated fields
    """
    slug = models.SlugField(unique=True)
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name=_("Published the"))
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name=_("Last updated the"))

    def _get_user_perms(self, user):
        permissions = {"reply"}
        if user == self.author:
            permissions.update(["add", "change", "delete", "view"])
        return permissions

    def slug_generator(self):
        return self.title

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        save() method is overridden to generate the slug field.
        :return:
        """
        self.slug = generate_slug_for_model(QuestionMixin, self)
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return _("Question “%(title)s” published on %(date)s") % {
            'title': self.title, 'date': self.created.strftime("%B %d, %Y, %I:%M %p")
        }


class QuestionCourse(QuestionMixin):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name=_("Course")
    )

    def __str__(self):
        return _("Question on course %(course)s asked by %(author)s") % {'course': self.course, 'author': self.author}

    class Meta:
        ordering = ['course', 'created']
        verbose_name = pgettext_lazy("Course question (singular form)", "course question")
        verbose_name_plural = pgettext_lazy("Course questions (plural form)", "course questions")


class Response(ObjectPermissionManagerMixin, models.Model):
    question = models.ForeignKey(
        QuestionMixin,
        on_delete=models.CASCADE,
        related_name="responses",
        verbose_name=_("Question")
    )
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name=_("Author")
    )
    body = models.TextField(
        verbose_name=_("Response body"),
        blank=False
    )
    score = models.IntegerField(
        verbose_name=_("Score Count"),
        default=0
    )
    voters = models.ManyToManyField(
        get_user_model(),
        related_name='responses_votes',
        verbose_name=_("Users that voted for the response")
    )

    """
    Auto-generated fields
    """
    created = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name=_("Response publication date"))
    updated = models.DateTimeField(auto_now_add=False, auto_now=True, verbose_name=_("Last updated the"))

    # noinspection PyUnresolvedReferences
    def handle_vote(self, voter):
        #  The user has already voted for this question, hence, vote is cancelled
        if voter in self.voters.all():
            self.score -= 1
            self.voters.remove(voter)
            self.save()
        #  User never voted, hence vote is added
        else:
            self.score += 1
            self.voters.add(voter)
            self.save()

    def _get_user_perms(self, user):
        permissions = set()
        if user == self.author:
            permissions.update(["view", "add", "change", "delete"])
        return permissions

    def __str__(self):
        return _("Response to question “%(question)s” published the %(created)s") % {
            'question': getattr(self.question, 'title', None),
            'created': self.created.strftime("%B %d, %Y, %I:%M %p")
        }

    class Meta:
        ordering = ['question', 'created']
        verbose_name = pgettext_lazy("Response to a question in the agora (singular form)", "response")
        verbose_name_plural = pgettext_lazy("Response to a question in the agora (plural form)", "responses")

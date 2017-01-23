from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.timezone import now

from datahub.company import tasks
from datahub.core.mixins import DeferredSaveModelMixin


class BaseModel(DeferredSaveModelMixin, models.Model):
    """Common fields for most of the models we use."""

    archived = models.BooleanField(default=False)
    archived_on = models.DateTimeField(null=True)
    archived_reason = models.TextField(blank=True, null=True)
    archived_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    created_on = models.DateTimeField(null=True, blank=True)
    modified_on = models.DateTimeField(null=True, blank=True)

    class Meta:  # noqa: D101
        abstract = True

    def archive(self, user, reason=None):
        """Archive the model instance."""
        self.archived = True
        self.archived_by = user
        self.archived_reason = reason
        self.archived_on = now()
        self.save(skip_custom_validation=True)  # it will skip the custom validation

    def unarchive(self):
        """Unarchive the model instance."""
        self.archived = False
        self.archived_reason = ''
        self.archived_by = None
        self.archived_on = None
        self.save(skip_custom_validation=True)  # it will skip the custom validation

    def clean(self):
        """Custom validation for created_on and modified_on.

        If the fields are empty, populate them.
        """
        super().clean()
        self.created_on = self.created_on if self.created_on else now()
        self.modified_on = self.modified_on if self.modified_on else now()

    def get_datetime_fields(self):
        """Return list of fields that should be mapped as datetime."""
        return ['archived_on', 'created_on', 'modified_on']


class BaseConstantModel(models.Model):
    """Constant tables for FKs."""

    id = models.UUIDField(primary_key=True)
    name = models.TextField(blank=True)
    selectable = models.BooleanField(default=True)

    class Meta:  # noqa: D101
        abstract = True
        ordering = ('name', )

    def __str__(self):
        """Human readable admin name."""
        return self.name


class TaskInfo(models.Model):
    """Holds information about the tasks."""

    task_id = models.UUIDField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    note = models.CharField(max_length=255, null=True)
    db_table = models.CharField(max_length=100)
    update = models.BooleanField()
    changes = JSONField()

    class Meta:  # noqa: D101
        verbose_name_plural = 'Task info'

    @property
    def async_result(self):
        """Return the result of the task."""
        return tasks.save_to_korben.AsyncResult(str(self.task_id))

    @property
    def status(self):
        """Handy shortcut to get the task status."""
        return self.async_result.status

    def __str__(self):
        """Human readable name."""
        return self.name

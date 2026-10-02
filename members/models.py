from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """Returns only non-deleted records (deleted_at is null)."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager):
    """Returns all records including soft-deleted ones."""

    def get_queryset(self):
        return super().get_queryset()


class Member(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        SUSPENDED = "SUSPENDED", "Suspended"

    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"

    # Personal info
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    # Soft delete
    deleted_at = models.DateTimeField(null=True, blank=True, default=None)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = SoftDeleteManager()       # Default: excludes deleted  (like Member::all() in Laravel)
    all_objects = AllObjectsManager()   # Includes deleted            (like Member::withTrashed() in Laravel)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def delete(self, using=None, keep_parents=False):
        """Soft delete: sets deleted_at instead of removing the row."""
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def restore(self):
        """Restore a soft-deleted member. (Like Member::restore() in Laravel)"""
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])

    def hard_delete(self):
        """Permanently delete the record from the database."""
        super().delete()

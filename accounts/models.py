from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class CreatorUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required")
        user = self.model(email=self.normalize_email(email).lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True or extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_staff=True and is_superuser=True")
        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CreatorUserManager()

    def __str__(self):
        return self.email

class Workspace(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=50, unique=True)
    owner = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="owned_workspaces")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Membership(models.Model):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    ROLE_CHOICES = [(OWNER, "Owner"), (ADMIN, "Admin"), (MEMBER, "Member")]
    ACTIVE = "active"
    SUSPENDED = "suspended"
    STATUS_CHOICES = [(ACTIVE, "Active"), (SUSPENDED, "Suspended")]
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default=OWNER)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["workspace", "user"], name="unique_workspace_membership")]
        indexes = [models.Index(fields=["user", "status"])]


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import Membership, User, Workspace

class CreatorAdminCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email",)

class CreatorAdminChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"

@admin.register(User)
class CreatorUserAdmin(UserAdmin):
    form = CreatorAdminChangeForm
    add_form = CreatorAdminCreationForm
    ordering = ("email",)
    list_display = ("email", "first_name", "is_active", "is_staff", "date_joined")
    fieldsets = ((None, {"fields": ("email", "password")}), ("Profile", {"fields": ("first_name", "last_name")}), ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}), ("Dates", {"fields": ("last_login", "date_joined")}))
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "is_staff", "is_superuser")}),)
    search_fields = ("email", "first_name")

admin.site.register(Workspace)
admin.site.register(Membership)

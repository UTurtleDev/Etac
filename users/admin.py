from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Cabinet


class CustomUserAdmin(UserAdmin):
    model = User

    list_display = ('email', 'first_name', 'last_name', 'is_collaborateur', 'is_staff', 'is_active')
    list_filter = ('is_collaborateur', 'is_staff', 'is_active')

    fieldsets = (
        (None, {'fields': ('email', 'password', 'cabinet')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name')}),
        ('Statut', {'fields': ('is_collaborateur', 'is_staff', 'is_active')}),
        ('Permissions', {'fields': ('is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'cabinet', 'password1', 'password2', 'is_collaborateur', 'is_staff', 'is_active')
        }),
    )

    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)


class CustomCabinetAdmin(admin.ModelAdmin):
    list_display = ('nom', 'nombre_comptables')
    search_fields = ('nom',)
    ordering = ('nom',)

    def nombre_comptables(self, obj):
        return obj.Comptables.count()
    nombre_comptables.short_description = 'Nombre de comptables'

admin.site.register(User, CustomUserAdmin)
admin.site.register(Cabinet, CustomCabinetAdmin)

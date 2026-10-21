from django.contrib import admin
from .models import Directory, Machine, Maintenance, Claim


class AdministratorOnly(admin.ModelAdmin):
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Directory)
class DirectoryAdmin(AdministratorOnly):
    list_display = ['name', 'kind', 'description']
    list_filter = ['kind']
    search_fields = ['name']


@admin.register(Machine)
class MachineAdmin(AdministratorOnly):
    list_display = ['serial_number', 'machine_model', 'shipment_date', 'client', 'service_company']
    search_fields = ['serial_number']
    list_filter = ['machine_model', 'service_company']


@admin.register(Maintenance)
class MaintenanceAdmin(AdministratorOnly):
    list_display = ['machine', 'maintenance_type', 'maintenance_date', 'operating_hours']
    list_filter = ['maintenance_type', 'service_company']


@admin.register(Claim)
class ClaimAdmin(AdministratorOnly):
    list_display = ['machine', 'failure_date', 'failure_node', 'recovery_date', 'downtime']
    readonly_fields = ['downtime']

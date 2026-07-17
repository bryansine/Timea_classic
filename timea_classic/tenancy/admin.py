from django.contrib import admin
from .models import Tenant

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'owner', 'created_at', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug', 'owner__username')
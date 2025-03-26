from django.contrib import admin
from .models import Promotion

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('title', 'promotion_type', 'location', 'start_date', 'end_date', 'is_active')
    list_filter = ('promotion_type', 'location', 'is_active')
    search_fields = ('title', 'content')
from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'origin', 'influencer', 'campaign',
        'status', 'proposed_rate', 'applied_at', 'reviewed_at',
    )
    list_filter = ('status', 'origin')
    search_fields = (
        'influencer__user__email',
        'influencer__user__first_name',
        'campaign__title',
    )
    readonly_fields = ('id', 'applied_at', 'updated_at')
    list_per_page = 25

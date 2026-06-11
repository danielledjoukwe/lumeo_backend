from django.contrib import admin
from .models import Campaign, CampaignCategory


class CampaignCategoryInline(admin.TabularInline):
    model  = CampaignCategory
    extra  = 1
    fields = ('category',)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display  = ('title', 'business', 'status', 'budget', 'deadline', 'created_at')
    list_filter   = ('status',)
    search_fields = ('title', 'business__company_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering      = ('-created_at',)
    inlines       = [CampaignCategoryInline]


@admin.register(CampaignCategory)
class CampaignCategoryAdmin(admin.ModelAdmin):
    list_display  = ('campaign', 'category')
    search_fields = ('campaign__title', 'category__name')

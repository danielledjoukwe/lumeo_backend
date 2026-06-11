from django.contrib import admin
from django.utils.html import format_html
from .models import Category, InfluencerProfile, SocialPlatform


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    ordering = ('name',)


class SocialPlatformInline(admin.TabularInline):
    model = SocialPlatform
    extra = 1
    fields = ('platform', 'profile_url', 'followers')


@admin.register(InfluencerProfile)
class InfluencerProfileAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'get_email', 'get_city', 'get_country', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'categories', 'user__country')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'user__username', 'bio')
    filter_horizontal = ('categories',)
    readonly_fields = ('created_at', 'updated_at', 'get_avatar')
    inlines = (SocialPlatformInline,)

    fieldsets = (
        ('Compte utilisateur', {
            'fields': ('user', 'get_avatar', 'is_verified')
        }),
        ('Profil influenceur', {
            'fields': ('bio', 'categories')
        }),
        ('Horodatage', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Nom complet')
    def get_full_name(self, obj):
        return obj.user.full_name

    @admin.display(description='Email')
    def get_email(self, obj):
        return obj.user.email

    @admin.display(description='Ville')
    def get_city(self, obj):
        return obj.user.city or '—'

    @admin.display(description='Pays')
    def get_country(self, obj):
        return obj.user.country or '—'

    @admin.display(description='Avatar')
    def get_avatar(self, obj):
        if obj.user.avatar:
            return format_html('<img src="{}" style="width:48px;height:48px;border-radius:8px;object-fit:cover;">', obj.user.avatar.url)
        return '—'


@admin.register(SocialPlatform)
class SocialPlatformAdmin(admin.ModelAdmin):
    list_display = ('platform', 'get_influencer', 'profile_url', 'followers')
    list_filter = ('platform',)
    search_fields = ('profile__user__email', 'profile__user__first_name', 'profile_url')
    ordering = ('platform',)

    @admin.display(description='Influenceur')
    def get_influencer(self, obj):
        return obj.profile.user.full_name
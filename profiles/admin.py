from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category,
    InfluencerProfile,
    SocialPlatform,
    BusinessProfile,
    VerificationDocument,
)


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


class VerificationDocumentInline(admin.TabularInline):
    model = VerificationDocument
    extra = 1
    fields = ('document_name', 'file', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'get_email', 'account_type', 'verification_status', 'is_verified', 'created_at')
    list_filter = ('verification_status', 'is_verified', 'account_type')
    search_fields = ('company_name', 'user__email', 'user__first_name', 'user__last_name', 'niu')
    readonly_fields = ('created_at', 'updated_at', 'is_verified', 'verification_requested_at', 'verification_reviewed_at')
    inlines = (VerificationDocumentInline,)

    fieldsets = (
        ('Compte utilisateur', {
            'fields': ('user', 'company_name', 'account_type')
        }),
        ('Informations Entreprise', {
            'fields': ('industry', 'website', 'description', 'niu')
        }),
        ('Vérification', {
            'fields': ('verification_status', 'is_verified', 'verification_note', 'verification_requested_at', 'verification_reviewed_at')
        }),
        ('Horodatage', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Email')
    def get_email(self, obj):
        return obj.user.email


@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    list_display = ('document_name', 'get_company_name', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('document_name', 'profile__company_name', 'profile__user__email')
    readonly_fields = ('uploaded_at',)

    @admin.display(description='Entreprise')
    def get_company_name(self, obj):
        return obj.profile.company_name or str(obj.profile.user)
from rest_framework import serializers
from categories.serializers import CategorySerializer
from .models import Campaign, CampaignCategory


# ── Nested helpers ────────────────────────────────────────────────────────────

class CampaignCategorySerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model  = CampaignCategory
        fields = ['id', 'category']


class BusinessInfoSerializer(serializers.Serializer):
    """Compact business snapshot shown to influencers on each campaign."""
    company_name  = serializers.CharField(source='business.company_name')
    industry      = serializers.CharField(source='business.industry')
    website       = serializers.URLField(source='business.website')
    description   = serializers.CharField(source='business.description')
    is_verified   = serializers.BooleanField(source='business.is_verified')
    # Contact person name from the User model
    contact_name  = serializers.SerializerMethodField()
    avatar        = serializers.SerializerMethodField()

    def get_contact_name(self, obj):
        user = obj.business.user
        return f"{user.first_name} {user.last_name}".strip() or user.email

    def get_avatar(self, obj):
        user = obj.business.user
        request = self.context.get('request')
        if user.avatar and request:
            return request.build_absolute_uri(user.avatar.url)
        return None


# ── Business-side (full detail) ───────────────────────────────────────────────

class CampaignSerializer(serializers.ModelSerializer):
    """Full read serializer — used by the business owner."""
    categories    = CampaignCategorySerializer(source='campaign_categories', many=True, read_only=True)
    status_label  = serializers.CharField(read_only=True)
    business_name = serializers.CharField(source='business.company_name', read_only=True)

    class Meta:
        model  = Campaign
        fields = [
            'id', 'business_name',
            'title', 'description', 'deliverables_brief',
            'budget', 'duration', 'deadline', 'status', 'status_label',
            'categories',
            'created_at', 'updated_at',
        ]


class CampaignWriteSerializer(serializers.Serializer):
    """Write serializer for create / update."""
    title              = serializers.CharField(max_length=200)
    description        = serializers.CharField()
    deliverables_brief = serializers.CharField()
    budget             = serializers.DecimalField(max_digits=10, decimal_places=2)
    duration           = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    deadline           = serializers.DateField()
    category_ids       = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )


# ── Influencer-side (public list) ─────────────────────────────────────────────

class CampaignPublicListSerializer(serializers.ModelSerializer):
    """
    Compact card view for the marketplace list.
    Description is intentionally excluded — it belongs only on the detail page.
    """
    categories   = CampaignCategorySerializer(source='campaign_categories', many=True, read_only=True)
    status_label = serializers.CharField(read_only=True)
    # Just the essentials about the brand
    company_name = serializers.CharField(source='business.company_name', read_only=True)
    industry     = serializers.CharField(source='business.industry',     read_only=True)
    is_verified  = serializers.BooleanField(source='business.is_verified', read_only=True)

    class Meta:
        model  = Campaign
        fields = [
            'id',
            'company_name', 'industry', 'is_verified',
            'title', 'deliverables_brief',
            'budget', 'duration', 'deadline', 'status', 'status_label',
            'categories',
            'created_at',
        ]


# ── Influencer-side (public detail) ──────────────────────────────────────────

class CampaignPublicDetailSerializer(serializers.ModelSerializer):
    """
    Full detail view for a single campaign — includes description and
    a richer business section.
    """
    categories   = CampaignCategorySerializer(source='campaign_categories', many=True, read_only=True)
    status_label = serializers.CharField(read_only=True)
    business     = serializers.SerializerMethodField()

    class Meta:
        model  = Campaign
        fields = [
            'id',
            'business',
            'title', 'description', 'deliverables_brief',
            'budget', 'duration', 'deadline', 'status', 'status_label',
            'categories',
            'created_at',
        ]

    def get_business(self, obj):
        request = self.context.get('request')
        bp      = obj.business
        user    = bp.user
        avatar_url = None
        if user.avatar:
            try:
                avatar_url = request.build_absolute_uri(user.avatar.url) if request else user.avatar.url
            except Exception:
                pass
        return {
            'company_name': bp.company_name,
            'industry':     bp.industry,
            'website':      bp.website,
            'description':  bp.description,
            'is_verified':  bp.is_verified,
            'contact_name': f"{user.first_name} {user.last_name}".strip() or user.email,
            'avatar':       avatar_url,
        }


# Keep this alias so existing imports don't break
CampaignPublicSerializer = CampaignPublicListSerializer

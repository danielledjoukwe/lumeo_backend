from rest_framework import serializers
from authentication.serializers import UserSerializer
from campaigns.serializers import CampaignPublicListSerializer
from .models import Application


# ── Influencer snapshot (shown to enterprise on each application) ─────────────

class InfluencerSnapshotSerializer(serializers.Serializer):
    """
    Compact influencer profile shown to the enterprise when reviewing applications.
    """
    id         = serializers.UUIDField(source='influencer.id')
    bio        = serializers.CharField(source='influencer.bio')
    is_verified = serializers.BooleanField(source='influencer.is_verified')
    # User fields
    first_name = serializers.CharField(source='influencer.user.first_name')
    last_name  = serializers.CharField(source='influencer.user.last_name')
    email      = serializers.EmailField(source='influencer.user.email')
    avatar     = serializers.SerializerMethodField()
    city       = serializers.CharField(source='influencer.user.city')
    country    = serializers.CharField(source='influencer.user.country')
    # Social platforms
    platforms  = serializers.SerializerMethodField()
    # Categories / niches
    categories = serializers.SerializerMethodField()

    def get_avatar(self, obj):
        request = self.context.get('request')
        user    = obj.influencer.user
        if user.avatar and request:
            return request.build_absolute_uri(user.avatar.url)
        return None

    def get_platforms(self, obj):
        return [
            {
                'platform':    p.platform,
                'profile_url': p.profile_url,
                'followers':   p.followers,
            }
            for p in obj.influencer.platforms.all()
        ]

    def get_categories(self, obj):
        return [
            {'id': str(c.id), 'name': c.name}
            for c in obj.influencer.categories.all()
        ]


# ── Application read serializers ──────────────────────────────────────────────

class ApplicationSerializer(serializers.ModelSerializer):
    """
    Full read serializer for an application.
    Used on the enterprise side — includes full influencer snapshot.
    """
    influencer    = InfluencerSnapshotSerializer(source='*', read_only=True)
    status_label  = serializers.CharField(source='get_status_display', read_only=True)
    can_be_reviewed  = serializers.BooleanField(read_only=True)
    can_be_withdrawn = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Application
        fields = [
            'id',
            'influencer',
            'cover_message', 'proposed_rate',
            'status', 'status_label',
            'enterprise_note',
            'can_be_reviewed', 'can_be_withdrawn',
            'applied_at', 'reviewed_at',
        ]


class ApplicationInfluencerSerializer(serializers.ModelSerializer):
    """
    Read serializer for the influencer's own view of their applications.
    Includes campaign info, hides internal enterprise fields.
    """
    campaign     = CampaignPublicListSerializer(read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    can_be_withdrawn = serializers.BooleanField(read_only=True)
    company_name = serializers.CharField(source='campaign.business.company_name', read_only=True)
    is_verified  = serializers.BooleanField(source='campaign.business.is_verified', read_only=True)

    class Meta:
        model  = Application
        fields = [
            'id',
            'campaign', 'company_name', 'is_verified',
            'cover_message', 'proposed_rate',
            'status', 'status_label',
            'enterprise_note',
            'can_be_withdrawn',
            'applied_at', 'accepted_at', 'reviewed_at',
        ]


# ── Write serializers ─────────────────────────────────────────────────────────

class ApplicationCreateSerializer(serializers.Serializer):
    """Payload for submitting a new application."""
    cover_message = serializers.CharField(
        min_length=30,
        error_messages={'min_length': 'Votre message doit contenir au moins 30 caractères.'},
    )
    proposed_rate = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        required=False, allow_null=True,
        min_value=0,
    )


class ApplicationRejectSerializer(serializers.Serializer):
    """Payload for rejecting an application — note is optional."""
    enterprise_note = serializers.CharField(required=False, allow_blank=True, default='')

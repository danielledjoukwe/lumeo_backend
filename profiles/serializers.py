from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import InfluencerProfile, BusinessProfile, SocialPlatform, VerificationDocument
from categories.serializers import CategorySerializer

User = get_user_model()


# ── Shared user fields serializer ─────────────────────────────────────────────

class UserPublicSerializer(serializers.ModelSerializer):
    """Minimal user info exposed on profiles."""
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'username', 'avatar', 'phone', 'city', 'country']
        read_only_fields = ['id', 'email']

    def get_avatar(self, obj):
        if not obj.avatar:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.avatar.url)
        return obj.avatar.url


# ── Social platforms ──────────────────────────────────────────────────────────

class SocialPlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialPlatform
        fields = ['id', 'platform', 'profile_url', 'followers']
        read_only_fields = ['id']


# ── Influencer profile ────────────────────────────────────────────────────────

class InfluencerProfileSerializer(serializers.ModelSerializer):
    """Read serializer — full nested representation."""
    user = UserPublicSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    platforms = SocialPlatformSerializer(many=True, read_only=True)

    class Meta:
        model = InfluencerProfile
        fields = ['id', 'user', 'bio', 'categories', 'platforms', 'is_verified', 'created_at', 'updated_at']


class InfluencerProfileUpdateSerializer(serializers.Serializer):
    """Write serializer for updating influencer profile + user fields together."""
    # User fields
    first_name  = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name   = serializers.CharField(max_length=100, required=False, allow_blank=True)
    username    = serializers.CharField(max_length=150, required=False, allow_null=True)
    phone       = serializers.CharField(max_length=20,  required=False, allow_null=True, allow_blank=True)
    city        = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    country     = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    avatar      = serializers.ImageField(required=False, allow_null=True)

    # Profile fields
    bio            = serializers.CharField(required=False, allow_blank=True)
    # List of category UUIDs (max 5)
    category_ids   = serializers.ListField(
        child=serializers.UUIDField(), required=False, max_length=5
    )
    # Social platforms as a list of objects
    platforms      = SocialPlatformSerializer(many=True, required=False)

    def validate_username(self, value):
        if value is None:
            return value
        value = value.strip() or None
        if value:
            request = self.context.get('request')
            qs = User.objects.filter(username=value)
            if request:
                qs = qs.exclude(pk=request.user.pk)
            if qs.exists():
                raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value


# ── Business profile & Verification ──────────────────────────────────────────

class VerificationDocumentSerializer(serializers.ModelSerializer):
    """Serializer for verification documents."""
    class Meta:
        model = VerificationDocument
        fields = ['id', 'document_name', 'file', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class BusinessProfileSerializer(serializers.ModelSerializer):
    """Read serializer — full nested representation."""
    user = UserPublicSerializer(read_only=True)
    verification_documents = VerificationDocumentSerializer(many=True, read_only=True)
    account_type_label = serializers.CharField(source='get_account_type_display', read_only=True)
    verification_status_label = serializers.CharField(source='get_verification_status_display', read_only=True)

    class Meta:
        model = BusinessProfile
        fields = [
            'id', 'user', 'company_name', 'industry', 'website', 'description',
            'is_verified', 'created_at', 'updated_at',
            'account_type', 'account_type_label', 'niu',
            'verification_status', 'verification_status_label',
            'verification_note', 'verification_requested_at', 'verification_reviewed_at',
            'verification_documents'
        ]


class BusinessProfileUpdateSerializer(serializers.Serializer):
    """Write serializer for updating business profile + user fields together."""
    # User fields
    first_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name  = serializers.CharField(max_length=100, required=False, allow_blank=True)
    phone      = serializers.CharField(max_length=20,  required=False, allow_null=True, allow_blank=True)
    city       = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    country    = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    avatar     = serializers.ImageField(required=False, allow_null=True)

    # Profile fields
    company_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    industry     = serializers.CharField(max_length=100, required=False, allow_blank=True)
    website      = serializers.URLField(required=False, allow_blank=True)
    description  = serializers.CharField(required=False, allow_blank=True)

    # Verification fields that can be updated before submission
    account_type = serializers.ChoiceField(choices=BusinessProfile.ACCOUNT_TYPE_CHOICES, required=False)
    niu          = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)

from rest_framework import serializers
from django.conf import settings
from .models import Thread, Message

User = settings.AUTH_USER_MODEL


class MessageSerializer(serializers.ModelSerializer):
    sender_name   = serializers.SerializerMethodField()
    sender_avatar = serializers.SerializerMethodField()
    is_mine       = serializers.SerializerMethodField()

    class Meta:
        model  = Message
        fields = [
            'id', 'message_type', 'body',
            'attachment', 'draft_status',
            'sender', 'sender_name', 'sender_avatar',
            'is_mine', 'read_by', 'created_at',
        ]
        read_only_fields = ['id', 'message_type', 'sender', 'created_at']

    def get_sender_name(self, obj):
        return obj.sender.full_name if obj.sender else 'Système'

    def get_sender_avatar(self, obj):
        request = self.context.get('request')
        if obj.sender and obj.sender.avatar and request:
            return request.build_absolute_uri(obj.sender.avatar.url)
        return None

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and obj.sender:
            return obj.sender == request.user
        return False


class ThreadSerializer(serializers.ModelSerializer):
    application_id    = serializers.UUIDField(source='application.id', read_only=True)
    campaign_title    = serializers.CharField(source='application.campaign.title', read_only=True)
    other_party_name  = serializers.SerializerMethodField()
    other_party_avatar = serializers.SerializerMethodField()
    last_message      = serializers.SerializerMethodField()
    unread_count      = serializers.SerializerMethodField()

    class Meta:
        model  = Thread
        fields = [
            'id', 'application_id', 'campaign_title',
            'other_party_name', 'other_party_avatar',
            'last_message', 'unread_count', 'updated_at',
        ]

    def _other_party(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        user = request.user
        return obj.influencer_user if user == obj.business_user else obj.business_user

    def get_other_party_name(self, obj):
        other = self._other_party(obj)
        return other.full_name if other else ''

    def get_other_party_avatar(self, obj):
        request = self.context.get('request')
        other = self._other_party(obj)
        if other and other.avatar and request:
            return request.build_absolute_uri(other.avatar.url)
        return None

    def get_last_message(self, obj):
        last = obj.messages.order_by('-created_at').first()
        if last:
            return {'body': last.body[:80], 'created_at': last.created_at}
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request:
            return 0
        return obj.messages.exclude(read_by=request.user).exclude(sender=request.user).count()
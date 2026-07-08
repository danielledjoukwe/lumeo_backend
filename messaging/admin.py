from django.contrib import admin
from .models import Thread, Message


class MessageInline(admin.TabularInline):
    model  = Message
    extra  = 0
    fields = ['message_type', 'sender', 'body', 'draft_status', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display  = ['id', 'application', 'created_at', 'updated_at']
    search_fields = ['application__influencer__user__email', 'application__campaign__title']
    inlines       = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display  = ['id', 'thread', 'sender', 'message_type', 'draft_status', 'created_at']
    list_filter   = ['message_type', 'draft_status']
    search_fields = ['body', 'sender__email']
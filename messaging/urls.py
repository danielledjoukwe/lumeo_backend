from django.urls import path
from .app_views.thread_views import my_thread_list, thread_detail
from .app_views.message_views import send_message, review_draft

urlpatterns = [
    # Inbox
    path('', my_thread_list, name='thread-list'),
    # Thread detail + full message history
    path('<uuid:pk>/', thread_detail,  name='thread-detail'),
    # Send a message or draft
    path('<uuid:thread_pk>/messages/', send_message,   name='send-message'),
    # Business reviews a draft
    path('<uuid:thread_pk>/messages/<uuid:message_pk>/review/', review_draft, name='review-draft'),
]
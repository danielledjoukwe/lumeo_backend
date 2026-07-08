from django.urls import path
from . import views

from .app_views.verification_views import (
    get_verification_status, submit_verification, 
    upload_verification_document, delete_verification_document
)

urlpatterns = [
    # Influencer profile
    path('influencer/profile/', views.influencer_profile_detail, name='influencer-profile-detail'),
    path('influencer/profile/edit/', views.influencer_profile_edit, name='influencer-profile-edit'),

    # Influencer social platforms
    path('influencer/platforms/', views.influencer_platforms_list, name='influencer-platforms-list'),
    path('influencer/platforms/add/', views.influencer_platform_add, name='influencer-platform-add'),
    path('influencer/platforms/<uuid:pk>/edit/', views.influencer_platform_edit, name='influencer-platform-edit'),
    path('influencer/platforms/<uuid:pk>/delete/', views.influencer_platform_delete, name='influencer-platform-delete'),

    # Business profile
    path('business/profile/', views.business_profile_detail, name='business-profile-detail'),
    path('business/profile/edit/', views.business_profile_edit, name='business-profile-edit'),

    # Partner verification
    path('business/verification/', get_verification_status, name='verification-status'),
    path('business/verification/submit/', submit_verification, name='verification-submit'),
    path('business/verification/documents/add/', upload_verification_document, name='verification-document-add'),
    path('business/verification/documents/<uuid:doc_id>/delete/', delete_verification_document, name='verification-document-delete'),

    # Influencer discovery (partner side — browse & view influencer profiles)
    path('influencers/', views.influencer_list, name='influencer-list'),
    path('influencers/<uuid:pk>/', views.influencer_public_detail, name='influencer-public-detail'),
]

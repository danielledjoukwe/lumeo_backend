from django.urls import path
from .app_views.category_views import manage_categories,add_category,edit_category,delete_category
from .app_views.admin_user_views import (
    admin_user_list, admin_user_detail,
    admin_approve_verification, admin_reject_verification
)

urlpatterns = [
    path('categories/',              manage_categories, name='manage-categories'),
    path('categories/add/',          add_category,      name='add-category'),
    path('categories/<uuid:pk>/edit/',   edit_category, name='edit-category'),
    path('categories/<uuid:pk>/delete/', delete_category, name='delete-category'),

    path('users/', admin_user_list, name='admin-user-list'),
    path('users/<int:user_id>/', admin_user_detail, name='admin-user-detail'),
    path('verifications/<int:user_id>/approve/', admin_approve_verification, name='admin-approve-verification'),
    path('verifications/<int:user_id>/reject/', admin_reject_verification, name='admin-reject-verification'),
]

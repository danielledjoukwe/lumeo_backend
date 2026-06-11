from django.urls import path
from . import views

urlpatterns = [
    # Authenticated users — search/autocomplete
    path('', views.category_list, name='category-list'),

    # Admin — CRUD
    path('manage/', views.admin_category_list, name='admin-category-list'),
    path('manage/create/', views.admin_category_create, name='admin-category-create'),
    path('manage/<uuid:pk>/', views.admin_category_detail, name='admin-category-detail'),
    path('manage/<uuid:pk>/edit/', views.admin_category_edit, name='admin-category-edit'),
    path('manage/<uuid:pk>/delete/', views.admin_category_delete, name='admin-category-delete'),
]

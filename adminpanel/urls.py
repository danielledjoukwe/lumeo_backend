from django.urls import path
from .app_views.category_views import manage_categories,add_category,edit_category,delete_category

urlpatterns = [
    path('categories/',              manage_categories, name='manage-categories'),
    path('categories/add/',          add_category,      name='add-category'),
    path('categories/<uuid:pk>/edit/',   edit_category, name='edit-category'),
    path('categories/<uuid:pk>/delete/', delete_category, name='delete-category'),
]

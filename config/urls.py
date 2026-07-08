from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from .views import base_view, home, enterprise_home, influencer_home, admin_home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('welcome/', base_view, name='welcome'),
    path('', home, name='home'),
    path('dashboard/enterprise/', enterprise_home, name='enterprise_home'),
    path('dashboard/influencer/', influencer_home, name='influencer_home'),
    path('auth/', include('authentication.urls')),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('categories/', include('categories.urls')),
    path('profiles/', include('profiles.urls')),
    path('campaigns/', include('campaigns.urls')),
    path('collaborations/', include('collaborations.urls')),
    path('dashboard/admin/', include('adminpanel.urls')),
    path('dashboard/admin/home', admin_home, name='admin_home'),
    path('api/threads/', include('messaging.urls')),
    path('api/dashboard/', include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
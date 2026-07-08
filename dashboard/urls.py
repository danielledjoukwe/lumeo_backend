from django.urls import path
from .app_views.influencers_dasbhaord_views import influencer_dashboard
from .app_views.partner_dashboard_views import partner_dashboard

urlpatterns = [
    path('influencer/', influencer_dashboard, name='influencer_dashboard'),
    path('partner/',    partner_dashboard,    name='partner_dashboard'),
]

from django.urls import path

from .api_views.my_campaign_views import (
    my_campaign_list,
    my_campaign_create,
    my_campaign_detail,
    my_campaign_edit,
    my_campaign_delete,
    my_campaign_publish,
    my_campaign_pause,
    my_campaign_unpublish,
)
from .api_views.campagin_views import (
    campaign_list,
    campaign_detail,
)

urlpatterns = [
    # ── Enterprise: own campaign management ───────────────────────────────────
    path('my/',                           my_campaign_list,      name='my-campaign-list'),
    path('my/create/',                    my_campaign_create,    name='my-campaign-create'),
    path('my/<uuid:pk>/',                 my_campaign_detail,    name='my-campaign-detail'),
    path('my/<uuid:pk>/edit/',            my_campaign_edit,      name='my-campaign-edit'),
    path('my/<uuid:pk>/delete/',          my_campaign_delete,    name='my-campaign-delete'),
    path('my/<uuid:pk>/publish/',         my_campaign_publish,   name='my-campaign-publish'),
    path('my/<uuid:pk>/pause/',           my_campaign_pause,     name='my-campaign-pause'),
    path('my/<uuid:pk>/unpublish/',       my_campaign_unpublish, name='my-campaign-unpublish'),

    # ── Influencer: public marketplace ────────────────────────────────────────
    path('',                              campaign_list,         name='campaign-list'),
    path('<uuid:pk>/',                    campaign_detail,       name='campaign-detail'),
]

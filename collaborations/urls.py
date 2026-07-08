from django.urls import path

from .app_views.my_application_views import (
    apply_to_campaign,
    my_application_list,
    my_application_detail,
    withdraw_application,
    accept_invitation,
    reject_invitation,
)
from .app_views.my_mission_views import (
    my_mission_list,
    my_mission_detail,
)
from .app_views.application_views import (
    campaign_application_list,
    campaign_application_detail,
    campaign_invitation_list,
    campaign_invitation_detail,
    accept_application,
    reject_application,
)
from .app_views.invitation_views import (
    send_invitation,
)

urlpatterns = [
    # ── Influencer: own applications & invitations ────────────────────────────
    # Apply to a campaign
    path('campaigns/<uuid:campaign_pk>/apply/',     apply_to_campaign,    name='apply-to-campaign'),
    # List / detail of own applications & invitations
    path('my/',                                     my_application_list,  name='my-application-list'),
    path('my/<uuid:pk>/',                           my_application_detail, name='my-application-detail'),
    # Withdraw a pending application
    path('my/<uuid:pk>/withdraw/',                  withdraw_application,  name='withdraw-application'),
    # Respond to received invitations
    path('my/<uuid:pk>/accept/',                    accept_invitation,   name='accept-invitation'),
    path('my/<uuid:pk>/reject/',                    reject_invitation,   name='reject-invitation'),

    # ── Influencer: missions (accepted/in_progress/completed) ─────────────────
    path('missions/',                               my_mission_list,       name='my-mission-list'),
    path('missions/<uuid:pk>/',                     my_mission_detail,     name='my-mission-detail'),

    # ── Enterprise: manage applications on their campaigns ────────────────────
    # List applications for a specific campaign
    path('campaigns/<uuid:campaign_pk>/',           campaign_application_list,   name='campaign-application-list'),
    # Detail of a single application
    path('campaigns/<uuid:campaign_pk>/<uuid:pk>/', campaign_application_detail, name='campaign-application-detail'),
    # Accept / reject
    path('campaigns/<uuid:campaign_pk>/<uuid:pk>/accept/', accept_application,   name='accept-application'),
    path('campaigns/<uuid:campaign_pk>/<uuid:pk>/reject/', reject_application,   name='reject-application'),

    # ── Enterprise: manage invitations sent on their campaigns ────────────────
    # List invitations for a specific campaign
    path('campaigns/<uuid:campaign_pk>/invitations/', campaign_invitation_list, name='campaign-invitation-list'),
    # Detail of a single invitation
    path('campaigns/<uuid:campaign_pk>/invitations/<uuid:pk>/', campaign_invitation_detail, name='campaign-invitation-detail'),

    # ── Partner: send direct invitation to an influencer ──────────────────────
    path('influencers/<uuid:influencer_pk>/invite/', send_invitation,     name='send-invitation'),
]


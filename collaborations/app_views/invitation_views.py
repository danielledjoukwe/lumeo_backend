"""
Direct invitation API.

Partners browse influencers and send invitations.
Influencers receive and can accept or reject them.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from config.utils.role_check import check_access
from config.utils.pagination import paginate_queryset
from campaigns.models import Campaign
from profiles.models import InfluencerProfile, BusinessProfile
from collaborations.models import Application
from collaborations.serializers import (
    ApplicationSerializer,
    ApplicationInfluencerSerializer,
    ApplicationCreateSerializer,
)


# ── Partner: send invitation ──────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_invitation(request, influencer_pk):
    """
    Partner sends a direct invitation to an influencer for one of their campaigns.

    Body:
      campaign_id   — UUID of the campaign (must belong to the authenticated partner)
      cover_message — motivation message (min 30 chars)
      proposed_rate — optional proposed rate (FCFA)
    """
    error = check_access(request, roles=['business'])
    if error:
        return error

    influencer = get_object_or_404(InfluencerProfile, pk=influencer_pk)
    business   = BusinessProfile.objects.get_or_create(user=request._db_user)[0]

    # Validate campaign belongs to this partner
    campaign_id = request.data.get('campaign_id')
    if not campaign_id:
        return Response({"error": "campaign_id est requis."}, status=status.HTTP_400_BAD_REQUEST)

    campaign = get_object_or_404(Campaign, pk=campaign_id, business=business)

    if campaign.status not in ('open', 'draft'):
        return Response(
            {"error": "Vous ne pouvez inviter que pour une campagne ouverte ou en brouillon."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check for duplicate
    if Application.objects.filter(campaign=campaign, influencer=influencer).exists():
        return Response(
            {"error": "Une candidature ou invitation existe déjà pour cet influenceur sur cette campagne."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ApplicationCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    invitation = Application.objects.create(
        campaign      = campaign,
        influencer    = influencer,
        cover_message = data['cover_message'],
        proposed_rate = data.get('proposed_rate'),
        status        = 'pending',
        origin        = 'partner',         # ← marks this as an invitation
    )

    return Response(
        ApplicationSerializer(invitation, context={'request': request}).data,
        status=status.HTTP_201_CREATED,
    )





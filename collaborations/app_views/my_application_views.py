"""
Influencer-side application API.

All endpoints require the authenticated user to have the 'influencer' role.
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
from profiles.models import InfluencerProfile
from collaborations.models import Application
from collaborations.serializers import (
    ApplicationInfluencerSerializer,
    ApplicationCreateSerializer,
)



def _get_influencer(request):
    """Return the InfluencerProfile for the authenticated user."""
    profile, _ = InfluencerProfile.objects.get_or_create(user=request._db_user)
    return profile


# ── Apply to a campaign ───────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_to_campaign(request, campaign_pk):
    """
    Submit a new application to an open campaign.

    Rules:
    - Campaign must be 'open'.
    - Influencer cannot apply twice to the same campaign.
    """
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    campaign = get_object_or_404(Campaign, pk=campaign_pk)

    if campaign.status != 'open':
        return Response(
            {"error": "Cette campagne n'accepte plus de candidatures."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    influencer = _get_influencer(request)

    # Check for duplicate application
    if Application.objects.filter(campaign=campaign, influencer=influencer).exists():
        return Response(
            {"error": "Vous avez déjà postulé à cette campagne."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ApplicationCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    application = Application.objects.create(
        campaign      = campaign,
        influencer    = influencer,
        cover_message = data['cover_message'],
        proposed_rate = data.get('proposed_rate'),
        status        = 'pending',
    )

    return Response(
        ApplicationInfluencerSerializer(application, context={'request': request}).data,
        status=status.HTTP_201_CREATED,
    )


# ── My applications list ──────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_application_list(request):
    """
    List all applications & invitations for the authenticated influencer.

    Supports:
      ?status=<str>     — filter by status
      ?origin=<str>     — filter by origin ('influencer' or 'partner')
      ?page=&page_size= — pagination
    """
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    influencer   = _get_influencer(request)
    applications = Application.objects.filter(influencer=influencer).select_related(
        'campaign', 'campaign__business', 'campaign__business__user',
    ).prefetch_related('campaign__campaign_categories__category')

    status_filter = request.query_params.get('status', '').strip()
    if status_filter:
        applications = applications.filter(status=status_filter)

    origin_filter = request.query_params.get('origin', '').strip()
    if origin_filter in ('influencer', 'partner'):
        applications = applications.filter(origin=origin_filter)

    return paginate_queryset(request, applications, ApplicationInfluencerSerializer)


# ── My application detail ─────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_application_detail(request, pk):
    """Retrieve one of the authenticated influencer's applications."""
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    influencer  = _get_influencer(request)
    application = get_object_or_404(Application, pk=pk, influencer=influencer)

    return Response(
        ApplicationInfluencerSerializer(application, context={'request': request}).data
    )


# ── Respond to an invitation ──────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_invitation(request, pk):
    """
    Influencer accepts a pending invitation sent by a partner.
    Sets status → 'accepted' and records accepted_at.
    """
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    influencer = _get_influencer(request)
    invitation = get_object_or_404(
        Application, pk=pk, influencer=influencer, origin='partner'
    )

    if not invitation.can_be_reviewed:
        return Response(
            {"error": "Seules les invitations en attente peuvent être acceptées."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    invitation.status      = 'accepted'
    invitation.accepted_at = timezone.now()
    invitation.reviewed_at = timezone.now()
    invitation.save(update_fields=['status', 'accepted_at', 'reviewed_at', 'updated_at'])

    return Response(
        ApplicationInfluencerSerializer(invitation, context={'request': request}).data
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_invitation(request, pk):
    """
    Influencer rejects a pending invitation.
    Sets status → 'rejected'.
    """
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    influencer = _get_influencer(request)
    invitation = get_object_or_404(
        Application, pk=pk, influencer=influencer, origin='partner'
    )

    if not invitation.can_be_reviewed:
        return Response(
            {"error": "Seules les invitations en attente peuvent être refusées."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    invitation.status      = 'rejected'
    invitation.reviewed_at = timezone.now()
    invitation.save(update_fields=['status', 'reviewed_at', 'updated_at'])

    return Response(
        ApplicationInfluencerSerializer(invitation, context={'request': request}).data
    )# ── Withdraw an application ───────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def withdraw_application(request, pk):
    """
    Withdraw a pending application.
    Only possible while status is 'pending'.
    """
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    influencer  = _get_influencer(request)
    application = get_object_or_404(Application, pk=pk, influencer=influencer)

    if not application.can_be_withdrawn:
        return Response(
            {"error": "Seules les candidatures en attente peuvent être retirées."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    application.status      = 'withdrawn'
    application.reviewed_at = timezone.now()
    application.save(update_fields=['status', 'reviewed_at', 'updated_at'])

    return Response(
        ApplicationInfluencerSerializer(application, context={'request': request}).data
    )


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

# A mission is simply an accepted application
MISSION_STATUSES = ('accepted',)


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
    List all applications submitted by the authenticated influencer.

    Supports:
      ?status=<str>     — filter by status
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


# ── Withdraw an application ───────────────────────────────────────────────────

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


# ── Missions (accepted / in_progress / completed applications) ────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_mission_list(request):
    """
    List all missions for the authenticated influencer.
    A mission is an application that has been accepted.

    Supports:
      ?page=&page_size= — pagination
    """
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    influencer = _get_influencer(request)
    missions   = Application.objects.filter(
        influencer=influencer,
        status__in=MISSION_STATUSES,
    ).select_related(
        'campaign',
        'campaign__business',
        'campaign__business__user',
    ).prefetch_related('campaign__campaign_categories__category')

    status_filter = request.query_params.get('status', '').strip()
    if status_filter and status_filter in MISSION_STATUSES:
        missions = missions.filter(status=status_filter)

    missions = missions.order_by('-accepted_at')

    return paginate_queryset(request, missions, ApplicationInfluencerSerializer)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_mission_detail(request, pk):
    """
    Retrieve the detail of a single mission.
    The application must belong to the influencer and be in a mission status.
    """
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    influencer = _get_influencer(request)
    mission    = get_object_or_404(
        Application,
        pk=pk,
        influencer=influencer,
        status__in=MISSION_STATUSES,
    )
    return Response(
        ApplicationInfluencerSerializer(mission, context={'request': request}).data
    )

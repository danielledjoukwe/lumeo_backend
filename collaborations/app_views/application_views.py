"""
Enterprise-side application management API.

All endpoints require the authenticated user to have the 'business' role.
The enterprise can only see and act on applications for their own campaigns.
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
from profiles.models import BusinessProfile
from collaborations.models import Application
from collaborations.serializers import (
    ApplicationSerializer,
    ApplicationRejectSerializer,
)


def _get_business(request):
    """Return the BusinessProfile for the authenticated user."""
    profile, _ = BusinessProfile.objects.get_or_create(user=request._db_user)
    return profile


def _get_own_campaign(request, campaign_pk):
    """
    Return a campaign that belongs to the authenticated business,
    or raise 404.
    """
    business = _get_business(request)
    return get_object_or_404(Campaign, pk=campaign_pk, business=business)


# ── Applications for a campaign ───────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campaign_application_list(request, campaign_pk):
    """
    List all applications received for one of the enterprise's campaigns.

    Supports:
      ?status=<str>     — filter by status (pending, accepted, rejected…)
      ?page=&page_size= — pagination
    """
    error = check_access(request, roles=['business'])
    if error:
        return error

    campaign     = _get_own_campaign(request, campaign_pk)
    applications = Application.objects.filter(campaign=campaign, origin='influencer').select_related(
        'influencer', 'influencer__user',
    ).prefetch_related(
        'influencer__platforms',
        'influencer__categories',
    )

    status_filter = request.query_params.get('status', '').strip()
    if status_filter:
        applications = applications.filter(status=status_filter)

    return paginate_queryset(request, applications, ApplicationSerializer)


# ── Single application detail ─────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campaign_application_detail(request, campaign_pk, pk):
    """Retrieve a single application for one of the enterprise's campaigns."""
    error = check_access(request, roles=['business'])
    if error:
        return error

    campaign    = _get_own_campaign(request, campaign_pk)
    application = get_object_or_404(Application, pk=pk, campaign=campaign, origin='influencer')

    return Response(
        ApplicationSerializer(application, context={'request': request}).data
    )


# ── Direct invitations sent for a campaign ─────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campaign_invitation_list(request, campaign_pk):
    """
    List all direct invitations sent to influencers for one of the enterprise's campaigns.

    Supports:
      ?status=<str>     — filter by status (pending, accepted, rejected…)
      ?page=&page_size= — pagination
    """
    error = check_access(request, roles=['business'])
    if error:
        return error

    campaign    = _get_own_campaign(request, campaign_pk)
    invitations = Application.objects.filter(campaign=campaign, origin='partner').select_related(
        'influencer', 'influencer__user',
    ).prefetch_related(
        'influencer__platforms',
        'influencer__categories',
    )

    status_filter = request.query_params.get('status', '').strip()
    if status_filter:
        invitations = invitations.filter(status=status_filter)

    return paginate_queryset(request, invitations, ApplicationSerializer)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campaign_invitation_detail(request, campaign_pk, pk):
    """Retrieve details of a single sent invitation for one of the enterprise's campaigns."""
    error = check_access(request, roles=['business'])
    if error:
        return error

    campaign   = _get_own_campaign(request, campaign_pk)
    invitation = get_object_or_404(Application, pk=pk, campaign=campaign, origin='partner')

    return Response(
        ApplicationSerializer(invitation, context={'request': request}).data
    )


# ── Accept an application ─────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_application(request, campaign_pk, pk):
    """
    Accept a pending application.

    Sets status → 'accepted'.
    The campaign stays open — other influencers can still apply.
    The enterprise decides when to stop accepting.
    """
    error = check_access(request, roles=['business'])
    if error:
        return error

    campaign    = _get_own_campaign(request, campaign_pk)
    application = get_object_or_404(Application, pk=pk, campaign=campaign)

    if not application.can_be_reviewed:
        return Response(
            {"error": "Seules les candidatures en attente peuvent être acceptées."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    application.status      = 'accepted'
    application.reviewed_at = timezone.now()
    application.accepted_at = timezone.now()
    application.save(update_fields=['status', 'reviewed_at', 'accepted_at', 'updated_at'])

    return Response(
        ApplicationSerializer(application, context={'request': request}).data
    )


# ── Reject an application ─────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_application(request, campaign_pk, pk):
    """
    Reject a pending application with an optional note for the influencer.

    Sets status → 'rejected'.
    The enterprise_note is visible to the influencer.
    """
    error = check_access(request, roles=['business'])
    if error:
        return error

    campaign    = _get_own_campaign(request, campaign_pk)
    application = get_object_or_404(Application, pk=pk, campaign=campaign)

    if not application.can_be_reviewed:
        return Response(
            {"error": "Seules les candidatures en attente peuvent être refusées."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ApplicationRejectSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    application.status          = 'rejected'
    application.enterprise_note = serializer.validated_data.get('enterprise_note', '')
    application.reviewed_at     = timezone.now()
    application.save(update_fields=['status', 'enterprise_note', 'reviewed_at', 'updated_at'])

    return Response(
        ApplicationSerializer(application, context={'request': request}).data
    )

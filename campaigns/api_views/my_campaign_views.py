"""
Enterprise / business campaign management API.

All endpoints require the authenticated user to have the 'business' role.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from config.utils.role_check import check_access
from config.utils.pagination import paginate_queryset
from categories.models import Category
from profiles.models import BusinessProfile
from campaigns.models import Campaign, CampaignCategory
from campaigns.serializers import CampaignSerializer, CampaignWriteSerializer


def _get_business(request):
    """Return the BusinessProfile for the authenticated user."""
    profile, _ = BusinessProfile.objects.get_or_create(user=request._db_user)
    return profile


# ── List ──────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_campaign_list(request):
    """
    List all campaigns belonging to the authenticated business.

    Query params:
      ?q=<str>          — search by title
      ?status=<str>     — filter by status
      ?category=<uuid>  — filter by target category
      ?ordering=<str>   — 'newest' | 'oldest' | 'title_asc' | 'title_desc'
                          default: newest
      ?page=&page_size= — pagination
    """
    error = check_access(request, roles=['business'])
    if error:
        return error

    business  = _get_business(request)
    campaigns = Campaign.objects.filter(business=business)

    # ── Search ────────────────────────────────────────────────────────────────
    q = request.query_params.get('q', '').strip()
    if q:
        campaigns = campaigns.filter(title__icontains=q)

    # ── Status filter ─────────────────────────────────────────────────────────
    status_filter = request.query_params.get('status', '').strip()
    if status_filter:
        campaigns = campaigns.filter(status=status_filter)

    # ── Category filter ───────────────────────────────────────────────────────
    category_id = request.query_params.get('category', '').strip()
    if category_id:
        campaigns = campaigns.filter(campaign_categories__category__id=category_id).distinct()

    # ── Ordering ──────────────────────────────────────────────────────────────
    ordering = request.query_params.get('ordering', 'newest').strip()
    ORDER_MAP = {
        'newest':     '-created_at',
        'oldest':      'created_at',
        'title_asc':   'title',
        'title_desc': '-title',
    }
    campaigns = campaigns.order_by(ORDER_MAP.get(ordering, '-created_at'))

    return paginate_queryset(request, campaigns, CampaignSerializer)


# ── Create ────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def my_campaign_create(request):
    """
    Create a new campaign.
    Always saved as 'draft' — use the publish endpoint to open it.
    """
    error = check_access(request, roles=['business'])
    if error:
        return error

    serializer = CampaignWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data     = serializer.validated_data
    business = _get_business(request)

    campaign = Campaign.objects.create(
        business           = business,
        title              = data['title'],
        description        = data['description'],
        deliverables_brief = data['deliverables_brief'],
        budget             = data['budget'],
        deadline           = data['deadline'],
        status             = 'draft',
    )

    # Attach categories via the through model
    for cat_id in data.get('category_ids', []):
        try:
            category = Category.objects.get(pk=cat_id)
            CampaignCategory.objects.get_or_create(campaign=campaign, category=category)
        except Category.DoesNotExist:
            pass

    return Response(CampaignSerializer(campaign).data, status=status.HTTP_201_CREATED)


# ── Detail ────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_campaign_detail(request, pk):
    """Retrieve a single campaign owned by the authenticated business."""
    error = check_access(request, roles=['business'])
    if error:
        return error

    business = _get_business(request)
    campaign = get_object_or_404(Campaign, pk=pk, business=business)
    return Response(CampaignSerializer(campaign).data)


# ── Edit ──────────────────────────────────────────────────────────────────────

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def my_campaign_edit(request, pk):
    """
    Partially update a campaign.
    Only allowed when status is 'draft' or 'paused'.
    """
    error = check_access(request, roles=['business'])
    if error:
        return error

    business = _get_business(request)
    campaign = get_object_or_404(Campaign, pk=pk, business=business)

    if campaign.status not in ('draft', 'paused'):
        return Response(
            {"error": "Seules les campagnes en brouillon ou en pause peuvent être modifiées."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = CampaignWriteSerializer(data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    editable_fields = ['title', 'description', 'deliverables_brief', 'budget', 'deadline']
    for field in editable_fields:
        if field in data:
            setattr(campaign, field, data[field])
    campaign.save()

    # Replace categories if provided
    if 'category_ids' in data:
        CampaignCategory.objects.filter(campaign=campaign).delete()
        for cat_id in data['category_ids']:
            try:
                category = Category.objects.get(pk=cat_id)
                CampaignCategory.objects.get_or_create(campaign=campaign, category=category)
            except Category.DoesNotExist:
                pass

    return Response(CampaignSerializer(campaign).data)


# ── Delete ────────────────────────────────────────────────────────────────────

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def my_campaign_delete(request, pk):
    """
    Delete a campaign.
    Only allowed when status is 'draft' or 'cancelled'.
    """
    error = check_access(request, roles=['business'])
    if error:
        return error

    business = _get_business(request)
    campaign = get_object_or_404(Campaign, pk=pk, business=business)

    if campaign.status not in ('draft', 'cancelled'):
        return Response(
            {"error": "Seules les campagnes en brouillon ou annulées peuvent être supprimées."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    campaign.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Status transitions ────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def my_campaign_publish(request, pk):
    """Publish a draft campaign → status becomes 'open'."""
    error = check_access(request, roles=['business'])
    if error:
        return error

    business = _get_business(request)
    campaign = get_object_or_404(Campaign, pk=pk, business=business)

    if campaign.status != 'draft':
        return Response(
            {"error": "Seules les campagnes en brouillon peuvent être publiées."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    campaign.status = 'open'
    campaign.save(update_fields=['status'])
    return Response(CampaignSerializer(campaign).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def my_campaign_pause(request, pk):
    """Pause an open campaign → status becomes 'paused'."""
    error = check_access(request, roles=['business'])
    if error:
        return error

    business = _get_business(request)
    campaign = get_object_or_404(Campaign, pk=pk, business=business)

    if campaign.status != 'open':
        return Response(
            {"error": "Seules les campagnes ouvertes peuvent être mises en pause."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    campaign.status = 'paused'
    campaign.save(update_fields=['status'])
    return Response(CampaignSerializer(campaign).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def my_campaign_unpublish(request, pk):
    """Unpublish an open or paused campaign → back to 'draft'."""
    error = check_access(request, roles=['business'])
    if error:
        return error

    business = _get_business(request)
    campaign = get_object_or_404(Campaign, pk=pk, business=business)

    if campaign.status not in ('open', 'paused'):
        return Response(
            {"error": "Seules les campagnes ouvertes ou en pause peuvent être dépubliées."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    campaign.status = 'draft'
    campaign.save(update_fields=['status'])
    return Response(CampaignSerializer(campaign).data)

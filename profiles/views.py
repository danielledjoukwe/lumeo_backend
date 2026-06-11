from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from config.utils.role_check import check_access
from categories.models import Category
from .models import InfluencerProfile, BusinessProfile, SocialPlatform
from .serializers import (
    InfluencerProfileSerializer, InfluencerProfileUpdateSerializer,
    BusinessProfileSerializer, BusinessProfileUpdateSerializer,
    SocialPlatformSerializer,
)


# ── Influencer Profile ────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def influencer_profile_detail(request):
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    user = request._db_user
    profile, _ = InfluencerProfile.objects.get_or_create(user=user)
    return Response(InfluencerProfileSerializer(profile).data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def influencer_profile_edit(request):
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    user = request._db_user
    profile, _ = InfluencerProfile.objects.get_or_create(user=user)

    serializer = InfluencerProfileUpdateSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.validated_data

    for field in ['first_name', 'last_name', 'username', 'phone', 'city', 'country']:
        if field in data:
            setattr(user, field, data[field])
    if data.get('avatar'):
        user.avatar = data['avatar']
    user.save()

    if 'bio' in data:
        profile.bio = data['bio']
    profile.save()

    if 'category_ids' in data:
        profile.categories.set(Category.objects.filter(id__in=data['category_ids']))

    return Response(InfluencerProfileSerializer(profile).data)


# ── Influencer Social Platforms ───────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def influencer_platforms_list(request):
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    profile = get_object_or_404(InfluencerProfile, user=request._db_user)
    return Response(SocialPlatformSerializer(profile.platforms.all(), many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def influencer_platform_add(request):
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    profile, _ = InfluencerProfile.objects.get_or_create(user=request._db_user)
    serializer = SocialPlatformSerializer(data=request.data)
    if serializer.is_valid():
        platform, created = SocialPlatform.objects.update_or_create(
            profile=profile,
            platform=serializer.validated_data['platform'],
            defaults={
                'profile_url': serializer.validated_data['profile_url'],
                'followers': serializer.validated_data.get('followers', 0),
            }
        )
        return Response(
            SocialPlatformSerializer(platform).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def influencer_platform_edit(request, pk):
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    profile = get_object_or_404(InfluencerProfile, user=request._db_user)
    platform = get_object_or_404(SocialPlatform, pk=pk, profile=profile)
    serializer = SocialPlatformSerializer(platform, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def influencer_platform_delete(request, pk):
    error = check_access(request, roles=['influencer'])
    if error:
        return error

    profile = get_object_or_404(InfluencerProfile, user=request._db_user)
    platform = get_object_or_404(SocialPlatform, pk=pk, profile=profile)
    platform.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Business Profile ──────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def business_profile_detail(request):
    error = check_access(request, roles=['business'])
    if error:
        return error

    profile, _ = BusinessProfile.objects.get_or_create(user=request._db_user)
    return Response(BusinessProfileSerializer(profile).data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def business_profile_edit(request):
    error = check_access(request, roles=['business'])
    if error:
        return error

    user = request._db_user
    profile, _ = BusinessProfile.objects.get_or_create(user=user)

    serializer = BusinessProfileUpdateSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.validated_data

    for field in ['first_name', 'last_name', 'phone', 'city', 'country']:
        if field in data:
            setattr(user, field, data[field])
    if data.get('avatar'):
        user.avatar = data['avatar']
    user.save()

    for field in ['company_name', 'industry', 'website', 'description']:
        if field in data:
            setattr(profile, field, data[field])
    profile.save()

    return Response(BusinessProfileSerializer(profile).data)


# ── Influencer Discovery (partner side) ──────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def influencer_list(request):
    """
    Browse all influencer profiles.
    Available to partners (business role).

    Supports:
      ?q=<str>          — search by name or bio
      ?category=<uuid>  — filter by niche/category
      ?platform=<str>   — filter by social platform (instagram, tiktok, etc.)
      ?ordering=         — newest | oldest | name_asc | name_desc
      ?page=&page_size= — pagination
    """
    from django.db.models import Q
    from config.utils.pagination import paginate_queryset
    from .serializers import InfluencerProfileSerializer

    error = check_access(request, roles=['business'])
    if error:
        return error

    profiles = InfluencerProfile.objects.select_related('user').prefetch_related(
        'categories', 'platforms'
    )

    # Search by name or bio
    q = request.query_params.get('q', '').strip()
    if q:
        profiles = profiles.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q)  |
            Q(bio__icontains=q)
        ).distinct()

    # Category filter
    category_id = request.query_params.get('category', '').strip()
    if category_id:
        profiles = profiles.filter(categories__id=category_id).distinct()

    # Platform filter
    platform = request.query_params.get('platform', '').strip()
    if platform:
        profiles = profiles.filter(platforms__platform=platform).distinct()

    # Ordering
    ORDER_MAP = {
        'newest':    '-created_at',
        'oldest':     'created_at',
        'name_asc':   'user__first_name',
        'name_desc': '-user__first_name',
    }
    ordering = request.query_params.get('ordering', 'newest').strip()
    profiles = profiles.order_by(ORDER_MAP.get(ordering, '-created_at'))

    return paginate_queryset(request, profiles, InfluencerProfileSerializer)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def influencer_public_detail(request, pk):
    """Full public profile of a single influencer — for partners."""
    from django.shortcuts import get_object_or_404
    from .serializers import InfluencerProfileSerializer

    error = check_access(request, roles=['business'])
    if error:
        return error

    profile = get_object_or_404(
        InfluencerProfile.objects.select_related('user').prefetch_related('categories', 'platforms'),
        pk=pk,
    )
    return Response(InfluencerProfileSerializer(profile).data)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from config.utils.pagination import paginate_queryset
from profiles.models import BusinessProfile, InfluencerProfile
from profiles.serializers import BusinessProfileSerializer, InfluencerProfileSerializer

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_user_list(request):
    """
    List all users for the admin dashboard.
    Supports ?role=influencer|business and ?search=
    """
    users = User.objects.all().select_related('business_profile', 'influencer_profile')
    
    role = request.query_params.get('role', '').strip()
    if role == 'influencer':
        users = users.filter(role='influencer')
    elif role == 'business':
        users = users.filter(role='business')
        
    search = request.query_params.get('search', '').strip()
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(business_profile__company_name__icontains=search)
        )
        
    users = users.order_by('-created_at')
    
    # We will build a simple dict representation for the list since UserPublicSerializer is minimal
    # and we want role-specific data like verification_status or is_verified.
    def serialize_user(u):
        data = {
            'id': u.id,
            'email': u.email,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'role': u.role,
            'created_at': u.created_at,
        }
        if u.role == 'business' and hasattr(u, 'business_profile'):
            data['company_name'] = u.business_profile.company_name
            data['verification_status'] = u.business_profile.verification_status
            data['is_verified'] = u.business_profile.is_verified
        elif u.role == 'influencer' and hasattr(u, 'influencer_profile'):
            data['is_verified'] = u.influencer_profile.is_verified
            
        return data

    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 10)
    
    from django.core.paginator import Paginator
    paginator = Paginator(users, page_size)
    try:
        current_page = paginator.page(page)
    except Exception:
        current_page = paginator.page(1)
        
    return Response({
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'results': [serialize_user(u) for u in current_page.object_list]
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_user_detail(request, user_id):
    """Get full profile details for a specific user based on their role."""
    user = get_object_or_404(User, id=user_id)
    
    if user.role == 'business':
        profile, _ = BusinessProfile.objects.get_or_create(user=user)
        return Response({
            'role': 'business',
            'profile': BusinessProfileSerializer(profile, context={'request': request}).data
        })
    elif user.role == 'influencer':
        profile, _ = InfluencerProfile.objects.get_or_create(user=user)
        return Response({
            'role': 'influencer',
            'profile': InfluencerProfileSerializer(profile, context={'request': request}).data
        })
    else:
        # Admin or other role
        return Response({
            'role': user.role,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_approve_verification(request, user_id):
    """Approve a business profile's verification."""
    user = get_object_or_404(User, id=user_id, role='business')
    profile = get_object_or_404(BusinessProfile, user=user)
    
    profile.verification_status = 'approved'
    profile.is_verified = True
    profile.verification_note = ''
    profile.verification_reviewed_at = timezone.now()
    profile.save(update_fields=['verification_status', 'is_verified', 'verification_note', 'verification_reviewed_at'])
    
    return Response(BusinessProfileSerializer(profile, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_reject_verification(request, user_id):
    """Reject a business profile's verification with a note."""
    user = get_object_or_404(User, id=user_id, role='business')
    profile = get_object_or_404(BusinessProfile, user=user)
    
    note = request.data.get('note', '').strip()
    if not note:
        return Response({"error": "Une note explicative est requise pour le rejet."}, status=status.HTTP_400_BAD_REQUEST)
        
    profile.verification_status = 'rejected'
    profile.verification_note = note
    profile.verification_reviewed_at = timezone.now()
    profile.save(update_fields=['verification_status', 'is_verified', 'verification_note', 'verification_reviewed_at'])
    
    return Response(BusinessProfileSerializer(profile, context={'request': request}).data)

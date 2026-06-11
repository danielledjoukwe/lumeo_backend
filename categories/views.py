from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from config.utils.role_check import check_access
from .models import Category
from .serializers import CategorySerializer, CategoryWriteSerializer


# ── Public / Authenticated ────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def category_list(request):
    """
    List / search categories.
    Any authenticated, active, verified user can access this
    (used for dropdowns / autocomplete in forms).
    """
    error = check_access(request)
    if error:
        return error

    q = request.query_params.get('q', '').strip()
    qs = Category.objects.all()
    if q:
        qs = qs.filter(name__icontains=q)
    return Response(CategorySerializer(qs[:50], many=True).data)


# ── Admin CRUD ────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_category_list(request):
    error = check_access(request, roles=['administrator'])
    if error:
        return error

    qs = Category.objects.all()
    return Response(CategorySerializer(qs, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_category_create(request):
    error = check_access(request, roles=['administrator'])
    if error:
        return error

    serializer = CategoryWriteSerializer(data=request.data)
    if serializer.is_valid():
        category = serializer.save()
        return Response(CategorySerializer(category).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_category_detail(request, pk):
    error = check_access(request, roles=['administrator'])
    if error:
        return error

    category = get_object_or_404(Category, pk=pk)
    return Response(CategorySerializer(category).data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def admin_category_edit(request, pk):
    error = check_access(request, roles=['administrator'])
    if error:
        return error

    category = get_object_or_404(Category, pk=pk)
    serializer = CategoryWriteSerializer(
        category, data=request.data, partial=(request.method == 'PATCH')
    )
    if serializer.is_valid():
        category = serializer.save()
        return Response(CategorySerializer(category).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def admin_category_delete(request, pk):
    error = check_access(request, roles=['administrator'])
    if error:
        return error

    category = get_object_or_404(Category, pk=pk)
    category.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

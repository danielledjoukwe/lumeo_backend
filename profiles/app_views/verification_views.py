from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from config.utils.role_check import check_access
from profiles.models import BusinessProfile, VerificationDocument
from profiles.serializers import BusinessProfileSerializer, VerificationDocumentSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_verification_status(request):
    """Fetch the business profile verification status and documents."""
    error = check_access(request, roles=['business'])
    if error:
        return error

    profile, _ = BusinessProfile.objects.get_or_create(user=request._db_user)
    return Response(BusinessProfileSerializer(profile, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_verification(request):
    """
    Submit the verification dossier.
    Validates minimum requirements:
    - individual: at least 1 document
    - organization: at least 2 documents
    """
    error = check_access(request, roles=['business'])
    if error:
        return error

    profile = get_object_or_404(BusinessProfile, user=request._db_user)

    if profile.verification_status in ['pending', 'approved']:
        return Response(
            {"error": "Votre dossier est déjà en cours de révision ou a été approuvé."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Save account_type and niu if provided
    account_type = request.data.get('account_type')
    niu = request.data.get('niu')
    
    if account_type in ['individual', 'organization']:
        profile.account_type = account_type
    if niu is not None:
        profile.niu = niu
        
    doc_count = profile.verification_documents.count()
    
    if profile.account_type == 'individual' and doc_count < 1:
        return Response({"error": "Vous devez fournir au moins 1 document d'identité."}, status=status.HTTP_400_BAD_REQUEST)
    
    if profile.account_type == 'organization' and doc_count < 2:
        return Response({"error": "Vous devez fournir au moins 2 documents (ex: RCCM, statuts, CNI du dirigeant)."}, status=status.HTTP_400_BAD_REQUEST)

    profile.verification_status = 'pending'
    profile.verification_requested_at = timezone.now()
    profile.save(update_fields=['account_type', 'niu', 'verification_status', 'verification_requested_at'])

    return Response(BusinessProfileSerializer(profile, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_verification_document(request):
    """Upload a verification document."""
    error = check_access(request, roles=['business'])
    if error:
        return error

    profile = get_object_or_404(BusinessProfile, user=request._db_user)
    
    if profile.verification_status in ['pending', 'approved']:
        return Response(
            {"error": "Vous ne pouvez pas modifier les documents pendant la révision."},
            status=status.HTTP_400_BAD_REQUEST
        )

    file_obj = request.FILES.get('file')
    document_name = request.data.get('document_name')

    if not file_obj or not document_name:
        return Response({"error": "Fichier et nom du document requis."}, status=status.HTTP_400_BAD_REQUEST)

    doc = VerificationDocument.objects.create(
        profile=profile,
        document_name=document_name,
        file=file_obj
    )

    return Response(VerificationDocumentSerializer(doc, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_verification_document(request, doc_id):
    """Delete a previously uploaded document."""
    error = check_access(request, roles=['business'])
    if error:
        return error

    profile = get_object_or_404(BusinessProfile, user=request._db_user)
    
    if profile.verification_status in ['pending', 'approved']:
        return Response(
            {"error": "Vous ne pouvez pas modifier les documents pendant la révision."},
            status=status.HTTP_400_BAD_REQUEST
        )

    doc = get_object_or_404(VerificationDocument, id=doc_id, profile=profile)
    doc.file.delete() # delete physical file
    doc.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)

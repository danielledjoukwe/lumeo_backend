import os
from django.core.exceptions import ValidationError

# Centralized configuration for allowed document extensions
ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png']

def validate_document_extension(value):
    """
    Validator for file extensions.
    Raises ValidationError if the extension is not in ALLOWED_DOCUMENT_EXTENSIONS.
    """
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError(
            f"Type de fichier non supporté. Extensions autorisées : {', '.join(ALLOWED_DOCUMENT_EXTENSIONS)}"
        )

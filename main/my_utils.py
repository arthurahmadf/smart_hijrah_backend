import base64
import uuid
from django.core.files.base import ContentFile
from django.conf import settings

def base64_to_image_file(base64_string, prefix="file"):
    """
    Convert base64 string into Django ContentFile for ImageField.
    
    """
    if not base64_string:
        return None

    try:
        format, imgstr = base64_string.split(';base64,')
    except ValueError:
        # If base64 doesn't include prefix like "data:image/jpeg;base64,"
        # ASUMSI JIKA BASE64 YG DIKIRIM RAW 
        imgstr = base64_string
        format = "image/jpeg"

    ext = format.split('/')[-1] if '/' in format else "jpg"
    file_name = f"{prefix}_{uuid.uuid4().hex[:12]}.{ext}"
    return ContentFile(base64.b64decode(imgstr), name=file_name)


def generate_url(file_field, request=None):
    """
    Converts a FileField/ImageField into an absolute URL.
    
    :param file_field: The FileField or ImageField instance
    :param request: Optional HttpRequest object to build full URL
    :return: Absolute URL string or None
    
    """
    if not file_field:
        return None

    try:
        url = file_field.url
    except ValueError:
        return None

    if request:
        return request.build_absolute_uri(url)
    else:
        return f"{settings.MEDIA_URL}{file_field.name}"
    



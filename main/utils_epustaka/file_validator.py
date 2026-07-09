from django.core.exceptions import ValidationError


def validate_pdf_size(file):

    max_mb = 100

    if file.size > max_mb * 1024 * 1024:

        raise ValidationError(
            f"Ukuran PDF maksimal {max_mb} MB."
        )
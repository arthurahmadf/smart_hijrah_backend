from django.core.exceptions import ValidationError


def validate_video_size(video):

    limit_mb = 100

    if video.size > limit_mb * 1024 * 1024:

        raise ValidationError(
            f"Ukuran video maksimal {limit_mb} MB."
        )
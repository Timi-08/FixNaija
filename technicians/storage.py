
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateVerificationStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "location",
            Path(settings.BASE_DIR) / "private_verification_documents",
        )
        kwargs.setdefault("base_url", None)
        super().__init__(*args, **kwargs)

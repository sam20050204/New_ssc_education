import os
import zipfile

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from PIL import Image

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
ALLOWED_IMAGE_MIMETYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024


def validate_image_file(file):
    """Validate image file for extension, size, MIME type, and actual image data"""

    if not file:
        return

    file_ext = os.path.splitext(file.name)[1].lower().lstrip(".")

    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            _("Invalid file extension. Allowed: %(allowed)s"),
            code="invalid_extension",
            params={"allowed": ", ".join(ALLOWED_IMAGE_EXTENSIONS)},
        )

    if file.size > MAX_IMAGE_SIZE:
        raise ValidationError(
            _("File size too large. Maximum size: 5 MB. Your file: %(size)s MB"),
            code="file_too_large",
            params={"size": round(file.size / (1024 * 1024), 2)},
        )

    # Get MIME type from file - handle both UploadedFile and existing ImageFieldFile
    content_type = getattr(file, "content_type", None)
    if not content_type:
        # Try to determine MIME type from extension
        mime_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
        }
        content_type = mime_map.get(file_ext, "application/octet-stream")

    if content_type not in ALLOWED_IMAGE_MIMETYPES:
        raise ValidationError(
            _("Invalid file type: %(type)s. Allowed types: %(allowed)s"),
            code="invalid_mimetype",
            params={"type": content_type, "allowed": ", ".join(ALLOWED_IMAGE_MIMETYPES)},
        )

    try:
        file.seek(0)
        img = Image.open(file)
        img.verify()
        file.seek(0)
    except Exception:
        raise ValidationError(
            _("File is not a valid image or is corrupted."),
            code="invalid_image_data",
        )


def validate_filename(filename):
    """Validate filename to prevent path traversal attacks"""

    suspicious_patterns = ["..", "/", "\\", "\0"]

    for pattern in suspicious_patterns:
        if pattern in filename:
            raise ValidationError(
                _("Invalid characters in filename. Filename must not contain path separators."),
                code="invalid_filename",
            )

    if any(ord(c) < 32 for c in filename):
        raise ValidationError(
            _("Filename contains invalid control characters."),
            code="invalid_characters",
        )


def validate_zip_upload(file, allowed_extensions=None, max_file_count=500, max_uncompressed_size=250 * 1024 * 1024):
    """Validate ZIP uploads before extraction."""
    if not file:
        raise ValidationError(_("ZIP file is required."), code="missing_zip")

    if not file.name.lower().endswith(".zip"):
        raise ValidationError(_("Only ZIP archives are allowed."), code="invalid_zip_extension")

    try:
        archive = zipfile.ZipFile(file)
    except zipfile.BadZipFile as exc:
        raise ValidationError(_("Invalid or corrupted ZIP archive."), code="invalid_zip") from exc

    allowed_extensions = {ext.lower() for ext in (allowed_extensions or set())}
    total_size = 0
    file_count = 0

    for member in archive.infolist():
        file_count += 1
        total_size += member.file_size
        normalized_name = member.filename.replace("\\", "/")

        if normalized_name.startswith("/") or ".." in normalized_name.split("/"):
            raise ValidationError(_("ZIP archive contains unsafe paths."), code="unsafe_zip_path")
        if file_count > max_file_count:
            raise ValidationError(_("ZIP archive contains too many files."), code="zip_too_many_files")
        if total_size > max_uncompressed_size:
            raise ValidationError(_("ZIP archive is too large when extracted."), code="zip_too_large")
        if allowed_extensions and not member.is_dir():
            extension = os.path.splitext(normalized_name)[1].lower()
            if extension not in allowed_extensions:
                raise ValidationError(
                    _("ZIP archive contains unsupported files."),
                    code="zip_invalid_member",
                )

    file.seek(0)

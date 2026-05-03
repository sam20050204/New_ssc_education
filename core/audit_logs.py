import logging

from django.contrib.contenttypes.models import ContentType

from core.models import AuditLog

logger = logging.getLogger(__name__)


def get_client_ip(request):
    if not request:
        return ""

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def build_audit_metadata(request=None, **metadata):
    details = {key: value for key, value in metadata.items() if value not in (None, "", [], {})}
    if request:
        details.setdefault("path", request.path)
        details.setdefault("method", request.method)
    return details


def log_audit_event(*, action, actor=None, target=None, request=None, metadata=None):
    metadata = build_audit_metadata(request=request, **(metadata or {}))
    content_type = None
    object_id = ""
    target_repr = ""

    if target is not None:
        target_repr = str(target)[:255]
        if getattr(target, "pk", None) is not None:
            content_type = ContentType.objects.get_for_model(target.__class__)
            object_id = str(target.pk)

    try:
        return AuditLog.objects.create(
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            action=action,
            content_type=content_type,
            object_id=object_id,
            target_repr=target_repr,
            metadata=metadata,
            ip_address=get_client_ip(request),
        )
    except Exception:
        logger.exception("Failed to persist audit event", extra={"action": action, "target": target_repr})
        return None

import re
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from core.models import (
    AdmittedStudent,
    CommentEntry,
    CommunicationThread,
    Enquiry,
    Notification,
    NotificationSetting,
    ThreadParticipantState,
)

MENTION_RE = re.compile(r"@([A-Za-z0-9_.-]+)")


ROLE_GROUP_MAP = {
    "admin": ["Admin"],
    "counselor": ["Counselor"],
    "accountant": ["Accountant"],
    "attendance": ["Attendance Manager"],
}


def get_role_users(role_key):
    group_names = ROLE_GROUP_MAP.get(role_key, [])
    users = User.objects.filter(is_active=True)
    if role_key == "admin":
        return users.filter(Q(is_superuser=True) | Q(groups__name__in=group_names)).distinct()
    return users.filter(groups__name__in=group_names).distinct()


def ensure_notification_settings(user):
    settings_by_category = {item.category: item for item in NotificationSetting.objects.filter(user=user)}
    for category, _label in NotificationSetting.CATEGORY_CHOICES:
        if category not in settings_by_category:
            NotificationSetting.objects.create(user=user, category=category)


def user_allows_category(user, category):
    setting = NotificationSetting.objects.filter(user=user, category=category).first()
    return True if setting is None else setting.in_app_enabled


def create_notification(
    *,
    recipients,
    category,
    priority,
    event_key,
    title,
    message,
    actor=None,
    link_url="",
    action_label="",
    content_object=None,
    due_at=None,
    metadata=None,
    dedupe_window_hours=0,
):
    created = []
    metadata = metadata or {}
    for recipient in recipients:
        if not recipient or not recipient.is_active or not user_allows_category(recipient, category):
            continue

        if dedupe_window_hours:
            since = timezone.now() - timedelta(hours=dedupe_window_hours)
            existing = Notification.objects.filter(
                recipient=recipient,
                event_key=event_key,
                created_at__gte=since,
            )
            if content_object is not None:
                content_type = ContentType.objects.get_for_model(content_object.__class__)
                existing = existing.filter(content_type=content_type, object_id=str(content_object.pk))
            if existing.exists():
                continue

        notification = Notification.objects.create(
            recipient=recipient,
            actor=actor,
            category=category,
            priority=priority,
            event_key=event_key,
            title=title,
            message=message,
            link_url=link_url,
            action_label=action_label,
            due_at=due_at,
            metadata=metadata,
            content_object=content_object,
        )
        created.append(notification)
    return created


def create_role_notification(**kwargs):
    role_key = kwargs.pop("role_key")
    recipients = list(get_role_users(role_key))
    return create_notification(recipients=recipients, **kwargs)


def resolve_mentions(body):
    usernames = set(MENTION_RE.findall(body or ""))
    if not usernames:
        return User.objects.none()
    return User.objects.filter(username__in=usernames, is_active=True)


def can_access_thread(user, thread):
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    visibility = thread.visibility or []
    if not visibility:
        return True
    user_groups = set(user.groups.values_list("name", flat=True))
    return bool(user_groups.intersection(set(visibility)))


def touch_thread_participant(thread, user, *, mark_read=False):
    if not user or not user.is_authenticated:
        return None
    state, _created = ThreadParticipantState.objects.get_or_create(thread=thread, user=user)
    if mark_read:
        state.last_read_at = timezone.now()
        state.save(update_fields=["last_read_at", "updated_at"])
    return state


@transaction.atomic
def add_comment_entry(
    *,
    thread,
    author,
    body,
    parent=None,
    attachment=None,
    status_update="none",
    is_internal=True,
):
    entry = CommentEntry.objects.create(
        thread=thread,
        author=author,
        parent=parent,
        body=body,
        attachment=attachment,
        status_update=status_update,
        is_internal=is_internal,
    )
    mentions = resolve_mentions(body)
    if mentions.exists():
        entry.mentions.set(mentions)
    thread.last_activity_at = timezone.now()
    if status_update in {"resolved", "pending_docs", "follow_up"}:
        thread.status = "resolved" if status_update == "resolved" else "pending"
    thread.save(update_fields=["last_activity_at", "status", "updated_at"])

    recipients = set()
    if thread.created_by_id and thread.created_by_id != getattr(author, "id", None):
        recipients.add(thread.created_by)
    if thread.assigned_to_id and thread.assigned_to_id != getattr(author, "id", None):
        recipients.add(thread.assigned_to)
    for mentioned_user in mentions:
        if mentioned_user.id != getattr(author, "id", None):
            recipients.add(mentioned_user)

    if recipients:
        create_notification(
            recipients=list(recipients),
            category="operational",
            priority="info",
            event_key="comment.new",
            title=f"New comment in {thread.title}",
            message=(body[:117] + "...") if len(body) > 120 else body,
            actor=author,
            link_url=f"/communications/?thread={thread.id}",
            action_label="Open Thread",
            content_object=thread.content_object or thread,
            metadata={"thread_id": thread.id},
            dedupe_window_hours=0,
        )
    return entry


def create_thread_for_object(
    *,
    title,
    scope,
    created_by,
    content_object=None,
    assigned_to=None,
    tags=None,
    visibility=None,
):
    thread = CommunicationThread.objects.create(
        title=title,
        scope=scope,
        created_by=created_by,
        assigned_to=assigned_to,
        content_object=content_object,
        tags=tags or [],
        visibility=visibility or [],
    )
    touch_thread_participant(thread, created_by, mark_read=True)
    if assigned_to and assigned_to != created_by:
        touch_thread_participant(thread, assigned_to)
    return thread


def seed_operational_notifications():
    now = timezone.now()

    recent_enquiry = Enquiry.objects.order_by("-created_at").first()
    if recent_enquiry:
        create_role_notification(
            role_key="counselor",
            category="admissions",
            priority="info",
            event_key="seed.enquiry.recent",
            title="Recent enquiry requires follow-up",
            message=f"{recent_enquiry.name} submitted an enquiry for {recent_enquiry.get_display_course()}.",
            link_url="/enquiry/",
            action_label="Review Enquiries",
            content_object=recent_enquiry,
            dedupe_window_hours=12,
        )

    overdue_students = AdmittedStudent.objects.filter(
        is_archived=False,
        total_fees__gt=0,
        paid_fees__lt=F("total_fees"),
    ).order_by("admission_date")[:8]
    for student in overdue_students:
        create_role_notification(
            role_key="accountant",
            category="financial",
            priority="pending",
            event_key="seed.fees.pending",
            title="Fee follow-up pending",
            message=f"{student.full_name} has pending fees of Rs. {student.remaining_fees}.",
            link_url="/payment-tracking/",
            action_label="Open Tracking",
            content_object=student,
            due_at=now,
            metadata={"student_id": student.id},
            dedupe_window_hours=24,
        )


def get_recent_threads_for_user(user, limit=8):
    qs = CommunicationThread.objects.select_related("created_by", "assigned_to").order_by("-last_activity_at")
    if user.is_superuser:
        return qs[:limit]

    visible = []
    for thread in qs[: max(limit * 4, 20)]:
        if can_access_thread(user, thread):
            visible.append(thread)
        if len(visible) >= limit:
            break
    return visible

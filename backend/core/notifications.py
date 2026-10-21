from notifications.models import Notification


def create_notification(user, title, message, notification_type="SYSTEM"):
    if not user or not getattr(user, "pk", None):
        return None
    return Notification.objects.create(
        recipient=user,
        title=title,
        message=message,
        notification_type=notification_type,
    )

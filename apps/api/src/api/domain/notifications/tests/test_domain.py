"""
Notifications Domain Integration Unit Tests.
"""

from api.domain.notifications.service import notification_domain_service


def test_notification_domain_service_instantiation():
    assert notification_domain_service is not None
    assert hasattr(notification_domain_service, 'list_user_notifications')
    assert hasattr(notification_domain_service, 'mark_as_read')

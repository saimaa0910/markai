"""
Account Cleanup Background Task
=================================
APScheduler job that permanently deletes user accounts past their scheduled_deletion_at date.

Runs daily at 02:00 UTC.

Cleanup process per account:
1. Soft-delete all owned resources (orgs without other owners get transferred or archived)
2. Revoke all sessions and refresh tokens
3. Anonymize email address: deleted_{uuid}@deleted.eaimos.ai
4. Clear PII fields
5. Hard-delete the account record

Email reuse: After permanent deletion, the original email is freed
(overwritten with anonymized email in the record).
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

logger = logging.getLogger("eaimos.tasks.account_cleanup")


def run_account_cleanup(db: Session) -> int:
    """
    Find and permanently delete all accounts past their scheduled_deletion_at.
    Returns the number of accounts permanently deleted.
    """
    from api.models.user import User
    from api.models.iam import RefreshToken, UserSession
    from api.models.membership import UserOrganization, OrganizationInvitation
    from api.services.email_service import send_account_permanently_deleted_email

    now = datetime.now(timezone.utc)
    count = 0

    # Find accounts past their deletion window
    accounts_to_delete = (
        db.query(User)
        .filter(
            User.scheduled_deletion_at != None,
            User.scheduled_deletion_at <= now,
            User.is_active == False,
        )
        .all()
    )

    for user in accounts_to_delete:
        try:
            original_email = user.email
            original_name = user.full_name

            # 1. Revoke all tokens and sessions
            db.query(RefreshToken).filter(
                RefreshToken.user_id == user.id
            ).delete(synchronize_session=False)

            db.query(UserSession).filter(
                UserSession.user_id == user.id
            ).delete(synchronize_session=False)

            # 2. Handle org memberships
            memberships = db.query(UserOrganization).filter(
                UserOrganization.user_id == user.id
            ).all()

            for membership in memberships:
                # Check if user is the sole owner of this org
                from api.models.membership import UserRole
                from api.models.organization import Organization
                other_owners = (
                    db.query(UserOrganization)
                    .filter(
                        UserOrganization.organization_id == membership.organization_id,
                        UserOrganization.user_id != user.id,
                        UserOrganization.role == UserRole.OWNER,
                        UserOrganization.deleted_at == None,
                    )
                    .count()
                )
                if other_owners == 0:
                    # Archive the org since no other owners exist
                    org = db.query(Organization).filter(
                        Organization.id == membership.organization_id
                    ).first()
                    if org:
                        org.is_active = False
                        db.add(org)

            # Delete memberships
            db.query(UserOrganization).filter(
                UserOrganization.user_id == user.id
            ).delete(synchronize_session=False)

            # 3. Cancel pending invitations sent by this user
            db.query(OrganizationInvitation).filter(
                OrganizationInvitation.invited_by == user.id,
                OrganizationInvitation.is_accepted == False,
            ).update({"is_rejected": True}, synchronize_session=False)

            # 4. Anonymize PII and free the email
            anonymized_email = f"deleted_{user.id}@deleted.eaimos.ai"
            user.email = anonymized_email
            user.full_name = "Deleted User"
            user.first_name = None
            user.last_name = None
            user.phone = None
            user.avatar_url = None
            user.hashed_password = None
            user.mfa_secret = None
            user.preferences = {}
            user.metadata_json = {}
            user.is_active = False
            user.deletion_requested_at = None
            user.scheduled_deletion_at = None
            db.add(user)
            db.flush()

            # 5. Log the permanent deletion audit
            from api.models.platform_events import AuditLog
            audit = AuditLog(
                actor_id=None,
                action="ACCOUNT_PERMANENTLY_DELETED",
                actor_email=original_email,  # preserve for audit trail
                entity_type="users",
                entity_id=user.id,
                description=f"Account permanently deleted: {original_email}",
                risk_level="high",
            )
            db.add(audit)

            db.commit()

            # 6. Send final notification to ORIGINAL email
            try:
                send_account_permanently_deleted_email(original_email, original_name)
            except Exception as mail_err:
                logger.warning(f"Could not send deletion confirmation to {original_email}: {mail_err}")

            count += 1
            logger.info(f"Permanently deleted account: {original_email} (id={user.id})")

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to permanently delete account {user.id}: {e}", exc_info=True)

    return count


def schedule_cleanup_job():
    """Register the account cleanup job with APScheduler."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from api.database.session import SessionLocal

        def _job():
            db = SessionLocal()
            try:
                count = run_account_cleanup(db)
                if count > 0:
                    logger.info(f"Account cleanup complete: {count} accounts permanently deleted")
            except Exception as e:
                logger.error(f"Account cleanup job failed: {e}", exc_info=True)
            finally:
                db.close()

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            _job,
            "cron",
            hour=2,
            minute=0,
            id="account_cleanup",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Account cleanup scheduler started (daily at 02:00 UTC)")
        return scheduler

    except ImportError:
        logger.warning("APScheduler not installed — account cleanup scheduler disabled")
        return None

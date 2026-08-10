"""Device Trust Service — Sprint 8.3.1 Phase 4

Manages trusted device lifecycle for reducing authentication friction while
maintaining security.

Core Features:
- Device fingerprinting and trust establishment
- Trust verification for MFA bypass
- Device lifecycle management (list, revoke)
- Automatic expiration and cleanup

Security Considerations:
- Device fingerprints are probabilistic (not 100% reliable)
- Trust duration is configurable per user/org
- Admins can force-revoke all devices
- All actions are audit-logged
"""
import uuid
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


logger = logging.getLogger(__name__)


class DeviceTrustService:
    """Service for managing trusted devices."""
    
    @staticmethod
    def generate_device_fingerprint(
        user_agent: str,
        ip_address: str,
        accept_language: str = None,
    ) -> str:
        """
        Generate device fingerprint from request metadata.
        
        Note: This is a simple implementation. Production systems might use
        more sophisticated browser fingerprinting libraries.
        
        Args:
            user_agent: Browser user agent string
            ip_address: Client IP address
            accept_language: Browser language preference
            
        Returns:
            SHA-256 hash as hex string
        """
        components = [
            user_agent or "",
            ip_address or "",
            accept_language or "",
        ]
        fingerprint_str = "|".join(components)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()
    
    @staticmethod
    async def trust_device(
        db: AsyncSession,
        user_id: uuid.UUID,
        device_fingerprint: str,
        device_info: Dict[str, Any],
        duration_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Mark a device as trusted for a user.
        
        Args:
            db: Database session
            user_id: User ID
            device_fingerprint: Unique device identifier
            device_info: Device metadata (name, type, browser, os, ip, location)
            duration_days: Trust duration (None = use user preference)
            
        Returns:
            Trusted device record
            
        Raises:
            ValueError: If user not found or device trust disabled
        """
        from api.models.user import User
        
        # Get user and check if device trust is enabled
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        if not user.trusted_devices_enabled:
            raise ValueError("Device trust is disabled for this user")
        
        # Determine trust duration
        if duration_days is None:
            duration_days = user.trust_device_duration_days or 30
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days) if duration_days > 0 else None
        
        # Check if device already exists
        from api.models.security import TrustedDevice
        
        result = await db.execute(
            select(TrustedDevice).where(
                and_(
                    TrustedDevice.user_id == user_id,
                    TrustedDevice.device_fingerprint == device_fingerprint,
                    TrustedDevice.is_active == True,
                )
            )
        )
        existing_device = result.scalar_one_or_none()
        
        if existing_device:
            # Update existing device
            existing_device.trusted_at = datetime.now(timezone.utc)
            existing_device.expires_at = expires_at
            existing_device.last_used_at = datetime.now(timezone.utc)
            existing_device.device_name = device_info.get("device_name", existing_device.device_name)
            existing_device.updated_at = datetime.now(timezone.utc)
            
            await db.commit()
            await db.refresh(existing_device)
            
            logger.info(
                f"Updated trusted device for user {user_id}: "
                f"device_id={existing_device.id}, fingerprint={device_fingerprint[:16]}..."
            )
            
            return {
                "id": str(existing_device.id),
                "device_name": existing_device.device_name,
                "device_type": existing_device.device_type,
                "trusted_at": existing_device.trusted_at.isoformat(),
                "expires_at": existing_device.expires_at.isoformat() if existing_device.expires_at else None,
                "is_active": existing_device.is_active,
            }
        
        # Create new trusted device
        trusted_device = TrustedDevice(
            user_id=user_id,
            device_fingerprint=device_fingerprint,
            device_name=device_info.get("device_name"),
            device_type=device_info.get("device_type"),
            browser=device_info.get("browser"),
            os=device_info.get("os"),
            ip_address=device_info.get("ip_address"),
            location=device_info.get("location"),
            trusted_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            is_active=True,
        )
        
        db.add(trusted_device)
        await db.commit()
        await db.refresh(trusted_device)
        
        logger.info(
            f"Created trusted device for user {user_id}: "
            f"device_id={trusted_device.id}, fingerprint={device_fingerprint[:16]}..."
        )
        
        return {
            "id": str(trusted_device.id),
            "device_name": trusted_device.device_name,
            "device_type": trusted_device.device_type,
            "browser": trusted_device.browser,
            "os": trusted_device.os,
            "location": trusted_device.location,
            "trusted_at": trusted_device.trusted_at.isoformat(),
            "expires_at": trusted_device.expires_at.isoformat() if trusted_device.expires_at else None,
            "is_active": trusted_device.is_active,
        }
    
    @staticmethod
    async def verify_trusted_device(
        db: AsyncSession,
        user_id: uuid.UUID,
        device_fingerprint: str,
    ) -> bool:
        """
        Check if a device is trusted for a user.
        
        Args:
            db: Database session
            user_id: User ID
            device_fingerprint: Device fingerprint to verify
            
        Returns:
            True if device is trusted and active, False otherwise
        """
        from api.models.security import TrustedDevice
        
        now = datetime.now(timezone.utc)
        
        result = await db.execute(
            select(TrustedDevice).where(
                and_(
                    TrustedDevice.user_id == user_id,
                    TrustedDevice.device_fingerprint == device_fingerprint,
                    TrustedDevice.is_active == True,
                    or_(
                        TrustedDevice.expires_at == None,
                        TrustedDevice.expires_at > now,
                    ),
                )
            )
        )
        device = result.scalar_one_or_none()
        
        if device:
            # Update last_used_at
            device.last_used_at = now
            device.updated_at = now
            await db.commit()
            
            logger.debug(
                f"Verified trusted device for user {user_id}: "
                f"device_id={device.id}, fingerprint={device_fingerprint[:16]}..."
            )
            return True
        
        logger.debug(
            f"Device not trusted for user {user_id}: "
            f"fingerprint={device_fingerprint[:16]}..."
        )
        return False
    
    @staticmethod
    async def list_trusted_devices(
        db: AsyncSession,
        user_id: uuid.UUID,
        include_revoked: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        List all trusted devices for a user.
        
        Args:
            db: Database session
            user_id: User ID
            include_revoked: Include revoked devices
            
        Returns:
            List of trusted device records
        """
        from api.models.security import TrustedDevice
        
        conditions = [TrustedDevice.user_id == user_id]
        
        if not include_revoked:
            conditions.append(TrustedDevice.is_active == True)
        
        result = await db.execute(
            select(TrustedDevice)
            .where(and_(*conditions))
            .order_by(TrustedDevice.trusted_at.desc())
        )
        devices = result.scalars().all()
        
        return [
            {
                "id": str(device.id),
                "device_name": device.device_name,
                "device_type": device.device_type,
                "browser": device.browser,
                "os": device.os,
                "ip_address": device.ip_address,
                "location": device.location,
                "trusted_at": device.trusted_at.isoformat(),
                "expires_at": device.expires_at.isoformat() if device.expires_at else None,
                "last_used_at": device.last_used_at.isoformat() if device.last_used_at else None,
                "is_active": device.is_active,
                "revoked_at": device.revoked_at.isoformat() if device.revoked_at else None,
                "revoke_reason": device.revoke_reason,
            }
            for device in devices
        ]
    
    @staticmethod
    async def revoke_device(
        db: AsyncSession,
        user_id: uuid.UUID,
        device_id: uuid.UUID,
        revoked_by: Optional[uuid.UUID] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Revoke trust for a specific device.
        
        Args:
            db: Database session
            user_id: User ID (device owner)
            device_id: Device ID to revoke
            revoked_by: User ID who performed revocation (for admin actions)
            reason: Reason for revocation
            
        Returns:
            True if device was revoked, False if not found
        """
        from api.models.security import TrustedDevice
        
        result = await db.execute(
            select(TrustedDevice).where(
                and_(
                    TrustedDevice.id == device_id,
                    TrustedDevice.user_id == user_id,
                )
            )
        )
        device = result.scalar_one_or_none()
        
        if not device:
            logger.warning(f"Device {device_id} not found for user {user_id}")
            return False
        
        device.is_active = False
        device.revoked_at = datetime.now(timezone.utc)
        device.revoked_by = revoked_by
        device.revoke_reason = reason or "User requested"
        device.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        logger.info(
            f"Revoked trusted device for user {user_id}: "
            f"device_id={device_id}, reason={reason}"
        )
        
        return True
    
    @staticmethod
    async def revoke_all_devices(
        db: AsyncSession,
        user_id: uuid.UUID,
        revoked_by: Optional[uuid.UUID] = None,
        reason: str = "User requested",
    ) -> int:
        """
        Revoke all trusted devices for a user.
        
        Args:
            db: Database session
            user_id: User ID
            revoked_by: User ID who performed revocation
            reason: Reason for revocation
            
        Returns:
            Number of devices revoked
        """
        from api.models.security import TrustedDevice
        
        now = datetime.now(timezone.utc)
        
        result = await db.execute(
            update(TrustedDevice)
            .where(
                and_(
                    TrustedDevice.user_id == user_id,
                    TrustedDevice.is_active == True,
                )
            )
            .values(
                is_active=False,
                revoked_at=now,
                revoked_by=revoked_by,
                revoke_reason=reason,
                updated_at=now,
            )
        )
        
        count = result.rowcount
        await db.commit()
        
        logger.info(
            f"Revoked all trusted devices for user {user_id}: "
            f"count={count}, reason={reason}"
        )
        
        return count
    
    @staticmethod
    async def cleanup_expired_devices(db: AsyncSession) -> int:
        """
        Deactivate expired trusted devices.
        
        This is a maintenance task that should run periodically (e.g., daily cron).
        
        Args:
            db: Database session
            
        Returns:
            Number of devices deactivated
        """
        from api.models.security import TrustedDevice
        
        now = datetime.now(timezone.utc)
        
        result = await db.execute(
            update(TrustedDevice)
            .where(
                and_(
                    TrustedDevice.is_active == True,
                    TrustedDevice.expires_at != None,
                    TrustedDevice.expires_at < now,
                )
            )
            .values(
                is_active=False,
                revoked_at=now,
                revoke_reason="Expired",
                updated_at=now,
            )
        )
        
        count = result.rowcount
        await db.commit()
        
        logger.info(f"Cleaned up {count} expired trusted devices")
        
        return count

"""Audit Service for SecondLook Audit Trail & Compliance Traceability (Task 15).

Provides an append-only audit trail logging user and system actions, including requirement
approvals/rejections, compliance evaluation runs, government verifications, and document accesses.
Strictly append-only: No update or deletion capabilities.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Append-only audit service for tracking security, compliance, and verification events."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db

    def _get_session(self) -> Tuple[Session, bool]:
        if self.db is not None:
            return self.db, False
        if SessionLocal is not None:
            return SessionLocal(), True
        raise RuntimeError("Database session unavailable")

    def record_event(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[Union[uuid.UUID, str]] = None,
        user_id: Optional[Union[uuid.UUID, str]] = None,
        details: Optional[Dict[str, Any]] = None,
        session: Optional[Session] = None,
    ) -> AuditLog:
        """Record an immutable, append-only audit log entry."""
        sess = session
        should_close = False
        if sess is None:
            sess, should_close = self._get_session()

        try:
            e_uuid: Optional[uuid.UUID] = None
            if entity_id is not None:
                try:
                    e_uuid = uuid.UUID(str(entity_id))
                except ValueError:
                    e_uuid = None

            u_uuid: Optional[uuid.UUID] = None
            if user_id is not None:
                try:
                    u_uuid = uuid.UUID(str(user_id))
                except ValueError:
                    u_uuid = None

            log_entry = AuditLog(
                id=uuid.uuid4(),
                user_id=u_uuid,
                action=action,
                entity_type=entity_type,
                entity_id=e_uuid,
                details=details or {},
                created_at=datetime.now(timezone.utc),
            )
            sess.add(log_entry)
            sess.commit()
            sess.refresh(log_entry)
            logger.info("Audit log recorded: [%s] on %s:%s", action, entity_type, entity_id)
            return log_entry
        finally:
            if should_close and sess is not None:
                sess.close()

    def list_events(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[Union[uuid.UUID, str]] = None,
        action: Optional[str] = None,
        user_id: Optional[Union[uuid.UUID, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
        session: Optional[Session] = None,
    ) -> Tuple[List[AuditLog], int]:
        """List audit events with optional filtering and pagination."""
        sess = session
        should_close = False
        if sess is None:
            sess, should_close = self._get_session()

        try:
            stmt = select(AuditLog)
            count_stmt = select(func.count(AuditLog.id))

            if entity_type:
                stmt = stmt.where(AuditLog.entity_type == entity_type)
                count_stmt = count_stmt.where(AuditLog.entity_type == entity_type)

            if entity_id:
                try:
                    e_uuid = uuid.UUID(str(entity_id))
                    stmt = stmt.where(AuditLog.entity_id == e_uuid)
                    count_stmt = count_stmt.where(AuditLog.entity_id == e_uuid)
                except ValueError:
                    pass

            if action:
                stmt = stmt.where(AuditLog.action == action)
                count_stmt = count_stmt.where(AuditLog.action == action)

            if user_id:
                try:
                    u_uuid = uuid.UUID(str(user_id))
                    stmt = stmt.where(AuditLog.user_id == u_uuid)
                    count_stmt = count_stmt.where(AuditLog.user_id == u_uuid)
                except ValueError:
                    pass

            if start_time:
                stmt = stmt.where(AuditLog.created_at >= start_time)
                count_stmt = count_stmt.where(AuditLog.created_at >= start_time)

            if end_time:
                stmt = stmt.where(AuditLog.created_at <= end_time)
                count_stmt = count_stmt.where(AuditLog.created_at <= end_time)

            total = sess.scalar(count_stmt) or 0
            stmt = stmt.order_by(desc(AuditLog.created_at)).limit(limit).offset(offset)
            items = list(sess.execute(stmt).scalars().all())

            return items, total
        finally:
            if should_close and sess is not None:
                sess.close()

    def get_event(
        self, event_id: Union[uuid.UUID, str], session: Optional[Session] = None
    ) -> Optional[AuditLog]:
        """Retrieve a specific audit event by ID."""
        sess = session
        should_close = False
        if sess is None:
            sess, should_close = self._get_session()

        try:
            ev_uuid = uuid.UUID(str(event_id))
            return sess.get(AuditLog, ev_uuid)
        except (ValueError, TypeError):
            return None
        finally:
            if should_close and sess is not None:
                sess.close()


_audit_service_instance: Optional[AuditService] = None


def get_audit_service(db: Optional[Session] = None) -> AuditService:
    """Singleton / factory accessor for AuditService."""
    global _audit_service_instance
    if db is not None:
        return AuditService(db)
    if _audit_service_instance is None:
        _audit_service_instance = AuditService()
    return _audit_service_instance

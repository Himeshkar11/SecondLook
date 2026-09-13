from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.authz.dependencies import require_officer
from app.dashboard.service import DashboardService
from app.models.user import ApplicationRole

router = APIRouter(prefix="/api/v1/tenders")


@router.get("/{tender_id}/dashboard", tags=["Dashboard"])
def get_tender_dashboard(
    tender_id: str,
    db: Session = Depends(get_db),
    _officer=Depends(require_officer),
):
    try:
        return DashboardService(db).get_dashboard(tender_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": str(exc), "details": {}}}) from exc


@router.get("/{tender_id}/dashboard/requirements", tags=["Dashboard"])
def get_tender_dashboard_requirements(
    tender_id: str,
    db: Session = Depends(get_db),
    _officer=Depends(require_officer),
):
    try:
        return DashboardService(db).get_requirement_dashboard(tender_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": str(exc), "details": {}}}) from exc

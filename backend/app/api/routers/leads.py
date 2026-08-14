"""Public marketing lead capture."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import get_app_settings
from app.core.config import Settings
from app.core.rate_limit import enforce_leads_rate_limit
from app.schemas.leads import LeadCreate, LeadCreated
from app.services.lead_service import LeadService

router = APIRouter(prefix="/api", tags=["leads"])


def get_lead_service(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> LeadService:
    return LeadService(settings)


@router.post(
    "/leads",
    status_code=status.HTTP_201_CREATED,
    response_model=LeadCreated,
    dependencies=[Depends(enforce_leads_rate_limit)],
)
async def create_lead(
    request: Request,
    body: LeadCreate,
    service: Annotated[LeadService, Depends(get_lead_service)],
) -> LeadCreated:
    client_ip = request.client.host if request.client else None
    return await service.submit(body, client_ip=client_ip)

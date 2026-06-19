"""Global student leaderboard (Phase 13, SPEC §1.8).

| Method | Path              | Role    | Query                         | Response              |
|--------|-------------------|---------|-------------------------------|-----------------------|
| GET    | /api/leaderboard  | student | period=week\|all_time, limit  | list[LeaderboardEntry] |
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.api.deps import StudentUser, get_activity_service
from app.schemas.activity import LeaderboardEntry
from app.services.activity_service import ActivityService

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    student: StudentUser,
    activity: Annotated[ActivityService, Depends(get_activity_service)],
    period: Literal["week", "all_time"] = "week",
    limit: int = Query(default=50, ge=1, le=100),
) -> list[LeaderboardEntry]:
    del student  # auth gate only; leaderboard is global
    return await activity.get_leaderboard(period=period, limit=limit)

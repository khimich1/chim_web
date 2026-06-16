"""Shared enumerations for app DB models."""

from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"


class ExamTrack(str, enum.Enum):
    EGE = "ege"
    OGE = "oge"

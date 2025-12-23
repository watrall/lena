from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class CourseSummary(BaseModel):
    id: str
    name: str
    code: Optional[str] = None
    term: Optional[str] = None

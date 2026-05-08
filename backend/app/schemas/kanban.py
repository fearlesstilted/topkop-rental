from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import KanbanColumn


class ChecklistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    label: str
    done: bool
    sort_order: int
    done_at: datetime | None
    done_by_user_id: int | None


class ChecklistItemCreate(BaseModel):
    label: str
    sort_order: int = 0


class CardCreate(BaseModel):
    equipment_id: int
    rental_id: int | None = None
    title: str
    checklist: list[ChecklistItemCreate] = Field(default_factory=list)
    notes: str | None = None


class CardUpdate(BaseModel):
    title: str | None = None
    column: KanbanColumn | None = None
    sort_order: int | None = None
    assigned_user_id: int | None = None
    assigned_worker: str | None = None
    notes: str | None = None


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    equipment_id: int
    rental_id: int | None
    title: str
    column: KanbanColumn
    sort_order: int
    assigned_user_id: int | None
    assigned_worker: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    checklist: list[ChecklistItemOut] = Field(default_factory=list)

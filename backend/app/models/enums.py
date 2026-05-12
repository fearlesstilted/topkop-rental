from enum import StrEnum


class UserRole(StrEnum):
    BIURO = "biuro"
    MECHANIK = "mechanik"
    MANAGER = "manager"


class TrackingType(StrEnum):
    """Meter unit used for rental overage calculations."""

    MTH = "mth"
    RBH = "rbh"
    DAILY_ONLY = "daily"


class EquipmentStatus(StrEnum):
    AVAILABLE = "available"
    RENTED = "rented"
    SERVICE = "service"
    BROKEN = "broken"


class RentalStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    RETURNED = "returned"
    CANCELLED = "cancelled"


class RentalBillingMode(StrEnum):
    DAILY = "daily"
    HOURLY = "hourly"


class InspectionType(StrEnum):
    PICKUP = "pickup"
    RETURN = "return"


class KanbanColumn(StrEnum):
    NA_SERWIS = "na_serwis"
    W_TRAKCIE = "w_trakcie"
    GOTOWE = "gotowe"
    WYDANA = "wydana"


class BillingEntity(StrEnum):
    """Legal entity captured on a rental agreement snapshot."""

    TOPKOP_JDG = "topkop_jdg"
    TK_SPZOO = "tk_spzoo"

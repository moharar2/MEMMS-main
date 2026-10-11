"""
Consolidated models export for MEMMS.
"""
from src.models.base import BaseModel
from src.models.role import Role
from src.models.user import User
from src.models.audit import AuditLog
from src.models.hospital import Hospital, Department, Location
from src.models.vendor import Vendor, VendorEngineer
from src.models.contract import Contract
from src.models.technician import (
    Technician, TechnicianQualification,
    TechnicianExperience, TechnicianCompensation
)
from src.models.equipment import (
    Equipment, EquipmentTransfer,
    EquipmentAccessory, EquipmentReceiving
)
from src.models.work_order import WorkOrder, WorkOrderLog, WorkOrderPart
from src.models.preventive import PMPlan, PMSchedule, PMExecution
from src.models.inventory import SparePart, InventoryTransaction
from src.models.attachment import Attachment
from src.models.report import GeneratedReport

__all__ = [
    "BaseModel",
    "Role",
    "User",
    "AuditLog",
    "Hospital",
    "Department",
    "Location",
    "Vendor",
    "VendorEngineer",
    "Contract",
    "Technician",
    "TechnicianQualification",
    "TechnicianExperience",
    "TechnicianCompensation",
    "Equipment",
    "EquipmentTransfer",
    "EquipmentAccessory",
    "EquipmentReceiving",
    "WorkOrder",
    "WorkOrderLog",
    "WorkOrderPart",
    "PMPlan",
    "PMSchedule",
    "PMExecution",
    "SparePart",
    "InventoryTransaction",
    "Attachment",
    "GeneratedReport"
]

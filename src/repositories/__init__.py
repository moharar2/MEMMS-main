"""
Repositories package for MEMMS.
"""
from src.repositories.base_repository import BaseRepository
from src.models import (
    User, Role, AuditLog, Hospital, Department, Location,
    Vendor, Contract, Technician, Equipment, EquipmentTransfer,
    WorkOrder, WorkOrderLog, WorkOrderPart, PMPlan, PMSchedule,
    PMExecution, SparePart, InventoryTransaction, Attachment
)

user_repo = BaseRepository(User)
role_repo = BaseRepository(Role)
audit_repo = BaseRepository(AuditLog)
hospital_repo = BaseRepository(Hospital)
department_repo = BaseRepository(Department)
location_repo = BaseRepository(Location)
vendor_repo = BaseRepository(Vendor)
contract_repo = BaseRepository(Contract)
technician_repo = BaseRepository(Technician)
equipment_repo = BaseRepository(Equipment)
equipment_transfer_repo = BaseRepository(EquipmentTransfer)
work_order_repo = BaseRepository(WorkOrder)
work_order_log_repo = BaseRepository(WorkOrderLog)
work_order_part_repo = BaseRepository(WorkOrderPart)
pm_plan_repo = BaseRepository(PMPlan)
pm_schedule_repo = BaseRepository(PMSchedule)
pm_execution_repo = BaseRepository(PMExecution)
spare_part_repo = BaseRepository(SparePart)
inventory_tx_repo = BaseRepository(InventoryTransaction)
attachment_repo = BaseRepository(Attachment)

__all__ = [
    "BaseRepository",
    "user_repo", "role_repo", "audit_repo", "hospital_repo",
    "department_repo", "location_repo", "vendor_repo", "contract_repo",
    "technician_repo", "equipment_repo", "equipment_transfer_repo",
    "work_order_repo", "work_order_log_repo", "work_order_part_repo",
    "pm_plan_repo", "pm_schedule_repo", "pm_execution_repo",
    "spare_part_repo", "inventory_tx_repo", "attachment_repo"
]

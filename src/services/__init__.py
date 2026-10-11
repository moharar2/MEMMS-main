"""
Services package for MEMMS business logic.
"""
from src.services.audit_service import audit_service, AuditService
from src.services.auth_service import auth_service, AuthService
from src.services.hospital_service import hospital_service, HospitalService
from src.services.vendor_service import vendor_service, VendorService
from src.services.equipment_service import equipment_service, EquipmentService
from src.services.work_order_service import work_order_service, WorkOrderService
from src.services.report_service import report_service, ReportService

__all__ = [
    "audit_service", "AuditService",
    "auth_service", "AuthService",
    "hospital_service", "HospitalService",
    "vendor_service", "VendorService",
    "equipment_service", "EquipmentService",
    "work_order_service", "WorkOrderService",
    "report_service", "ReportService"
]


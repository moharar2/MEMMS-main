"""
Views package for MEMMS.
All enterprise views and dialogs, organized by module phase.
"""
# Phase 3 — Core Operational Views
from src.ui.views.dashboard_view import DashboardView
from src.ui.views.equipment_view import EquipmentView
from src.ui.views.departments_view import DepartmentsView
from src.ui.views.vendors_view import VendorsView
from src.ui.views.work_orders_view import WorkOrdersView
from src.ui.views.placeholder_view import PlaceholderView

# Phase 3 — Dialogs
from src.ui.views.equipment_dialog import EquipmentDialog
from src.ui.views.equipment_details_dialog import EquipmentDetailsDialog
from src.ui.views.transfer_dialog import TransferDialog
from src.ui.views.department_dialog import DepartmentDialog
from src.ui.views.vendor_dialog import VendorDialog
from src.ui.views.work_order_dialog import WorkOrderDialog

# Phase 4 — Technicians Management
from src.ui.views.technicians_view import TechniciansView
from src.ui.views.technician_dialog import TechnicianDialog

# Phase 5 — Preventive Maintenance
from src.ui.views.preventive_view import PreventiveView
from src.ui.views.pm_plan_dialog import PMPlanDialog
from src.ui.views.pm_execution_dialog import PMExecutionDialog

# Phase 6 — Spare Parts & Inventory Control
from src.ui.views.inventory_view import InventoryView
from src.ui.views.spare_part_dialog import SparePartDialog
from src.ui.views.stock_transaction_dialog import StockTransactionDialog

# Phase 6 — Contracts & Warranty
from src.ui.views.contracts_view import ContractsView
from src.ui.views.contract_dialog import ContractDialog

# Phase 7 — Audit Logs & System Settings & User Management
from src.ui.views.audit_logs_view import AuditLogsView
from src.ui.views.settings_view import SettingsView
from src.ui.views.users_view import UsersView
from src.ui.views.user_dialog import UserDialog
from src.ui.views.user_password_dialog import UserPasswordDialog

# Phase 8 — Reports & Analytics
from src.ui.views.reports_view import ReportsView

__all__ = [
    # Core
    "DashboardView",
    "EquipmentView",
    "DepartmentsView",
    "VendorsView",
    "WorkOrdersView",
    "PlaceholderView",
    # Core Dialogs
    "EquipmentDialog",
    "EquipmentDetailsDialog",
    "TransferDialog",
    "DepartmentDialog",
    "VendorDialog",
    "WorkOrderDialog",
    # Technicians
    "TechniciansView",
    "TechnicianDialog",
    # PM
    "PreventiveView",
    "PMPlanDialog",
    "PMExecutionDialog",
    # Inventory
    "InventoryView",
    "SparePartDialog",
    "StockTransactionDialog",
    # Contracts
    "ContractsView",
    "ContractDialog",
    # System & Users
    "AuditLogsView",
    "SettingsView",
    "UsersView",
    "UserDialog",
    "UserPasswordDialog",
    # Reports
    "ReportsView",
]



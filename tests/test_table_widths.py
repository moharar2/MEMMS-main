"""
Verification test to validate DataTable sizing and responsiveness across all system views.
"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from src.ui.components.data_table import DataTable
from src.ui.views.equipment_view import EquipmentView
from src.ui.views.work_orders_view import WorkOrdersView
from src.ui.views.inventory_view import InventoryView
from src.ui.views.technicians_view import TechniciansView
from src.ui.views.reports_view import ReportsView
from src.ui.views.preventive_view import PreventiveView
from src.ui.views.departments_view import DepartmentsView
from src.ui.views.vendors_view import VendorsView
from src.ui.views.contracts_view import ContractsView
from src.ui.views.audit_logs_view import AuditLogsView
from src.ui.views.users_view import UsersView
from src.ui.views.dashboard_view import DashboardView


def test_all_views_tables():
    app = QApplication.instance() or QApplication(sys.argv)

    # 1. Test DataTable component directly
    dt = DataTable(headers=["Col1", "Col2", "Col3"])
    dt.set_column_widths([100, 200, 300], stretch_cols=[1])
    assert dt.table.columnCount() == 3
    assert dt._min_widths == [100, 200, 300]
    assert dt._stretch_cols == [1]
    assert dt.table.horizontalHeader().defaultAlignment() == (Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

    # 2. Test instantiation of all views
    eq_v = EquipmentView()
    assert eq_v.table_widget.table.columnCount() == 8
    assert eq_v.table_widget._min_widths == [110, 190, 150, 155, 110, 115, 120, 130]

    wo_v = WorkOrdersView()
    assert wo_v.table_widget.table.columnCount() == 10
    assert wo_v.table_widget._min_widths == [110, 190, 150, 180, 95, 100, 120, 110, 95, 80]

    inv_v = InventoryView()
    assert inv_v.table_widget.table.columnCount() == 9
    assert inv_v.table_widget._min_widths == [45, 115, 185, 130, 125, 115, 110, 125, 155]

    tech_v = TechniciansView()
    assert tech_v.table_widget.table.columnCount() == 9
    assert tech_v.table_widget._min_widths == [45, 95, 150, 160, 110, 110, 110, 90, 80]

    pm_v = PreventiveView()
    assert pm_v.schedules_table.table.columnCount() == 8
    assert pm_v.schedules_table._min_widths == [50, 110, 180, 140, 170, 100, 100, 90]
    assert pm_v.plans_table.table.columnCount() == 7
    assert pm_v.plans_table._min_widths == [50, 200, 150, 100, 100, 120, 80]

    dept_v = DepartmentsView()
    assert dept_v.table_widget.table.columnCount() == 6
    assert dept_v.table_widget._min_widths == [100, 200, 180, 100, 120, 90]

    vend_v = VendorsView()
    assert vend_v.table_widget.table.columnCount() == 6
    assert vend_v.table_widget._min_widths == [200, 140, 150, 120, 180, 110]

    cntr_v = ContractsView()
    assert cntr_v.table_widget.table.columnCount() == 10
    assert cntr_v.table_widget._min_widths == [45, 95, 170, 140, 120, 90, 90, 100, 85, 80]

    aud_v = AuditLogsView()
    assert aud_v.table_widget.table.columnCount() == 7

    user_v = UsersView()
    assert user_v.table_widget.table.columnCount() == 7
    assert user_v.table_widget._min_widths == [45, 120, 180, 140, 160, 95, 120]

    dash_v = DashboardView()
    assert dash_v is not None

    rep_v = ReportsView()
    assert rep_v.table_widget.table is not None

    print("ALL 13 VIEWS AND TABLES INITIALIZED AND VERIFIED SUCCESSFULLY!")


if __name__ == "__main__":
    test_all_views_tables()

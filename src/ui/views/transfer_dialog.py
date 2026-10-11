"""
Dialog for transferring medical equipment between departments and rooms.
Zero emojis, fully localized.
"""
from typing import Union
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QTextEdit, QLabel, QPushButton, QMessageBox, QFrame
)
from sqlalchemy.orm import joinedload
from src.core.i18n import tr, i18n
from src.core.database import get_db
from src.services.equipment_service import equipment_service
from src.services.hospital_service import hospital_service
from src.services.auth_service import auth_service
from src.models.equipment import Equipment
from src.ui.theme.icons import icon


class TransferDialog(QDialog):
    def __init__(self, equipment: Union[Equipment, int], parent=None):
        super().__init__(parent)
        eq_id = equipment if isinstance(equipment, int) else equipment.id
        with get_db() as db:
            self.equipment = db.query(Equipment).options(
                joinedload(Equipment.department),
                joinedload(Equipment.location)
            ).filter_by(id=eq_id).first()

        equipment = self.equipment
        self.setWindowTitle(f"{tr('transfer.title')} — {equipment.asset_number if equipment else ''}")
        self.setFixedSize(520, 420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)

        # Current Location Banner
        curr_dept = "—"
        curr_loc = "—"
        if equipment:
            curr_dept = (equipment.department.name_en if not i18n.is_rtl() and equipment.department.name_en else equipment.department.name_ar) if equipment.department else "—"
            curr_loc = equipment.location.room_name if equipment.location else "—"

        info_card = QFrame()
        info_card.setStyleSheet("""
            background-color: #F0F9FF;
            border: 1px solid #BAE6FD;
            border-radius: 6px;
            padding: 12px;
        """)
        info_layout = QVBoxLayout(info_card)
        info_layout.setSpacing(4)

        eq_title = QLabel(f"<b>{equipment.asset_number}</b> — {equipment.name_en if not i18n.is_rtl() and equipment.name_en else equipment.name_ar}")
        eq_title.setStyleSheet("font-size: 14px; color: #0369A1;")

        loc_lbl = QLabel(f"{tr('transfer.current_location')} <b>{curr_dept}</b> ({tr('transfer.room')}: {curr_loc})")
        loc_lbl.setStyleSheet("font-size: 12px; color: #0284C7;")

        info_layout.addWidget(eq_title)
        info_layout.addWidget(loc_lbl)
        layout.addWidget(info_card)

        # Form
        form = QFormLayout()
        form.setSpacing(12)

        self.to_dept_combo = QComboBox()
        self.to_loc_combo = QComboBox()
        self.reason_input = QTextEdit()
        self.reason_input.setPlaceholderText(tr("transfer.reason"))
        self.reason_input.setMaximumHeight(80)

        form.addRow(tr("transfer.new_department") + " *:", self.to_dept_combo)
        form.addRow(tr("transfer.new_room") + ":", self.to_loc_combo)
        form.addRow(tr("transfer.reason") + ":", self.reason_input)

        layout.addLayout(form)
        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        cancel_btn = QPushButton(tr("common.cancel"))
        cancel_btn.setProperty("variant", "secondary")
        cancel_btn.setIcon(icon("cancel", color="#64748B", size=14))
        cancel_btn.clicked.connect(self.reject)

        transfer_btn = QPushButton(tr("transfer.confirm_button"))
        transfer_btn.setIcon(icon("transfer", color="#FFFFFF", size=14))
        transfer_btn.clicked.connect(self._transfer)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(transfer_btn)
        layout.addLayout(btn_layout)

        self._load_departments()
        self.to_dept_combo.currentIndexChanged.connect(self._on_dept_changed)

    def _load_departments(self):
        with get_db() as db:
            depts = hospital_service.get_departments(db)
            self.to_dept_combo.clear()
            for d in depts:
                name = d.name_en if not i18n.is_rtl() and d.name_en else d.name_ar
                self.to_dept_combo.addItem(f"{name} ({d.code})", d.id)

    def _on_dept_changed(self):
        dept_id = self.to_dept_combo.currentData()
        self.to_loc_combo.clear()
        none_text = "— None —" if not i18n.is_rtl() else "— بدون غرفة محددة —"
        self.to_loc_combo.addItem(none_text, None)
        if dept_id:
            with get_db() as db:
                locs = hospital_service.get_locations(db, department_id=dept_id)
                for loc in locs:
                    self.to_loc_combo.addItem(f"{loc.room_name} ({loc.room_number})", loc.id)

    def _transfer(self):
        to_dept_id = self.to_dept_combo.currentData()
        if not to_dept_id:
            QMessageBox.warning(self, tr("dialog.confirm_title"), tr("dialog.validation_error"))
            return

        to_loc_id = self.to_loc_combo.currentData()
        reason = self.reason_input.toPlainText().strip()
        user = auth_service.current_user

        try:
            with get_db() as db:
                equipment_service.transfer_equipment(
                    db=db,
                    user=user,
                    eq_id=self.equipment.id,
                    to_department_id=to_dept_id,
                    to_location_id=to_loc_id,
                    reason=reason
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, tr("common.error"), str(e))

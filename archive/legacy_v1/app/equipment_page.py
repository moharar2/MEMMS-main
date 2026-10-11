"""Equipment registry CRUD page (Phase 2)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,
    QTableWidget,QTableWidgetItem,QMessageBox,QDialog,QFormLayout,QComboBox,QTextEdit,QDialogButtonBox)
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from database import get_session
from models import Equipment
from .translations import Translator

STATUSES = [("operational", "equipment.status.operational"), ("under_maintenance", "equipment.status.maintenance"),
            ("out_of_service", "equipment.status.out_of_service"), ("retired", "equipment.status.retired")]

class EquipmentDialog(QDialog):
    def __init__(self, translator: Translator, equipment: Equipment | None = None, parent=None):
        super().__init__(parent); self.t=translator; self.equipment=equipment
        self.setMinimumWidth(480)
        form=QFormLayout(self)
        self.code=QLineEdit(); self.name_ar=QLineEdit(); self.name_en=QLineEdit()
        self.model=QLineEdit(); self.manufacturer=QLineEdit(); self.serial=QLineEdit(); self.kind=QLineEdit()
        self.status=QComboBox()
        for value,key in STATUSES: self.status.addItem(self.t.t(key), value)
        self.notes=QTextEdit(); self.notes.setMaximumHeight(90)
        self.fields=[self.code,self.name_ar,self.name_en,self.model,self.manufacturer,self.serial,self.kind]
        for key,w in [("equipment.field.code",self.code),("equipment.field.name_ar",self.name_ar),("equipment.field.name_en",self.name_en),
                      ("equipment.field.model",self.model),("equipment.field.manufacturer",self.manufacturer),
                      ("equipment.field.serial",self.serial),("equipment.field.type",self.kind),("equipment.field.status",self.status),
                      ("equipment.field.notes",self.notes)]: form.addRow(self.t.t(key),w)
        self.buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._validate); self.buttons.rejected.connect(self.reject); form.addRow(self.buttons)
        if equipment:
            self.code.setText(equipment.hospital_code); self.name_ar.setText(equipment.name_ar); self.name_en.setText(equipment.name_en)
            self.model.setText(equipment.model or ""); self.manufacturer.setText(equipment.manufacturer or "")
            self.serial.setText(equipment.serial_number or ""); self.kind.setText(equipment.equipment_type or "")
            self.notes.setPlainText(equipment.notes or "")
            idx=self.status.findData(equipment.status or "operational"); self.status.setCurrentIndex(max(idx,0))
        self.setWindowTitle(self.t.t("equipment.edit_title" if equipment else "equipment.add_title"))
    def _validate(self):
        if not self.code.text().strip() or not self.name_ar.text().strip() or not self.name_en.text().strip():
            QMessageBox.warning(self,self.t.t("app.error"),self.t.t("equipment.required")); return
        self.accept()
    def values(self):
        return dict(hospital_code=self.code.text().strip(),name_ar=self.name_ar.text().strip(),name_en=self.name_en.text().strip(),
            model=self.model.text().strip() or None,manufacturer=self.manufacturer.text().strip() or None,
            serial_number=self.serial.text().strip() or None,equipment_type=self.kind.text().strip() or None,
            status=self.status.currentData(),notes=self.notes.toPlainText().strip() or None)

class EquipmentPage(QWidget):
    def __init__(self, translator: Translator, parent=None):
        super().__init__(parent); self.t=translator
        root=QVBoxLayout(self); root.setContentsMargins(24,20,24,24); root.setSpacing(14)
        top=QHBoxLayout(); self.heading=QLabel(); self.search=QLineEdit(); self.search.setClearButtonEnabled(True)
        self.add_btn=QPushButton(); self.edit_btn=QPushButton(); self.delete_btn=QPushButton(); self.reload_btn=QPushButton()
        self.add_btn.setObjectName("btnPrimary"); self.edit_btn.setObjectName("btnSecondary")
        self.delete_btn.setObjectName("btnDanger"); self.reload_btn.setObjectName("btnSecondary")
        for b in (self.add_btn,self.edit_btn,self.delete_btn,self.reload_btn): b.setCursor(Qt.PointingHandCursor)
        top.addWidget(self.heading); top.addStretch(1); top.addWidget(self.search,2); top.addWidget(self.add_btn); top.addWidget(self.edit_btn); top.addWidget(self.delete_btn); top.addWidget(self.reload_btn)
        root.addLayout(top)
        self.table=QTableWidget(0,7); self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers); self.table.setAlternatingRowColors(True); self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table,1)
        self.search.textChanged.connect(self.refresh); self.add_btn.clicked.connect(self.add_equipment); self.edit_btn.clicked.connect(self.edit_equipment); self.delete_btn.clicked.connect(self.delete_equipment); self.reload_btn.clicked.connect(self.refresh)
        self.retranslate_ui(self.t.lang); self.refresh()
    def retranslate_ui(self,lang):
        self.heading.setText(self.t.t("equipment.heading")); self.search.setPlaceholderText(self.t.t("equipment.search"))
        self.add_btn.setText(self.t.t("equipment.add")); self.edit_btn.setText(self.t.t("equipment.edit")); self.delete_btn.setText(self.t.t("equipment.delete")); self.reload_btn.setText(self.t.t("app.refresh"))
        self.table.setHorizontalHeaderLabels([self.t.t(k) for k in ["equipment.col.code","equipment.col.name","equipment.col.model","equipment.col.manufacturer","equipment.col.serial","equipment.col.department","equipment.col.status"]])
        for i,(value,key) in enumerate(STATUSES): self.status_label_refresh(i,key)
        self.refresh()
    def status_label_refresh(self,i,key):
        # Dialogs are populated with translated status labels when opened.
        pass
    def refresh(self,*_):
        term=self.search.text().strip()
        with get_session() as s:
            q=s.query(Equipment)
            if term:
                like=f"%{term}%"; q=q.filter(or_(Equipment.hospital_code.ilike(like),Equipment.name_ar.ilike(like),Equipment.name_en.ilike(like),Equipment.model.ilike(like),Equipment.serial_number.ilike(like)))
            rows=q.order_by(Equipment.id.desc()).all()
            data=[(e.id,e.hospital_code,e.name_ar if self.t.lang=="ar" else e.name_en,e.model or "—",e.manufacturer or "—",e.serial_number or "—",e.department.name_ar if e.department and self.t.lang=="ar" else (e.department.name_en if e.department else "—"),self.t.t(dict(STATUSES).get(e.status,"equipment.status.operational"))) for e in rows]
        self.table.setRowCount(len(data))
        for r,row in enumerate(data):
            # Keep ID in UserRole rather than displaying it.
            for c,val in enumerate(row[1:]):
                item=QTableWidgetItem(str(val)); item.setData(Qt.UserRole,row[0]); self.table.setItem(r,c,item)
        self.table.resizeColumnsToContents()
    def selected_id(self):
        row=self.table.currentRow()
        return self.table.item(row,0).data(Qt.UserRole) if row>=0 and self.table.item(row,0) else None
    def add_equipment(self):
        d=EquipmentDialog(self.t,parent=self)
        if d.exec()!=QDialog.Accepted:return
        try:
            with get_session() as s: s.add(Equipment(**d.values())); s.commit()
        except IntegrityError:
            QMessageBox.warning(self,self.t.t("app.error"),self.t.t("equipment.duplicate")); return
        self.refresh()
    def edit_equipment(self):
        eid=self.selected_id()
        if eid is None: QMessageBox.information(self,self.t.t("app.title"),self.t.t("equipment.select")); return
        with get_session() as s: item=s.get(Equipment,eid); values={c:getattr(item,c) for c in ["id","hospital_code","name_ar","name_en","model","manufacturer","serial_number","equipment_type","status","notes"]}
        obj=Equipment(**{k:v for k,v in values.items() if k!="id"}); obj.id=eid
        d=EquipmentDialog(self.t,obj,self)
        if d.exec()!=QDialog.Accepted:return
        try:
            with get_session() as s:
                item=s.get(Equipment,eid)
                for k,v in d.values().items(): setattr(item,k,v)
                s.commit()
        except IntegrityError:
            QMessageBox.warning(self,self.t.t("app.error"),self.t.t("equipment.duplicate")); return
        self.refresh()
    def delete_equipment(self):
        eid=self.selected_id()
        if eid is None: QMessageBox.information(self,self.t.t("app.title"),self.t.t("equipment.select")); return
        if QMessageBox.question(self,self.t.t("equipment.delete"),self.t.t("equipment.confirm_delete"))!=QMessageBox.Yes:return
        try:
            with get_session() as s: s.delete(s.get(Equipment,eid)); s.commit()
        except Exception:
            QMessageBox.warning(self,self.t.t("app.error"),self.t.t("equipment.delete_blocked")); return
        self.refresh()

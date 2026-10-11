"""
Tests for Phase 3: Equipment, Departments, Locations, Vendors, and Lifecycle Transfers.
"""
import pytest
from datetime import date
from src.models import User, Department, Location, Vendor, Equipment, EquipmentTransfer
from src.services.hospital_service import hospital_service
from src.services.vendor_service import vendor_service
from src.services.equipment_service import equipment_service
from src.core.exceptions import ValidationError, DuplicateRecordError, NotFoundError


def test_department_and_location_lifecycle(test_db):
    admin = test_db.query(User).filter_by(username="admin").first()

    # Create department
    dept = hospital_service.create_department(
        db=test_db,
        user=admin,
        data={"name_ar": "قسم القلب والأوعية", "name_en": "Cardiology Dept", "code": "CARD-01", "floor": "1"}
    )
    assert dept.id is not None
    assert dept.name_ar == "قسم القلب والأوعية"

    # Create room
    loc = hospital_service.create_location(
        db=test_db,
        user=admin,
        data={"department_id": dept.id, "room_number": "C-101", "room_name": "غرفة فحص القلب"}
    )
    assert loc.id is not None
    assert loc.department_id == dept.id


def test_vendor_lifecycle(test_db):
    admin = test_db.query(User).filter_by(username="admin").first()

    vendor = vendor_service.create_vendor(
        db=test_db,
        user=admin,
        data={
            "name": "Siemens Healthineers",
            "vendor_type": "manufacturer",
            "contact_person": "Eng. Tariq",
            "phone": "0551122334"
        }
    )
    assert vendor.id is not None
    assert vendor.name == "Siemens Healthineers"

    # Update vendor
    updated = vendor_service.update_vendor(
        db=test_db,
        user=admin,
        vendor_id=vendor.id,
        data={"phone": "0559988776"}
    )
    assert updated.phone == "0559988776"


def test_equipment_creation_and_uniqueness(test_db):
    admin = test_db.query(User).filter_by(username="admin").first()
    dept = hospital_service.create_department(
        db=test_db,
        user=admin,
        data={"name_ar": "العناية المركزة", "code": "ICU-TEST"}
    )

    eq_data = {
        "asset_number": "EQ-TEST-001",
        "serial_number": "SN-TEST-001",
        "name_ar": "جهاز مراقبة مريض",
        "name_en": "Patient Monitor",
        "department_id": dept.id,
        "status": "operational",
        "risk_level": "medium",
        "criticality": "semi_critical"
    }

    eq = equipment_service.create_equipment(test_db, admin, eq_data)
    assert eq.id is not None
    assert eq.asset_number == "EQ-TEST-001"

    # Duplicate asset number should fail
    with pytest.raises(DuplicateRecordError):
        equipment_service.create_equipment(test_db, admin, {**eq_data, "serial_number": "SN-DIFF"})

    # Duplicate serial number should fail
    with pytest.raises(DuplicateRecordError):
        equipment_service.create_equipment(test_db, admin, {**eq_data, "asset_number": "EQ-DIFF"})


def test_equipment_transfer_flow(test_db):
    admin = test_db.query(User).filter_by(username="admin").first()
    dept_a = hospital_service.create_department(test_db, admin, {"name_ar": "قسم أ", "code": "D-A"})
    dept_b = hospital_service.create_department(test_db, admin, {"name_ar": "قسم ب", "code": "D-B"})

    eq = equipment_service.create_equipment(
        test_db,
        admin,
        {
            "asset_number": "EQ-TR-001",
            "serial_number": "SN-TR-001",
            "name_ar": "جهاز أشعة متنقل",
            "department_id": dept_a.id
        }
    )
    assert eq.department_id == dept_a.id

    # Transfer to dept B
    transfer = equipment_service.transfer_equipment(
        db=test_db,
        user=admin,
        eq_id=eq.id,
        to_department_id=dept_b.id,
        reason="نقل عاجل لدعم حالات الطوارئ"
    )

    assert transfer.id is not None
    assert transfer.from_department_id == dept_a.id
    assert transfer.to_department_id == dept_b.id
    assert eq.department_id == dept_b.id

    # Transfer history query
    transfers = test_db.query(EquipmentTransfer).filter_by(equipment_id=eq.id).all()
    assert len(transfers) == 1
    assert transfers[0].reason == "نقل عاجل لدعم حالات الطوارئ"


def test_equipment_stats_calculation(test_db):
    admin = test_db.query(User).filter_by(username="admin").first()
    dept = hospital_service.create_department(test_db, admin, {"name_ar": "قسم الطوارئ", "code": "ER"})

    equipment_service.create_equipment(test_db, admin, {
        "asset_number": "EQ-S-1", "serial_number": "SN-S-1", "name_ar": "جهاز 1",
        "department_id": dept.id, "status": "operational", "risk_level": "high"
    })
    equipment_service.create_equipment(test_db, admin, {
        "asset_number": "EQ-S-2", "serial_number": "SN-S-2", "name_ar": "جهاز 2",
        "department_id": dept.id, "status": "under_maintenance", "risk_level": "medium"
    })

    stats = equipment_service.get_equipment_stats(test_db)
    assert stats["total"] == 2
    assert stats["operational"] == 1
    assert stats["under_maintenance"] == 1
    assert stats["high_risk"] == 1

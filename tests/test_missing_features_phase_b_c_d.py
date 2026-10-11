"""
Automated unit & integration tests for MEMMS missing functional features:
- Section 1: Equipment PDF Operation & Service Manuals
- Section 2: Equipment Accessories & Financial Cost Tracking
- Section 3: Receiving & Commissioning Records
- Section 4: Staff Qualifications, Experiences & RBAC Compensation Protection
- Section 5: Vendors, Suppliers & Support Engineers
"""
import pytest
from datetime import date, datetime
from pathlib import Path

from src.models import (
    User, Role, Equipment, Vendor, VendorEngineer, Department, Location,
    EquipmentAccessory, EquipmentReceiving, Technician,
    TechnicianQualification, TechnicianExperience, TechnicianCompensation,
    Attachment
)
from src.core.exceptions import PermissionDeniedError, ValidationError
from src.core.security import hash_password
from src.services.attachment_service import attachment_service
from src.services.equipment_service import equipment_service
from src.services.vendor_service import vendor_service
from src.services.technician_service import technician_service


def _get_or_create_dept(db):
    from src.models import Hospital
    hosp = db.query(Hospital).first()
    if not hosp:
        hosp = Hospital(name_ar="مستشفى الملك فهد", name_en="KFSH", code="KFSH-01")
        db.add(hosp)
        db.commit()

    dept = db.query(Department).first()
    if not dept:
        dept = Department(hospital_id=hosp.id, name_ar="العناية المركزة", name_en="ICU", code="ICU")
        db.add(dept)
        db.commit()
    return dept


def _create_equipment(db, asset_number="EQ-TEST-001", name_ar="جهاز طبي", **kwargs):
    dept = _get_or_create_dept(db)
    defaults = {
        "asset_number": asset_number,
        "serial_number": f"SN-{asset_number}",
        "name_ar": name_ar,
        "name_en": f"Equipment {asset_number}",
        "category": "Therapeutic",
        "department_id": dept.id,
        "status": "operational",
        "purchase_price": 0.0
    }
    defaults.update(kwargs)
    eq = Equipment(**defaults)
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq


def test_equipment_pdf_manuals_upload_and_filter(test_db, tmp_path):
    """Test PDF manual upload, categorization into operation/service, and querying."""
    admin = test_db.query(User).filter_by(username="admin").first()

    eq = _create_equipment(
        test_db,
        asset_number="EQ-PDF-001",
        name_ar="جهاز تنفس اصطناعي",
        model="Vent-X"
    )

    # Create dummy PDF files
    dummy_op_pdf = tmp_path / "operation_guide.pdf"
    dummy_op_pdf.write_bytes(b"%PDF-1.4 dummy operation manual content")
    dummy_svc_pdf = tmp_path / "service_manual.pdf"
    dummy_svc_pdf.write_bytes(b"%PDF-1.4 dummy service manual content")

    # Save Operation Manual
    att_op = attachment_service.save_attachment(
        db=test_db,
        user=admin,
        equipment_id=eq.id,
        file_path=str(dummy_op_pdf),
        attachment_type="operation_manual",
        notes="دليل تشغيل معتمد"
    )
    assert att_op.id is not None
    assert att_op.attachment_type == "operation_manual"
    assert att_op.file_name == "operation_guide.pdf"

    # Save Service Manual
    att_svc = attachment_service.save_attachment(
        db=test_db,
        user=admin,
        equipment_id=eq.id,
        file_path=str(dummy_svc_pdf),
        attachment_type="service_manual",
        notes="دليل صيانة دورية"
    )
    assert att_svc.id is not None
    assert att_svc.attachment_type == "service_manual"

    # Query equipment manuals
    manuals = attachment_service.get_equipment_manuals(test_db, eq.id)
    assert len(manuals["operation_manuals"]) == 1
    assert len(manuals["service_manuals"]) == 1
    assert manuals["operation_manuals"][0].file_name == "operation_guide.pdf"
    assert manuals["service_manuals"][0].file_name == "service_manual.pdf"


def test_equipment_accessories_and_total_cost_calculation(test_db):
    """Test equipment accessories CRUD and dynamic cost accumulation."""
    admin = test_db.query(User).filter_by(username="admin").first()

    eq = _create_equipment(
        test_db,
        asset_number="EQ-ACC-001",
        name_ar="موجات فوق صوتية",
        purchase_price=50000.0
    )

    # Initial accessory costs should be zero
    assert eq.total_accessories_cost == 0.0
    assert eq.total_asset_cost == 50000.0

    # Add Accessory 1 (Probe 1: 2 * 3000 = 6000)
    acc1 = equipment_service.add_accessory(
        db=test_db,
        user=admin,
        equipment_id=eq.id,
        data={
            "name": "مجس قطاعي قلب (Cardiac Probe)",
            "model_number": "PRB-C1",
            "serial_number": "SN-PRB-991",
            "quantity": 2.0,
            "unit_cost": 3000.0,
            "manufacturer": "GE"
        }
    )
    assert acc1.total_cost == 6000.0

    # Add Accessory 2 (Battery pack: 1 * 1500 = 1500)
    acc2 = equipment_service.add_accessory(
        db=test_db,
        user=admin,
        equipment_id=eq.id,
        data={
            "name": "وحدة بطارية احتياطية",
            "quantity": 1.0,
            "unit_cost": 1500.0
        }
    )
    assert acc2.total_cost == 1500.0

    # Verify equipment calculations
    test_db.refresh(eq)
    assert eq.total_accessories_cost == 7500.0
    assert eq.total_asset_cost == 57500.0

    # Delete an accessory
    equipment_service.delete_accessory(test_db, admin, acc2.id)
    test_db.refresh(eq)
    assert eq.total_accessories_cost == 6000.0
    assert eq.total_asset_cost == 56000.0


def test_equipment_receiving_and_commissioning_record(test_db):
    """Test receiving, commissioning, installation, and inspection records."""
    admin = test_db.query(User).filter_by(username="admin").first()

    eq = _create_equipment(
        test_db,
        asset_number="EQ-REC-001",
        name_ar="جهاز تخدير متقدم"
    )

    rec = equipment_service.set_receiving_data(
        db=test_db,
        user=admin,
        equipment_id=eq.id,
        data={
            "commissioning_number": "COMM-2026-0045",
            "commissioning_date": date(2026, 3, 15),
            "receipt_date": date(2026, 3, 20),
            "receiving_technician_name": "م. أحمد الغامدي",
            "registration_officer_name": "سلطان القحطاني",
            "receipt_report_number": "REP-INSP-991",
            "receipt_notes": "تم اجتياز فحص السلامة الكهربائية واختبار المعايرة بنجاح"
        }
    )

    assert rec.id is not None
    assert rec.commissioning_number == "COMM-2026-0045"
    assert rec.receipt_report_number == "REP-INSP-991"

    test_db.refresh(eq)
    assert eq.receiving is not None
    assert eq.receiving.receiving_technician_name == "م. أحمد الغامدي"
    assert eq.receiving.registration_officer_name == "سلطان القحطاني"


def test_technician_hr_data_qualifications_experiences_and_rbac(test_db):
    """Test technician qualification, experience, and salary protection via RBAC."""
    admin = test_db.query(User).filter_by(username="admin").first()

    # Create Viewer user (does NOT have technicians:salary_view)
    viewer_role = test_db.query(Role).filter_by(name="viewer").first()
    viewer_user = User(
        username="viewer_test",
        password_hash=hash_password("Viewer@123"),
        full_name="Viewer User",
        email="viewer@test.local",
        role_id=viewer_role.id,
        is_active=True
    )
    test_db.add(viewer_user)
    test_db.commit()

    # 1. Create Technician
    tech = technician_service.create_technician(
        db=test_db,
        employee_id="EMP-9001",
        full_name="م. عادل الشمري",
        specialization="العناية المركزة وحاضنات الأطفال",
        nationality="سعودي",
        id_document_type="national_id",
        id_number="1098765432",
        job_title="مهندس أجهزة طبية أول",
        phone="0559988776",
        email="adel@hospital.sa",
        operator_user_id=admin.id
    )
    assert tech.id is not None
    assert tech.id_number_masked == "******5432"

    # 2. Add Qualifications
    q1 = technician_service.add_qualification(
        db=test_db,
        user=admin,
        tech_id=tech.id,
        data={
            "name": "بكالوريوس هندسة طبية حيوية",
            "specialization": "أنظمة دعم الحياة",
            "issuing_organization": "جامعة الملك سعود",
            "issue_date": date(2018, 6, 1)
        }
    )
    assert q1.id is not None

    # 3. Add Experience
    exp1 = technician_service.add_experience(
        db=test_db,
        user=admin,
        tech_id=tech.id,
        data={
            "previous_employer": "مدينة الملك فهد الطبية",
            "job_title": "مهندس صيانة أجهزة تنفس وتخدير",
            "specialization": "العناية الفائقة",
            "start_date": date(2018, 7, 1),
            "end_date": date(2022, 12, 31)
        }
    )
    assert exp1.id is not None

    # 4. Set Compensation (Admin has technicians:salary_manage)
    comp = technician_service.set_compensation(
        db=test_db,
        user=admin,
        tech_id=tech.id,
        data={
            "basic_salary": 14000.0,
            "allowances": 6500.0,
            "allowance_type": "بدل سكن ونقل وطبيعة عمل",
            "effective_date": date(2026, 1, 1),
            "notes": "الراتب الأساسي والبدلات المعتمدة"
        }
    )
    assert comp.total_package == 20500.0

    # 5. Admin can view compensation
    fetched_comp = technician_service.get_compensation(test_db, admin, tech.id)
    assert fetched_comp is not None
    assert fetched_comp.total_package == 20500.0

    # 6. Viewer user without permission MUST get PermissionDeniedError
    with pytest.raises(PermissionDeniedError):
        technician_service.get_compensation(test_db, viewer_user, tech.id)

    with pytest.raises(PermissionDeniedError):
        technician_service.set_compensation(test_db, viewer_user, tech.id, {"basic_salary": 20000.0})


def test_vendor_support_engineers_and_delete_protection(test_db):
    """Test vendor support engineer CRUD and protection against deleting linked vendors."""
    admin = test_db.query(User).filter_by(username="admin").first()

    # Create vendor
    vendor = vendor_service.create_vendor(
        db=test_db,
        user=admin,
        data={
            "name": "شركة فيليبس للرعاية الصحية",
            "vendor_type": "manufacturer",
            "phone": "0112223333"
        }
    )
    assert vendor.id is not None

    # Add vendor engineer
    eng = vendor_service.add_vendor_engineer(
        db=test_db,
        user=admin,
        vendor_id=vendor.id,
        data={
            "name": "م. ماجد عبد العزيز",
            "phone": "0543219876",
            "email": "majed@philips.sa",
            "specialization": "أجهزة الرنين المغناطيسي والأشعة المقطعية"
        }
    )
    assert eng.id is not None
    assert eng.vendor_id == vendor.id

    # Create equipment linked to vendor and engineer
    eq = _create_equipment(
        test_db,
        asset_number="EQ-MRI-001",
        name_ar="جهاز رنين مغناطيسي 3 تسلا",
        agent_id=vendor.id,
        assigned_engineer_id=eng.id
    )

    # Attempting to delete vendor must raise error due to linked equipment
    with pytest.raises(Exception, match="مرتبطة بها"):
        vendor_service.delete_vendor(test_db, admin, vendor.id)

    # Re-assign equipment away, then delete succeeds
    eq.agent_id = None
    eq.assigned_engineer_id = None
    test_db.commit()

    vendor_service.delete_vendor(test_db, admin, vendor.id)
    v_check = test_db.query(Vendor).filter_by(id=vendor.id).first()
    assert v_check is None

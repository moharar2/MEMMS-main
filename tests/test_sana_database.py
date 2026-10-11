"""
Comprehensive validation test for Al-Thawra Hospital Sana'a master dataset.
Verifies entities, relationships, foreign manufacturers, Sana'a agents,
vendor engineers, equipment accessories, and commissioning records.
"""
from src.core.database import get_db
from src.models import (
    Hospital, Department, Location, Vendor, VendorEngineer,
    Technician, TechnicianQualification, TechnicianExperience, TechnicianCompensation,
    Equipment, EquipmentAccessory, EquipmentReceiving,
    SparePart, WorkOrder, PMPlan, PMSchedule, Contract, GeneratedReport
)


def test_al_thawra_hospital_master_record():
    with get_db() as db:
        hosp = db.query(Hospital).first()
        assert hosp is not None
        assert "الثورة" in hosp.name_ar
        assert "صنعاء" in hosp.name_ar
        assert hosp.code == "THW-SNA-01"
        assert "صنعاء" in (hosp.address or "")
        assert hosp.is_active is True


def test_sanaa_clinical_departments():
    with get_db() as db:
        depts = db.query(Department).all()
        assert len(depts) >= 10
        dept_codes = {d.code for d in depts}
        expected_codes = {"CATH", "ICU", "RAD", "DIA", "OR", "NICU", "ER", "LAB", "CSSD", "ENDO"}
        assert expected_codes.issubset(dept_codes)

        locations = db.query(Location).all()
        assert len(locations) >= 20


def test_foreign_manufacturers_and_sanaa_agents():
    with get_db() as db:
        foreign_mfg = db.query(Vendor).filter_by(vendor_type="manufacturer").all()
        assert len(foreign_mfg) >= 10
        mfg_names = {m.name for m in foreign_mfg}
        assert "Siemens Healthineers" in mfg_names
        assert "GE Healthcare" in mfg_names
        assert "Dräger Medical" in mfg_names
        assert "Philips Healthcare" in mfg_names
        assert "Fresenius Medical Care" in mfg_names
        assert "Mindray Bio-Medical Electronics" in mfg_names

        sanaa_agents = db.query(Vendor).filter(Vendor.vendor_type != "manufacturer").all()
        assert len(sanaa_agents) >= 5
        agent_names = " ".join(a.name for a in sanaa_agents)
        assert "ناتكو" in agent_names
        assert "يمن ميديكال" in agent_names
        assert "الشرقية" in agent_names
        assert "تهامة" in agent_names
        assert "الشفاء" in agent_names

        # Verify address contains Sana'a streets
        agent_addresses = " ".join(a.address or "" for a in sanaa_agents)
        assert "الزبيري" in agent_addresses
        assert "حدة" in agent_addresses
        assert "بغداد" in agent_addresses
        assert "عصر" in agent_addresses


def test_sanaa_vendor_support_engineers():
    with get_db() as db:
        engineers = db.query(VendorEngineer).all()
        assert len(engineers) >= 10
        for eng in engineers:
            assert eng.vendor_id is not None
            assert eng.phone is not None
            assert eng.phone.startswith("+967")
            assert eng.status == "active"
            assert eng.specialization is not None


def test_biomedical_technicians_full_profiles():
    with get_db() as db:
        techs = db.query(Technician).all()
        assert len(techs) >= 5
        for t in techs:
            assert t.employee_id.startswith("EMP-SNA-")
            assert "يمني" in (t.nationality or "")
            assert t.id_number is not None
            assert len(t.qualifications) > 0
            assert len(t.experiences) > 0
            assert len(t.compensations) > 0
            assert t.compensations[0].total_package > 0


def test_medical_equipment_with_accessories_and_commissioning():
    with get_db() as db:
        equipment = db.query(Equipment).all()
        assert len(equipment) >= 16

        for eq in equipment:
            assert eq.asset_number.startswith("EQ-")
            assert eq.serial_number is not None
            assert eq.department_id is not None
            assert eq.location_id is not None
            # Manufacturer must be foreign maker or vendor
            assert eq.manufacturer_id is not None
            # Supplier / agent must be linked
            assert eq.supplier_id is not None
            assert eq.agent_id is not None
            assert eq.assigned_engineer_id is not None

            # Accessories check
            assert len(eq.accessories) >= 1
            assert eq.total_accessories_cost > 0
            assert eq.total_asset_cost >= eq.purchase_price

            # Commissioning check
            assert eq.receiving is not None
            assert eq.receiving.commissioning_number.startswith("COM-THW-")
            assert eq.receiving.receiving_technician_name is not None
            assert eq.receiving.receipt_report_number.startswith("REC-REP-")


def test_spare_parts_and_work_orders():
    with get_db() as db:
        parts = db.query(SparePart).all()
        assert len(parts) >= 12
        for p in parts:
            assert p.storage_bin_location is not None
            assert p.quantity_on_hand > 0

        orders = db.query(WorkOrder).all()
        assert len(orders) >= 4
        for wo in orders:
            assert wo.work_order_number.startswith("WO-THW-")
            assert wo.equipment_id is not None
            assert wo.department_id is not None
            assert wo.failure_description is not None
            assert len(wo.status_logs) >= 1


def test_pm_plans_and_contracts():
    with get_db() as db:
        plans = db.query(PMPlan).all()
        assert len(plans) >= 4
        schedules = db.query(PMSchedule).all()
        assert len(schedules) >= 8

        contracts = db.query(Contract).all()
        assert len(contracts) >= 4
        for c in contracts:
            assert c.contract_number.startswith("CNT-THW-")
            assert c.vendor_id is not None
            assert c.cost > 0

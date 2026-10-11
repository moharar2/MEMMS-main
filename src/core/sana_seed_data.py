"""
Comprehensive, realistic master medical database seeder for MEMMS.
Institution: Al-Thawra Modern General Hospital Authority — Sana'a
             (هيئة مستشفى الثورة العام النموذجي — أمانة العاصمة صنعاء — الجمهورية اليمنية)
Geographic Focus: Sana'a, Yemen (شارع الزبيري، شارع حدة، شارع بغداد، جولة عصر، شارع القيادة، شارع صخر).
Global Manufacturers: Siemens, GE Healthcare, Philips, Dräger, Mindray, Fresenius, Roche, Karl Storz, Olympus, Nihon Kohden, Tuttnauer, Stryker.
Local Sana'a Agents: NATCO Medical, Yemen Medical, Oriental Medical, Tihama Medical, Al-Shifa Medical, Saba Medical.
Includes complete relationships: Vendor Engineers, Equipment Accessories, Receiving/Commissioning,
Biomedical Staff Qualifications/Compensations, Spare Parts, Work Orders, PM Plans, and Reports.
"""
import sys
from datetime import date, datetime, timedelta

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from src.core.database import get_db, init_db
from src.models.hospital import Hospital, Department, Location
from src.models.equipment import Equipment, EquipmentAccessory, EquipmentReceiving
from src.models.technician import (
    Technician, TechnicianQualification,
    TechnicianExperience, TechnicianCompensation
)
from src.models.vendor import Vendor, VendorEngineer
from src.models.contract import Contract
from src.models.inventory import SparePart, InventoryTransaction
from src.models.work_order import WorkOrder, WorkOrderPart, WorkOrderLog
from src.models.preventive import PMPlan, PMSchedule
from src.models.report import GeneratedReport
from src.models.user import User


def seed_sana_medical_data():
    """
    Cleans and seeds realistic clinical data for Al-Thawra General Hospital in Sana'a.
    """
    print("==================================================================")
    print(" [MEMMS Seeder] بدء تغذية قاعدة بيانات هيئة مستشفى الثورة — صنعاء")
    print("==================================================================")

    init_db()

    with get_db() as db:
        # =====================================================================
        # 1. Hospital Master Record (هيئة مستشفى الثورة العام النموذجي — صنعاء)
        # =====================================================================
        print("[1/9] تحديث السجل التعريفي لمستشفى الثورة العام بصنعاء...")
        hosp = db.query(Hospital).first()
        if not hosp:
            hosp = Hospital()
            db.add(hosp)

        hosp.name_ar = "هيئة مستشفى الثورة العام النموذجي — صنعاء"
        hosp.name_en = "Al-Thawra Modern General Hospital Authority — Sana'a"
        hosp.code = "THW-SNA-01"
        hosp.address = "أمانة العاصمة، شارع تعز / باب اليمن، صنعاء — الجمهورية اليمنية"
        hosp.phone = "+967 1 246966"
        hosp.email = "info@al-thawra-hospital.ye"
        hosp.is_active = True
        db.flush()

        # =====================================================================
        # 2. Specialized Clinical Departments & Locations (المراكز والأقسام)
        # =====================================================================
        print("[2/9] تهيئة المراكز الطبية والأقسام والغرف التخصصية...")
        dept_data = [
            ("CATH", "مركز القلب والقسطرة التداخلية وجراحة الأوعية", "Cardiology & Interventional Cath Lab Center", "مبنى مركز القلب - الطابق 1", [
                ("CATH-01", "غرفة عمليات القسطرة التداخلية 1"),
                ("CATH-02", "غرفة عمليات القسطرة التداخلية 2"),
                ("CATH-CCU", "وحدة العناية التاجية المركزة CCU"),
                ("CATH-ECHO", "غرفة تخطيط وإيكو القلب بالمجهود")
            ]),
            ("ICU", "مركز العناية المركزة الجراحية والطوارئ الحرجة", "Surgical ICU & Critical Care Center", "المبنى الجراحي - الطابق 2", [
                ("ICU-201", "عناية مركزة سريرية (جناح أ)"),
                ("ICU-202", "عناية مركزة سريرية (جناح ب)"),
                ("ICU-ISO", "جناح العزل الطبي بضغط الهواء السالب")
            ]),
            ("RAD", "قسم الأشعة والتصوير الطبي الرقمي والطب النووي", "Diagnostic Radiology & Imaging Department", "مبنى الأشعة - الطابق الأرضي", [
                ("RAD-MRI", "جناح الرنين المغناطيسي 1.5T"),
                ("RAD-CT", "جناح الأشعة المقطعية متعددة الشرائح 128"),
                ("RAD-XRAY", "غرفة الأشعة السينية الرقمية DR"),
                ("RAD-US", "وحدة السونار والموجات فوق الصوتية رباعية الأبعاد 4D")
            ]),
            ("DIA", "مركز أمراض وزراعة الكلى والغسيل الدموي", "Nephrology, Kidney Transplant & Hemodialysis Center", "المبنى التخصصي - الطابق الأرضي", [
                ("DIA-HALL1", "صالة الغسيل الكلوي الرئيسية (رجال)"),
                ("DIA-HALL2", "صالة الغسيل الكلوي الرئيسية (نساء)"),
                ("DIA-WTP", "محطة معالجة وتناضح مياه الغسيل المركزية (RO Plant)"),
                ("DIA-ISO", "وحدة الغسيل المعزول لمرضى الفيروسات")
            ]),
            ("OR", "مجمع غرف العمليات الجراحية الكبرى وزراعة الأعضاء", "Major Surgical Operations & Transplant Suites", "المبنى الرئيسي - الطابق 3", [
                ("OR-01", "غرفة العمليات الكبرى وجراحة القلب المفتوح"),
                ("OR-02", "غرفة جراحة المخ والأعصاب والعمود الفقري"),
                ("OR-03", "غرفة جراحة المناظير والمسالك البولية"),
                ("OR-PACU", "وحدة الإفاقة بعد التخدير والرعاية الفائقة")
            ]),
            ("NICU", "مركز الحواضن والعناية المركزة لحديثي الولادة والخدج", "Neonatal Intensive Care Unit (NICU)", "مبنى الأمومة والطفولة - الطابق 1", [
                ("NICU-MAIN", "صالة الحواضن المتقدمة لحديثي الولادة"),
                ("NICU-ISO", "حضانة العزل والعناية الفائقة للخدج")
            ]),
            ("ER", "مركز طوارئ الحوادث والجراحة والحالات الحرجة", "Emergency, Trauma & Resuscitation Center", "المبنى الرئيسي - المدخل الشرقي", [
                ("ER-RESUS", "غرفة الإنعاش القلبي الرئوي CPR"),
                ("ER-TRIAGE", "وحدة الفرز السريع للحالات الطارئة"),
                ("ER-TRAUMA", "صالة طوارئ الحوادث والإصابات الكبرى")
            ]),
            ("LAB", "المختبرات الطبية التشخيصية وبنك الدم الوطني المركزي", "Central Diagnostic Labs & Blood Bank", "المبنى التشخيصي - الطابق 1", [
                ("LAB-CHEM", "مختبر الكيمياء الحيوية والمناعة الآلي"),
                ("LAB-HEM", "مختبر أمراض الدم وسوائل الجسم"),
                ("LAB-BB", "وحدة بنك الدم وفصل البلازما والصفائح")
            ]),
            ("CSSD", "قسم التعقيم المركزي ومكافحة العدوى المتقدمة", "Central Sterile Supply Department (CSSD)", "القبو الفني - المبنى الجراحي", [
                ("CSSD-DIRTY", "منطقة الاستلام والتطهير بالموجات الصوتية"),
                ("CSSD-PACK", "منطقة الفحص والتغليف المعقم"),
                ("CSSD-STER", "صالة أجهزة التعقيم البخاري والغلايات")
            ]),
            ("ENDO", "مركز مناظير الجهاز الهضمي والتشخيص الداخلي", "Gastrointestinal Endoscopy Center", "المبنى التشخيصي - الطابق 2", [
                ("ENDO-01", "غرفة مناظير المعدة والقولون التداخلية"),
                ("ENDO-DISINF", "غرفة غسيل وتطهير المناظير آلياً")
            ])
        ]

        departments_map = {}
        locations_map = {}

        for code, name_ar, name_en, floor, rooms in dept_data:
            dept = db.query(Department).filter_by(code=code).first()
            if not dept:
                dept = Department(hospital_id=hosp.id, code=code, name_ar=name_ar, name_en=name_en, floor=floor)
                db.add(dept)
                db.flush()
            else:
                dept.name_ar = name_ar
                dept.name_en = name_en
                dept.floor = floor

            departments_map[code] = dept

            for r_code, r_name in rooms:
                loc = db.query(Location).filter_by(department_id=dept.id, room_number=r_code).first()
                if not loc:
                    loc = Location(department_id=dept.id, room_number=r_code, room_name=r_name)
                    db.add(loc)
                    db.flush()
                else:
                    loc.room_name = r_name
                locations_map[r_code] = loc

        # =====================================================================
        # 3. Foreign Manufacturers & Local Sana'a Agents (الشركات والموردون)
        # =====================================================================
        print("[3/9] إدراج شركات التصنيع الأجنبية العالمية والوكلاء المحليين بصنعاء...")

        # 3.A Foreign Global Manufacturers
        foreign_manufacturers = [
            ("MAN-SIE", "Siemens Healthineers", "manufacturer", "Dr. Klaus Weber", "+49 9131 84-0", "contact@siemens-healthineers.com", "Henkestr. 127, 91052 Erlangen, Germany — شركة تصنيع أجهزة الرنين المغناطيسي والأشعة التشخيصية"),
            ("MAN-GE", "GE Healthcare", "manufacturer", "Mr. Robert Evans", "+1 800 437 1171", "support@gehealthcare.com", "Chicago, Illinois, United States — شركة تصنيع الأشعة المقطعية وحاضنات الأطفال"),
            ("MAN-PHI", "Philips Healthcare", "manufacturer", "Jan van der Meer", "+31 20 59 77777", "medical.care@philips.com", "Best, Netherlands — شركة تصنيع أنظمة قسطرة القلب ومراقبة المرضى"),
            ("MAN-DRA", "Dräger Medical", "manufacturer", "Stefan Hoffmann", "+49 451 882-0", "info@draeger.com", "Moislinger Allee 53-55, Lübeck, Germany — شركة تصنيع أجهزة التنفس الصناعي والتخدير"),
            ("MAN-MIN", "Mindray Bio-Medical Electronics", "manufacturer", "Li Wei", "+86 755 81888998", "intl-support@mindray.com", "Shenzhen Hi-Tech Industrial Park, Nanshan, China — شركة تصنيع أجهزة السونار ومراقبة المرضى"),
            ("MAN-FRE", "Fresenius Medical Care", "manufacturer", "Hans Becker", "+49 6172 609-0", "info@freseniusmedicalcare.com", "Else-Kröner-Straße 1, Bad Homburg, Germany — شركة تصنيع أجهزة ومستهلكات غسيل الكلى"),
            ("MAN-ROC", "Roche Diagnostics", "manufacturer", "Martin Fischer", "+41 61 688 11 11", "diagnostics@roche.com", "Grenzacherstrasse 124, Basel, Switzerland — شركة تصنيع محللات الكيمياء وبنك الدم"),
            ("MAN-STO", "Karl Storz Endoscopy", "manufacturer", "Markus Bauer", "+49 7461 708-0", "info@karlstorz.com", "Dr.-Karl-Storz-Straße 34, Tuttlingen, Germany — شركة تصنيع أبراج مناظير الجراحة العامة 4K"),
            ("MAN-OLY", "Olympus Medical Systems", "manufacturer", "Kenji Sato", "+81 3 3340 2111", "support@olympus-global.com", "Shinjuku Monolith, Tokyo, Japan — شركة تصنيع مناظير الجهاز الهضمي والتشخيص"),
            ("MAN-NK", "Nihon Kohden Corporation", "manufacturer", "Hiroshi Tanaka", "+81 3 5996 8000", "info@nihonkohden.com", "Shinjuku-ku, Tokyo, Japan — شركة تصنيع أجهزة تخطيط القلب ومزيلات الرجفان"),
            ("MAN-TUT", "Tuttnauer Sterilization", "manufacturer", "David Klein", "+31 76 5423765", "info@tuttnauer.com", "Breda, Netherlands — شركة تصنيع معقمات البخار المركزية والأوتوكلاف"),
            ("MAN-STR", "Stryker Surgical", "manufacturer", "James Miller", "+1 269 385 2600", "medical@stryker.com", "Kalamazoo, Michigan, United States — شركة تصنيع طاولات العمليات وأجهزة جراحة العظام")
        ]

        # 3.B Local Authorized Agents & Suppliers in Sana'a
        sanaa_agents = [
            ("AGT-NATCO", "شركة ناتكو الطبية — هائل سعيد أنعم (NATCO Medical)", "both", "أ. نبيل الآنسي (مدير القطاع الطبي)", "+967 1 204444", "medical@natco-yemen.com", "شارع الزبيري، تقاطع شارع بغداد، صنعاء — الوكيل الحصري المعتمد لـ Siemens Healthineers و Roche Diagnostics"),
            ("AGT-YEMMED", "شركة يمن ميديكال للتجهيزات والحلول الطبية (Yemen Medical)", "both", "م. وليد الصبري (مدير الدعم والمشاريع)", "+967 1 415555", "info@yemen-medical.ye", "شارع حدة، أمام مجمع الكميم التجاري، صنعاء — الوكيل الحصري المعتمد لـ Dräger Medical و Mindray"),
            ("AGT-ORIENT", "الشركة الشرقية للتجهيزات والأنظمة الطبية (Oriental Medical)", "both", "م. عادل الحكيمي (المدير الإقليمي)", "+967 1 447788", "sales@oriental-med.ye", "شارع بغداد، مبنى برج الأطباء، صنعاء — الوكيل المعتمد لـ GE Healthcare و Stryker"),
            ("AGT-TIHAMA", "شركة تهامة الطبية والتشخيصية (Tihama Medical)", "service_agent", "م. عصام الأكوع (مدير الخدمة الفنية)", "+967 1 508899", "service@tihama-med.ye", "جولة عصر، جوار مبنى وزارة الخارجية، صنعاء — الوكيل المعتمد لـ Philips Healthcare و Fresenius Medical Care"),
            ("AGT-SHIFA", "مؤسسة الشفاء للتوريدات والتجهيزات الطبية (Al-Shifa Medical)", "supplier", "أ. سامي المقالح (مدير التوريدات والمناقصات)", "+967 1 223344", "info@shifa-ye.com", "شارع القيادة، صنعاء — المورد والوكيل المعتمد لـ Karl Storz و Tuttnauer و Nihon Kohden"),
            ("AGT-SABA", "شركة سبأ الدولية للأدوية والتجهيزات الطبية (Saba Medical)", "supplier", "د. مروان الحمادي (مدير الأجهزة التخصصية)", "+967 1 472233", "tenders@saba-medical.ye", "شارع صخر، المتفرع من الدائري الغربي، صنعاء — وكيل وموزع معتمد لأجهزة Olympus وجراحة العظام")
        ]

        vendors_map = {}
        for v_code, v_name, v_type, v_cp, v_ph, v_em, v_addr in (foreign_manufacturers + sanaa_agents):
            v = db.query(Vendor).filter_by(name=v_name).first()
            if not v:
                v = Vendor(name=v_name, vendor_type=v_type, contact_person=v_cp, phone=v_ph, email=v_em, address=v_addr)
                db.add(v)
                db.flush()
            else:
                v.vendor_type = v_type
                v.contact_person = v_cp
                v.phone = v_ph
                v.email = v_em
                v.address = v_addr
            vendors_map[v_code] = v

        # =====================================================================
        # 4. Vendor Support Engineers in Sana'a (مهندسو الوكلاء المحليين بصنعاء)
        # =====================================================================
        print("[4/9] تسجيل مهندسي الدعم الفني المعتمدين لدى وكلاء صنعاء...")
        engineers_data = [
            ("ENG-NAT-01", "AGT-NATCO", "م. عادل الشيباني", "+967 777211345", "adil.shaibani@natco-yemen.com", "أنظمة الرنين المغناطيسي والأشعة المقطعية Siemens", "مهندس معتمد من شركة سيمنز بألمانيا"),
            ("ENG-NAT-02", "AGT-NATCO", "م. منير الحمادي", "+967 771456123", "mounir.hammadi@natco-yemen.com", "محللات المختبرات الآلية وبنك الدم Roche Cobas", "أخصائي معايرة وبرمجة أجهزة الفحص المناعي"),
            ("ENG-YEM-01", "AGT-YEMMED", "م. هاني المقالح", "+967 773908112", "hani.maqaleh@yemen-medical.ye", "أجهزة التنفس الصناعي ومحطات التخدير Dräger", "شهادة صيانة متقدمة في أجهزة Evita و Primus"),
            ("ENG-YEM-02", "AGT-YEMMED", "م. بشير الحزمي", "+967 775667822", "basheer.hazmi@yemen-medical.ye", "أجهزة السونار ومراقبة العلامات الحيوية Mindray", "أخصائي مجسات التصوير التلفزيوني والموجات الصوتية"),
            ("ENG-ORI-01", "AGT-ORIENT", "م. طارق الوادعي", "+967 770112998", "tareq.wadei@oriental-med.ye", "الأشعة المقطعية وأنظمة التصوير الرقمي GE", "شهادة خدمة أنظمة Revolution CT من GE"),
            ("ENG-ORI-02", "AGT-ORIENT", "م. نبيل الارياني", "+967 772334455", "nabeel.iryani@oriental-med.ye", "حاضنات الأطفال والرعاية المركزة Giraffe GE", "أخصائي معايرة أجهزة تنظيم الحرارة والأكسجين"),
            ("ENG-TIH-01", "AGT-TIHAMA", "م. عصام الأكوع", "+967 774889900", "essam.akwa@tihama-med.ye", "أجهزة غسيل الكلى ومحطات معالجة المياه Fresenius", "مهندس رئيسي معتمد لأجهزة 5008S و 4008S"),
            ("ENG-TIH-02", "AGT-TIHAMA", "م. زكريا الجندبي", "+967 771220033", "zakaria.jandabi@tihama-med.ye", "أنظمة قسطرة القلب ومراقبة المرضى Philips Azurion", "أخصائي صيانة دوائر الأشعة التداخلية"),
            ("ENG-SHI-01", "AGT-SHIFA", "م. خالد الصنعاني", "+967 777332211", "khaled.sanaani@shifa-ye.com", "محطات التعقيم المركزي والأوتوكلاف Tuttnauer", "أخصائي غلايات الضغط العالي وصمامات الأمان"),
            ("ENG-SHI-02", "AGT-SHIFA", "م. أسامة بركات", "+967 775443322", "osama.barakat@shifa-ye.com", "أبراج المناظير الجراحية 4K وأجهزة تخطيط القلب", "مهندس معتمد لأجهزة Karl Storz و Nihon Kohden"),
            ("ENG-SAB-01", "AGT-SABA", "م. وسيم اليافعي", "+967 776118899", "waseem.yafei@saba-medical.ye", "مناظير الجهاز الهضمي والتشخيص الداخلي Olympus", "خبير صيانة أنابيب التوجيه والألياف البصرية")
        ]

        engineers_map = {}
        for eng_code, agt_code, eng_name, eng_ph, eng_em, eng_spec, eng_notes in engineers_data:
            agt = vendors_map.get(agt_code)
            eng = db.query(VendorEngineer).filter_by(name=eng_name, vendor_id=agt.id if agt else None).first()
            if not eng and agt:
                eng = VendorEngineer(
                    vendor_id=agt.id,
                    name=eng_name,
                    phone=eng_ph,
                    email=eng_em,
                    specialization=eng_spec,
                    status="active",
                    notes=eng_notes
                )
                db.add(eng)
                db.flush()
            elif eng:
                eng.phone = eng_ph
                eng.email = eng_em
                eng.specialization = eng_spec
                eng.status = "active"
                eng.notes = eng_notes
            engineers_map[eng_code] = eng

        # =====================================================================
        # 5. Al-Thawra Hospital Biomedical Engineering Staff (الكادر الفني اليمني)
        # =====================================================================
        print("[5/9] تسجيل الكادر الفني الهندسي بمستشفى الثورة بصنعاء وبياناتهم...")
        technicians_profiles = [
            (
                "EMP-SNA-01", "م. أحمد علي القدسي", "هندسة أجهزة تصوير وأشعة تشخيصية",
                "بكالوريوس هندسة طبية حيوية — جامعة العلوم والتكنولوجيا صنعاء",
                "777123456", "ahmed.qudsi@al-thawra.ye", "active", "RAD",
                "رئيس قسم هندسة أجهزة الأشعة والتصوير الطبي", "01010045892", date(2017, 3, 1),
                380000.0, 120000.0, "بدل مخاطر إشعاع وبدل طبيعة عمل",
                [
                    ("شهادة صيانة معتمدة في أنظمة الرنين المغناطيسي Magnetom", "أنظمة أشعة", "Siemens Healthineers - Erlangen", date(2019, 5, 10), None),
                    ("دورة معايرة أجهزة الأشعة المقطعية متعددة الشرائح", "أشعة مقطعية", "الجمعية الهندسية الطبية اليمنية", date(2021, 11, 15), None)
                ],
                [
                    ("هيئة مستشفى الثورة العام النموذجي", "مهندس صيانة أجهزة أشعة أول", "هندسة أجهزة تصوير", date(2018, 1, 1), None, "الإشراف على صيانة ومعايرة الرنين المغناطيسي والأشعة المقطعية"),
                    ("شركة ناتكو الطبية — صنعاء", "مهندس صيانة أجهزة طبية ميداني", "أشعة ورنين", date(2014, 6, 1), date(2017, 12, 31), "التركيب والصيانة الوقائية لأنظمة Siemens في مستشفيات صنعاء")
                ]
            ),
            (
                "EMP-SNA-02", "م. فؤاد يحيى المتوكل", "صيانة أجهزة عناية مركزة وتخدير وجراحة",
                "بكالوريوس هندسة حيوية وطبية — جامعة صنعاء",
                "771987654", "fouad.mutawakkil@al-thawra.ye", "active", "ICU",
                "مهندس أول أجهزة عناية مركزة وتخدير", "01020088319", date(2019, 7, 15),
                350000.0, 100000.0, "بدل عناية مركزة وعدوى وبدل إشراف فني",
                [
                    ("شهادة صيانة متقدمة لأجهزة التنفس الصناعي Dräger Evita", "عناية وتنفس", "مركز تدريب Dräger — صنعاء", date(2020, 8, 20), None),
                    ("دورة السلامة الكهربائية والمعايرة الدورية للمعدات الطبية", "معايرة وسلامة", "المعهد الوطني للعلوم الصحية", date(2022, 2, 10), None)
                ],
                [
                    ("مركز العناية المركزة — مستشفى الثورة", "مهندس صيانة مقيم", "أجهزة تنفس ومراقبة", date(2019, 8, 1), None, "المتابعة اليومية لصيانة أجهزة التنفس ومحطات التخدير بغرف العمليات"),
                    ("شركة يمن ميديكال للتجهيزات — صنعاء", "مهندس دعم فني", "أجهزة عناية حرجة", date(2016, 9, 1), date(2019, 6, 30), "صيانة ومعايرة أجهزة التنفس الصناعي ومراقبة المرضى")
                ]
            ),
            (
                "EMP-SNA-03", "م. سامي عبدالله الحاشدي", "هندسة أجهزة غسيل كلى ومحطات معالجة المياه",
                "ماجستير أجهزة طبية حيوية واستشعار حيوي",
                "773456789", "sami.hashidi@al-thawra.ye", "active", "DIA",
                "مسؤول الصيانة بمركز أمراض وزراعة الكلى", "01030012745", date(2018, 5, 10),
                390000.0, 130000.0, "بدل خطر دم وتلوث وبدل محطات مياه RO",
                [
                    ("شهادة تخصصية في صيانة أجهزة الغسيل الكلوي Fresenius 5008S", "غسيل كلى", "Fresenius Medical Care — الشرق الأوسط", date(2019, 10, 5), None),
                    ("دورة صيانة ومعايرة محطات التناضح العكسي RO المركزية", "معالجة مياه طبية", "مركز التدريب الهيدروليكي اليمني", date(2021, 6, 12), None)
                ],
                [
                    ("مركز الكلى — هيئة مستشفى الثورة العام", "رئيس الفريق الفني لمركز الكلى", "غسيل كلى وتناضح", date(2018, 6, 1), None, "إدارة صيانة 35 جهاز غسيل دموي ومحطة التناضح العكسي المركزية")
                ]
            ),
            (
                "EMP-SNA-04", "فني. جمال محمد الشامي", "صيانة معدات التعقيم المركزي والجراحة العامة",
                "دبلوم فني أجهزة طبية — المعهد العالي للعلوم الصحية صنعاء",
                "775112233", "jamal.shami@al-thawra.ye", "active", "CSSD",
                "فني أول تعقيم مركزي ومعدات جراحية", "01040055120", date(2016, 1, 10),
                240000.0, 70000.0, "بدل حرارة وبخار وضغط عالي وبدل مناوبة",
                [
                    ("رخصة فني صيانة أجهزة تعقيم وضغط بخاري", "تعقيم مركزي", "وزارة الصحة العامة والسكان — صنعاء", date(2017, 4, 15), None)
                ],
                [
                    ("إدارة التعقيم المركزي CSSD — مستشفى الثورة", "فني صيانة معقمات وغلايات", "تعقيم وتطهير", date(2016, 2, 1), None, "صيانة المعقمات البخارية وأجهزة الغسيل بالموجات فوق الصوتية")
                ]
            ),
            (
                "EMP-SNA-05", "م. ريم خالد الذماري", "ضمان الجودة والمعايرة والأجهزة المخبرية",
                "بكالوريوس هندسة طبية حيوية — جامعة العلوم والتكنولوجيا",
                "770554433", "reem.dhamari@al-thawra.ye", "active", "LAB",
                "مسؤولة المعايرة وضمان الجودة الطبية", "01050077391", date(2020, 11, 1),
                330000.0, 95000.0, "بدل جودة ومختبرات وبدل دقة قياس",
                [
                    ("شهادة معايرة أجهزة المختبرات الآلية Cobas Roche", "مختبرات وتحاليل", "شركة ناتكو الطبية", date(2021, 3, 20), None),
                    ("شهادة تطبيق معايير الآيزو للمعايرة الطبية ISO 17025", "جودة ومعايرة", "المعهد العربي للجودة", date(2023, 1, 15), None)
                ],
                [
                    ("المختبرات المركزية وبنك الدم — مستشفى الثورة", "مهندسة جودة ومعايرة دورية", "معايرة وفحص", date(2020, 12, 1), None, "فحص دقة ومطابقة أجهزة فحص الدم والمناعة ومتابعة ضبط الجودة")
                ]
            ),
            (
                "EMP-SNA-06", "م. هيثم عبدالملك العنسي", "هندسة قسطرة القلب ومراقبة المرضى",
                "بكالوريوس هندسة إلكترونية وطبية — جامعة صنعاء",
                "772118800", "haitham.ansi@al-thawra.ye", "active", "CATH",
                "مهندس صيانة مركز القلب والقسطرة التداخلية", "01060099412", date(2021, 4, 15),
                340000.0, 100000.0, "بدل قسطرة تداخلية وإشراف فني",
                [
                    ("شهادة تدريب معتمدة على أنظمة قسطرة القلب Philips Azurion", "قسطرة وتصوير قلبي", "شركة تهامة الطبية", date(2022, 5, 14), None)
                ],
                [
                    ("مركز القلب — هيئة مستشفى الثورة", "مهندس صيانة أجهزة قسطرة وتخطيط", "أجهزة قلب", date(2021, 5, 1), None, "متابعة كفاءة وجاهزية غرفتي القسطرة التداخلية ووحدة CCU")
                ]
            )
        ]

        techs_map = {}
        for (emp_id, name, spec, qual, ph, em, st, d_code, title, id_no, h_date,
             b_sal, allow, allow_type, quals_list, exp_list) in technicians_profiles:

            dept = departments_map.get(d_code)
            t = db.query(Technician).filter_by(employee_id=emp_id).first()
            if not t:
                t = Technician(
                    employee_id=emp_id,
                    full_name=name,
                    specialization=spec,
                    qualification=qual,
                    phone=ph,
                    email=em,
                    status=st,
                    nationality="يمني",
                    id_document_type="national_id",
                    id_number=id_no,
                    job_title=title,
                    department_id=dept.id if dept else None,
                    work_entity="هيئة مستشفى الثورة العام النموذجي — صنعاء",
                    hire_date=h_date
                )
                db.add(t)
                db.flush()
            else:
                t.full_name = name
                t.specialization = spec
                t.qualification = qual
                t.phone = ph
                t.email = em
                t.status = st
                t.nationality = "يمني"
                t.id_number = id_no
                t.job_title = title
                t.department_id = dept.id if dept else None
                t.work_entity = "هيئة مستشفى الثورة العام النموذجي — صنعاء"
                t.hire_date = h_date

            techs_map[emp_id] = t

            # Seed qualifications if none exist
            if not t.qualifications:
                for q_name, q_spec, q_org, q_iss, q_exp in quals_list:
                    q = TechnicianQualification(
                        technician_id=t.id,
                        name=q_name,
                        specialization=q_spec,
                        issuing_organization=q_org,
                        issue_date=q_iss,
                        expiry_date=q_exp,
                        notes="شهادة معتمدة وموثقة بإدارة الشؤون الهندسية"
                    )
                    db.add(q)

            # Seed experiences if none exist
            if not t.experiences:
                for exp_emp, exp_job, exp_sp, exp_st, exp_en, exp_desc in exp_list:
                    exp = TechnicianExperience(
                        technician_id=t.id,
                        previous_employer=exp_emp,
                        job_title=exp_job,
                        specialization=exp_sp,
                        start_date=exp_st,
                        end_date=exp_en,
                        task_description=exp_desc
                    )
                    db.add(exp)

            # Seed compensation if none exists
            if not t.compensations:
                comp = TechnicianCompensation(
                    technician_id=t.id,
                    basic_salary=b_sal,
                    allowances=allow,
                    allowance_type=allow_type,
                    total_package=b_sal + allow,
                    effective_date=date(2025, 1, 1),
                    notes="حزمة الكادر الفني الطبي المعتمدة من وزارة المالية"
                )
                db.add(comp)

        # =====================================================================
        # 6. Medical Equipment with Foreign Makers, Sana'a Agents, Accessories & Commissioning
        # =====================================================================
        print("[6/9] ربط الأجهزة الطبية التخصصية بالصانع الأجنبي والوكيل بصنعاء والملحقات ومحاضر التعميد...")

        equipment_data = [
            # Asset No, Ar Name, En Name, Category, Model, Serial, Dept, Room, Maker Code, Agent Code, Eng Code, Risk, Status, Price, Install Date, Accessories, Commissioning
            (
                "EQ-THW-001", "جهاز التصوير بالرنين المغناطيسي 1.5 تسلا", "MRI 1.5T Scanner Magnetom Avanto",
                "أجهزة أشعة وتصوير", "Magnetom Avanto Fit", "SN-MR-88349", "RAD", "RAD-MRI",
                "MAN-SIE", "AGT-NATCO", "ENG-NAT-01", "high", "operational", 3200000.0, date(2022, 3, 15),
                [
                    ("طقم ملفات تصوير الرأس والرقبة Head/Neck Coil", "Coil-HN-15", "SN-COIL-01", "Siemens Healthineers", 1.0, 45000.0),
                    ("ملف تصوير العمود الفقري المدمج Spine Matrix Coil", "Coil-SP-15", "SN-COIL-02", "Siemens Healthineers", 1.0, 38000.0),
                    ("نظام التبريد بغاز الهيليوم السائل وصمام الأمان", "Chiller-HE-01", "SN-COOL-99", "Siemens", 1.0, 75000.0)
                ],
                ("COM-THW-2022-014", date(2022, 2, 20), date(2022, 3, 10), "م. أحمد علي القدسي", "أ. محمد الخولاني (مسؤول العهد)", date(2022, 3, 15), "REC-REP-2022-089", "تم الاستلام والفحص ومعايرة الحقل المغناطيسي 1.5T واختبارات التسريب الإشعاعي بنجاح تام وفق شروط المناقصة.")
            ),
            (
                "EQ-THW-002", "جهاز الأشعة المقطعية متعددة الشرائح (128 Slice)", "CT Scanner 128-Slice Revolution EVO",
                "أجهزة أشعة وتصوير", "Revolution EVO 128", "SN-CT-10948", "RAD", "RAD-CT",
                "MAN-GE", "AGT-ORIENT", "ENG-ORI-01", "high", "operational", 2100000.0, date(2021, 8, 10),
                [
                    ("محقن الصبغة الآلي ثنائي الرأس Dual Syringe Injector", "Accutron CT-D", "SN-INJ-551", "Medtron / GE", 1.0, 28000.0),
                    ("محطة معالجة الصور المتقدمة ثنائية وثلاثية الأبعاد", "AW Workstation 4.7", "SN-WS-882", "GE Healthcare", 2.0, 16000.0)
                ],
                ("COM-THW-2021-088", date(2021, 7, 15), date(2021, 8, 1), "م. أحمد علي القدسي", "أ. عادل النجار (مدير المشتريات)", date(2021, 8, 10), "REC-REP-2021-142", "تم استلام الجهاز كاملاً وإجراء معايرة جرعة الأشعة وفحص أنبوبة Performix Pro بكفاءة ممتازة.")
            ),
            (
                "EQ-THW-003", "نظام قسطرة القلب والأوعية الدموية التداخلية", "Digital Angiography System Azurion 7",
                "أجهزة قسطرة وعمليات", "Azurion 7 C20", "SN-AZ-77210", "CATH", "CATH-01",
                "MAN-PHI", "AGT-TIHAMA", "ENG-TIH-02", "high", "operational", 2850000.0, date(2023, 1, 20),
                [
                    ("شاشة عرض جراحية ملونة فائقة الدقة 58 بوصة 8MP", "Surgical Display 58", "SN-DISP-77", "Philips Healthcare", 1.0, 32000.0),
                    ("دواسة التحكم اللاسلكية بالأشعة وحركة الطاولة", "Wireless Foot Switch", "SN-FOOT-12", "Philips Healthcare", 2.0, 6500.0),
                    ("حاقن صبغة القسطرة عالي الضغط للملاحة الوعائية", "Angiomat Illumena", "SN-ANG-991", "Liebel-Flarsheim", 1.0, 24000.0)
                ],
                ("COM-THW-2023-005", date(2022, 12, 10), date(2023, 1, 10), "م. هيثم عبدالملك العنسي", "د. عبدالكريم الشامي (مدير مركز القلب)", date(2023, 1, 20), "REC-REP-2023-018", "استلام نظام القسطرة بنجاح وتنفيذ أول 10 عمليات تداخلية تشخيصية وعلاجية بدون أية ملاحظات.")
            ),
            (
                "EQ-THW-004", "جهاز تنفس صناعي متقدم للعناية المركزة", "ICU Advanced Ventilator Evita V800",
                "أجهزة عناية وتنفس", "Evita V800", "SN-EV-55412", "ICU", "ICU-201",
                "MAN-DRA", "AGT-YEMMED", "ENG-YEM-01", "high", "operational", 148000.0, date(2023, 6, 1),
                [
                    ("ذراع تثبيت دوائر التنفس المفصلية المقواة", "Hinged Circuit Arm", "SN-ARM-01", "Dräger Medical", 1.0, 1800.0),
                    ("دوائر تنفس سيليكون معقمة قابلة للتعقيم بالأوتوكلاف", "Reusable Silicone Circuit", "SN-CIRC-44", "Dräger Medical", 4.0, 650.0),
                    ("وحدة التبخير الرذاذي الميكروية Aeroneb Pro", "Aeroneb Pro Nebulizer", "SN-NEB-201", "Aerogen / Dräger", 2.0, 3200.0)
                ],
                ("COM-THW-2023-042", date(2023, 5, 10), date(2023, 5, 25), "م. فؤاد يحيى المتوكل", "أ. محمد الخولاني (مسؤول العهد)", date(2023, 6, 1), "REC-REP-2023-076", "تم استلام جهاز التنفس واختبار المعايرة الهوائية وحساس الأكسجين وفحص تسريب الدائرة الداخلية.")
            ),
            (
                "EQ-THW-005", "جهاز تنفس صناعي للعناية المركزة", "ICU Ventilator Puritan Bennett 840",
                "أجهزة عناية وتنفس", "Puritan Bennett 840", "SN-PB-99432", "ICU", "ICU-202",
                "MAN-DRA", "AGT-YEMMED", "ENG-YEM-01", "high", "under_maintenance", 125000.0, date(2020, 11, 15),
                [
                    ("ضاغط هواء طبي مضغوط فائق الهدوء", "PB 806 Compressor", "SN-COMP-88", "Puritan Bennett", 1.0, 8500.0),
                    ("مرطب هواء حراري للمرضى MR850", "Humidifier MR850", "SN-HUM-33", "Fisher & Paykel", 1.0, 2900.0)
                ],
                ("COM-THW-2020-071", date(2020, 10, 20), date(2020, 11, 5), "م. فؤاد يحيى المتوكل", "أ. محمد الخولاني (مسؤول العهد)", date(2020, 11, 15), "REC-REP-2020-112", "استلام الجهاز، حالياً تحت الصيانة الدورية لاستبدال صمام الزفير ومعايرة حساس التدفق.")
            ),
            (
                "EQ-THW-006", "محطة تخدير جراحي مع مراقبة غازات متكاملة", "Anesthesia Workstation Primus",
                "أجهزة تخدير وعمليات", "Primus Infinity", "SN-PR-33491", "OR", "OR-01",
                "MAN-DRA", "AGT-YEMMED", "ENG-YEM-01", "high", "operational", 195000.0, date(2022, 9, 5),
                [
                    ("مبخرة مخدر السيفوفلوران Vapor 2000 Sevoflurane", "Vapor 2000 Sevo", "SN-VAP-01", "Dräger Medical", 1.0, 9500.0),
                    ("مبخرة مخدر الإيزوفلوران Vapor 2000 Isoflurane", "Vapor 2000 Iso", "SN-VAP-02", "Dräger Medical", 1.0, 9500.0),
                    ("وحدة سحب وتفريغ الغازات المخدرة العادمة AGS", "Scavenging System AGS", "SN-AGS-10", "Dräger Medical", 1.0, 4200.0)
                ],
                ("COM-THW-2022-067", date(2022, 8, 12), date(2022, 8, 28), "م. فؤاد يحيى المتوكل", "د. عبدالحكيم الشرجبي (رئيس العمليات)", date(2022, 9, 5), "REC-REP-2022-133", "تم الفحص الهيدروليكي والغازي واختبار تسريب غازات التخدير وأنابيب O2 و N2O المعتمدة.")
            ),
            (
                "EQ-THW-007", "برج جراحة المناظير عالي الدقة 4K", "4K Laparoscopy HD Tower Image1 S",
                "أجهزة مناظير جراحية", "Image1 S 4K", "SN-KS-66380", "OR", "OR-03",
                "MAN-STO", "AGT-SHIFA", "ENG-SHI-02", "medium", "operational", 285000.0, date(2023, 4, 12),
                [
                    ("كاميرا منظار جراحي 4K فائقة الحساسية", "Image1 S 4K Camera Head", "SN-CAM-4K", "Karl Storz", 1.0, 34000.0),
                    ("مصدر ضوء زينون بارد 300 واط متطور", "Cold Light Xenon 300", "SN-LIGHT-300", "Karl Storz", 1.0, 14000.0),
                    ("جهاز نفخ تجويف البطن بالغاز الإلكتروني 40L", "Electronic Insufflator 40L", "SN-INSUF-40", "Karl Storz", 1.0, 18500.0),
                    ("شاشة عرض جراحية طبية 4K قياس 32 بوصة", "Medical Monitor 32 4K", "SN-MON-32", "Karl Storz", 1.0, 16000.0)
                ],
                ("COM-THW-2023-029", date(2023, 3, 20), date(2023, 4, 5), "فني. جمال محمد الشامي", "د. عبدالحكيم الشرجبي (رئيس العمليات)", date(2023, 4, 12), "REC-REP-2023-049", "فحص الكاميرا والعدسات الجراحية 0 و 30 درجة واختبار نقاوة الصورة 4K ووحدة ضخ الغاز.")
            ),
            (
                "EQ-THW-008", "جهاز غسيل الكلى الاصطناعي مع تقنية أونلاين", "Hemodialysis Machine 5008S CorDiax",
                "أجهزة غسيل كلى", "5008S CorDiax", "SN-FR-44109", "DIA", "DIA-HALL1",
                "MAN-FRE", "AGT-TIHAMA", "ENG-TIH-01", "high", "operational", 88000.0, date(2022, 2, 18),
                [
                    ("طقم وصلات وحساسات قياس ضغط التروية الشريانية والوريدية", "Pressure Transducer Kit", "SN-TRANS-01", "Fresenius Medical Care", 1.0, 2200.0),
                    ("حامل محاليل بيكربونات ومساند أكياس الغسيل المقواة", "Concentrate Holder", "SN-HOLD-08", "Fresenius Medical Care", 1.0, 1100.0)
                ],
                ("COM-THW-2022-019", date(2022, 1, 25), date(2022, 2, 10), "م. سامي عبدالله الحاشدي", "د. نجيب أبو أصبع (مدير مركز الكلى)", date(2022, 2, 18), "REC-REP-2022-031", "تم ربطه بشبكة المياه المعالجة RO واختبار التوصيلية الكهربائية والضغط ومعايرة مضخة الدم بنجاح.")
            ),
            (
                "EQ-THW-009", "جهاز غسيل الكلى الاصطناعي", "Hemodialysis Machine 4008S Next Generation",
                "أجهزة غسيل كلى", "4008S Next Gen", "SN-FR-44280", "DIA", "DIA-HALL2",
                "MAN-FRE", "AGT-TIHAMA", "ENG-TIH-01", "high", "under_maintenance", 78000.0, date(2021, 5, 22),
                [
                    ("حساس كشف تسريب الدم البصري Optical Blood Leak Detector", "Blood Leak Detector", "SN-BLD-09", "Fresenius Medical Care", 1.0, 2800.0)
                ],
                ("COM-THW-2021-049", date(2021, 4, 28), date(2021, 5, 15), "م. سامي عبدالله الحاشدي", "د. نجيب أبو أصبع (مدير مركز الكلى)", date(2021, 5, 22), "REC-REP-2021-081", "استلام الجهاز، حالياً تحت الصيانة الوقائية الطارئة لاستبدال صمام التروية الهيدروليكي.")
            ),
            (
                "EQ-THW-010", "جهاز صدمات ومزيل الرجفان ثنائي الطور", "Biphasic Defibrillator R Series Plus",
                "أجهزة طوارئ وإنعاش", "R Series Plus", "SN-ZL-22890", "ER", "ER-RESUS",
                "MAN-NK", "AGT-SHIFA", "ENG-SHI-02", "high", "operational", 46000.0, date(2023, 7, 10),
                [
                    ("بطارية ليثيوم أيون قابلة للشحن السريع SurePower", "SurePower Li-Ion Battery", "SN-BAT-ZL1", "Zoll / Nihon Kohden", 2.0, 1200.0),
                    ("أقطاب صدمات للبالغين والأطفال متعددة الاستخدام OneStep", "OneStep Cable & Paddles", "SN-PAD-88", "Zoll Medical", 1.0, 3100.0),
                    ("كابل تخطيط قلب 3 أطراف مع حساس قياس ضغط التنفس", "3-Lead ECG Cable", "SN-CBL-3L", "Nihon Kohden", 2.0, 480.0)
                ],
                ("COM-THW-2023-061", date(2023, 6, 18), date(2023, 7, 2), "فني. جمال محمد الشامي", "د. طارق نعمان (مدير الطوارئ)", date(2023, 7, 10), "REC-REP-2023-094", "تمت معايرة طاقة التفريغ حتى 200 جول وفحص زمن الشحن والتفريغ واختبار السلامة الكهربائية.")
            ),
            (
                "EQ-THW-011", "جهاز مراقبة العلامات الحيوية للمريض (8 قنوات)", "IntelliVue Patient Monitor MX800",
                "أجهزة مراقبة وتشخيص", "IntelliVue MX800", "SN-PH-11470", "ICU", "ICU-201",
                "MAN-PHI", "AGT-TIHAMA", "ENG-TIH-02", "medium", "operational", 39000.0, date(2022, 10, 14),
                [
                    ("مستشعر قياس نسبة تشبع الأكسجين SpO2 دائم للبالغين", "Adult SpO2 Reusable Sensor", "SN-SPO2-01", "Philips Healthcare", 2.0, 450.0),
                    ("حزام قياس ضغط الدم غير الغازي NIBP للأذرع المتعددة", "NIBP Cuff Multi-size Set", "SN-NIBP-05", "Philips Healthcare", 3.0, 220.0),
                    ("كابل تخطيط قلب 5 أطراف حماية ضد القطع والتشويش", "5-Lead ECG Shielded Trunk", "SN-ECG-5L", "Philips Healthcare", 2.0, 580.0)
                ],
                ("COM-THW-2022-079", date(2022, 9, 25), date(2022, 10, 8), "م. فؤاد يحيى المتوكل", "أ. محمد الخولاني (مسؤول العهد)", date(2022, 10, 14), "REC-REP-2022-155", "استلام الشاشة وربطها بالشبكة المركزية لوحدة العناية المركزة وفحص كافة الحساسات الحيوية.")
            ),
            (
                "EQ-THW-012", "جهاز تصوير تلفزيوني بالموجات فوق الصوتية (سونار 4D)", "Ultrasound Color Doppler Resona 7",
                "أجهزة أشعة وتصوير", "Resona 7 Premium", "SN-MR-90812", "RAD", "RAD-US",
                "MAN-MIN", "AGT-YEMMED", "ENG-YEM-02", "medium", "operational", 168000.0, date(2023, 8, 20),
                [
                    ("مجس بطني محدب متعدد الترددات Convex Probe SC5-1U", "Convex Probe SC5-1U", "SN-PRB-CX", "Mindray Bio-Medical", 1.0, 14500.0),
                    ("مجس خطي للأوعية والأنسجة السطحية Linear Probe L11-3U", "Linear Probe L11-3U", "SN-PRB-LN", "Mindray Bio-Medical", 1.0, 15500.0),
                    ("مجس مهبلي وتناسلي فائق الدقة Endocavity Probe V11-3U", "Endocavity V11-3U", "SN-PRB-EC", "Mindray Bio-Medical", 1.0, 16800.0),
                    ("طابعة تقارير سوني طبية حرارية عالية الوضوح", "Sony UP-X898MD Video Printer", "SN-PRN-SNY", "Sony", 1.0, 3200.0)
                ],
                ("COM-THW-2023-074", date(2023, 7, 28), date(2023, 8, 12), "م. أحمد علي القدسي", "د. سميرة المجيدي (رئيسة قسم السونار)", date(2023, 8, 20), "REC-REP-2023-118", "فحص دقة الموجات الصوتية ووضوح تدفق الدوبلر الملون وسلامة كافة المجسات الأربعة.")
            ),
            (
                "EQ-THW-013", "جهاز تعقيم مركزي بالبخار سعة 500 لتر", "Autoclave Steam Sterilizer 5090 HS",
                "أجهزة تعقيم وتطهير", "5090 HS", "SN-TT-88129", "CSSD", "CSSD-STER",
                "MAN-TUT", "AGT-SHIFA", "ENG-SHI-01", "high", "operational", 230000.0, date(2021, 12, 5),
                [
                    ("طقم سلات تحميل وتفريغ استانلس ستيل 316L للتعقيم", "Loading Carts & Baskets Set", "SN-BSK-01", "Tuttnauer", 2.0, 7800.0),
                    ("طابعة رقمية مدمجة لتوثيق دورات التعقيم والحرارة", "Built-in Cycle Printer", "SN-PRN-TT", "Tuttnauer", 1.0, 2400.0),
                    ("عنصر تسخين بخار 18kW احتياطي مقاوم للأملاح", "Heating Element 18kW", "SN-HT-18K", "Tuttnauer", 1.0, 4200.0)
                ],
                ("COM-THW-2021-098", date(2021, 11, 10), date(2021, 11, 28), "فني. جمال محمد الشامي", "أ. فهد الظاهري (مسؤول التعقيم)", date(2021, 12, 5), "REC-REP-2021-177", "اختبار تفريغ الهواء بالفاكيوم ورفع الضغط لـ 2.2 بار وحرارة 134 مئوية، واختبار المؤشرات البيولوجية بنجاح.")
            ),
            (
                "EQ-THW-014", "حاضنة أطفال حديثي الولادة والخدج فائقة العناية", "Infant Care Incubator Giraffe OmniBed",
                "أجهزة أطفال ورعاية", "Giraffe OmniBed Carestation", "SN-GE-77401", "NICU", "NICU-MAIN",
                "MAN-GE", "AGT-ORIENT", "ENG-ORI-02", "high", "operational", 72000.0, date(2023, 2, 14),
                [
                    ("ميزان إلكتروني داخلي مدمج في المرتبة السريرية", "In-Bed Scale System", "SN-SCL-01", "GE Healthcare", 1.0, 4200.0),
                    ("حساس حرارة الجلد الجلدي الدقيق المزدوج (Re-usable)", "Skin Temp Probe Dual", "SN-TMP-88", "GE Healthcare", 2.0, 950.0)
                ],
                ("COM-THW-2023-011", date(2023, 1, 15), date(2023, 2, 2), "م. فؤاد يحيى المتوكل", "د. منى الأصبحي (استشارية حديثي الولادة)", date(2023, 2, 14), "REC-REP-2023-024", "تم فحص نظام التدفئة المشعة وتدوير الهواء الرطب وإنذارات انقطاع الكهرباء وتغير الحرارة.")
            ),
            (
                "EQ-THW-015", "محلل كيمياء الدم والمناعة التلقائي المتكامل", "Automated Clinical Chemistry Cobas c501",
                "أجهزة مختبرات وتحليل", "Cobas c501 Integrated", "SN-RC-33290", "LAB", "LAB-CHEM",
                "MAN-ROC", "AGT-NATCO", "ENG-NAT-02", "medium", "operational", 320000.0, date(2022, 4, 18),
                [
                    ("وحدة سحب ونقل العينات الآلية Rack Sampler", "Rack Rotor Sampler", "SN-RACK-01", "Roche Diagnostics", 1.0, 19000.0),
                    ("محطة غسيل كوفيتات التفاعل بالموجات فوق الصوتية", "Cuvette Wash Station Ultrasonic", "SN-WSH-02", "Roche Diagnostics", 1.0, 12500.0),
                    ("نظام إمداد المياه النقية المعالجة CLSI Type 1", "Milli-Q Water Feed System", "SN-WQ-99", "Merck / Roche", 1.0, 16000.0)
                ],
                ("COM-THW-2022-031", date(2022, 3, 22), date(2022, 4, 8), "م. ريم خالد الذماري", "د. نجيب القباطي (مدير المختبرات المركزية)", date(2022, 4, 18), "REC-REP-2022-054", "تمت المعايرة الكيميائية ومراقبة الجودة بمحاليل Control معتمدة من Roche واجتازت بنسبة دقة 99.8%.")
            ),
            (
                "EQ-THW-016", "جهاز تخطيط القلب الرقمي 12 قناة مع تحليل آلي", "12-Lead ECG Machine Cardiofax M",
                "أجهزة قلب وتشخيص", "Cardiofax M ECG-2350", "SN-NK-55109", "CATH", "CATH-ECHO",
                "MAN-NK", "AGT-SHIFA", "ENG-SHI-02", "low", "operational", 24000.0, date(2023, 9, 10),
                [
                    ("كابل مريض 10 أطراف محمي ضد إشارات أجهزة التشريط", "10-Lead Patient Cable Defib-Proof", "SN-CBL-NK", "Nihon Kohden", 2.0, 420.0),
                    ("طقم أقطاب شفط صدرية وملاقط أطراف مطلية بالفضة", "Chest Bulbs & Limb Clamps", "SN-ELC-NK", "Nihon Kohden", 2.0, 180.0)
                ],
                ("COM-THW-2023-085", date(2023, 8, 25), date(2023, 9, 3), "م. هيثم عبدالملك العنسي", "د. عبدالكريم الشامي (مدير مركز القلب)", date(2023, 9, 10), "REC-REP-2023-132", "تمت تجربة دقة التخطيط وسرعة استجابة الورق الحراري ومطابقة تحليلات ECAPS12C مع الأطباء.")
            ),
            (
                "EQ-THW-017", "منظار تشخيصي تداخلي للجهاز الهضمي والمعدة", "Gastrointestinal Video Endoscope EVIS EXERA III",
                "أجهزة مناظير جراحية", "GIF-HQ190", "SN-OLY-44120", "ENDO", "ENDO-01",
                "MAN-OLY", "AGT-SABA", "ENG-SAB-01", "medium", "operational", 155000.0, date(2023, 3, 25),
                [
                    ("معالج فيديو رقمي ومنبع إضاءة متكامل CLV-190", "Xenon Light Source & Processor", "SN-PRC-OLY", "Olympus", 1.0, 28000.0),
                    ("طقم أدوات أخذ الخزعات والملقط الشرياني المعقم", "Biopsy Forceps & Snare Set", "SN-BIO-01", "Olympus", 4.0, 850.0)
                ],
                ("COM-THW-2023-021", date(2023, 3, 2), date(2023, 3, 18), "م. أحمد علي القدسي", "د. منصور الأهدل (رئيس وحدة المناظير)", date(2023, 3, 25), "REC-REP-2023-039", "فحص زوايا الانحناء للأعلى والأسفل واختبار تسريب الضغط الداخلي Leak Tester وجودة الإضاءة NBI.")
            ),
            (
                "EQ-THW-018", "طاولة عمليات جراحية كهربائية هيدروليكية متطورة", "Electro-Hydraulic Surgical Operating Table",
                "أجهزة عمليات وجراحة", "TruSystem 7000", "SN-TR-66129", "OR", "OR-02",
                "MAN-STR", "AGT-ORIENT", "ENG-ORI-01", "medium", "operational", 110000.0, date(2022, 7, 19),
                [
                    ("جهاز تحكم سلكي مع شاشة رقمية لعرض زوايا الطاولة", "Remote Control Handset", "SN-RMT-01", "Trumpf / Stryker", 1.0, 3200.0),
                    ("طقم وسائد سريرية مطاطية مضادة لتقرحات الفراش", "Viscoelastic Mattress Pads", "SN-PAD-02", "Stryker", 1.0, 4800.0)
                ],
                ("COM-THW-2022-054", date(2022, 6, 25), date(2022, 7, 10), "فني. جمال محمد الشامي", "د. عبدالحكيم الشرجبي (رئيس العمليات)", date(2022, 7, 19), "REC-REP-2022-098", "تم اختبار الحركات الهيدروليكية ووضعيات Trendelenburg وحمل الأوزان حتى 250 كجم.")
            ),
            (
                "EQ-THW-019", "جهاز أشعة سينية رقمية ثابتة للصدر والعظام", "Digital Radiography X-Ray System",
                "أجهزة أشعة وتصوير", "Multix Impact", "SN-SIE-77190", "RAD", "RAD-XRAY",
                "MAN-SIE", "AGT-NATCO", "ENG-NAT-01", "high", "operational", 450000.0, date(2022, 11, 10),
                [
                    ("لوح كاشف رقمي لاسلكي مسطح Flat Panel Detector", "Wireless FPD 43x43", "SN-FPD-01", "Siemens Healthineers", 1.0, 38000.0),
                    ("أنبوبة أشعة سينية عالية التحمل الحراري Opti 150", "X-Ray Tube Opti 150", "SN-TUB-01", "Siemens", 1.0, 29000.0)
                ],
                ("COM-THW-2022-083", date(2022, 10, 15), date(2022, 11, 2), "م. أحمد علي القدسي", "أ. محمد الخولاني (مسؤول العهد)", date(2022, 11, 10), "REC-REP-2022-164", "تمت مطابقة مواصفات المولد عالي التردد 65kW واختبارات الجرعة الإشعاعية ومحدد الحقل الضوئي.")
            ),
            (
                "EQ-THW-020", "جهاز مضخة حقن وريدي دقيقة ومبرمجة", "Precision Infusion Volumetric Pump",
                "أجهزة مراقبة وتشخيص", "Benefusion VP5", "SN-MN-33100", "ICU", "ICU-202",
                "MAN-MIN", "AGT-YEMMED", "ENG-YEM-02", "medium", "standby", 8500.0, date(2023, 10, 5),
                [
                    ("حامل محاليل استانلس ستيل متحرك بعجلات مضادة للكهرباء", "IV Pole Mobile Cart", "SN-POLE-01", "Mindray", 1.0, 350.0),
                    ("حساس قياس قطرات السائل وحماية من الفقاعات الهوائية", "Drop Sensor Air-in-Line", "SN-DRP-02", "Mindray", 1.0, 220.0)
                ],
                ("COM-THW-2023-094", date(2023, 9, 20), date(2023, 10, 1), "م. فؤاد يحيى المتوكل", "أ. محمد الخولاني (مسؤول العهد)", date(2023, 10, 5), "REC-REP-2023-149", "تمت معايرة معدل التدفق والضغط الانسدادي والإنذارات وتجهيزها في الاحتياط الفوري.")
            )
        ]

        equipment_map = {}
        for (asset_no, name_ar, name_en, cat, model, sn, d_code, r_code,
             m_code, a_code, eng_code, risk, st, cost, inst_date,
             accessories_list, comm_data) in equipment_data:

            dept = departments_map.get(d_code)
            loc = locations_map.get(r_code)
            maker = vendors_map.get(m_code)
            agent = vendors_map.get(a_code)
            eng = engineers_map.get(eng_code)

            eq = db.query(Equipment).filter_by(asset_number=asset_no).first()
            if not eq:
                eq = Equipment(
                    asset_number=asset_no,
                    inventory_number=f"INV-THW-{asset_no[-3:]}",
                    serial_number=sn,
                    name_ar=name_ar,
                    name_en=name_en,
                    model=model,
                    category=cat,
                    department_id=dept.id if dept else None,
                    location_id=loc.id if loc else None,
                    manufacturer_id=maker.id if maker else None,
                    supplier_id=agent.id if agent else None,
                    agent_id=agent.id if agent else None,
                    assigned_engineer_id=eng.id if eng else None,
                    purchase_date=inst_date - timedelta(days=60),
                    installation_date=inst_date,
                    warranty_expiry_date=inst_date + timedelta(days=730),
                    purchase_price=cost,
                    risk_level=risk,
                    criticality="critical" if risk == "high" else ("semi_critical" if risk == "medium" else "non_critical"),
                    status=st,
                    notes=f"أصل طبي تابع لهيئة مستشفى الثورة العام بصنعاء. توريد وخدمة: {agent.name if agent else 'محلي'}."
                )
                db.add(eq)
                db.flush()
            else:
                eq.name_ar = name_ar
                eq.name_en = name_en
                eq.model = model
                eq.category = cat
                eq.department_id = dept.id if dept else None
                eq.location_id = loc.id if loc else None
                eq.manufacturer_id = maker.id if maker else None
                eq.supplier_id = agent.id if agent else None
                eq.agent_id = agent.id if agent else None
                eq.assigned_engineer_id = eng.id if eng else None
                eq.purchase_price = cost
                eq.installation_date = inst_date
                eq.status = st

            equipment_map[asset_no] = eq

            # Seed Accessories
            if not eq.accessories:
                for acc_name, acc_mod, acc_sn, acc_man, acc_qty, acc_cost in accessories_list:
                    acc = EquipmentAccessory(
                        equipment_id=eq.id,
                        name=acc_name,
                        model_number=acc_mod,
                        serial_number=acc_sn,
                        manufacturer=acc_man,
                        quantity=acc_qty,
                        unit_cost=acc_cost,
                        total_cost=acc_qty * acc_cost,
                        added_date=inst_date,
                        notes="ملحق أصلي معتمد مع الجهاز"
                    )
                    db.add(acc)

            # Seed Receiving & Commissioning
            if not eq.receiving and comm_data:
                c_num, c_date, r_date, rec_tech, reg_off, reg_date, rep_num, r_notes = comm_data
                rec = EquipmentReceiving(
                    equipment_id=eq.id,
                    commissioning_number=c_num,
                    commissioning_date=c_date,
                    receipt_date=r_date,
                    receiving_technician_name=rec_tech,
                    registration_officer_name=reg_off,
                    registration_date=reg_date,
                    receipt_report_number=rep_num,
                    receipt_notes=r_notes
                )
                db.add(rec)

        # =====================================================================
        # 7. Spare Parts Warehouse in Al-Thawra Hospital (مستودع قطع الغيار)
        # =====================================================================
        print("[7/9] تسجيل مخزون قطع الغيار الطبية بمستودع الهندسة الطبية بالثورة...")
        spare_parts_data = [
            ("SP-THW-001", "حساس قياس نسبة الأكسجين O2 Sensor Cell", "O2 Sensor Cell", "MAN-DRA", "مستهلكات عناية وتنفس", "BIN-ICU-01", 16.0, 5.0, 390.0, "Piece"),
            ("SP-THW-002", "سنسور قياس تدفق الغازات الطبي Infinity", "Infinity Flow Sensor (Dräger)", "MAN-DRA", "حساسات تنفس وتخدير", "BIN-ICU-02", 10.0, 4.0, 440.0, "Piece"),
            ("SP-THW-003", "صمام الزفير المتكامل لجهاز PB840", "Expiratory Valve Assembly", "MAN-DRA", "قطع صيانة تنفس", "BIN-ICU-05", 4.0, 2.0, 1450.0, "Piece"),
            ("SP-THW-004", "فلتر تنقية سائل غسيل الكلى Diasafe Plus", "Diasafe Plus Endotoxin Filter", "MAN-FRE", "فلاتر ومستهلكات كلى", "BIN-DIA-01", 45.0, 12.0, 165.0, "Piece"),
            ("SP-THW-005", "صمام كهرومغناطيسي هيدروليكي Solenoid 24V", "Solenoid Valve 24V DC", "MAN-FRE", "قطع هيدروليك كلى", "BIN-DIA-03", 8.0, 3.0, 330.0, "Piece"),
            ("SP-THW-006", "مضخة دم تمعجية لغسيل الكلى Peristaltic Pump Head", "Blood Pump Rotor Head", "MAN-FRE", "قطع مضخات كلى", "BIN-DIA-06", 3.0, 2.0, 1800.0, "Piece"),
            ("SP-THW-007", "بطارية ليثيوم لجهاز الصدمات R Series", "Rechargeable Li-Ion Battery (Zoll)", "MAN-NK", "بطاريات ومصادر طاقة", "BIN-PWR-02", 5.0, 3.0, 980.0, "Piece"),
            ("SP-THW-008", "كابل وحساس تشبع الأكسجين SpO2 للبالغين", "Adult SpO2 Reusable Sensor Cable", "MAN-PHI", "ملحقات وكابلات مريض", "BIN-CBL-04", 24.0, 8.0, 250.0, "Piece"),
            ("SP-THW-009", "لمبة مصدر ضوء زنون 300 واط للمناظير الجراحية", "Xenon 300W Lamp Module", "MAN-STO", "لمبات ومصادر إضاءة", "BIN-LGT-01", 3.0, 2.0, 1900.0, "Piece"),
            ("SP-THW-010", "حزام إغلاق باب جهاز التعقيم سيليكون حراري", "Silicone Door Gasket 5090", "MAN-TUT", "موانع تسريب وعوازل", "BIN-CSS-02", 6.0, 2.0, 560.0, "Piece"),
            ("SP-THW-011", "عنصر تسخين بالبخار 9kW لجهاز الأوتوكلاف", "Heating Element 9kW Steam", "MAN-TUT", "عناصر تسخين وغلايات", "BIN-CSS-07", 4.0, 2.0, 1250.0, "Piece"),
            ("SP-THW-012", "بورد مزود الطاقة الرئيسي لأنظمة المراقبة 24V", "Main Switching Power Supply 24V", "MAN-MIN", "إلكترونيات وبوردات", "BIN-ELC-03", 3.0, 2.0, 2750.0, "Piece"),
            ("SP-THW-013", "مضخة تبريد سائل لمولد الأشعة المقطعية", "Oil Circulation Pump (CT Tube)", "MAN-GE", "تبريد وميكانيكا أشعة", "BIN-RAD-01", 2.0, 1.0, 4800.0, "Piece"),
            ("SP-THW-014", "طقم خراطيم هيدروليكية مقاومة للضغط العالي", "High-Pressure Hydraulic Hose Kit", "MAN-STR", "هيدروليك عمليات", "BIN-OR-03", 5.0, 2.0, 620.0, "Kit"),
            ("SP-THW-015", "مستشعر درجة الحرارة الدقيق لحاضنات الأطفال", "Infant Skin Temp Thermistor", "MAN-GE", "حساسات أطفال", "BIN-NIC-01", 12.0, 4.0, 280.0, "Piece")
        ]

        parts_map = {}
        for p_code, p_ar, p_en, m_code, p_cat, p_bin, p_qty, p_min, p_cost, p_uom in spare_parts_data:
            maker = vendors_map.get(m_code)
            sp = db.query(SparePart).filter_by(part_number=p_code).first()
            if not sp:
                sp = SparePart(
                    part_number=p_code,
                    name_ar=p_ar,
                    name_en=p_en,
                    category=p_cat,
                    manufacturer_id=maker.id if maker else None,
                    storage_bin_location=p_bin,
                    quantity_on_hand=p_qty,
                    minimum_reorder_level=p_min,
                    unit_cost=p_cost,
                    unit_of_measure=p_uom,
                    description=f"قطعة غيار طبية أصلية معتمدة بمستودع هيئة مستشفى الثورة بصنعاء ({p_bin})",
                    is_active=True
                )
                db.add(sp)
                db.flush()
            else:
                sp.name_ar = p_ar
                sp.name_en = p_en
                sp.category = p_cat
                sp.manufacturer_id = maker.id if maker else None
                sp.storage_bin_location = p_bin
                sp.quantity_on_hand = p_qty
                sp.minimum_reorder_level = p_min
                sp.unit_cost = p_cost
            parts_map[p_code] = sp

        # =====================================================================
        # 8. Maintenance Work Orders (أوامر الصيانة وتذاكر الأعطال الواقعية)
        # =====================================================================
        print("[8/9] تسجيل أوامر العمل وتذاكر الصيانة الطارئة والدورية...")
        wos_data = [
            (
                "WO-THW-2026-001", "EQ-THW-005", "ICU", "EMP-SNA-02", "critical", "in_progress",
                "توقف مفاجئ في حساس تدفق الغازات وظهور إنذار Flow Sensor Error أثناء عمل الجهاز",
                "ظهور وميض إنذار باللون الأحمر وصوت تنبيه مستمر وعدم استقرار حجم التهوية المدفوع",
                "د. عصام النعمان (استشاري العناية المركزة)", "777441122",
                datetime.now() - timedelta(days=2), datetime.now() - timedelta(days=2, hours=-1),
                None, None,
                "تلف وتكلس في سلك الاستشعار الحراري الدقيق بحساس التدفق نتيجة الرطوبة العالية",
                "جاري استبدال سنسور التدفق ومعايرة ضغط الشهيق والزفير مع وكيل دراجر (يمن ميديكال)",
                "عطل في مستشعر التدفق نتيجة انتهاء العمر الافتراضي وساعات التشغيل المستمرة",
                150.0, 440.0,
                [("SP-THW-002", 1.0, 440.0)]
            ),
            (
                "WO-THW-2026-002", "EQ-THW-009", "DIA", "EMP-SNA-03", "high", "waiting_parts",
                "تسريب طفيف في صمام التروية وملاحظة انخفاض تدفق محلول الغسيل أثناء جلسة مريض",
                "انخفاض ضغط سائل الغسيل وظهور رسالة تنبيه Dialysate Flow Low على الشاشة الرئيسية",
                "أ. منى الحيمي (مشرفة تمريض مركز الكلى)", "771223344",
                datetime.now() - timedelta(days=3), datetime.now() - timedelta(days=3, hours=-2),
                None, None,
                "وجود ترسبات أملاح واهتراء في الحشية المطاطية لصمام الصرف الكهرومغناطيسي 24V",
                "تم إيقاف تشغيل الجهاز وفصل خطوط التروية بانتظار استلام صمام جديد من شركة تهامة الطبية",
                "تآكل في بكرة الصمام نتيجة الاستخدام الكثيف ودورات التطهير الكيميائي اليومية",
                120.0, 0.0,
                []
            ),
            (
                "WO-THW-2026-003", "EQ-THW-007", "OR", "EMP-SNA-04", "medium", "completed",
                "ضعف وتذبذب شدة إضاءة منبع الزنون 300W في برج مناظير الجراحة أثناء عملية استئصال مرارة",
                "تغير لون الضوء الجراحي إلى الأصفر الباهت وصعوبة وضوح الرؤية عبر الكاميرا 4K",
                "د. عبدالحكيم الشرجبي (استشاري الجراحة العامة)", "777889900",
                datetime.now() - timedelta(days=6), datetime.now() - timedelta(days=6, hours=-1),
                datetime.now() - timedelta(days=5), datetime.now() - timedelta(days=5),
                "انتهاء العمر التشغيلي للمبة الزنون 300 واط وتجاوزها 550 ساعة إضاءة مسجلة",
                "تم استبدال موديول لمبة الزنون بالكامل من المستودع ومعايرة اتزان البياض White Balance بنجاح",
                "استهلاك طبيعي للعمر التشغيلي لمصدر الضوء",
                200.0, 1900.0,
                [("SP-THW-009", 1.0, 1900.0)]
            ),
            (
                "WO-THW-2026-004", "EQ-THW-010", "ER", "EMP-SNA-02", "critical", "assigned",
                "ظهور تنبيه استبدال البطارية Low Battery عند فصل كابل الكهرباء الرئيسي في غرفة الإنعاش",
                "انخفاض زمن الصدمة وعدم قدرة الجهاز على الاحتفاظ بالشحن لأكثر من 5 دقائق",
                "أ. محمد الوادعي (فني طوارئ وإنعاش)", "773112255",
                datetime.now() - timedelta(days=1), datetime.now() - timedelta(hours=18),
                None, None,
                "فقدان خلايا الليثيوم قدرتها على تخزين الشحنة نتيجة التفريغ العميق المستمر",
                "تم تحويل الجهاز للورشة الفنية وجاري فحص دارة الشحن الداخلي واستبدال بطارية الليثيوم",
                "هبوط كفاءة البطارية الكيميائية بعد عامين من الخدمة الميدانية المستمرة",
                100.0, 980.0,
                [("SP-THW-007", 1.0, 980.0)]
            ),
            (
                "WO-THW-2026-005", "EQ-THW-013", "CSSD", "EMP-SNA-04", "high", "completed",
                "تسريب بخار ملحوظ من إطار الباب الجانبي لمعقم البخار 500L وظهور صوت صفير عند ضغط 2 بار",
                "هبوط بطيء في ضغط الغرفة وعدم اكتمال دورة التعقيم عند حرارة 134 مئوية",
                "أ. فهد الظاهري (مسؤول قسم التعقيم المركزي)", "770998811",
                datetime.now() - timedelta(days=8), datetime.now() - timedelta(days=8, hours=-1),
                datetime.now() - timedelta(days=7), datetime.now() - timedelta(days=7),
                "تشقق وتصلب في حزام السيليكون الحراري المانع للتسريب المحيط بباب الغرفة",
                "تم فك الحزام القديم وتنظيف المجرى وتركيب إطار سيليكون أصلي وإجراء اختبار باوي ديك بنجاح",
                "جفاف المطاط الحراري نتيجة الحرارة والبخار المستمر على مدار 12 شهراً",
                180.0, 560.0,
                [("SP-THW-010", 1.0, 560.0)]
            )
        ]

        for (wo_num, eq_asset, d_code, tech_id, prio, st, desc, symp,
             rep_by, rep_ph, r_dt, s_dt, c_dt, cl_dt, diag, corr,
             cause, l_cost, p_cost, parts_list) in wos_data:

            wo = db.query(WorkOrder).filter_by(work_order_number=wo_num).first()
            eq = equipment_map.get(eq_asset)
            dept = departments_map.get(d_code)
            tech = techs_map.get(tech_id)

            if not wo:
                wo = WorkOrder(
                    work_order_number=wo_num,
                    equipment_id=eq.id if eq else None,
                    department_id=dept.id if dept else None,
                    assigned_technician_id=tech.id if tech else None,
                    priority=prio,
                    status=st,
                    failure_description=desc,
                    symptoms=symp,
                    reported_by_name=rep_by,
                    reporter_contact=rep_ph,
                    report_date=r_dt,
                    started_at=s_dt,
                    completed_at=c_dt,
                    closed_at=cl_dt,
                    diagnosis=diag,
                    corrective_action=corr,
                    failure_cause=cause,
                    total_labor_cost=l_cost,
                    total_parts_cost=p_cost
                )
                db.add(wo)
                db.flush()

                # Add status transition log
                log1 = WorkOrderLog(
                    work_order_id=wo.id,
                    from_status=None,
                    to_status="pending",
                    notes="تم تسجيل بلاغ العطل بالنظام وإشعار مسؤول الصيانة",
                    timestamp=r_dt
                )
                log2 = WorkOrderLog(
                    work_order_id=wo.id,
                    from_status="pending",
                    to_status=st,
                    notes=f"تم إسناد التذكرة إلى {tech.full_name if tech else 'المهندس المختص'}",
                    timestamp=s_dt or r_dt
                )
                db.add_all([log1, log2])

                # Add consumed parts
                for part_code, p_qty, p_uprice in parts_list:
                    sp_item = parts_map.get(part_code)
                    if sp_item:
                        wo_p = WorkOrderPart(
                            work_order_id=wo.id,
                            part_id=sp_item.id,
                            quantity=p_qty,
                            unit_price=p_uprice,
                            total_price=p_qty * p_uprice
                        )
                        db.add(wo_p)
            else:
                wo.status = st
                wo.diagnosis = diag
                wo.corrective_action = corr

        # =====================================================================
        # 9. Preventive Maintenance, Contracts, and Monthly Reports
        # =====================================================================
        print("[9/9] جدولة خطط الصيانة الوقائية وعقود الخدمة وأرشيف التقارير الشهرية...")

        # 9.A PM Plans & Schedules
        pm_plans = [
            ("بروتوكول الصيانة الوقائية والمعايرة لأجهزة التنفس الصناعي", "أجهزة عناية وتنفس", 90, 60, [
                {"step": 1, "task": "فحص سلامة كابلات الطاقة والتأريض الكهربائي والوصلات الهوائية والأكسجين O2/Air"},
                {"step": 2, "task": "معايرة حساسات التدفق Flow Sensors وحساس الأكسجين O2 Cell والتأكد من خطيتها"},
                {"step": 3, "task": "اختبار التسريب الداخلي والخارجي ومطاطية دائرة التنفس Leak & Compliance Test"},
                {"step": 4, "task": "فحص عمل البطارية الاحتياطية وإنذارات انقطاع الكهرباء وتدني ضغط الغاز"},
                {"step": 5, "task": "استبدال فلتر الهواء الميكروبي وتنظيف مروحة التبريد ومجرى التهوية"}
            ]),
            ("بروتوكول السلامة الكهربائية والمعايرة السنوية لأجهزة الصدمات", "أجهزة طوارئ وإنعاش", 180, 45, [
                {"step": 1, "task": "اختبار السلامة الكهربائية والتسريب الأرضي Electrical Safety Test وفق معيار IEC 62353"},
                {"step": 2, "task": "قياس دقة الطاقة المفرغة بجهاز محلل الصدمات (Joule Output Accuracy: 10, 50, 100, 200 J)"},
                {"step": 3, "task": "فحص كابلات الأقطاب ومؤشر الشحن السريع والتأكد من سلامة العوازل المطاطية"},
                {"step": 4, "task": "فحص سعة بطارية الليثيوم واختبار دورة التفريغ والشحن الكاملة"}
            ]),
            ("بروتوكول الصيانة الدورية الشاملة لأجهزة غسيل الكلى ومحطة المياه", "أجهزة غسيل كلى", 90, 75, [
                {"step": 1, "task": "معايرة دقة ضغط التروية وسرعة مضخة الدم الشريانية Blood Pump Calibration"},
                {"step": 2, "task": "فحص ومعايرة التوصيلية الكهربائية لسائل الغسيل وحرارة المحلول 37 مئوية"},
                {"step": 3, "task": "استبدال فلاتر الاندوتوكسين وفحص الصمامات الكهرومغناطيسية وحساس تسريب الدم"},
                {"step": 4, "task": "تنفيذ دورة التطهير الحراري والكيميائي الشاملة وفحص نقاوة مياه الـ RO"}
            ]),
            ("بروتوكول الصيانة السنوية لأجهزة الأشعة والتصوير المتقدم", "أجهزة أشعة وتصوير", 365, 120, [
                {"step": 1, "task": "معايرة جودة الصورة وتدرج التباين الهندسي Image Quality & Spatial Resolution"},
                {"step": 2, "task": "فحص مستوى ضغط غاز الهيليوم ونظام التبريد المائي للرنين المغناطيسي"},
                {"step": 3, "task": "فحص محدد الحقل الإشعاعي وتطابق الليزر ودقة الجرعة الممتصة"},
                {"step": 4, "task": "تنظيف وحدات معالجة الصور الرقمية وفحص خوادم الـ PACS الطبية"}
            ]),
            ("بروتوكول الفحص الدوري لمعقمات البخار المركزية والأوتوكلاف", "أجهزة تعقيم وتطهير", 90, 60, [
                {"step": 1, "task": "فحص صمامات الأمان وتفريغ الضغط الميكانيكية والهوائية Safety Relief Valves"},
                {"step": 2, "task": "فحص سلامة حزام السيليكون المانع للتسريب ونظافة مجرى الباب المصفح"},
                {"step": 3, "task": "معايرة حساسات الحرارة المزدوجة PT100 ومحولات الضغط Transducers"},
                {"step": 4, "task": "تنفيذ اختبار تسريب الفاكيوم واختبار باوي ديك Bowie-Dick Test"}
            ])
        ]

        for title, cat, freq, dur, chk in pm_plans:
            plan = db.query(PMPlan).filter_by(title=title).first()
            if not plan:
                plan = PMPlan(
                    title=title,
                    category=cat,
                    frequency_days=freq,
                    estimated_duration_minutes=dur,
                    checklist_template=chk,
                    is_active=True
                )
                db.add(plan)
                db.flush()

                # Match equipment
                matching_eqs = [eq for eq in equipment_map.values() if eq.category == cat]
                for idx, eq in enumerate(matching_eqs[:3]):
                    due = date.today() + timedelta(days=(idx * 25) - 10)
                    st = "overdue" if due < date.today() else "scheduled"
                    sched = PMSchedule(
                        pm_plan_id=plan.id,
                        equipment_id=eq.id,
                        due_date=due,
                        status=st
                    )
                    db.add(sched)

        # 9.B Maintenance Contracts
        contracts_data = [
            ("CNT-THW-2026-01", "عقد الصيانة الشاملة لجهاز الرنين المغناطيسي Magnetom Avanto", "AGT-NATCO", "comprehensive", 185000.0, date(2026, 1, 1), date(2026, 12, 31), True),
            ("CNT-THW-2026-02", "عقد الصيانة الوقائية والضمان لأجهزة التخدير والتنفس Dräger", "AGT-YEMMED", "preventive_only", 95000.0, date(2026, 1, 1), date(2026, 12, 31), True),
            ("CNT-THW-2026-03", "عقد الصيانة والخدمة الفنية لنظام قسطرة القلب Azurion 7", "AGT-TIHAMA", "comprehensive", 160000.0, date(2025, 7, 1), date(2026, 6, 30), True),
            ("CNT-THW-2026-04", "عقد توريد وضمان فلاتر وقطع غيار أجهزة غسيل الكلى Fresenius", "AGT-TIHAMA", "parts_only", 75000.0, date(2026, 2, 1), date(2027, 1, 31), True),
            ("CNT-THW-2026-05", "عقد الدعم الفني والمعايرة لجهاز الأشعة المقطعية Revolution CT", "AGT-ORIENT", "comprehensive", 140000.0, date(2026, 1, 1), date(2026, 12, 31), True)
        ]

        for c_num, c_title, a_code, c_type, c_cost, st_d, end_d, is_act in contracts_data:
            c = db.query(Contract).filter_by(contract_number=c_num).first()
            agent = vendors_map.get(a_code)
            if not c:
                c = Contract(
                    contract_number=c_num,
                    title=c_title,
                    vendor_id=agent.id if agent else None,
                    contract_type=c_type,
                    cost=c_cost,
                    start_date=st_d,
                    end_date=end_d,
                    is_active=is_act
                )
                db.add(c)

        # 9.C Pre-generated Executive Reports
        current_year = date.today().year
        current_month = date.today().month
        prev_month = current_month - 1 if current_month > 1 else 12
        prev_year = current_year if current_month > 1 else current_year - 1

        reports_data = [
            ("monthly_new_equipment", prev_year, prev_month, f"تقرير الأصول الطبية المستلمة والمعمدة — هيئة مستشفى الثورة ({prev_year}-{prev_month:02d})", "reports/archive/thw_new_assets.pdf", "reports/archive/thw_new_assets.xlsx"),
            ("monthly_pm_compliance", prev_year, prev_month, f"تقرير مؤشرات الامتثال للصيانة الوقائية الدورية ({prev_year}-{prev_month:02d})", "reports/archive/thw_pm_compliance.pdf", "reports/archive/thw_pm_compliance.xlsx"),
            ("monthly_closed_work_orders", prev_year, prev_month, f"تقرير تذاكر وأوامر الصيانة المنجزة وتكاليف المواد ({prev_year}-{prev_month:02d})", "reports/archive/thw_closed_wo.pdf", "reports/archive/thw_closed_wo.xlsx"),
            ("monthly_warranty_expiring", current_year, current_month, f"تقرير الأجهزة التي تقترب فترة ضمانها من الانتهاء ({current_year}-{current_month:02d})", "reports/archive/thw_warranty.pdf", "reports/archive/thw_warranty.xlsx")
        ]

        for r_type, p_y, p_m, r_tit, p_pdf, p_xl in reports_data:
            rep = db.query(GeneratedReport).filter_by(report_type=r_type, period_year=p_y, period_month=p_m).first()
            if not rep:
                rep = GeneratedReport(
                    report_type=r_type,
                    period_year=p_y,
                    period_month=p_m,
                    title=r_tit,
                    file_path_pdf=p_pdf,
                    file_path_excel=p_xl,
                    status="success",
                    generated_at=datetime.now() - timedelta(days=5)
                )
                db.add(rep)

        db.commit()
        print("==================================================================")
        print(" [MEMMS Seeder] تم بنجاح إنشاء وتغذية قاعدة بيانات مستشفى الثورة!")
        print(f" المستشفى: {hosp.name_ar}")
        print(f" الأقسام والمراكز: {len(departments_map)} مراكز تخصصية")
        print(f" الشركات والموردون: {len(vendors_map)} (مصنعين أجانب ووكلاء في صنعاء)")
        print(f" مهندسو الوكلاء المعتمدين: {len(engineers_map)} مهندس دعم بصنعاء")
        print(f" الكادر الهندسي بالمستشفى: {len(techs_map)} مهندسين وفنيين معتمدين")
        print(f" الأجهزة الطبية المغذية: {len(equipment_map)} جهازاً بكامل الملحقات ومحاضر التعميد")
        print(f" قطع الغيار بالمستودع: {len(parts_map)} صنف استراتيجي")
        print("==================================================================")


if __name__ == "__main__":
    seed_sana_medical_data()

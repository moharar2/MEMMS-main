"""
translations.py
---------------
A tiny, beginner-friendly translation system.

Why not Qt's .ts/.qm?
- Compiling translations needs the `lupdate` / `lrelease` toolchain.
- For a college project this is overkill and confusing.

So we keep every translatable string in a Python dictionary, keyed by a
stable identifier. Each entry has both an Arabic and an English value.
"""

from __future__ import annotations

from typing import Dict, List

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QApplication


# Supported language codes.
LANG_AR = "ar"
LANG_EN = "en"
SUPPORTED_LANGS: List[str] = [LANG_AR, LANG_EN]


# ---------------------------------------------------------------------------
# Translation table
# ---------------------------------------------------------------------------
# Group keys by section so a beginner can find what they need.
# Format: "section.semantic_key": {"ar": "...", "en": "..."}
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # --- App-wide ---------------------------------------------------------
    "app.title":             {"ar": "MEMMS — نظام إدارة صيانة الأجهزة الطبية",
                              "en": "MEMMS — Medical Equipment Maintenance Management"},
    "app.language":          {"ar": "اللغة",              "en": "Language"},
    "app.switch_to_english": {"ar": "English",             "en": "English"},
    "app.switch_to_arabic":  {"ar": "العربية",             "en": "العربية"},
    "app.refresh":           {"ar": "تحديث",              "en": "Refresh"},
    "app.loading":           {"ar": "جاري التحميل...",     "en": "Loading..."},
    "app.error":             {"ar": "خطأ",                 "en": "Error"},
    "app.ok":                {"ar": "موافق",               "en": "OK"},

    # --- Sidebar navigation ----------------------------------------------
    "nav.dashboard":             {"ar": "لوحة التحكم",          "en": "Dashboard"},
    "nav.equipment":             {"ar": "الأجهزة الطبية",       "en": "Medical Equipment"},
    "nav.work_orders":           {"ar": "أوامر الصيانة",        "en": "Work Orders"},
    "nav.preventive":            {"ar": "الصيانة الوقائية",     "en": "Preventive Maintenance"},
    "nav.spare_parts":           {"ar": "قطع الغيار",           "en": "Spare Parts"},
    "nav.staff":                 {"ar": "العاملون",             "en": "Staff"},
    "nav.reports":               {"ar": "التقارير والإحصائيات", "en": "Reports & Statistics"},
    "nav.settings":              {"ar": "الإعدادات",            "en": "Settings"},

    # --- Dashboard -------------------------------------------------------
    "dashboard.title":           {"ar": "لوحة التحكم",          "en": "Dashboard"},
    "dashboard.subtitle":        {"ar": "نظرة عامة على النظام", "en": "System overview"},
    "dashboard.card.equipment":  {"ar": "إجمالي الأجهزة",       "en": "Total Equipment"},
    "dashboard.card.work_orders":{"ar": "أوامر الصيانة المفتوحة","en": "Open Work Orders"},
    "dashboard.card.staff":      {"ar": "العاملون المسجلون",    "en": "Registered Staff"},
    "dashboard.empty":           {"ar": "لا توجد بيانات بعد.",  "en": "No data yet."},

    # --- Placeholder pages ----------------------------------------------
    "placeholder.title.equipment":      {"ar": "الأجهزة الطبية",       "en": "Medical Equipment"},
    "placeholder.title.work_orders":    {"ar": "أوامر الصيانة",        "en": "Work Orders"},
    "placeholder.title.preventive":     {"ar": "الصيانة الوقائية",     "en": "Preventive Maintenance"},
    "placeholder.title.spare_parts":    {"ar": "قطع الغيار",           "en": "Spare Parts"},
    "placeholder.title.staff":          {"ar": "العاملون",             "en": "Staff"},
    "placeholder.title.reports":        {"ar": "التقارير والإحصائيات", "en": "Reports & Statistics"},
    "placeholder.title.settings":       {"ar": "الإعدادات",            "en": "Settings"},

    "placeholder.body":   {
        "ar": "هذه الصفحة ستنفذ في المراحل القادمة من المشروع.",
        "en": "This page will be implemented in the upcoming project phases.",
    },
    "placeholder.phase":  {"ar": "المرحلة القادمة", "en": "Coming in a future phase"},

    # --- Equipment registry (Phase 2) ------------------------------------
    "equipment.heading": {"ar":"سجل الأجهزة الطبية", "en":"Medical Equipment Registry"},
    "equipment.search": {"ar":"ابحث بالرمز أو الاسم أو الموديل أو الرقم التسلسلي...", "en":"Search code, name, model, or serial..."},
    "equipment.add": {"ar":"+ إضافة جهاز", "en":"+ Add Equipment"},
    "equipment.edit": {"ar":"تعديل", "en":"Edit"}, "equipment.delete": {"ar":"حذف", "en":"Delete"},
    "equipment.add_title": {"ar":"إضافة جهاز طبي", "en":"Add Medical Equipment"},
    "equipment.edit_title": {"ar":"تعديل بيانات الجهاز", "en":"Edit Equipment"},
    "equipment.required": {"ar":"الرمز واسم الجهاز بالعربية والإنجليزية حقول مطلوبة.", "en":"Asset code and Arabic/English names are required."},
    "equipment.duplicate": {"ar":"رمز الجهاز مستخدم بالفعل. أدخل رمزًا فريدًا.", "en":"That asset code already exists. Use a unique code."},
    "equipment.select": {"ar":"حدد جهازًا من الجدول أولًا.", "en":"Select an equipment row first."},
    "equipment.confirm_delete": {"ar":"هل تريد حذف هذا الجهاز؟", "en":"Delete this equipment record?"},
    "equipment.delete_blocked": {"ar":"تعذر الحذف؛ قد يكون للجهاز أوامر صيانة أو سجلات مرتبطة.", "en":"Cannot delete: related maintenance records may exist."},
    "equipment.field.code":{"ar":"الرمز الداخلي *","en":"Asset code *"}, "equipment.field.name_ar":{"ar":"الاسم بالعربية *","en":"Arabic name *"},
    "equipment.field.name_en":{"ar":"الاسم بالإنجليزية *","en":"English name *"}, "equipment.field.model":{"ar":"الموديل","en":"Model"},
    "equipment.field.manufacturer":{"ar":"الشركة المصنعة","en":"Manufacturer"}, "equipment.field.serial":{"ar":"الرقم التسلسلي","en":"Serial number"},
    "equipment.field.type":{"ar":"نوع الجهاز","en":"Equipment type"}, "equipment.field.status":{"ar":"الحالة","en":"Status"}, "equipment.field.notes":{"ar":"ملاحظات","en":"Notes"},
    "equipment.col.code":{"ar":"الرمز","en":"Asset Code"}, "equipment.col.name":{"ar":"اسم الجهاز","en":"Equipment"},
    "equipment.col.model":{"ar":"الموديل","en":"Model"}, "equipment.col.manufacturer":{"ar":"الشركة المصنعة","en":"Manufacturer"},
    "equipment.col.serial":{"ar":"الرقم التسلسلي","en":"Serial"}, "equipment.col.department":{"ar":"القسم","en":"Department"}, "equipment.col.status":{"ar":"الحالة","en":"Status"},
    "equipment.status.operational":{"ar":"يعمل","en":"Operational"}, "equipment.status.maintenance":{"ar":"قيد الصيانة","en":"Under maintenance"},
    "equipment.status.out_of_service":{"ar":"خارج الخدمة","en":"Out of service"}, "equipment.status.retired":{"ar":"مستبعد","en":"Retired"},

    # --- Staff management (Phase 3) --------------------------------------
    "staff.heading":             {"ar": "إدارة الكادر الفني والموظفين",         "en": "Staff & Technicians Management"},
    "staff.subtitle":            {"ar": "سجل المهندسين والفنيين ومسؤولي الصيانة", "en": "Technicians, biomedical engineers, and staff registry"},
    "staff.search":              {"ar": "بحث بالاسم، الرقم الوظيفي، التخصص، أو الهاتف...", "en": "Search name, ID, specialty, or phone..."},
    "staff.add":                 {"ar": "+ إضافة موظف / فني",                 "en": "+ Add Staff Member"},
    "staff.edit":                {"ar": "تعديل",                               "en": "Edit"},
    "staff.delete":              {"ar": "حذف",                                 "en": "Delete"},
    "staff.add_title":           {"ar": "إضافة موظف / فني جديد",              "en": "Add New Staff Member"},
    "staff.edit_title":          {"ar": "تعديل بيانات الموظف",                 "en": "Edit Staff Member"},
    "staff.required":            {"ar": "الرقم الوظيفي والاسم والمسمى الوظيفي حقول مطلوبة.", "en": "Employee ID, Full Name, and Job Title are required."},
    "staff.duplicate":           {"ar": "الرقم الوظيفي مستخدم مسبقًا لموظف آخر. أدخل رقمًا فريدًا.", "en": "Employee ID already exists. Please provide a unique ID."},
    "staff.invalid_email":       {"ar": "صيغة البريد الإلكتروني غير صحيحة.",   "en": "Invalid email address format."},
    "staff.select":              {"ar": "يرجى تحديد موظف من الجدول أولاً.",     "en": "Please select a staff member from the table first."},
    "staff.confirm_delete":      {"ar": "هل أنت متأكد من حذف هذا الموظف؟",     "en": "Are you sure you want to delete this staff member?"},
    "staff.delete_blocked":      {"ar": "تعذر حذف الموظف لوجود سجلات مرتبطة به.", "en": "Cannot delete staff member: associated records exist."},
    "staff.filter.all_depts":    {"ar": "جميع الأقسام",                       "en": "All Departments"},
    "staff.filter.all_roles":    {"ar": "جميع المسميات",                      "en": "All Job Titles"},
    "staff.filter.all_statuses": {"ar": "جميع الحالات",                       "en": "All Statuses"},
    "staff.filter.reset":        {"ar": "إعادة ضبط",                           "en": "Reset Filters"},
    "staff.stats.total":         {"ar": "إجمالي الكادر",                       "en": "Total Staff"},
    "staff.stats.active":        {"ar": "الكادر النشط",                        "en": "Active Staff"},
    "staff.stats.technicians":   {"ar": "المهندسون والفنيون",                  "en": "Biomedical / Techs"},
    "staff.col.staff_id":        {"ar": "الرقم الوظيفي",                       "en": "Staff ID"},
    "staff.col.name":            {"ar": "الاسم الكامل",                        "en": "Full Name"},
    "staff.col.job_title":       {"ar": "المسمى الوظيفي",                      "en": "Job Title"},
    "staff.col.specialty":       {"ar": "التخصص",                             "en": "Specialty"},
    "staff.col.department":      {"ar": "القسم",                              "en": "Department"},
    "staff.col.phone":           {"ar": "رقم الهاتف",                         "en": "Phone"},
    "staff.col.email":           {"ar": "البريد الإلكتروني",                   "en": "Email"},
    "staff.col.hire_date":       {"ar": "تاريخ التعيين",                       "en": "Hire Date"},
    "staff.col.status":          {"ar": "الحالة",                             "en": "Status"},
    "staff.field.staff_id":      {"ar": "الرقم الوظيفي *",                     "en": "Staff ID *"},
    "staff.field.name":          {"ar": "الاسم الكامل *",                      "en": "Full Name *"},
    "staff.field.job_title":     {"ar": "المسمى الوظيفي *",                    "en": "Job Title *"},
    "staff.field.specialty":     {"ar": "التخصص الدقيق",                      "en": "Specialty"},
    "staff.field.department":    {"ar": "القسم التابع له",                     "en": "Department"},
    "staff.field.phone":         {"ar": "رقم الهاتف",                         "en": "Phone Number"},
    "staff.field.email":         {"ar": "البريد الإلكتروني",                   "en": "Email Address"},
    "staff.field.hire_date":     {"ar": "تاريخ التعيين",                       "en": "Hire Date"},
    "staff.field.status":        {"ar": "الحالة *",                            "en": "Status *"},
    "staff.field.notes":         {"ar": "ملاحظات إضافية",                      "en": "Additional Notes"},
    "staff.status.active":       {"ar": "نشط",                                "en": "Active"},
    "staff.status.inactive":     {"ar": "غير نشط",                            "en": "Inactive"},
    "common.save":               {"ar": "حفظ",                                "en": "Save"},
    "common.cancel":             {"ar": "إلغاء",                              "en": "Cancel"},
    "common.none":               {"ar": "غير محدد",                            "en": "None"},
}


def tr(key: str, lang: str) -> str:
    """
    Look up a translation by key. Falls back to English, then to the key
    itself so missing strings are obvious instead of crashing.
    """
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    return entry.get(lang) or entry.get(LANG_EN) or key


def is_rtl(lang: str) -> bool:
    """Arabic is RTL. Everything else (for now) is LTR."""
    return lang == LANG_AR


# ---------------------------------------------------------------------------
# Translator — broadcasts language changes to subscribed widgets.
# ---------------------------------------------------------------------------
class Translator(QObject):
    """
    Holds the current language. Widgets that show translatable text connect
    to `language_changed` and call `tr()` again to refresh themselves.
    """
    language_changed = Signal(str)  # emits the new language code

    def __init__(self, initial_lang: str = LANG_AR) -> None:
        super().__init__()
        self._lang = initial_lang if initial_lang in SUPPORTED_LANGS else LANG_EN

    @property
    def lang(self) -> str:
        return self._lang

    def set_language(self, lang: str) -> None:
        if lang not in SUPPORTED_LANGS or lang == self._lang:
            return
        self._lang = lang
        # Flip layout direction app-wide.
        app = QApplication.instance()
        if app is not None:
            app.setLayoutDirection(Qt.RightToLeft if is_rtl(lang) else Qt.LeftToRight)
        self.language_changed.emit(lang)

    def t(self, key: str) -> str:
        return tr(key, self._lang)


# A small helper mixin for any widget that wants to auto-retranslate on
# language change.
class TranslatableWidget:
    """
    Mix this into a QWidget subclass. In the subclass, implement
    `retranslate_ui(lang: str)` to refresh all visible strings.

    The base MainWindow wires every TranslatableWidget up to the Translator.
    """

    def retranslate_ui(self, lang: str) -> None:  # pragma: no cover - overridden
        raise NotImplementedError

    @staticmethod
    def collect_translatable(root) -> List["TranslatableWidget"]:
        """Return every TranslatableWidget found inside `root` (including `root` itself)."""
        result: List[TranslatableWidget] = []
        if isinstance(root, TranslatableWidget):
            result.append(root)
        if hasattr(root, "findChildren"):
            for child in root.findChildren(object):
                if isinstance(child, TranslatableWidget) and child is not root:
                    result.append(child)
        return result

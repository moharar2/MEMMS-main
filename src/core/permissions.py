"""
Role-Based Access Control (RBAC) definitions and permission checking logic for MEMMS.
Pure Arabic RTL enterprise security framework.
"""
from typing import Set, Dict, List, Optional
from src.core.exceptions import PermissionDeniedError

# Permission Constants
PERM_EQUIPMENT_VIEW = "equipment:view"
PERM_EQUIPMENT_CREATE = "equipment:create"
PERM_EQUIPMENT_EDIT = "equipment:edit"
PERM_EQUIPMENT_DELETE = "equipment:delete"

PERM_WORK_ORDER_VIEW = "work_order:view"
PERM_WORK_ORDER_CREATE = "work_order:create"
PERM_WORK_ORDER_EDIT = "work_order:edit"
PERM_WORK_ORDER_CLOSE = "work_order:close"
PERM_WORK_ORDER_DELETE = "work_order:delete"

PERM_PM_VIEW = "pm:view"
PERM_PM_CREATE = "pm:create"
PERM_PM_EDIT = "pm:edit"
PERM_PM_EXECUTE = "pm:execute"
PERM_PM_DELETE = "pm:delete"

PERM_INVENTORY_VIEW = "inventory:view"
PERM_INVENTORY_MANAGE = "inventory:manage"
PERM_INVENTORY_CONSUME = "inventory:consume"

PERM_CONTRACTS_VIEW = "contracts:view"
PERM_CONTRACTS_MANAGE = "contracts:manage"

PERM_DEPARTMENTS_VIEW = "departments:view"
PERM_DEPARTMENTS_MANAGE = "departments:manage"

PERM_VENDORS_VIEW = "vendors:view"
PERM_VENDORS_MANAGE = "vendors:manage"

PERM_TECHNICIANS_VIEW = "technicians:view"
PERM_TECHNICIANS_MANAGE = "technicians:manage"
PERM_TECHNICIANS_SALARY_VIEW = "technicians:salary_view"
PERM_TECHNICIANS_SALARY_MANAGE = "technicians:salary_manage"

PERM_ATTACHMENTS_MANAGE = "attachments:manage"
PERM_ACCESSORIES_MANAGE = "accessories:manage"
PERM_RECEIVING_MANAGE = "receiving:manage"

PERM_REPORTS_VIEW = "reports:view"
PERM_REPORTS_EXPORT = "reports:export"
PERM_REPORTS_AUTO_MANAGE = "reports:auto_manage"

PERM_AUDIT_VIEW = "audit:view"
PERM_BACKUP_MANAGE = "backup:manage"
PERM_USERS_MANAGE = "users:manage"

ALL_PERMISSIONS: List[str] = [
    PERM_EQUIPMENT_VIEW, PERM_EQUIPMENT_CREATE, PERM_EQUIPMENT_EDIT, PERM_EQUIPMENT_DELETE,
    PERM_WORK_ORDER_VIEW, PERM_WORK_ORDER_CREATE, PERM_WORK_ORDER_EDIT, PERM_WORK_ORDER_CLOSE, PERM_WORK_ORDER_DELETE,
    PERM_PM_VIEW, PERM_PM_CREATE, PERM_PM_EDIT, PERM_PM_EXECUTE, PERM_PM_DELETE,
    PERM_INVENTORY_VIEW, PERM_INVENTORY_MANAGE, PERM_INVENTORY_CONSUME,
    PERM_CONTRACTS_VIEW, PERM_CONTRACTS_MANAGE,
    PERM_DEPARTMENTS_VIEW, PERM_DEPARTMENTS_MANAGE,
    PERM_VENDORS_VIEW, PERM_VENDORS_MANAGE,
    PERM_TECHNICIANS_VIEW, PERM_TECHNICIANS_MANAGE,
    PERM_TECHNICIANS_SALARY_VIEW, PERM_TECHNICIANS_SALARY_MANAGE,
    PERM_ATTACHMENTS_MANAGE, PERM_ACCESSORIES_MANAGE, PERM_RECEIVING_MANAGE,
    PERM_REPORTS_VIEW, PERM_REPORTS_EXPORT, PERM_REPORTS_AUTO_MANAGE,
    PERM_AUDIT_VIEW, PERM_BACKUP_MANAGE, PERM_USERS_MANAGE
]

# Predefined System Roles & Permission Sets
DEFAULT_ROLES: Dict[str, Dict] = {
    "admin": {
        "display_name_ar": "مدير النظام",
        "display_name_en": "System Administrator",
        "permissions": ALL_PERMISSIONS,
        "description": "صلاحيات مطلقة لإدارة كامل وظائف وإعدادات النظام والمستخدمين والنسخ الاحتياطي"
    },
    "biomedical_engineer": {
        "display_name_ar": "مهندس الأجهزة الطبية",
        "display_name_en": "Biomedical Engineer",
        "permissions": [
            PERM_EQUIPMENT_VIEW, PERM_EQUIPMENT_CREATE, PERM_EQUIPMENT_EDIT,
            PERM_WORK_ORDER_VIEW, PERM_WORK_ORDER_CREATE, PERM_WORK_ORDER_EDIT, PERM_WORK_ORDER_CLOSE,
            PERM_PM_VIEW, PERM_PM_CREATE, PERM_PM_EDIT, PERM_PM_EXECUTE,
            PERM_INVENTORY_VIEW, PERM_INVENTORY_CONSUME,
            PERM_CONTRACTS_VIEW,
            PERM_DEPARTMENTS_VIEW,
            PERM_VENDORS_VIEW,
            PERM_TECHNICIANS_VIEW,
            PERM_ATTACHMENTS_MANAGE,
            PERM_ACCESSORIES_MANAGE,
            PERM_RECEIVING_MANAGE,
            PERM_REPORTS_VIEW, PERM_REPORTS_EXPORT, PERM_REPORTS_AUTO_MANAGE
        ],
        "description": "إدارة دورة حياة الأجهزة الطبية، أوامر الصيانة التصحيحية، خطط الفحص الوقائي، والتقارير"
    },
    "technician": {
        "display_name_ar": "فني الصيانة",
        "display_name_en": "Maintenance Technician",
        "permissions": [
            PERM_EQUIPMENT_VIEW,
            PERM_WORK_ORDER_VIEW, PERM_WORK_ORDER_EDIT,
            PERM_PM_VIEW, PERM_PM_EXECUTE,
            PERM_INVENTORY_VIEW, PERM_INVENTORY_CONSUME,
            PERM_DEPARTMENTS_VIEW,
            PERM_TECHNICIANS_VIEW
        ],
        "description": "تنفيذ أعمال الصيانة المسندة وتسجيل القياسات الفنية وقطع الغيار المستهلكة"
    },
    "inventory_manager": {
        "display_name_ar": "مسؤول المخزون",
        "display_name_en": "Inventory Manager",
        "permissions": [
            PERM_EQUIPMENT_VIEW,
            PERM_INVENTORY_VIEW, PERM_INVENTORY_MANAGE, PERM_INVENTORY_CONSUME,
            PERM_VENDORS_VIEW,
            PERM_REPORTS_VIEW, PERM_REPORTS_EXPORT
        ],
        "description": "إدارة مخزون قطع الغيار، حركات الإدخال والصرف، والحد الأدنى للطلب"
    },
    "viewer": {
        "display_name_ar": "مستخدم للقراءة فقط",
        "display_name_en": "Viewer (Read Only)",
        "permissions": [
            PERM_EQUIPMENT_VIEW,
            PERM_WORK_ORDER_VIEW,
            PERM_PM_VIEW,
            PERM_INVENTORY_VIEW,
            PERM_CONTRACTS_VIEW,
            PERM_DEPARTMENTS_VIEW,
            PERM_VENDORS_VIEW,
            PERM_TECHNICIANS_VIEW,
            PERM_REPORTS_VIEW
        ],
        "description": "اطلاع واستعلام فقط على كافة السجلات والتقارير دون صلاحيات الإضافة أو التعديل أو الحذف"
    }
}

# Backward compatibility alias for engineer / maintenance_manager
DEFAULT_ROLES["engineer"] = DEFAULT_ROLES["biomedical_engineer"]
DEFAULT_ROLES["maintenance_manager"] = DEFAULT_ROLES["biomedical_engineer"]



def user_has_permission(user_permissions: List[str], required_permission: str) -> bool:
    """
    Checks if a list of user permissions includes the required permission.
    Admins with '*' or ALL_PERMISSIONS have full access.
    """
    if not user_permissions:
        return False
    if "*" in user_permissions:
        return True
    return required_permission in user_permissions


def can_user(user, required_permission: str) -> bool:
    """
    Returns True if user is active and has the required permission, False otherwise.
    """
    if not user or not getattr(user, "is_active", False):
        return False
    role = getattr(user, "role", None)
    if not role:
        return False
    permissions = role.permissions if hasattr(role, "permissions") else []
    return user_has_permission(permissions, required_permission)


def is_admin(user) -> bool:
    """
    Returns True if the user has the admin role.
    """
    if not user or not getattr(user, "is_active", False):
        return False
    role = getattr(user, "role", None)
    if not role:
        return False
    return role.name == "admin" or "*" in (role.permissions or [])


def check_permission(user, required_permission: str) -> None:
    """
    Raises PermissionDeniedError with Arabic message if the user does not possess required_permission.
    """
    if not user or not getattr(user, "is_active", False):
        raise PermissionDeniedError("المستخدم غير مسجل أو الحساب معطل. يرجى تسجيل الدخول بحساب نشط.")
    
    role = getattr(user, "role", None)
    if not role:
        raise PermissionDeniedError("المستخدم لا يملك دوراً وظيفياً مسنداً في النظام.")
    
    permissions = role.permissions if hasattr(role, "permissions") else []
    if not user_has_permission(permissions, required_permission):
        raise PermissionDeniedError(f"ليس لديك الصلاحية المطلوبة لتنفيذ هذا الإجراء ({required_permission}).")

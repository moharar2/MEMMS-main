"""
Attachment & Document Management Service for Equipment Manuals (Operation/Service), Certificates, and Reports.
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
import config
from src.models.attachment import Attachment
from src.core.exceptions import ValidationError, NotFoundError
from src.core.permissions import check_permission, PERM_ATTACHMENTS_MANAGE
from src.services.audit_service import audit_service


class AttachmentService:
    def __init__(self):
        self.base_dir = config.ATTACHMENTS_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def upload_attachment(
        self,
        db: Session,
        user,
        entity_type: str,
        entity_id: int,
        source_file_path: str,
        attachment_type: str = "other",
        description: Optional[str] = None
    ) -> Attachment:
        check_permission(user, PERM_ATTACHMENTS_MANAGE)

        source_path = Path(source_file_path)
        if not source_path.exists() or not source_path.is_file():
            raise ValidationError(f"الملف المحدد غير موجود: {source_file_path}")

        file_ext = source_path.suffix.lower()
        if file_ext not in config.ALLOWED_ATTACHMENT_EXTENSIONS:
            raise ValidationError(f"نوع الملف غير مسموح ({file_ext}). الأنواع المسموحة: {', '.join(config.ALLOWED_ATTACHMENT_EXTENSIONS)}")

        file_size = source_path.stat().st_size
        if file_size > config.MAX_UPLOAD_SIZE_BYTES:
            max_mb = config.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
            raise ValidationError(f"حجم الملف يتجاوز الحد الأقصى المسموح ({max_mb:.0f} ميجابايت).")

        # Destination directory organized by entity_type/entity_id
        dest_dir = self.base_dir / entity_type / str(entity_id)
        dest_dir.mkdir(parents=True, exist_ok=True)

        unique_filename = f"{uuid.uuid4().hex[:10]}_{source_path.name}"
        dest_file_path = dest_dir / unique_filename

        # Safely copy file
        shutil.copy2(source_path, dest_file_path)

        mime_type = "application/pdf" if file_ext == ".pdf" else "application/octet-stream"

        attachment = Attachment(
            entity_type=entity_type,
            entity_id=entity_id,
            file_name=source_path.name,
            stored_file_path=str(dest_file_path),
            file_size=file_size,
            mime_type=mime_type,
            attachment_type=attachment_type,
            description=description,
            uploaded_by_user_id=user.id if user else None
        )
        db.add(attachment)
        db.commit()
        db.refresh(attachment)

        audit_service.log_action(
            db=db,
            user=user,
            action="upload_attachment",
            entity_type=entity_type,
            entity_id=entity_id,
            details=f"رفع مرفق: {source_path.name} (النوع: {attachment_type})"
        )

        return attachment

    def get_attachments(
        self,
        db: Session,
        entity_type: str,
        entity_id: int,
        attachment_type: Optional[str] = None
    ) -> List[Attachment]:
        query = db.query(Attachment).filter(
            Attachment.entity_type == entity_type,
            Attachment.entity_id == entity_id
        )
        if attachment_type and attachment_type != "all":
            query = query.filter(Attachment.attachment_type == attachment_type)
        return query.order_by(Attachment.id.desc()).all()

    def get_attachment_by_id(self, db: Session, attachment_id: int) -> Attachment:
        att = db.query(Attachment).filter_by(id=attachment_id).first()
        if not att:
            raise NotFoundError("Attachment", attachment_id)
        return att

    def delete_attachment(self, db: Session, user, attachment_id: int) -> bool:
        check_permission(user, PERM_ATTACHMENTS_MANAGE)
        att = self.get_attachment_by_id(db, attachment_id)

        file_path = Path(att.stored_file_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass  # Ignore file deletion lock error on local system

        file_name = att.file_name
        e_type = att.entity_type
        e_id = att.entity_id

        db.delete(att)
        db.commit()

        audit_service.log_action(
            db=db,
            user=user,
            action="delete_attachment",
            entity_type=e_type,
            entity_id=e_id,
            details=f"حذف مرفق: {file_name}"
        )
        return True

    def export_attachment_copy(self, attachment: Attachment, target_path: str):
        source = Path(attachment.stored_file_path)
        if not source.exists():
            raise ValidationError("الملف المخزن غير موجود على القرص أو تم نقله.")
        shutil.copy2(source, target_path)

    def save_attachment(
        self,
        db: Session,
        user,
        equipment_id: int,
        file_path: str,
        attachment_type: str = "other",
        notes: Optional[str] = None
    ) -> Attachment:
        return self.upload_attachment(
            db=db,
            user=user,
            entity_type="equipment",
            entity_id=equipment_id,
            source_file_path=file_path,
            attachment_type=attachment_type,
            description=notes
        )

    def get_equipment_manuals(self, db: Session, equipment_id: int) -> dict:
        op_manuals = self.get_attachments(db, "equipment", equipment_id, attachment_type="operation_manual")
        svc_manuals = self.get_attachments(db, "equipment", equipment_id, attachment_type="service_manual")
        other_files = self.get_attachments(db, "equipment", equipment_id, attachment_type="other")
        return {
            "operation_manuals": op_manuals,
            "service_manuals": svc_manuals,
            "other_files": other_files,
            "all": op_manuals + svc_manuals + other_files
        }


attachment_service = AttachmentService()

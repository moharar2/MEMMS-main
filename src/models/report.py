"""
Generated / Scheduled Reports entity model for automated monthly reports and historical archiving.
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel, utc_now


class GeneratedReport(BaseModel):
    __tablename__ = "generated_reports"

    report_type = Column(String(100), nullable=False, index=True)
    # Types: 'monthly_new_equipment', 'monthly_closed_work_orders', 'monthly_pm_compliance',
    #        'monthly_down_equipment', 'monthly_warranty_expiring', 'monthly_department_summary',
    #        'monthly_vendor_performance'
    period_year = Column(Integer, nullable=False, index=True)
    period_month = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    file_path_pdf = Column(String(500), nullable=True)
    file_path_excel = Column(String(500), nullable=True)
    status = Column(String(30), default="success", nullable=False)  # 'success', 'failed', 'generating'
    error_message = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=utc_now, nullable=False)
    generated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    generated_by = relationship("User")

    @property
    def title_ar(self) -> str:
        return self.title or self.report_type

    @property
    def pdf_path(self) -> str:
        return self.file_path_pdf or ""

    @property
    def excel_path(self) -> str:
        return self.file_path_excel or ""

    @property
    def record_count(self) -> int:
        return 0

    def __repr__(self):
        return f"<GeneratedReport(type='{self.report_type}', period='{self.period_year}-{self.period_month:02d}', status='{self.status}')>"

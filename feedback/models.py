from datetime import datetime, timezone
from extensions import db

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)  # Category could be "Appendix" or "Abstract"
    description = db.Column(db.String(1000), nullable=False)
    resolved_status = db.Column(db.String(5), nullable=False)  # 'Yes' or 'No'
    priority_level = db.Column(db.String(50), nullable=True)
    related_section = db.Column(db.String(50), nullable=True)
    created_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    assigned_to = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "description": self.description,
            "resolved_status": self.resolved_status,
            "priority_level": self.priority_level,
            "related_section": self.related_section,
            "assigned_to": self.assigned_to,
            "created_date": self.created_date.strftime("%d/%m/%Y"),
            "last_updated_date": self.last_updated_date.strftime("%d/%m/%Y"),
        }

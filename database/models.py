"""
SQLAlchemy ORM models for the Invoice Rule Engine.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Rule(Base):
    """A business rule that maps invoice conditions to a routing action."""

    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=100, nullable=False)
    action = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(String(100), default="system", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    conditions = relationship(
        "RuleCondition",
        back_populates="rule",
        cascade="all, delete-orphan",
        order_by="RuleCondition.condition_order",
    )

    def __repr__(self) -> str:
        return f"<Rule id={self.id} name='{self.name}' action='{self.action}'>"


class RuleCondition(Base):
    """A single condition within a Rule (AND logic between conditions)."""

    __tablename__ = "rule_conditions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey("rules.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    operator = Column(String(50), nullable=False)
    value = Column(String(500), nullable=False)
    condition_order = Column(Integer, default=0, nullable=False)

    rule = relationship("Rule", back_populates="conditions")

    def __repr__(self) -> str:
        return (
            f"<RuleCondition id={self.id} "
            f"field='{self.field_name}' {self.operator} '{self.value}'>"
        )


class AuditLog(Base):
    """Immutable record of every rule evaluation."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(String(200), nullable=True)
    invoice_data = Column(Text, nullable=True)  # JSON snapshot
    matched_rule = Column(String(200), nullable=True)
    decision = Column(String(50), nullable=False)
    execution_time_ms = Column(Float, default=0.0, nullable=False)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} "
            f"invoice='{self.invoice_id}' decision='{self.decision}'>"
        )

"""
Billing Models — Sprint 12
============================
Complete SaaS monetization infrastructure for EAIMOS.
Provides plans, subscriptions, invoices, payments, credit ledger,
usage metering, and promo codes.

Tables:
- billing_plans           : Subscription plan definitions
- plan_features           : Plan → Feature capability matrix
- subscriptions           : Active org subscriptions
- subscription_items      : Line items per subscription
- invoices                : Invoice records
- invoice_line_items      : Invoice line items
- payments                : Payment transactions
- payment_methods         : Stored payment methods (tokenized)
- usage_records           : Usage metering events
- credits                 : Credit balance per org
- credit_transactions     : IMMUTABLE ledger (append-only)
- billing_alerts          : Threshold alert configurations
- promo_codes             : Discount codes
- promo_code_redemptions  : Redemption tracking

Design Rules:
- credit_transactions is APPEND-ONLY — no UPDATE, no DELETE
- Balance = SUM of all credit_transactions for an org
- Stripe IDs stored for webhook reconciliation
- All monetary values in NUMERIC(12,4) to avoid float imprecision
- currency defaults to USD (ISO 4217)
"""
import uuid
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index,
    Integer, Numeric, String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

if TYPE_CHECKING:
    from api.models.organization import Organization
    from api.models.user import User


class BillingPlan(Base):
    """
    Subscription plan definition.

    Pricing:
    - price_monthly: charged per month
    - price_annual:  charged per year (lower than 12 × monthly)
    - Stripe IDs link to Stripe Product/Price objects

    Plan tiers mirror organizations.plan_tier:
    free | starter | professional | enterprise
    """
    __tablename__ = "billing_plans"

    __table_args__ = (
        UniqueConstraint("slug", name="uq_billing_plans_slug"),
        CheckConstraint(
            "tier IN ('free','starter','professional','enterprise')",
            name="ck_billing_plans_tier",
        ),
        CheckConstraint(
            "billing_cycle IN ('monthly','annual','usage','lifetime')",
            name="ck_billing_plans_cycle",
        ),
        Index("idx_billing_plans_tier", "tier"),
        Index("idx_billing_plans_is_active", "is_active", postgresql_where="is_active = TRUE"),
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False,
        comment="URL-safe identifier e.g. professional-monthly",
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tier: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="free | starter | professional | enterprise",
    )
    billing_cycle: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="monthly | annual | usage | lifetime",
    )

    # ── Pricing ───────────────────────────────────────────────────────────────
    price_monthly: Mapped[float] = mapped_column(
        Numeric(12, 4), nullable=False, default=0.0,
        comment="Monthly price in USD",
    )
    price_annual: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 4), nullable=True,
        comment="Annual price in USD (NULL if not offered annually)",
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD", server_default="USD"
    )

    # ── Limits ────────────────────────────────────────────────────────────────
    max_members: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="NULL = unlimited"
    )
    max_ai_credits: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 4), nullable=True, comment="Monthly AI credit budget"
    )
    max_storage_gb: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="NULL = unlimited"
    )
    max_agents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_workflows: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_campaigns: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_contacts: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ── Stripe References ─────────────────────────────────────────────────────
    stripe_product_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Stripe Product ID"
    )
    stripe_price_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Stripe Price ID"
    )

    # ── Visibility ────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="TRUE"
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="TRUE",
        comment="FALSE = hidden from pricing page (internal/custom plans)",
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    plan_features: Mapped[List["PlanFeature"]] = relationship(
        "PlanFeature", back_populates="plan", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="plan"
    )


class PlanFeature(Base):
    """Plan → Feature capability matrix (what each plan can do)."""
    __tablename__ = "plan_features"

    __table_args__ = (
        UniqueConstraint("plan_id", "feature_key", name="uq_plan_feature_key"),
        Index("idx_plan_features_plan_id", "plan_id"),
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("billing_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    feature_key: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Feature identifier e.g. ai_agents, a_b_testing, sso",
    )
    is_included: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    limit_value: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Numeric limit (NULL = unlimited)"
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationship ──────────────────────────────────────────────────────────
    plan: Mapped[BillingPlan] = relationship("BillingPlan", back_populates="plan_features")


class Subscription(Base):
    """
    Active organization subscription.

    States: TRIAL → ACTIVE → PAST_DUE → CANCELLED | EXPIRED

    Business Rules:
    - Only one ACTIVE/TRIAL/PAST_DUE subscription per organization
    - cancel_at_period_end=TRUE: access until current_period_end, then CANCELLED
    - Stripe subscription_id used for webhook reconciliation
    """
    __tablename__ = "subscriptions"

    __table_args__ = (
        # One active sub per org
        Index(
            "uq_subscriptions_org_active",
            "organization_id",
            unique=True,
            postgresql_where="status IN ('TRIAL','ACTIVE','PAST_DUE')",
        ),
        CheckConstraint(
            "status IN ('TRIAL','ACTIVE','PAST_DUE','CANCELLED','EXPIRED','PAUSED')",
            name="ck_subscription_status",
        ),
        Index("idx_subscriptions_org_id", "organization_id"),
        Index("idx_subscriptions_plan_id", "plan_id"),
        Index("idx_subscriptions_status", "status"),
        Index("idx_subscriptions_period_end", "current_period_end"),
        Index("idx_subscriptions_trial_ends", "trial_ends_at"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("billing_plans.id"),
        nullable=False,
    )
    payment_method_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_methods.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Status ────────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="TRIAL", server_default="TRIAL"
    )
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # ── Cancellation ──────────────────────────────────────────────────────────
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Stripe ────────────────────────────────────────────────────────────────
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    billing_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    plan: Mapped[BillingPlan] = relationship("BillingPlan", back_populates="subscriptions")
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice", back_populates="subscription"
    )


class PaymentMethod(Base):
    """
    Stored payment method (tokenized — no raw card data stored ever).
    References Stripe PaymentMethod or similar tokenization provider.
    """
    __tablename__ = "payment_methods"

    __table_args__ = (
        Index("idx_payment_methods_org_id", "organization_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="card | bank_transfer | paypal | wire",
    )
    provider_token: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="Stripe PaymentMethod ID or equivalent token",
    )
    last_four: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    expiry_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expiry_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="TRUE"
    )
    billing_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    billing_country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)


class Invoice(Base):
    """
    Invoice record. Linked to a subscription billing period.

    States: DRAFT → OPEN → PAID | VOID | UNCOLLECTIBLE

    Databricks:
    - Bronze: bronze.invoices_raw
    - Silver: silver.fact_invoices
    - Gold:   gold.mrr_arr_summary
    """
    __tablename__ = "invoices"

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "invoice_number",
            name="uq_invoices_number_org",
        ),
        CheckConstraint(
            "status IN ('DRAFT','OPEN','PAID','VOID','UNCOLLECTIBLE')",
            name="ck_invoice_status",
        ),
        Index("idx_invoices_org_id", "organization_id"),
        Index("idx_invoices_subscription_id", "subscription_id"),
        Index("idx_invoices_status", "status"),
        Index("idx_invoices_due_date", "due_date"),
        Index("idx_invoices_created_at", "created_at"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Invoice Identity ──────────────────────────────────────────────────────
    invoice_number: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Human-readable sequential ID e.g. INV-2026-00001",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DRAFT", server_default="DRAFT"
    )

    # ── Billing Period ────────────────────────────────────────────────────────
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # ── Amounts (NUMERIC for exact precision) ─────────────────────────────────
    subtotal: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0.0)
    tax_amount: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0.0)
    discount_amount: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0.0)
    total: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0.0)
    amount_paid: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0.0)
    amount_due: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # ── Payment ───────────────────────────────────────────────────────────────
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Stripe ────────────────────────────────────────────────────────────────
    stripe_invoice_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)
    pdf_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription", back_populates="invoices"
    )
    line_items: Mapped[List["InvoiceLineItem"]] = relationship(
        "InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan"
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment", back_populates="invoice"
    )


class InvoiceLineItem(Base):
    """Line items within an invoice (plan, usage charges, one-time fees)."""
    __tablename__ = "invoice_line_items"

    __table_args__ = (
        Index("idx_invoice_line_items_invoice_id", "invoice_id"),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    item_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="subscription | usage | one_time | credit | discount",
    )
    quantity: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=1.0)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False, default=0.0)
    amount: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ── Relationship ──────────────────────────────────────────────────────────
    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="line_items")


class Payment(Base):
    """
    Payment transaction record.
    References Stripe PaymentIntent or charge.
    """
    __tablename__ = "payments"

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING','PROCESSING','SUCCEEDED','FAILED','REFUNDED','CANCELLED')",
            name="ck_payment_status",
        ),
        Index("idx_payments_org_id", "organization_id"),
        Index("idx_payments_invoice_id", "invoice_id"),
        Index("idx_payments_status", "status"),
        Index("idx_payments_created_at", "created_at"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    payment_method_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_methods.id", ondelete="SET NULL"),
        nullable=True,
    )

    amount: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", server_default="PENDING"
    )

    # ── Stripe ────────────────────────────────────────────────────────────────
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True
    )
    stripe_charge_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    failure_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    failure_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    refund_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    invoice: Mapped[Optional[Invoice]] = relationship("Invoice", back_populates="payments")


class Credit(Base):
    """
    Current credit balance record per organization.
    This is the cached balance — source of truth is credit_transactions SUM.
    """
    __tablename__ = "credits"

    __table_args__ = (
        UniqueConstraint("organization_id", name="uq_credits_org"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    balance: Mapped[float] = mapped_column(
        Numeric(12, 8), nullable=False, default=0.0,
        comment="Cached balance — always recomputable from credit_transactions",
    )
    lifetime_purchased: Mapped[float] = mapped_column(
        Numeric(12, 4), nullable=False, default=0.0
    )
    lifetime_used: Mapped[float] = mapped_column(
        Numeric(12, 4), nullable=False, default=0.0
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")


class CreditTransaction(Base):
    """
    IMMUTABLE credit ledger. Append-only. No UPDATE. No DELETE.

    Every credit movement (purchase, usage, refund, bonus, adjustment)
    is recorded as a separate transaction row.

    Running balance is always: SUM(amount) WHERE organization_id = ?
    balance_after is denormalized for efficient current-balance queries.

    Transaction types:
    - PURCHASE  : Credits bought by the organization
    - USAGE     : Credits consumed (AI request, embedding, etc.)
    - REFUND    : Credits returned from a failed charge
    - BONUS     : Platform-granted free credits
    - ADJUSTMENT: Manual admin adjustment
    - EXPIRY    : Expired credits removed

    Partitioned monthly by created_at.
    """
    __tablename__ = "credit_transactions"

    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('PURCHASE','USAGE','REFUND','BONUS','ADJUSTMENT','EXPIRY')",
            name="ck_credit_tx_type",
        ),
        Index("idx_credit_tx_org_created", "organization_id", "created_at"),
        Index("idx_credit_tx_reference", "reference_type", "reference_id"),
        Index("idx_credit_tx_type", "transaction_type"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[float] = mapped_column(
        Numeric(12, 8), nullable=False,
        comment="Positive = credit added; Negative = credit consumed",
    )
    balance_after: Mapped[float] = mapped_column(
        Numeric(12, 8), nullable=False,
        comment="Running balance after this transaction (denormalized)",
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Reference ─────────────────────────────────────────────────────────────
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="invoice | ai_request | payment | campaign",
    )
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # ── Actor ─────────────────────────────────────────────────────────────────
    performed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="NULL = system-automated",
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)


class UsageRecord(Base):
    """
    Fine-grained usage metering event for billing calculations.
    Powers usage-based billing and monthly usage reports.
    """
    __tablename__ = "usage_records"

    __table_args__ = (
        CheckConstraint(
            "unit IN ('token','request','seat','storage_gb','email','compute_minute')",
            name="ck_usage_record_unit",
        ),
        Index("idx_usage_records_org_created", "organization_id", "created_at"),
        Index("idx_usage_records_metric", "metric_key"),
        Index("idx_usage_records_subscription", "subscription_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    metric_key: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="ai_tokens | emails_sent | storage_gb | seats | api_calls",
    )
    quantity: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 8), nullable=True)
    total_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 8), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_module: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)


class BillingAlert(Base):
    """
    Threshold-based billing alert configuration.
    Fires notifications when usage exceeds defined thresholds.
    """
    __tablename__ = "billing_alerts"

    __table_args__ = (
        Index("idx_billing_alerts_org_id", "organization_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    metric_key: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Metric to monitor"
    )
    threshold_value: Mapped[float] = mapped_column(
        Numeric(12, 4), nullable=False, comment="Trigger threshold"
    )
    threshold_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="absolute",
        comment="absolute | percentage",
    )
    notification_channels: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, comment="[\"email\", \"slack\", \"in_app\"]"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cooldown_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60,
        comment="Minimum time between repeated alerts",
    )


class PromoCode(Base):
    """
    Discount/promo code definition.
    Applied at checkout to reduce invoice total.
    """
    __tablename__ = "promo_codes"

    __table_args__ = (
        UniqueConstraint("code", name="uq_promo_codes_code"),
        Index("idx_promo_codes_code", "code"),
        Index("idx_promo_codes_expires_at", "expires_at"),
    )

    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False,
        comment="The code users enter at checkout e.g. LAUNCH50",
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    discount_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="percentage | fixed_amount | free_credits",
    )
    discount_value: Mapped[float] = mapped_column(
        Numeric(12, 4), nullable=False,
        comment="50 for 50%, or 50.00 for $50 fixed",
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    max_redemptions: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="NULL = unlimited"
    )
    redemption_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    applicable_plans: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, comment="NULL = all plans"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    stripe_coupon_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    redemptions: Mapped[List["PromoCodeRedemption"]] = relationship(
        "PromoCodeRedemption", back_populates="promo_code", cascade="all, delete-orphan"
    )


class PromoCodeRedemption(Base):
    """Tracks when and by whom a promo code was redeemed."""
    __tablename__ = "promo_code_redemptions"

    __table_args__ = (
        UniqueConstraint(
            "promo_code_id", "organization_id",
            name="uq_promo_redemption_org",
        ),
        Index("idx_promo_redemptions_promo_id", "promo_code_id"),
        Index("idx_promo_redemptions_org_id", "organization_id"),
    )

    promo_code_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("promo_codes.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    redeemed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    discount_applied: Mapped[float] = mapped_column(
        Numeric(12, 4), nullable=False,
        comment="Actual discount amount applied in USD",
    )

    # ── Relationship ──────────────────────────────────────────────────────────
    promo_code: Mapped[PromoCode] = relationship("PromoCode", back_populates="redemptions")

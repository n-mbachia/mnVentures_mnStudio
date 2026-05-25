"""
compliance/services.py
────────────────────────────────────────────────────────────────────────────
MN Ventures — Compliance Calculation Engine

ComplianceCalculator is the single authoritative source for all statutory
and operational metrics.  It is intentionally free of Django view logic
so it can be called from views, management commands, or tests identically.

Statutory rules encoded (Kenya, 2024–2025 regime):
  • Turnover Tax (TOT)           — 1.5% of monthly gross sales
                                   Income Tax Act, s.12C  |  iTax filing by 20th
  • Affordable Housing Levy (AHL)— 1.5% of personal income (drawings or net profit)
                                   Affordable Housing Act, 2024  |  due 9th working day
  • Social Health Authority (SHA)— KES 450 flat (voluntary self-employed tier)
                                   SHA Act, 2023  |  due 9th working day
  • NSSF                         — Voluntary for self-employed  |  default KES 0

All monetary arithmetic uses Python's Decimal type throughout.
"""

import calendar
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from django.db.models import Sum

# ─── Constants (statutory rates, Kenya 2024–2025) ────────────────────────────

TOT_RATE            = Decimal("0.015")   # 1.5 %
AHL_RATE            = Decimal("0.015")   # 1.5 %
SHA_MONTHLY_FLAT    = Decimal("450.00")  # KES 450 — self-employed voluntary tier
NSSF_DEFAULT        = Decimal("0.00")    # Voluntary; owner may override

ZERO = Decimal("0.00")


def _d(value) -> Decimal:
    """Cast any numeric to a two-decimal Decimal."""
    if value is None:
        return ZERO
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _ninth_working_day(month: int, year: int) -> str:
    """
    Return a human-readable string for the 9th working day (Mon–Fri) of the
    month *following* the reference month — the standard AHL / SHA due date.
    """
    # Move to following month
    if month == 12:
        target_month, target_year = 1, year + 1
    else:
        target_month, target_year = month + 1, year

    working_day_count = 0
    day = 1
    _, last_day = calendar.monthrange(target_year, target_month)

    while day <= last_day:
        weekday = calendar.weekday(target_year, target_month, day)
        if weekday < 5:             # Monday=0 … Friday=4
            working_day_count += 1
            if working_day_count == 9:
                import datetime
                dt = datetime.date(target_year, target_month, day)
                return dt.strftime("%-d %B %Y")   # e.g. "12 February 2025"
        day += 1

    return f"9th working day of {calendar.month_name[target_month]} {target_year}"


def _twentieth_of_following_month(month: int, year: int) -> str:
    """Return the 20th of the following month — TOT filing deadline."""
    if month == 12:
        return f"20 January {year + 1}"
    return f"20 {calendar.month_name[month + 1]} {year}"


# ─── Result dataclasses ───────────────────────────────────────────────────────

@dataclass
class OperationalMetrics:
    total_purchases:    Decimal
    total_opex:         Decimal
    cogs:               Decimal
    gross_sales:        Decimal
    gross_profit:       Decimal
    net_profit:         Decimal

    # Breakdowns for dashboard detail rows
    purchase_breakdown: dict = field(default_factory=dict)   # category → KES
    expense_breakdown:  dict = field(default_factory=dict)   # category → KES
    invoice_count:      int  = 0
    etims_compliant_count: int = 0
    etims_non_compliant_count: int = 0


@dataclass
class StatutoryCard:
    """One card on the compliance dashboard per statutory obligation."""
    name:           str
    short_name:     str
    amount_due:     Decimal
    basis:          str          # Human description of how the number was derived
    calculation_detail: str      # e.g. "1.5% × KES 120,000 = KES 1,800"
    due_date:       str
    itax_head:      str          # Tax Head in iTax
    itax_sub_head:  str          # Tax Sub-Head in iTax
    payment_code:   str          # PRN payment code description
    alert:          Optional[str] = None   # Warning message if applicable
    is_voluntary:   bool = False
    nssf_override:  Optional[Decimal] = None


@dataclass
class ComplianceResult:
    month:        int
    year:         int
    period_label: str            # e.g. "January 2025"
    operational:  OperationalMetrics
    statutory:    list[StatutoryCard]
    total_statutory_due: Decimal
    drawings_used:       Decimal  # Amount used as AHL base
    drawings_source:     str      # "net_profit" | "drawings_override"
    warnings:            list[str] = field(default_factory=list)


# ─── Main service class ───────────────────────────────────────────────────────

class ComplianceCalculator:
    """
    Compute all operational analytics and statutory obligations for a given
    month and year.

    Usage:
        calc   = ComplianceCalculator(month=1, year=2025, nssf_contribution=200)
        result = calc.compute()
        # result is a ComplianceResult dataclass — pass directly to template context
    """

    def __init__(
        self,
        month: int,
        year: int,
        nssf_contribution: Decimal = NSSF_DEFAULT,
        use_drawings_override: bool = False,   # If True, use DrawingsLog instead of net profit
    ):
        if not (1 <= month <= 12):
            raise ValueError(f"month must be 1–12, got {month}")
        if year < 2000:
            raise ValueError(f"year seems invalid: {year}")

        self.month  = month
        self.year   = year
        self.nssf   = _d(nssf_contribution)
        self.use_drawings_override = use_drawings_override

    # ── Internal query helpers ────────────────────────────────────────────────

    def _qs_filter(self, queryset, date_field: str = "date"):
        """Filter a queryset to the calculator's month/year."""
        return queryset.filter(**{
            f"{date_field}__year":  self.year,
            f"{date_field}__month": self.month,
        })

    def _sum(self, queryset, field_name: str) -> Decimal:
        result = queryset.aggregate(total=Sum(field_name))["total"]
        return _d(result)

    # ── Operational computations ─────────────────────────────────────────────

    def _compute_purchases(self):
        from .models import PurchaseLog
        qs = self._qs_filter(PurchaseLog.objects.all())
        total = self._sum(qs, "total_cost")

        # Per-category breakdown
        breakdown = {}
        for choice_value, choice_label in PurchaseLog.CATEGORY_CHOICES:
            cat_total = self._sum(qs.filter(category=choice_value), "total_cost")
            if cat_total > ZERO:
                breakdown[choice_label] = cat_total

        return total, breakdown

    def _compute_opex(self):
        from .models import ExpenseLog
        qs = self._qs_filter(ExpenseLog.objects.all())
        total = self._sum(qs, "amount")

        breakdown = {}
        for choice_value, choice_label in ExpenseLog.CATEGORY_CHOICES:
            cat_total = self._sum(qs.filter(category=choice_value), "amount")
            if cat_total > ZERO:
                breakdown[choice_label] = cat_total

        return total, breakdown

    def _compute_cogs(self) -> Decimal:
        from .models import MaterialUseLog
        qs = self._qs_filter(MaterialUseLog.objects.all())
        return self._sum(qs, "line_cost")

    def _compute_sales(self):
        from .models import SalesInvoice
        qs = self._qs_filter(SalesInvoice.objects.all())
        total      = self._sum(qs, "gross_amount")
        count      = qs.count()
        etims_ok   = qs.filter(etims_registered=True).count()
        etims_bad  = qs.filter(etims_registered=False).count()
        return total, count, etims_ok, etims_bad

    def _get_drawings(self, net_profit: Decimal) -> tuple[Decimal, str]:
        if self.use_drawings_override:
            from .models import DrawingsLog
            try:
                d = DrawingsLog.objects.get(month=self.month, year=self.year)
                return _d(d.amount), "drawings_override"
            except DrawingsLog.DoesNotExist:
                pass   # Fall through to net profit
        return net_profit, "net_profit"

    # ── Statutory cards ───────────────────────────────────────────────────────

    def _card_tot(self, gross_sales: Decimal) -> StatutoryCard:
        due_date = _twentieth_of_following_month(self.month, self.year)

        if gross_sales <= ZERO:
            return StatutoryCard(
                name            = "Turnover Tax (TOT)",
                short_name      = "TOT",
                amount_due      = ZERO,
                basis           = "No sales recorded this month",
                calculation_detail = "No taxable turnover",
                due_date        = due_date,
                itax_head       = "Income Tax",
                itax_sub_head   = "Turnover Tax",
                payment_code    = "Income Tax → Turnover Tax → Self Assessment",
                alert           = (
                    f"⚠ File a Nil Return on iTax before {due_date}. "
                    "Failure to file attracts a KES 5,000 penalty."
                ),
            )

        amount = (gross_sales * TOT_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return StatutoryCard(
            name            = "Turnover Tax (TOT)",
            short_name      = "TOT",
            amount_due      = amount,
            basis           = (
                f"1.5% of monthly gross sales "
                f"(Income Tax Act s.12C — TOT regime for turnover KES 1M–50M p.a.)"
            ),
            calculation_detail = f"1.5% × KES {gross_sales:,.2f} = KES {amount:,.2f}",
            due_date        = due_date,
            itax_head       = "Income Tax",
            itax_sub_head   = "Turnover Tax",
            payment_code    = "Income Tax → Turnover Tax → Self Assessment",
        )

    def _card_ahl(self, drawings: Decimal, drawings_source: str) -> StatutoryCard:
        due_date    = _ninth_working_day(self.month, self.year)
        source_label = (
            "owner drawings (manual override)"
            if drawings_source == "drawings_override"
            else "monthly net profit (proxy for personal income)"
        )

        if drawings <= ZERO:
            return StatutoryCard(
                name            = "Affordable Housing Levy (AHL)",
                short_name      = "AHL",
                amount_due      = ZERO,
                basis           = f"Base income is KES 0 ({source_label})",
                calculation_detail = "No assessable personal income this period",
                due_date        = due_date,
                itax_head       = "Agency Revenue",
                itax_sub_head   = "Housing Levy — Self Assessment",
                payment_code    = "Agency Revenue → Housing Levy → Self Assessment",
                alert           = (
                    "ℹ AHL is KES 0 because net profit / drawings ≤ 0 this month. "
                    "No payment required but consider recording a nil declaration."
                ),
            )

        amount = (drawings * AHL_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return StatutoryCard(
            name            = "Affordable Housing Levy (AHL)",
            short_name      = "AHL",
            amount_due      = amount,
            basis           = (
                f"1.5% of personal income drawn from business "
                f"({source_label}) — Affordable Housing Act, 2024 s.8(2)"
            ),
            calculation_detail = f"1.5% × KES {drawings:,.2f} = KES {amount:,.2f}",
            due_date        = due_date,
            itax_head       = "Agency Revenue",
            itax_sub_head   = "Housing Levy — Self Assessment",
            payment_code    = "Agency Revenue → Housing Levy → Self Assessment",
        )

    def _card_sha(self) -> StatutoryCard:
        due_date = _ninth_working_day(self.month, self.year)
        return StatutoryCard(
            name            = "Social Health Authority (SHA)",
            short_name      = "SHA",
            amount_due      = SHA_MONTHLY_FLAT,
            basis           = (
                "Flat KES 450/month — voluntary self-employed tier "
                "(SHA Act 2023, Self-Employed Voluntary Contribution Schedule)"
            ),
            calculation_detail = "Fixed rate: KES 450.00 (self-employed voluntary declaration)",
            due_date        = due_date,
            itax_head       = "Agency Revenue",
            itax_sub_head   = "SHA Contribution — Self Employed",
            payment_code    = "Agency Revenue → SHA → Self-Employed Voluntary",
        )

    def _card_nssf(self) -> StatutoryCard:
        due_date = _ninth_working_day(self.month, self.year)
        label = (
            f"Voluntary contribution: KES {self.nssf:,.2f}"
            if self.nssf > ZERO
            else "Not contributing this month (voluntary)"
        )
        return StatutoryCard(
            name            = "NSSF (National Social Security Fund)",
            short_name      = "NSSF",
            amount_due      = self.nssf,
            basis           = (
                "Voluntary for self-employed sole proprietors. "
                "NSSF Act 2013 — Tier I/II contributions optional at this registration tier."
            ),
            calculation_detail = label,
            due_date        = due_date,
            itax_head       = "NSSF",
            itax_sub_head   = "Self-Employed Voluntary Contribution",
            payment_code    = "NSSF Portal → Self-Employed → Monthly Contribution",
            is_voluntary    = True,
        )

    # ── Master compute ────────────────────────────────────────────────────────

    def compute(self) -> "ComplianceResult":
        """
        Execute all queries, apply business rules, and return a fully-populated
        ComplianceResult.  This is the only public method callers need.
        """

        # ── Operational metrics ───────────────────────────────────────────────
        total_purchases, purchase_breakdown = self._compute_purchases()
        total_opex,      expense_breakdown  = self._compute_opex()
        cogs                                = self._compute_cogs()
        gross_sales, inv_count, etims_ok, etims_bad = self._compute_sales()

        gross_profit = (gross_sales - cogs).quantize(Decimal("0.01"))
        net_profit   = (gross_profit - total_opex).quantize(Decimal("0.01"))

        operational = OperationalMetrics(
            total_purchases     = total_purchases,
            total_opex          = total_opex,
            cogs                = cogs,
            gross_sales         = gross_sales,
            gross_profit        = gross_profit,
            net_profit          = net_profit,
            purchase_breakdown  = purchase_breakdown,
            expense_breakdown   = expense_breakdown,
            invoice_count       = inv_count,
            etims_compliant_count    = etims_ok,
            etims_non_compliant_count= etims_bad,
        )

        # ── Drawings / AHL base ───────────────────────────────────────────────
        drawings, drawings_source = self._get_drawings(net_profit)

        # ── Statutory cards ───────────────────────────────────────────────────
        cards = [
            self._card_tot(gross_sales),
            self._card_ahl(drawings, drawings_source),
            self._card_sha(),
            self._card_nssf(),
        ]

        mandatory_total = sum(
            c.amount_due for c in cards if not c.is_voluntary
        ).quantize(Decimal("0.01"))

        # ── Warnings ─────────────────────────────────────────────────────────
        warnings = []
        if etims_bad > 0:
            warnings.append(
                f"⚠ {etims_bad} invoice(s) not yet raised on eTIMS. "
                "All sales must be recorded in eTIMS per KRA requirement."
            )
        if net_profit < ZERO:
            warnings.append(
                "📉 Net profit is negative this month. "
                "Review expenses and pricing — AHL base set to KES 0."
            )
        for c in cards:
            if c.alert:
                warnings.append(c.alert)

        return ComplianceResult(
            month        = self.month,
            year         = self.year,
            period_label = f"{calendar.month_name[self.month]} {self.year}",
            operational  = operational,
            statutory    = cards,
            total_statutory_due = mandatory_total,
            drawings_used    = drawings,
            drawings_source  = drawings_source,
            warnings         = warnings,
        )


# ─── Convenience: build context dict for Django templates ────────────────────

def build_dashboard_context(month: int, year: int, **calc_kwargs) -> dict:
    """
    Thin wrapper — returns a dict ready to unpack into a Django template context.

    Example usage in a view:
        context = build_dashboard_context(month=1, year=2025)
        return render(request, "compliance/dashboard.html", context)
    """
    result = ComplianceCalculator(month=month, year=year, **calc_kwargs).compute()
    op     = result.operational

    return {
        "result":           result,
        "op":               op,
        "statutory_cards":  result.statutory,
        "warnings":         result.warnings,
        "period_label":     result.period_label,
        "month":            month,
        "year":             year,
        # Convenience flat keys for simple template access
        "gross_sales":      op.gross_sales,
        "total_purchases":  op.total_purchases,
        "total_opex":       op.total_opex,
        "cogs":             op.cogs,
        "gross_profit":     op.gross_profit,
        "net_profit":       op.net_profit,
        "total_statutory":  result.total_statutory_due,
        "invoice_count":    op.invoice_count,
        "etims_ok":         op.etims_compliant_count,
        "etims_bad":        op.etims_non_compliant_count,
    }

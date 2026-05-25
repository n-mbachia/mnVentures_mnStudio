"""
compliance/templatetags/compliance_extras.py
────────────────────────────────────────────
Custom template filters for the compliance dashboard.

  {{ value|abs_value }}            → absolute value (for negative P&L display)
  {{ value|kes }}                  → "KES 1,234.56" formatted string
  {{ value|pct_of:total }}         → "12.5%" ratio string
  {{ value|friendly_source }}      → "net profit" / "drawings override"
  {{ value|neg_class:"base" }}     → appends "text-red-600" when value < 0

  Note: the broken |replace:"_":" " two-arg syntax has been removed.
  Use |friendly_source for the drawings_source field specifically.
"""

from decimal import Decimal, InvalidOperation
from django import template

register = template.Library()


@register.filter
def abs_value(value):
    """Return the absolute value of a Decimal or numeric."""
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value


@register.filter
def kes(value):
    """
    Format a Decimal as a comma-separated KES string.
    e.g.  Decimal("1234.5")  →  "KES 1,234.50"
    """
    try:
        d = Decimal(str(value))
        return f"KES {d:,.2f}"
    except (InvalidOperation, TypeError, ValueError):
        return f"KES {value}"


@register.filter
def pct_of(value, total):
    """
    Return value as a percentage of total, rounded to 1 dp.
    e.g.  pct_of(30, 200)  →  "15.0%"
    Returns "—" on division by zero or bad input.
    """
    try:
        if not total:
            return "0.0%"
        return f"{float(value) / float(total) * 100:.1f}%"
    except (TypeError, ZeroDivisionError, ValueError):
        return "—"


@register.filter
def friendly_source(value):
    """
    Convert the drawings_source string into a human-readable label.
    "net_profit"        →  "net profit"
    "drawings_override" →  "owner drawings (manual)"
    Anything else       →  the value with underscores replaced by spaces.
    """
    mapping = {
        "net_profit":        "net profit",
        "drawings_override": "owner drawings (manual)",
    }
    return mapping.get(str(value), str(value).replace("_", " "))


@register.filter
def neg_class(value, base_class=""):
    """
    Append 'text-red-600' to base_class when value is negative.
    Usage: class="{{ net_profit|neg_class:'text-indigo-700' }}"
    """
    try:
        if Decimal(str(value)) < 0:
            return f"{base_class} text-red-600".strip()
    except (InvalidOperation, TypeError, ValueError):
        pass
    return base_class


@register.filter
def payment_badge_class(status):
    """Return a Tailwind pill colour class for a payment_status value."""
    colours = {
        "paid":      "bg-green-100 text-green-800",
        "partial":   "bg-amber-100 text-amber-800",
        "unpaid":    "bg-stone-100 text-stone-600",
        "overdue":   "bg-red-100   text-red-800",
        "cancelled": "bg-stone-200 text-stone-500",
    }
    return colours.get(status, "bg-stone-100 text-stone-600")

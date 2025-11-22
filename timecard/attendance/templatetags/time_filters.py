from django import template

register = template.Library()

@register.filter
def hours(td):
    """Convert timedelta to decimal hours (float with 2 decimals)."""
    if td:
        return round(td.total_seconds() / 3600, 2)
    return 0

@register.filter
def hhmm(td):
    """Convert timedelta to HH:MM format."""
    if td:
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}"
    return "--:--"

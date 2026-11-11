import re
from datetime import datetime, date
from dateutil import parser

def normalize_text(value):
    if value is None:
        return None
    return re.sub(r"\s+", " ", str(value)).strip().casefold()

def normalize_email(value):
    if not value:
        return None
    value = str(value).strip().casefold().replace("[at]", "@")
    return value if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value) else None

def parse_date(value):
    if not value:
        return None
    try:
        # Explicitly support the malformed MM-DD/YYYY sample.
        if re.match(r"^\d{2}-\d{2}/\d{4}$", str(value)):
            value = str(value).replace("/", "-")
            return datetime.strptime(value, "%m-%d-%Y").date()
        return parser.parse(str(value)).date()
    except (ValueError, TypeError, OverflowError):
        return None

def parse_datetime(value):
    if not value:
        return None
    try:
        return parser.isoparse(str(value))
    except (ValueError, TypeError, OverflowError):
        return None

def time_minutes(value):
    if not value:
        return None
    try:
        parsed = parser.parse(str(value))
        return parsed.hour * 60 + parsed.minute
    except (ValueError, TypeError, OverflowError):
        return None

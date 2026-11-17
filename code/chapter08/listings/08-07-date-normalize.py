import re
from datetime import datetime

_US_DATE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{2,4})")

def normalize_date(raw: str) -> str:
    """Convert MM/DD/YYYY to ISO-8601 YYYY-MM-DD."""
    m = _US_DATE.search(raw)
    if not m:
        return raw
    month, day, year = m.groups()
    if len(year) == 2:
        year = "20" + year
    return datetime(int(year), int(month), int(day)).strftime("%Y-%m-%d")


def main() -> None:
    print(normalize_date("05/15/2026"))


if __name__ == "__main__":
    main()

from datetime import datetime, timedelta
from typing import Optional, Tuple

def parse_date_range(
    start_date_str: Optional[str],
    end_date_str: Optional[str]
) -> Optional[Tuple[datetime, datetime]]:
    """Parse start and end date strings into datetime objects."""
    if not start_date_str and not end_date_str:
        return None

    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    else:
        start_date = datetime.min

    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1)
    else:
        end_date = datetime.max

    return start_date, end_date
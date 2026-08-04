import random
from datetime import datetime


def get_formatted_current_date():
    """
    Returns today's date in M/D/YYYY format matching AB Ark reference format (e.g. 8/4/2026).
    """
    now = datetime.now()
    return f"{now.month}/{now.day}/{now.year}"


def generate_proposal_id(prefix: str = "ARK") -> str:
    """
    Generates a unique dynamic proposal reference ID matching AB Ark's reference format.
    Format: ARK-{MM}-{DD}-{RANDOM3} (e.g. ARK-08-04-391)
    """
    now = datetime.now()
    month_str = f"{now.month:02d}"
    day_str = f"{now.day:02d}"
    rand_num = random.randint(100, 999)
    return f"{prefix}-{month_str}-{day_str}-{rand_num}"


def get_default_version() -> str:
    """
    Returns default version string for new proposals.
    """
    return "1.0"
# Simple verification test when run directly
if __name__ == "__main__":
    print("--- Dynamic Metadata Utility Verification ---")
    print(f"Current Date : {get_formatted_current_date()}")
    print(f"Proposal ID  : {generate_proposal_id()}")
    print(f"Version      : {get_default_version()}")
    
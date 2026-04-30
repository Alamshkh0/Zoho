"""App configuration: brands, roles, env vars.

Edit BRANDS or ROLES here to add new options. No other code needs to change.
"""
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
ADMIN_PASSCODE = os.getenv("ADMIN_PASSCODE", "redington2026")

BRANDS = ["AWS", "Microsoft", "Red Hat"]

ROLES = ["PAM", "BSM", "PM", "Pre-Sales", "Business", "Marketing", "Services", "Finance", "Other"]

FIELD_TYPES = ["Text", "Number", "Date", "Dropdown", "Multi-select", "Yes/No"]

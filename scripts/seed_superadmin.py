"""
Seed script to create a super admin user.
Run this once to create the initial super admin account.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.auth import get_password_hash
from backend.services.db import get_db
from datetime import datetime


def seed_superadmin():
    """Create a super admin user if it doesn't exist."""
    db = get_db()
    
    # Check if superadmin already exists
    existing = db.users.find_one({"username": "superadmin"})
    if existing:
        print("✅ Super admin user already exists!")
        print(f"   Username: superadmin")
        print(f"   Role: {existing.get('role')}")
        return
    
    # Create super admin user
    superadmin_doc = {
        "username": "superadmin",
        "password_hash": get_password_hash("admin123"),
        "role": "superadmin",
        "client_id": None,
        "created_at": datetime.utcnow()
    }
    
    result = db.users.insert_one(superadmin_doc)
    
    print("=" * 60)
    print("✅ Super Admin User Created Successfully!")
    print("=" * 60)
    print(f"   ID: {result.inserted_id}")
    print(f"   Username: superadmin")
    print(f"   Password: admin123")
    print(f"   Role: superadmin")
    print("=" * 60)
    print("\n⚠️  IMPORTANT: Change the default password after first login!")
    print("\nYou can now login at http://localhost:3000")
    print("Click the ⚙️ icon and use these credentials.\n")


if __name__ == "__main__":
    try:
        seed_superadmin()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

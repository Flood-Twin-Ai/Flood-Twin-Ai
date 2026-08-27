from app.db.database import SessionLocal
from app.services import ensure_demo_data
from app.main import get_or_create_admin

def main():
    db = SessionLocal()
    ensure_demo_data(db)
    admin = get_or_create_admin(db)
    print(f"Seeded demo data. Admin: {admin.email} / Admin@12345")
    db.close()

if __name__ == "__main__":
    main()

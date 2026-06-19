import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models.user import User
from app.models.role import Role
from app.models.region import Region


def seed_roles():
    """Создание ролей"""
    db = SessionLocal()

    roles = [
        {"name": "citizen", "description": "Обычный пользователь"},
        {"name": "doctor", "description": "Врач"},
        {"name": "regional_admin", "description": "Региональный администратор"},
        {"name": "national_admin", "description": "Национальный администратор"}
    ]

    for role_data in roles:
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing:
            new_role = Role(**role_data)
            db.add(new_role)

    db.commit()
    db.close()
    print("✅ Roles seeded")


def seed_test_users():
    """Создание тестовых пользователей"""
    db = SessionLocal()

    users = [
        {
            "email": "admin@docshare.uz",
            "password": "Admin123!",
            "full_name": "Super Admin",
            "phone": "+998901234567",
            "role": "national_admin",
            "city": "Tashkent"
        },
        {
            "email": "regional@docshare.uz",
            "password": "Regional123!",
            "full_name": "Regional Admin",
            "phone": "+998901234568",
            "role": "regional_admin",
            "city": "Tashkent"
        },
        {
            "email": "doctor@docshare.uz",
            "password": "Doctor123!",
            "full_name": "Dr. John Doe",
            "phone": "+998901234569",
            "role": "doctor",
            "city": "Tashkent"
        },
        {
            "email": "citizen@docshare.uz",
            "password": "Citizen123!",
            "full_name": "Citizen User",
            "phone": "+998901234570",
            "role": "citizen",
            "city": "Tashkent"
        }
    ]

    for user_data in users:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing:
            password_hash = hash_password(user_data["password"])
            new_user = User(
                email=user_data["email"],
                password_hash=password_hash,
                full_name=user_data["full_name"],
                phone=user_data["phone"],
                city=user_data.get("city"),
                role=user_data["role"],
                is_active=True,
                is_verified=True
            )
            db.add(new_user)

    db.commit()
    db.close()
    print("✅ Test users seeded")


def seed_regions():
    """Создание регионов"""
    db = SessionLocal()

    regions = [
        {"name": "Tashkent", "code": "TASH"},
        {"name": "Samarkand", "code": "SAM"},
        {"name": "Bukhara", "code": "BUK"},
        {"name": "Fergana", "code": "FER"},
        {"name": "Navoi", "code": "NAV"},
    ]

    for region_data in regions:
        existing = db.query(Region).filter(Region.code == region_data["code"]).first()
        if not existing:
            new_region = Region(**region_data)
            db.add(new_region)

    db.commit()
    db.close()
    print("✅ Regions seeded")


if __name__ == "__main__":
    print("🌱 Seeding database...")
    init_db()
    seed_roles()
    seed_regions()
    seed_test_users()
    print("✅ Database seeded successfully!")
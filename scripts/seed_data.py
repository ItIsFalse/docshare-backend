import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models.user import User
from app.models.role import Role
from app.models.region import Region
from app.models.district import District
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.hospital import Hospital
from app.models.family_member import FamilyMember


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


def seed_regions_and_districts():
    """Создание регионов и районов"""
    db = SessionLocal()

    regions_data = [
        {"name": "Tashkent", "code": "TASH"},
        {"name": "Samarkand", "code": "SAM"},
        {"name": "Bukhara", "code": "BUK"},
        {"name": "Fergana", "code": "FER"},
        {"name": "Navoi", "code": "NAV"},
    ]

    districts_data = {
        "TASH": ["Yunusabad", "Mirabad", "Olmazor", "Shayxontohur", "Chilonzor", "Yakkasaroy", "Bektemir"],
        "SAM": ["Samarkand City", "Bulungur", "Ishtixon", "Jomboy", "Kattakurgan", "Oqdaryo"],
        "BUK": ["Bukhara City", "Gijduvon", "Kogon", "Olot", "Romitan", "Shofirkon"],
        "FER": ["Fergana City", "Margilan", "Quvasoy", "Rishton", "Toshloq", "Yozyovon"],
        "NAV": ["Navoi City", "Karmana", "Konimex", "Nurota", "Tomdi", "Uchquduq"],
    }

    created_regions = {}
    for region_data in regions_data:
        existing = db.query(Region).filter(Region.code == region_data["code"]).first()
        if not existing:
            new_region = Region(**region_data)
            db.add(new_region)
            db.flush()
            created_regions[region_data["code"]] = new_region
        else:
            created_regions[region_data["code"]] = existing

    db.commit()

    for region_code, district_names in districts_data.items():
        region = created_regions.get(region_code)
        if region:
            for district_name in district_names:
                existing = db.query(District).filter(
                    District.region_id == region.id,
                    District.name_en == district_name
                ).first()
                if not existing:
                    new_district = District(
                        region_id=region.id,
                        name_uz=district_name,
                        name_ru=district_name,
                        name_en=district_name,
                        type="district"
                    )
                    db.add(new_district)

    db.commit()
    db.close()
    print("✅ Regions and districts seeded")


def seed_hospitals():
    """Создание больниц"""
    db = SessionLocal()

    # Получаем регионы
    tashkent = db.query(Region).filter(Region.code == "TASH").first()
    samarkand = db.query(Region).filter(Region.code == "SAM").first()
    bukhara = db.query(Region).filter(Region.code == "BUK").first()
    fergana = db.query(Region).filter(Region.code == "FER").first()

    hospitals_data = [
        {
            "name_uz": "Toshkent Tibbiyot Markazi",
            "name_ru": "Ташкентский Медицинский Центр",
            "name_en": "Tashkent Medical Center",
            "region_id": tashkent.id if tashkent else None,
            "facility_type": "hospital",
            "description": "Ведущий медицинский центр Узбекистана",
            "full_address": "Tashkent, Shayxontohur district, Navoi street 1",
            "rating": 4.8,
            "has_icu": True,
            "has_emergency_home_visit": True,
            "registration_phone": "+998712345678"
        },
        {
            "name_uz": "Samarqand Davlat Kasalxonasi",
            "name_ru": "Самаркандская Государственная Больница",
            "name_en": "Samarkand State Hospital",
            "region_id": samarkand.id if samarkand else None,
            "facility_type": "hospital",
            "description": "Крупнейшая больница Самаркандской области",
            "full_address": "Samarkand, Registan street 15",
            "rating": 4.5,
            "has_icu": True,
            "has_emergency_home_visit": False,
            "registration_phone": "+998662345678"
        },
        {
            "name_uz": "Buxoro Viloyat Klinikasi",
            "name_ru": "Бухарская Областная Клиника",
            "name_en": "Bukhara Regional Clinic",
            "region_id": bukhara.id if bukhara else None,
            "facility_type": "hospital",
            "description": "Современная клиника в Бухаре",
            "full_address": "Bukhara, Ibn Sino street 45",
            "rating": 4.6,
            "has_icu": False,
            "has_emergency_home_visit": True,
            "registration_phone": "+998652345678"
        },
        {
            "name_uz": "Farg'ona Shahar Kasalxonasi",
            "name_ru": "Ферганская Городская Больница",
            "name_en": "Fergana City Hospital",
            "region_id": fergana.id if fergana else None,
            "facility_type": "hospital",
            "description": "Городская больница Ферганы",
            "full_address": "Fergana, Al-Fargoni street 22",
            "rating": 4.2,
            "has_icu": True,
            "has_emergency_home_visit": False,
            "registration_phone": "+998732345678"
        }
    ]

    created_hospitals = []
    for hospital_data in hospitals_data:
        if not hospital_data["region_id"]:
            continue
        existing = db.query(Hospital).filter(Hospital.name_en == hospital_data["name_en"]).first()
        if not existing:
            new_hospital = Hospital(**hospital_data)
            db.add(new_hospital)
            db.flush()
            created_hospitals.append(new_hospital)

    db.commit()
    db.close()
    print("✅ Hospitals seeded")


def seed_test_users():
    """Создание тестовых пользователей"""
    db = SessionLocal()

    tashkent = db.query(Region).filter(Region.code == "TASH").first()
    hospital = db.query(Hospital).filter(Hospital.name_en == "Tashkent Medical Center").first()

    users = [
        {
            "email": "admin@docshare.uz",
            "password": "Admin123",
            "full_name": "Super Admin",
            "phone": "+998901234567",
            "role": "national_admin",
            "city": "Tashkent",
            "is_doctor": False
        },
        {
            "email": "regional@docshare.uz",
            "password": "Regional123",
            "full_name": "Regional Admin",
            "phone": "+998901234568",
            "role": "regional_admin",
            "city": "Tashkent",
            "is_doctor": False
        },
        {
            "email": "doctor@docshare.uz",
            "password": "Doctor123",
            "full_name": "Dr. John Doe",
            "phone": "+998901234569",
            "role": "doctor",
            "city": "Tashkent",
            "is_doctor": True,
            "specialization": "Cardiology",
            "hospital_id": hospital.id if hospital else None
        },
        {
            "email": "citizen@docshare.uz",
            "password": "Citizen123",
            "full_name": "Citizen User",
            "phone": "+998901234570",
            "role": "citizen",
            "city": "Tashkent",
            "is_doctor": False
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
            db.flush()

            # Создаем запись пациента (для всех)
            patient = Patient(
                user_id=new_user.id,
                region_id=tashkent.id if tashkent else None,
                blood_type="O+",
                gender="male"
            )
            db.add(patient)
            db.flush()

            # Если доктор - создаем запись доктора
            if user_data.get("is_doctor"):
                doctor = Doctor(
                    user_id=new_user.id,
                    region_id=tashkent.id if tashkent else None,
                    hospital_id=user_data.get("hospital_id"),
                    specialization=user_data.get("specialization", "General"),
                    license_number=f"LIC-{new_user.id}",
                    years_of_experience=10,
                    is_accepting_patients=True,
                    rating=4.5
                )
                db.add(doctor)

    db.commit()
    db.close()
    print("✅ Test users seeded")


def seed_family_members():
    """Создание тестовых членов семьи"""
    db = SessionLocal()

    # Получаем пациента (citizen)
    user = db.query(User).filter(User.email == "citizen@docshare.uz").first()
    if not user:
        db.close()
        return

    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not patient:
        db.close()
        return

    family_members_data = [
        {
            "name": "Malika Karimova",
            "relationship_type": "wife",
            "gender": "female",
            "blood_type": "A+",
            "health_status": "good",
            "health_score": 92,
            "date_of_birth": "1995-03-15"
        },
        {
            "name": "Bobur Karimov",
            "relationship_type": "son",
            "gender": "male",
            "blood_type": "B+",
            "health_status": "attention",
            "health_score": 78,
            "date_of_birth": "2015-08-22"
        },
        {
            "name": "Nodira Karimova",
            "relationship_type": "daughter",
            "gender": "female",
            "blood_type": "O+",
            "health_status": "good",
            "health_score": 85,
            "date_of_birth": "2018-05-10"
        },
        {
            "name": "Dilshod Karimov",
            "relationship_type": "father",
            "gender": "male",
            "blood_type": "AB+",
            "health_status": "critical",
            "health_score": 65,
            "date_of_birth": "1965-12-01"
        },
        {
            "name": "Larisa Karimova",
            "relationship_type": "mother",
            "gender": "female",
            "blood_type": "A-",
            "health_status": "attention",
            "health_score": 72,
            "date_of_birth": "1970-07-20"
        }
    ]

    for member_data in family_members_data:
        existing = db.query(FamilyMember).filter(
            FamilyMember.patient_id == patient.id,
            FamilyMember.name == member_data["name"]
        ).first()

        if not existing:
            # Парсим дату рождения
            dob = None
            if member_data.get("date_of_birth"):
                try:
                    dob = datetime.strptime(member_data["date_of_birth"], "%Y-%m-%d").date()
                except:
                    pass

            new_member = FamilyMember(
                patient_id=patient.id,
                name=member_data["name"],
                relationship_type=member_data["relationship_type"],
                gender=member_data["gender"],
                blood_type=member_data["blood_type"],
                health_status=member_data["health_status"],
                health_score=member_data["health_score"],
                date_of_birth=dob,
                status="active"
            )
            db.add(new_member)

    db.commit()
    db.close()
    print("✅ Family members seeded")


if __name__ == "__main__":
    print("🌱 Seeding database...")
    init_db()
    seed_roles()
    seed_regions_and_districts()
    seed_hospitals()
    seed_test_users()
    seed_family_members()
    print("✅ Database seeded successfully!")
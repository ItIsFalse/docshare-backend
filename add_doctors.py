"""
Скрипт для добавления тестовых докторов в базу данных
Запуск: python add_doctors.py
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.doctor import Doctor
from app.models.region import Region
from app.models.hospital import Hospital


def add_doctors():
    """Добавление тестовых докторов"""
    db = SessionLocal()

    try:
        # Получаем регион Tashkent
        region = db.query(Region).filter(Region.code == "TASH").first()
        if not region:
            print("❌ Region Tashkent not found")
            return

        # Получаем больницу
        hospital = db.query(Hospital).filter(Hospital.name_en == "Tashkent Medical Center").first()
        if not hospital:
            print("❌ Hospital not found")
            return

        # Список докторов для добавления
        doctors_data = [
            {
                "email": "doctor1@docshare.uz",
                "password": "Doctor123",
                "full_name": "Dr. Karimova Nilufar",
                "specialization": "Cardiology",
                "phone": "+998901234571",
                "years_of_experience": 12,
                "rating": 4.9
            },
            {
                "email": "doctor2@docshare.uz",
                "password": "Doctor123",
                "full_name": "Dr. Abdullayev Jasur",
                "specialization": "Stomatology",
                "phone": "+998901234572",
                "years_of_experience": 8,
                "rating": 4.7
            },
            {
                "email": "doctor3@docshare.uz",
                "password": "Doctor123",
                "full_name": "Dr. Olimova Shahzoda",
                "specialization": "Cardiology",
                "phone": "+998901234573",
                "years_of_experience": 15,
                "rating": 4.8
            },
            {
                "email": "doctor4@docshare.uz",
                "password": "Doctor123",
                "full_name": "Dr. Rahimov Alisher",
                "specialization": "Neurology",
                "phone": "+998901234574",
                "years_of_experience": 10,
                "rating": 4.6
            },
            {
                "email": "doctor5@docshare.uz",
                "password": "Doctor123",
                "full_name": "Dr. Tursunov Bekzod",
                "specialization": "Ophthalmology",
                "phone": "+998901234575",
                "years_of_experience": 7,
                "rating": 4.4
            }
        ]

        from app.core.security import hash_password

        added_count = 0
        for data in doctors_data:
            # Проверяем, существует ли пользователь
            existing_user = db.query(User).filter(User.email == data["email"]).first()
            if existing_user:
                print(f"⚠️ User {data['email']} already exists, skipping...")
                continue

            # Создаем пользователя
            hashed_password = hash_password(data["password"])
            new_user = User(
                email=data["email"],
                password_hash=hashed_password,
                full_name=data["full_name"],
                phone=data["phone"],
                city="Tashkent",
                role="doctor",
                is_active=True,
                is_verified=True
            )
            db.add(new_user)
            db.flush()

            # Создаем доктора
            new_doctor = Doctor(
                user_id=new_user.id,
                region_id=region.id,
                hospital_id=hospital.id,
                specialization=data["specialization"],
                license_number=f"LIC-{new_user.id:04d}",
                years_of_experience=data["years_of_experience"],
                is_accepting_patients=True,
                rating=data["rating"]
            )
            db.add(new_doctor)

            added_count += 1
            print(f"✅ Added doctor: {data['full_name']} ({data['specialization']})")

        db.commit()
        print(f"\n🎉 Successfully added {added_count} doctors!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("👨‍⚕️ ADDING TEST DOCTORS")
    print("=" * 50)
    add_doctors()
"""
FULL API TEST SUITE — DocShare Backend
Адаптирован для пустой БД — создает данные сам
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import random
import string
import os

# ============ КОНФИГУРАЦИЯ ============
BASE_URL = "http://127.0.0.1:8000/api/v1"
# BASE_URL = "https://docshare-backend.onrender.com/api/v1"

# Тестовые пользователи (должны быть в БД после seed)
USERS = {
    "citizen": {
        "email": "citizen@docshare.uz",
        "password": "Citizen123",
        "role": "citizen"
    },
    "doctor": {
        "email": "doctor@docshare.uz",
        "password": "Doctor123",
        "role": "doctor"
    },
    "regional_admin": {
        "email": "regional@docshare.uz",
        "password": "Regional123",
        "role": "regional_admin"
    },
    "national_admin": {
        "email": "admin@docshare.uz",
        "password": "Admin123",
        "role": "national_admin"
    }
}


# ============ УТИЛИТЫ ============
class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.total = 0
        self.results = []

    def add(self, name: str, passed: bool, message: str = "", skipped: bool = False):
        self.total += 1
        if skipped:
            self.skipped += 1
            status = "⏭️ SKIP"
        elif passed:
            self.passed += 1
            status = "✅ PASS"
        else:
            self.failed += 1
            status = "❌ FAIL"
        self.results.append(f"{status} | {name} | {message}")
        print(f"{status} | {name} | {message}")

    def summary(self):
        print("\n" + "=" * 60)
        print(f"📊 RESULTS: {self.passed} passed, {self.failed} failed, {self.skipped} skipped")
        print("=" * 60)
        if self.failed > 0:
            print("\n❌ FAILED TESTS:")
            for r in self.results:
                if "❌" in r:
                    print(f"  {r}")


result = TestResult()


def get_token(email: str, password: str) -> Optional[str]:
    """Получает токен для пользователя"""
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=5
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
        return None
    except:
        return None


def get_headers(token: str) -> Dict:
    return {"Authorization": f"Bearer {token}"}


def random_string(length: int = 10) -> str:
    return ''.join(random.choices(string.ascii_letters, k=length))


def random_email() -> str:
    return f"test_{random_string(8)}@test.com"


def random_phone() -> str:
    return f"+998{random.randint(900000000, 999999999)}"


def random_date(future_days: int = 30) -> str:
    days = random.randint(1, future_days)
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


def random_time() -> str:
    return f"{random.randint(8, 18):02d}:{random.randint(0, 59):02d}"


def random_int(min_val: int, max_val: int) -> int:
    return random.randint(min_val, max_val)


def random_float(min_val: float, max_val: float) -> float:
    return round(random.uniform(min_val, max_val), 1)


# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============

def ensure_doctor_exists(token: str) -> Optional[int]:
    """Проверяет, есть ли доктора, и создает тестового если нет"""
    resp = requests.get(f"{BASE_URL}/doctors", headers=get_headers(token))
    if resp.status_code == 200 and resp.json():
        return resp.json()[0].get("id")

    # Пытаемся создать доктора (только если есть доступ)
    # Но обычно доктора уже есть из seed
    return None


def ensure_family_member(token: str) -> Optional[int]:
    """Создает тестового члена семьи если нет"""
    resp = requests.get(f"{BASE_URL}/family", headers=get_headers(token))
    if resp.status_code == 200 and resp.json():
        return resp.json()[0].get("id")

    # Создаем
    resp = requests.post(
        f"{BASE_URL}/family",
        headers=get_headers(token),
        json={
            "name": f"Test Family {random_string(5)}",
            "relation": "other",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "blood_type": "O+",
            "allergies": [],
            "chronic_conditions": [],
            "health_status": "good"
        }
    )
    if resp.status_code == 200:
        return resp.json().get("id")
    return None


# ============ ТЕСТЫ ============

def test_auth():
    """Тестирование аутентификации"""
    print("\n" + "=" * 60)
    print("🔐 TESTING AUTHENTICATION")
    print("=" * 60)

    # 1. Проверка существующих пользователей
    for role, user in USERS.items():
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": user["email"], "password": user["password"]},
            timeout=5
        )
        result.add(
            f"Auth: Login {role}",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )

    # 2. Негативный тест: неверный пароль
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "citizen@docshare.uz", "password": "wrongpassword"},
        timeout=5
    )
    result.add(
        "Auth: Wrong password (negative)",
        resp.status_code == 401,
        f"Status {resp.status_code} (expected 401)"
    )

    # 3. Регистрация нового пользователя
    test_email = random_email()
    resp = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": test_email,
            "password": "Test123!",
            "full_name": "Test User",
            "phone": random_phone(),
            "city": "Tashkent"
        },
        timeout=5
    )
    result.add(
        "Auth: Register new user",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )

    if resp.status_code == 200:
        token = resp.json().get("access_token")
        resp = requests.get(
            f"{BASE_URL}/auth/me",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            "Auth: Get profile",
            resp.status_code == 200,
            f"Email: {resp.json().get('email') if resp.status_code == 200 else 'N/A'}"
        )


def test_dashboard():
    """Тестирование дашборда"""
    print("\n" + "=" * 60)
    print("📊 TESTING DASHBOARD")
    print("=" * 60)

    token = get_token("citizen@docshare.uz", "Citizen123")
    if not token:
        result.add("Dashboard: No token", False, "No token")
        return

    resp = requests.get(
        f"{BASE_URL}/dashboard",
        headers=get_headers(token),
        timeout=10
    )
    result.add(
        "Dashboard: Get dashboard",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )

    if resp.status_code == 200:
        data = resp.json()
        fields = ["user", "daily_activity", "vitals", "daily_goals", "appointments", "family", "ai_tips", "hero_stats"]
        present = [f for f in fields if f in data]
        result.add(
            "Dashboard: Fields present",
            len(present) >= 5,
            f"Found {len(present)}/{len(fields)} fields"
        )


def test_vitals():
    """Тестирование витальных показателей"""
    print("\n" + "=" * 60)
    print("❤️ TESTING VITALS")
    print("=" * 60)

    token = get_token("citizen@docshare.uz", "Citizen123")
    if not token:
        result.add("Vitals: No token", False, "No token")
        return

    # 1. Создание vitals
    vitals_data = {
        "hr_bpm": random_int(60, 100),
        "bp_sys": random_int(110, 140),
        "bp_dia": random_int(70, 90),
        "spo2": random_int(95, 100),
        "weight": random_float(60, 90),
        "temperature": random_float(36.0, 37.2),
        "fasting_glucose": random_int(70, 100),
        "steps": random_int(5000, 15000),
        "distance_km": random_float(3, 10),
        "calories": random_int(300, 800),
        "notes": f"Test measurement {datetime.now()}"
    }

    resp = requests.post(
        f"{BASE_URL}/vitals/",
        headers=get_headers(token),
        json=vitals_data,
        timeout=5
    )
    result.add(
        "Vitals: Create",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )

    # 2. Получение истории
    resp = requests.get(
        f"{BASE_URL}/vitals/",
        headers=get_headers(token),
        timeout=5
    )
    result.add(
        "Vitals: Get history",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )

    # 3. Получение latest
    resp = requests.get(
        f"{BASE_URL}/vitals/latest",
        headers=get_headers(token),
        timeout=5
    )
    result.add(
        "Vitals: Get latest",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )

    # 4. Получение summary
    resp = requests.get(
        f"{BASE_URL}/vitals/summary",
        headers=get_headers(token),
        timeout=5
    )
    result.add(
        "Vitals: Get summary",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )


def test_appointments():
    """Тестирование записей к врачу"""
    print("\n" + "=" * 60)
    print("📅 TESTING APPOINTMENTS")
    print("=" * 60)

    token = get_token("citizen@docshare.uz", "Citizen123")
    if not token:
        result.add("Appointments: No token", False, "No token")
        return

    # 1. Получение списка врачей
    resp = requests.get(
        f"{BASE_URL}/doctors",
        headers=get_headers(token),
        timeout=5
    )
    result.add(
        "Appointments: Get doctors list",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )

    doctors = resp.json() if resp.status_code == 200 else []
    if not doctors:
        result.add("Appointments: No doctors available", False, "Doctor list empty", skipped=True)
        return

    doctor_id = doctors[0].get("id")

    # 2. Создание записи
    appointment_data = {
        "doctor_id": doctor_id,
        "date": random_date(14),
        "time": random_time(),
        "reason": "Regular checkup",
        "type": random.choice(["in_person", "video"])
    }

    resp = requests.post(
        f"{BASE_URL}/appointments/",
        headers=get_headers(token),
        json=appointment_data,
        timeout=5
    )
    result.add(
        "Appointments: Create",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )

    if resp.status_code == 200:
        apt_id = resp.json().get("id")

        # 3. Получение деталей
        resp = requests.get(
            f"{BASE_URL}/appointments/{apt_id}",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            "Appointments: Get details",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )

        # 4. Получение списка
        resp = requests.get(
            f"{BASE_URL}/appointments/",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            "Appointments: Get list",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )

        # 5. Отмена
        resp = requests.delete(
            f"{BASE_URL}/appointments/{apt_id}",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            "Appointments: Cancel",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )


def test_family():
    """Тестирование семейных отношений"""
    print("\n" + "=" * 60)
    print("👨‍👩‍👧‍👦 TESTING FAMILY")
    print("=" * 60)

    token = get_token("citizen@docshare.uz", "Citizen123")
    if not token:
        result.add("Family: No token", False, "No token")
        return

    # 1. Создание члена семьи
    family_data = {
        "name": f"Test Member {random_string(5)}",
        "relation": random.choice(["wife", "husband", "son", "daughter", "father", "mother", "other"]),
        "date_of_birth": "1990-01-01",
        "gender": random.choice(["male", "female"]),
        "blood_type": random.choice(["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]),
        "allergies": ["Pollen", "Dust"] if random.choice([True, False]) else [],
        "chronic_conditions": [],
        "health_status": random.choice(["good", "attention", "critical"])
    }

    resp = requests.post(
        f"{BASE_URL}/family",
        headers=get_headers(token),
        json=family_data,
        timeout=5
    )
    result.add(
        "Family: Add member",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )

    if resp.status_code == 200:
        member_id = resp.json().get("id")

        # 2. Получение списка
        resp = requests.get(
            f"{BASE_URL}/family",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            "Family: Get list",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )

        # 3. Получение деталей
        resp = requests.get(
            f"{BASE_URL}/family/{member_id}",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            "Family: Get details",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )

        # 4. Обновление
        resp = requests.patch(
            f"{BASE_URL}/family/{member_id}",
            headers=get_headers(token),
            json={"health_status": "good"},
            timeout=5
        )
        result.add(
            "Family: Update",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )

        # 5. Summary
        resp = requests.get(
            f"{BASE_URL}/family/summary",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            "Family: Get summary",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )

        # 6. Удаление
        resp = requests.delete(
            f"{BASE_URL}/family/{member_id}",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            "Family: Delete",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )


def test_activities():
    """Тестирование активности"""
    print("\n" + "=" * 60)
    print("🏃 TESTING ACTIVITIES")
    print("=" * 60)

    token = get_token("citizen@docshare.uz", "Citizen123")
    if not token:
        result.add("Activities: No token", False, "No token")
        return

    # 1. Получение статистики
    resp = requests.get(
        f"{BASE_URL}/activity/stats",
        headers=get_headers(token),
        timeout=5
    )
    result.add(
        "Activities: Get stats",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )

    # 2. Создание активности
    activity_data = {
        "title": f"Test Activity {random_string(5)}",
        "description": "Test description",
        "category": random.choice(["exercise", "meditation", "sleep", "nutrition"]),
        "duration_minutes": random_int(10, 60)
    }

    resp = requests.post(
        f"{BASE_URL}/activities",
        headers=get_headers(token),
        json=activity_data,
        timeout=5
    )
    result.add(
        "Activities: Create",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )

    if resp.status_code == 200:
        activity_id = resp.json().get("id")

        # 3. Получение списка
        resp = requests.get(
            f"{BASE_URL}/activities",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            "Activities: Get list",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )

        # 4. Toggle
        resp = requests.post(
            f"{BASE_URL}/activities/{activity_id}/toggle",
            headers=get_headers(token),
            json={"completed": True},
            timeout=5
        )
        result.add(
            "Activities: Toggle complete",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )


def test_documents():
    """Тестирование документов"""
    print("\n" + "=" * 60)
    print("📄 TESTING DOCUMENTS")
    print("=" * 60)

    token = get_token("citizen@docshare.uz", "Citizen123")
    if not token:
        result.add("Documents: No token", False, "No token")
        return

    # 1. Создание документа
    doc_data = {
        "title": f"Test Document {random_string(5)}",
        "type": random.choice(["report", "prescription", "lab_result", "imaging", "other"]),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "doctor_name": "Dr. Test",
        "hospital": "Test Hospital",
        "diagnosis": "Test diagnosis",
        "treatment": "Test treatment",
        "notes": "Test notes"
    }

    resp = requests.post(
        f"{BASE_URL}/documents",
        headers=get_headers(token),
        json=doc_data,
        timeout=5
    )
    result.add(
        "Documents: Create",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )

    if resp.status_code == 200:
        doc_id = resp.json().get("id")

        # 2. Получение документа
        resp = requests.get(
            f"{BASE_URL}/documents/{doc_id}",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            "Documents: Get details",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )

        # 3. Получение списка
        resp = requests.get(
            f"{BASE_URL}/documents",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            "Documents: Get list",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )

        # 4. Обновление
        resp = requests.patch(
            f"{BASE_URL}/documents/{doc_id}",
            headers=get_headers(token),
            json={"title": f"Updated {random_string(5)}"},
            timeout=5
        )
        result.add(
            "Documents: Update",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )

        # 5. Удаление
        resp = requests.delete(
            f"{BASE_URL}/documents/{doc_id}",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            "Documents: Delete",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )


def test_doctor():
    """Тестирование доктор-панели"""
    print("\n" + "=" * 60)
    print("🩺 TESTING DOCTOR PANEL")
    print("=" * 60)

    token = get_token("doctor@docshare.uz", "Doctor123")
    if not token:
        result.add("Doctor: No token", False, "No token")
        return

    endpoints = [
        ("/doctor/schedule", "Get schedule"),
        ("/doctor/requests", "Get requests"),
        ("/doctor/stats", "Get stats"),
        ("/doctor/ratings", "Get ratings"),
        ("/doctor/reviews", "Get reviews"),
        ("/doctor/history", "Get history"),
        ("/doctor/demand-map", "Get demand map"),
    ]

    for path, name in endpoints:
        resp = requests.get(
            f"{BASE_URL}{path}",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            f"Doctor: {name}",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )

    # Негативный тест: доступ к админке
    resp = requests.get(
        f"{BASE_URL}/admin/metrics",
        headers=get_headers(token),
        timeout=5
    )
    result.add(
        "Doctor: Access admin (should fail)",
        resp.status_code == 403,
        f"Status {resp.status_code} (expected 403)"
    )


def test_admin():
    """Тестирование админ-панели"""
    print("\n" + "=" * 60)
    print("👑 TESTING ADMIN PANEL")
    print("=" * 60)

    token = get_token("admin@docshare.uz", "Admin123")
    if not token:
        result.add("Admin: No token", False, "No token")
        return

    endpoints = [
        ("/admin/metrics", "Get metrics"),
        ("/admin/alerts", "Get alerts"),
        ("/admin/regions", "Get regions"),
        ("/admin/statistics", "Get statistics"),
        ("/admin/hospitals", "Get hospitals"),
        ("/admin/doctors", "Get doctors"),
        ("/admin/audit-logs", "Get audit logs"),
    ]

    for path, name in endpoints:
        resp = requests.get(
            f"{BASE_URL}{path}",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            f"Admin: {name}",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )


def test_notifications():
    """Тестирование уведомлений"""
    print("\n" + "=" * 60)
    print("🔔 TESTING NOTIFICATIONS")
    print("=" * 60)

    token = get_token("citizen@docshare.uz", "Citizen123")
    if not token:
        result.add("Notifications: No token", False, "No token")
        return

    # 1. Получение списка
    resp = requests.get(
        f"{BASE_URL}/notifications",
        headers=get_headers(token),
        timeout=5
    )
    result.add(
        "Notifications: Get list",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )

    # 2. Unread count
    resp = requests.get(
        f"{BASE_URL}/notifications/unread-count",
        headers=get_headers(token),
        timeout=5
    )
    result.add(
        "Notifications: Get unread count",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )

    # 3. Push token
    resp = requests.post(
        f"{BASE_URL}/devices/push-token",
        headers=get_headers(token),
        json={
            "token": f"push_token_{random_string(20)}",
            "platform": random.choice(["android", "ios"])
        },
        timeout=5
    )
    result.add(
        "Notifications: Register push token",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )


def test_symptoms():
    """Тестирование симптомов"""
    print("\n" + "=" * 60)
    print("🩺 TESTING SYMPTOMS")
    print("=" * 60)

    token = get_token("citizen@docshare.uz", "Citizen123")
    if not token:
        result.add("Symptoms: No token", False, "No token")
        return

    # 1. Категории
    resp = requests.get(
        f"{BASE_URL}/symptoms/categories",
        headers=get_headers(token),
        timeout=5
    )
    result.add(
        "Symptoms: Get categories",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )

    # 2. Симптомы
    resp = requests.get(
        f"{BASE_URL}/symptoms",
        headers=get_headers(token),
        timeout=5
    )
    result.add(
        "Symptoms: Get symptoms",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )

    # 3. Проверка
    resp = requests.post(
        f"{BASE_URL}/symptoms/check",
        headers=get_headers(token),
        json={
            "symptom_id": "1",
            "answers": [
                {"question_id": "q1", "option_id": "a"},
                {"question_id": "q2", "option_id": "b"}
            ]
        },
        timeout=5
    )
    result.add(
        "Symptoms: Check",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )


def test_environment():
    """Тестирование AQI"""
    print("\n" + "=" * 60)
    print("🌍 TESTING ENVIRONMENT")
    print("=" * 60)

    token = get_token("citizen@docshare.uz", "Citizen123")
    if not token:
        result.add("Environment: No token", False, "No token")
        return

    for region in ["Tashkent", "Samarkand", "Bukhara"]:
        resp = requests.get(
            f"{BASE_URL}/environment/aqi",
            headers=get_headers(token),
            params={"region": region},
            timeout=5
        )
        result.add(
            f"Environment: AQI {region}",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )


def test_devices():
    """Тестирование устройств"""
    print("\n" + "=" * 60)
    print("📱 TESTING DEVICES")
    print("=" * 60)

    token = get_token("citizen@docshare.uz", "Citizen123")
    if not token:
        result.add("Devices: No token", False, "No token")
        return

    # 1. Регистрация
    device_data = {
        "name": f"Test Device {random_string(5)}",
        "type": random.choice(["smartwatch", "fitness_band", "blood_pressure_monitor"]),
        "mac": f"{random_string(2)}:{random_string(2)}:{random_string(2)}:{random_string(2)}:{random_string(2)}:{random_string(2)}"
    }

    resp = requests.post(
        f"{BASE_URL}/devices",
        headers=get_headers(token),
        json=device_data,
        timeout=5
    )
    result.add(
        "Devices: Register",
        resp.status_code == 200,
        f"Status {resp.status_code}"
    )

    if resp.status_code == 200:
        device_id = resp.json().get("id")

        # 2. Синхронизация
        resp = requests.post(
            f"{BASE_URL}/devices/{device_id}/sync",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            "Devices: Sync",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )

        # 3. Получение списка
        resp = requests.get(
            f"{BASE_URL}/devices",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            "Devices: Get list",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )

        # 4. Отключение
        resp = requests.delete(
            f"{BASE_URL}/devices/{device_id}",
            headers=get_headers(token),
            timeout=5
        )
        result.add(
            "Devices: Disconnect",
            resp.status_code == 200,
            f"Status {resp.status_code}"
        )


def test_edge_cases():
    """Тестирование крайних случаев"""
    print("\n" + "=" * 60)
    print("🔬 EDGE CASES")
    print("=" * 60)

    token = get_token("citizen@docshare.uz", "Citizen123")
    if not token:
        result.add("Edge: No token", False, "No token")
        return

    # 1. Очень длинная строка
    long_str = "a" * 500
    resp = requests.post(
        f"{BASE_URL}/family",
        headers=get_headers(token),
        json={"name": long_str, "relation": "other"},
        timeout=5
    )
    result.add(
        "Edge: Very long string",
        resp.status_code in [200, 422],
        f"Status {resp.status_code}"
    )

    # 2. Отрицательные числа
    resp = requests.post(
        f"{BASE_URL}/vitals/",
        headers=get_headers(token),
        json={"hr_bpm": -10, "bp_sys": -20, "bp_dia": -15},
        timeout=5
    )
    result.add(
        "Edge: Negative numbers",
        resp.status_code in [200, 422],
        f"Status {resp.status_code}"
    )

    # 3. Пустые значения
    resp = requests.post(
        f"{BASE_URL}/family",
        headers=get_headers(token),
        json={"name": "", "relation": ""},
        timeout=5
    )
    result.add(
        "Edge: Empty strings",
        resp.status_code == 422,
        f"Status {resp.status_code} (expected 422)"
    )

    # 4. Доступ без токена
    resp = requests.get(f"{BASE_URL}/auth/me", timeout=5)
    result.add(
        "Edge: No token (should fail)",
        resp.status_code == 401,
        f"Status {resp.status_code} (expected 401)"
    )


def test_performance():
    """Базовый тест производительности"""
    print("\n" + "=" * 60)
    print("⚡ PERFORMANCE")
    print("=" * 60)

    token = get_token("citizen@docshare.uz", "Citizen123")
    if not token:
        result.add("Performance: No token", False, "No token")
        return

    start = time.time()
    resp = requests.get(
        f"{BASE_URL}/dashboard",
        headers=get_headers(token),
        timeout=10
    )
    elapsed = time.time() - start

    result.add(
        f"Performance: Dashboard {elapsed:.3f}s",
        elapsed < 2.0,
        f"{elapsed:.3f}s {'✅' if elapsed < 2.0 else '⚠️'}"
    )


# ============ MAIN ============

def main():
    print("=" * 60)
    print("🧪 DOCSHARE API — FULL TEST SUITE")
    print("=" * 60)
    print(f"🔗 Base URL: {BASE_URL}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Проверка доступности
    try:
        resp = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        if resp.status_code != 200:
            print("❌ Server is not responding!")
            return
        print("✅ Server is running\n")
    except:
        print("❌ Cannot connect to server!")
        return

    test_auth()
    test_dashboard()
    test_vitals()
    test_appointments()
    test_family()
    test_activities()
    test_documents()
    test_doctor()
    test_admin()
    test_notifications()
    test_symptoms()
    test_environment()
    test_devices()
    test_edge_cases()
    test_performance()

    result.summary()

    if result.failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n❌ {result.failed} tests failed. Check output above.")


if __name__ == "__main__":
    main()
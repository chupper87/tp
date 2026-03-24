"""Seed the database with an admin user and realistic test data.

Usage:
    uv run python seed.py
"""

import asyncio
import sys

# src/ contains the backend modules — add it to path before importing
sys.path.insert(0, "src")

from database import _get_database_session  # noqa: E402
from idp.email_and_password.repo import get_user_by_email, hash_password  # noqa: E402
from models import User, Employee, Customer, Measure, CustomerMeasure  # noqa: E402
from sqlalchemy import select, func  # noqa: E402

ADMIN_EMAIL = "admin@timepiece.se"
ADMIN_PASSWORD = "admin123"

EMPLOYEES = [
    {
        "first_name": "Anna",
        "last_name": "Svensson",
        "role": "assistant_nurse",
        "employment_type": "full_time",
        "phone": "070-123 45 01",
        "weekly_hours": 40.0,
        "gender": "female",
    },
    {
        "first_name": "Erik",
        "last_name": "Lindqvist",
        "role": "care_assistant",
        "employment_type": "full_time",
        "phone": "070-123 45 02",
        "weekly_hours": 40.0,
        "gender": "male",
    },
    {
        "first_name": "Fatima",
        "last_name": "Al-Hassan",
        "role": "assistant_nurse",
        "employment_type": "full_time",
        "phone": "070-123 45 03",
        "weekly_hours": 40.0,
        "gender": "female",
    },
    {
        "first_name": "Johan",
        "last_name": "Karlsson",
        "role": "care_assistant",
        "employment_type": "part_time",
        "phone": "070-123 45 04",
        "weekly_hours": 30.0,
        "gender": "male",
    },
    {
        "first_name": "Maria",
        "last_name": "Björk",
        "role": "assistant_nurse",
        "employment_type": "full_time",
        "phone": "070-123 45 05",
        "weekly_hours": 40.0,
        "gender": "female",
    },
    {
        "first_name": "Oscar",
        "last_name": "Nilsson",
        "role": "care_assistant",
        "employment_type": "on_call",
        "phone": "070-123 45 06",
        "weekly_hours": 20.0,
        "gender": "male",
    },
    {
        "first_name": "Sofia",
        "last_name": "Ekström",
        "role": "assistant_nurse",
        "employment_type": "part_time",
        "phone": "070-123 45 07",
        "weekly_hours": 30.0,
        "gender": "female",
    },
    {
        "first_name": "Ahmed",
        "last_name": "Ibrahim",
        "role": "care_assistant",
        "employment_type": "full_time",
        "phone": "070-123 45 08",
        "weekly_hours": 40.0,
        "gender": "male",
    },
]

CUSTOMERS = [
    {
        "first_name": "Margit",
        "last_name": "Björk",
        "key_number": 1001,
        "address": "Storgatan 12, Lgh 3",
        "care_level": "high",
        "approved_hours": 60.0,
        "gender": "female",
    },
    {
        "first_name": "Sven",
        "last_name": "Andersson",
        "key_number": 1002,
        "address": "Parkvägen 8B",
        "care_level": "medium",
        "approved_hours": 40.0,
        "gender": "male",
    },
    {
        "first_name": "Birgitta",
        "last_name": "Holm",
        "key_number": 1003,
        "address": "Björkgatan 3, Lgh 1",
        "care_level": "high",
        "approved_hours": 55.0,
        "gender": "female",
    },
    {
        "first_name": "Gösta",
        "last_name": "Pettersson",
        "key_number": 1004,
        "address": "Eklundavägen 15",
        "care_level": "low",
        "approved_hours": 20.0,
        "gender": "male",
    },
    {
        "first_name": "Astrid",
        "last_name": "Lundgren",
        "key_number": 1005,
        "address": "Vasagatan 22, Lgh 4",
        "care_level": "medium",
        "approved_hours": 35.0,
        "gender": "female",
    },
    {
        "first_name": "Karl-Erik",
        "last_name": "Johansson",
        "key_number": 1006,
        "address": "Nygatan 7",
        "care_level": "high",
        "approved_hours": 65.0,
        "gender": "male",
    },
]

MEASURES = [
    {
        "name": "Dusch",
        "default_duration": 20,
        "description": "Helkroppsdusch med assistans",
        "time_of_day": "morning",
        "is_standard": True,
    },
    {
        "name": "Frukost",
        "default_duration": 15,
        "description": "Förberedelse och servering av frukost",
        "time_of_day": "morning",
        "is_standard": True,
    },
    {
        "name": "Lunch",
        "default_duration": 20,
        "description": "Uppvärmning och servering av lunch",
        "time_of_day": "midday",
        "is_standard": True,
    },
    {
        "name": "Middag",
        "default_duration": 20,
        "description": "Förberedelse och servering av middag",
        "time_of_day": "evening",
        "is_standard": True,
    },
    {
        "name": "Kvällsmat",
        "default_duration": 15,
        "description": "Enklare kvällsmål",
        "time_of_day": "evening",
        "is_standard": True,
    },
    {
        "name": "Medicin morgon",
        "default_duration": 10,
        "description": "Utdelning av ordinerad morgonmedicin",
        "time_of_day": "morning",
        "is_standard": True,
    },
    {
        "name": "Medicin kväll",
        "default_duration": 10,
        "description": "Utdelning av ordinerad kvällsmedicin",
        "time_of_day": "evening",
        "is_standard": True,
    },
    {
        "name": "Tillsyn",
        "default_duration": 10,
        "description": "Kontroll av mående och situation",
        "is_standard": True,
    },
    {
        "name": "Städning",
        "default_duration": 45,
        "description": "Dammsugning, avtorkning, badrum",
        "is_standard": False,
    },
    {
        "name": "Tvätt",
        "default_duration": 30,
        "description": "Maskintvätt, torkning, vikt",
        "is_standard": False,
    },
    {
        "name": "Promenad",
        "default_duration": 30,
        "description": "Utevistelse med assistans",
        "time_of_day": "afternoon",
        "is_standard": False,
    },
    {
        "name": "Toalettbesök",
        "default_duration": 10,
        "description": "Assistans vid toalettbesök",
        "is_standard": True,
    },
    {
        "name": "Sänggående",
        "default_duration": 15,
        "description": "Hjälp att klä av sig och lägga sig",
        "time_of_day": "evening",
        "is_standard": True,
    },
    {
        "name": "Uppstigning",
        "default_duration": 15,
        "description": "Hjälp att stiga upp och klä på sig",
        "time_of_day": "morning",
        "is_standard": True,
    },
]


# Care plans: customer last_name → list of measure assignments
# Each entry: (measure_name, frequency, days_of_week, occurrences_per_week,
#               customer_duration, time_of_day)
CARE_PLANS: dict[str, list[tuple]] = {
    "Björk": [  # Margit — high care
        ("Dusch", "daily", None, None, None, "morning"),
        ("Frukost", "daily", None, None, None, "morning"),
        ("Medicin morgon", "daily", None, None, None, "morning"),
        ("Uppstigning", "daily", None, None, None, "morning"),
        ("Tillsyn", "daily", None, None, 10, None),
        ("Lunch", "daily", None, None, None, "midday"),
        ("Sänggående", "daily", None, None, None, "evening"),
        ("Medicin kväll", "daily", None, None, None, "evening"),
    ],
    "Andersson": [  # Sven — medium care
        ("Lunch", "daily", None, None, None, "midday"),
        ("Medicin kväll", "daily", None, None, None, "evening"),
        ("Tillsyn", "daily", None, None, 10, None),
        ("Dusch", "weekly", ["monday", "wednesday", "friday"], 3, None, "morning"),
    ],
    "Holm": [  # Birgitta — high care
        ("Dusch", "daily", None, None, None, "morning"),
        ("Frukost", "daily", None, None, None, "morning"),
        ("Uppstigning", "daily", None, None, None, "morning"),
        ("Sänggående", "daily", None, None, None, "evening"),
        ("Städning", "weekly", ["thursday"], 1, None, None),
        ("Tvätt", "weekly", ["monday"], 1, None, None),
    ],
    "Pettersson": [  # Gösta — low care
        ("Tillsyn", "daily", None, None, 10, None),
        ("Promenad", "weekly", ["tuesday", "thursday"], 2, None, "afternoon"),
    ],
    "Lundgren": [  # Astrid — medium care
        ("Frukost", "daily", None, None, None, "morning"),
        ("Medicin morgon", "daily", None, None, None, "morning"),
        ("Lunch", "daily", None, None, None, "midday"),
        ("Kvällsmat", "daily", None, None, None, "evening"),
        ("Tillsyn", "weekly", None, 3, 10, None),
    ],
    "Johansson": [  # Karl-Erik — high care
        ("Dusch", "daily", None, None, 25, "morning"),
        ("Frukost", "daily", None, None, None, "morning"),
        ("Uppstigning", "daily", None, None, 20, "morning"),
        ("Lunch", "daily", None, None, None, "midday"),
        ("Middag", "daily", None, None, None, "evening"),
        ("Sänggående", "daily", None, None, 20, "evening"),
        ("Medicin morgon", "daily", None, None, None, "morning"),
        ("Medicin kväll", "daily", None, None, None, "evening"),
        ("Toalettbesök", "daily", None, None, None, None),
    ],
}


async def seed():
    db = _get_database_session()
    try:
        # --- Admin user ---
        existing = await get_user_by_email(db, ADMIN_EMAIL)
        if existing:
            print(f"Admin user already exists: {ADMIN_EMAIL}")
        else:
            user = User(
                email=ADMIN_EMAIL,
                hashed_password=hash_password(ADMIN_PASSWORD),
                is_admin=True,
                is_active=True,
            )
            db.add(user)
            await db.commit()
            print(f"Created admin user: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")

        # --- Employees ---
        emp_count = (
            await db.execute(select(func.count()).select_from(Employee))
        ).scalar() or 0
        if emp_count > 0:
            print(f"Employees already seeded ({emp_count} found)")
        else:
            for emp_data in EMPLOYEES:
                first = emp_data["first_name"].lower()
                last = emp_data["last_name"].lower()
                email = f"{first}.{last}@timepiece.se"
                user = User(
                    email=email,
                    hashed_password=hash_password("password123"),
                    is_admin=False,
                    is_active=True,
                )
                db.add(user)
                await db.flush()

                employee = Employee(
                    user_id=user.id,
                    first_name=emp_data["first_name"],
                    last_name=emp_data["last_name"],
                    role=emp_data.get("role"),
                    employment_type=emp_data.get("employment_type"),
                    phone=emp_data.get("phone"),
                    weekly_hours=emp_data.get("weekly_hours"),
                    gender=emp_data.get("gender"),
                    is_active=True,
                )
                db.add(employee)

            await db.commit()
            print(f"Created {len(EMPLOYEES)} employees")

        # --- Customers ---
        cust_count = (
            await db.execute(select(func.count()).select_from(Customer))
        ).scalar() or 0
        if cust_count > 0:
            print(f"Customers already seeded ({cust_count} found)")
        else:
            for cust_data in CUSTOMERS:
                customer = Customer(**cust_data, is_active=True)
                db.add(customer)

            await db.commit()
            print(f"Created {len(CUSTOMERS)} customers")

        # --- Measures ---
        meas_count = (
            await db.execute(select(func.count()).select_from(Measure))
        ).scalar() or 0
        if meas_count > 0:
            print(f"Measures already seeded ({meas_count} found)")
        else:
            for meas_data in MEASURES:
                measure = Measure(**meas_data, is_active=True)
                db.add(measure)

            await db.commit()
            print(f"Created {len(MEASURES)} measures")

        # --- Customer Care Plans ---
        cm_count = (
            await db.execute(select(func.count()).select_from(CustomerMeasure))
        ).scalar() or 0
        if cm_count > 0:
            print(f"Care plans already seeded ({cm_count} found)")
        else:
            # Build lookup maps
            customers_result = await db.execute(select(Customer))
            customer_map = {c.last_name: c for c in customers_result.scalars().all()}
            measures_result = await db.execute(select(Measure))
            measure_map = {m.name: m for m in measures_result.scalars().all()}

            created_count = 0
            for last_name, plans in CARE_PLANS.items():
                customer = customer_map.get(last_name)
                if not customer:
                    print(f"  Warning: customer '{last_name}' not found, skipping")
                    continue

                for plan in plans:
                    (
                        measure_name,
                        frequency,
                        days_of_week,
                        occurrences_per_week,
                        customer_duration,
                        time_of_day,
                    ) = plan
                    measure = measure_map.get(measure_name)
                    if not measure:
                        print(f"  Warning: measure '{measure_name}' not found, skipping")
                        continue

                    cm = CustomerMeasure(
                        customer_id=customer.id,
                        measure_id=measure.id,
                        frequency=frequency,
                        days_of_week=days_of_week,
                        occurrences_per_week=occurrences_per_week,
                        customer_duration=customer_duration,
                        time_of_day=time_of_day,
                    )
                    db.add(cm)
                    created_count += 1

            await db.commit()
            print(f"Created {created_count} care plan entries")

        print("\nSeed complete! You can now log in and test the schedule planner.")

    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(seed())

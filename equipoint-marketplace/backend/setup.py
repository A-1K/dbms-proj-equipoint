"""
setup.py  -  Run this FIRST before anything else.

What it does:
  1. Creates all database tables via db.create_all()
     (PostgreSQL ENUMs are created automatically before tables)
  2. Installs the avg_rating trigger
  3. Seeds 15 Pakistani universities
  4. Creates a default admin account

Prerequisites:
  - PostgreSQL server running
  - Database 'uni_marketplace' created:
        CREATE DATABASE uni_marketplace;
  - DATABASE_URL set in .env (or defaults to localhost postgres)

Usage:
    cd backend
    python setup.py
"""

from app import create_app
from models import db, University, User, create_triggers


UNIVERSITIES = [
    {"name": "LUMS",                    "city": "Lahore",     "province": "Punjab",  "hec_status": "Recognized"},
    {"name": "NUST",                    "city": "Islamabad",  "province": "ICT",     "hec_status": "Recognized"},
    {"name": "FAST NUCES",              "city": "Karachi",    "province": "Sindh",   "hec_status": "Recognized"},
    {"name": "IBA Karachi",             "city": "Karachi",    "province": "Sindh",   "hec_status": "Recognized"},
    {"name": "UET Lahore",              "city": "Lahore",     "province": "Punjab",  "hec_status": "Recognized"},
    {"name": "COMSATS University",      "city": "Islamabad",  "province": "ICT",     "hec_status": "Recognized"},
    {"name": "University of Karachi",   "city": "Karachi",    "province": "Sindh",   "hec_status": "Recognized"},
    {"name": "Punjab University",       "city": "Lahore",     "province": "Punjab",  "hec_status": "Recognized"},
    {"name": "Quaid-i-Azam University", "city": "Islamabad",  "province": "ICT",     "hec_status": "Recognized"},
    {"name": "GIKI",                    "city": "Topi",       "province": "KPK",     "hec_status": "Recognized"},
    {"name": "Air University",          "city": "Islamabad",  "province": "ICT",     "hec_status": "Recognized"},
    {"name": "NED University",          "city": "Karachi",    "province": "Sindh",   "hec_status": "Recognized"},
    {"name": "UET Peshawar",            "city": "Peshawar",   "province": "KPK",     "hec_status": "Recognized"},
    {"name": "Bahria University",       "city": "Islamabad",  "province": "ICT",     "hec_status": "Recognized"},
    {"name": "ITU Lahore",              "city": "Lahore",     "province": "Punjab",  "hec_status": "Recognized"},
]


def setup():
    app = create_app()
    with app.app_context():

        print("Creating all tables and PostgreSQL ENUM types...")
        db.create_all()
        print("Tables created.\n")

        print("Installing avg_rating trigger...")
        create_triggers(db.engine)
        print("Trigger installed.\n")

        # --- Universities ---
        added = 0
        for u in UNIVERSITIES:
            if not University.query.filter_by(name=u["name"]).first():
                db.session.add(University(**u))
                added += 1
        db.session.commit()
        total = University.query.count()
        print(f"Universities: added {added} new  ({total} total)\n")

        # --- Default admin account ---
        if not User.query.filter_by(email="admin@unimarket.pk").first():
            uni = University.query.first()
            admin = User(
                full_name="Admin User",
                email="admin@unimarket.pk",
                student_id="ADMIN-001",
                uni_affil=uni.uni_id,
                role="Admin",
                active_status="Active",
                phone="03001234567",
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print("Admin account created:")
            print("  Email   : admin@unimarket.pk")
            print("  Password: admin123\n")
        else:
            print("Admin account already exists.\n")

        print("Setup complete!  Now run:  python seed_50_products.py")
        print("Then start the server:     python app.py")


if __name__ == "__main__":
    setup()

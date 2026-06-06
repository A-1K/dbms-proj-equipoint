"""
seed_50_products.py  -  Run this AFTER setup.py.
Usage:
    cd backend
    python seed_50_products.py
"""
from app import create_app
from models import db, User, University, ItemRegistry, ItemImage, Electronics, Tools, Vehicles

PRODUCTS = [
    {"title": "Dell Laptop Core i5 8th Gen 8GB RAM", "category": "Electronics", "condition": "Good", "listing_type": "Both", "sale_price": 45000, "price_per_day": 500, "security_dep": 5000, "description": "Runs perfectly. Includes charger and bag. Battery lasts 4 hrs.", "specs": {"brand": "Dell", "voltage": "220V", "battery_type": "Li-ion", "wattage": "65W"}},
    {"title": "HP ProBook 450 G5 Core i7", "category": "Electronics", "condition": "Like New", "listing_type": "Buy", "sale_price": 65000, "price_per_day": 0, "security_dep": 0, "description": "Barely used. 16GB RAM, 512GB SSD. Original box included.", "specs": {"brand": "HP", "voltage": "220V", "battery_type": "Li-ion", "wattage": "65W"}},
    {"title": "Samsung Galaxy A53 5G", "category": "Electronics", "condition": "Like New", "listing_type": "Buy", "sale_price": 38000, "price_per_day": 0, "security_dep": 0, "description": "6 months old. 128GB storage. No scratches.", "specs": {"brand": "Samsung", "voltage": "5V", "battery_type": "Li-ion", "wattage": "25W"}},
    {"title": "Canon EOS 1500D DSLR Camera", "category": "Electronics", "condition": "Good", "listing_type": "Rent", "sale_price": 0, "price_per_day": 800, "security_dep": 10000, "description": "18-55mm kit lens included. Perfect for events or projects.", "specs": {"brand": "Canon", "voltage": "220V", "battery_type": "Li-ion", "wattage": "10W"}},
    {"title": "Scientific Calculator Casio FX-991EX", "category": "Electronics", "condition": "New", "listing_type": "Buy", "sale_price": 3500, "price_per_day": 0, "security_dep": 0, "description": "Brand new sealed. Perfect for engineering students.", "specs": {"brand": "Casio", "voltage": "3V", "battery_type": "AAA", "wattage": "0.5W"}},
    {"title": "Lenovo ThinkPad X1 Carbon Core i7", "category": "Electronics", "condition": "Good", "listing_type": "Both", "sale_price": 85000, "price_per_day": 900, "security_dep": 8000, "description": "Business laptop. Very fast, lightweight. 16GB RAM 256GB SSD.", "specs": {"brand": "Lenovo", "voltage": "220V", "battery_type": "Li-ion", "wattage": "65W"}},
    {"title": "JBL Bluetooth Speaker", "category": "Electronics", "condition": "Good", "listing_type": "Rent", "sale_price": 0, "price_per_day": 300, "security_dep": 3000, "description": "Loud and clear. Waterproof. 10 hr battery.", "specs": {"brand": "JBL", "voltage": "5V", "battery_type": "Li-ion", "wattage": "10W"}},
    {"title": "Logitech MX Master 3 Wireless Mouse", "category": "Electronics", "condition": "Like New", "listing_type": "Buy", "sale_price": 8500, "price_per_day": 0, "security_dep": 0, "description": "Only 3 months old. Comes with USB receiver.", "specs": {"brand": "Logitech", "voltage": "5V", "battery_type": "Li-ion", "wattage": "5W"}},
    {"title": "Xiaomi Redmi Note 12 Pro", "category": "Electronics", "condition": "New", "listing_type": "Buy", "sale_price": 42000, "price_per_day": 0, "security_dep": 0, "description": "Sealed box. 256GB. Selling for upgrade.", "specs": {"brand": "Xiaomi", "voltage": "5V", "battery_type": "Li-ion", "wattage": "67W"}},
    {"title": "24-inch BenQ Monitor Full HD IPS", "category": "Electronics", "condition": "Good", "listing_type": "Both", "sale_price": 22000, "price_per_day": 400, "security_dep": 3000, "description": "Perfect colours, 75Hz refresh rate. Great for design work.", "specs": {"brand": "BenQ", "voltage": "220V", "battery_type": "N/A", "wattage": "30W"}},
    {"title": "Bosch Power Drill 650W", "category": "Tools", "condition": "Good", "listing_type": "Rent", "sale_price": 0, "price_per_day": 400, "security_dep": 5000, "description": "Corded drill with full bit set. Good for FYP projects.", "specs": {"tool_type": "Power Drill", "power_source": "Electric", "weight_kg": 1.8}},
    {"title": "Soldering Iron Station 60W", "category": "Tools", "condition": "Good", "listing_type": "Both", "sale_price": 4500, "price_per_day": 200, "security_dep": 1000, "description": "Temperature controlled. Includes solder wire and stand.", "specs": {"tool_type": "Soldering Iron", "power_source": "Electric", "weight_kg": 0.5}},
    {"title": "Digital Multimeter Fluke 117", "category": "Tools", "condition": "Like New", "listing_type": "Both", "sale_price": 12000, "price_per_day": 250, "security_dep": 2000, "description": "True RMS multimeter. Perfect for electronics labs.", "specs": {"tool_type": "Multimeter", "power_source": "Battery", "weight_kg": 0.3}},
    {"title": "Oscilloscope 2-Channel 100MHz", "category": "Tools", "condition": "Good", "listing_type": "Rent", "sale_price": 0, "price_per_day": 700, "security_dep": 8000, "description": "Useful for signal analysis in FYP or lab work.", "specs": {"tool_type": "Oscilloscope", "power_source": "Electric", "weight_kg": 3.0}},
    {"title": "Hydraulic Jack 2 Ton", "category": "Tools", "condition": "Good", "listing_type": "Rent", "sale_price": 0, "price_per_day": 300, "security_dep": 3000, "description": "For car maintenance. Works well.", "specs": {"tool_type": "Hydraulic Jack", "power_source": "Manual", "weight_kg": 5.5}},
    {"title": "Hero Bicycle 26 inch 21-Speed", "category": "Vehicles", "condition": "Good", "listing_type": "Both", "sale_price": 12000, "price_per_day": 150, "security_dep": 2000, "description": "Good condition. Gears work perfectly. Comfortable seat.", "specs": {"frame_size": "26 inch", "gear_count": 21, "fuel_type": "N/A"}},
    {"title": "Honda CD70 2020 Model", "category": "Vehicles", "condition": "Good", "listing_type": "Both", "sale_price": 95000, "price_per_day": 800, "security_dep": 10000, "description": "Registered in Lahore. All documents clear. Good mileage.", "specs": {"frame_size": "Standard", "gear_count": 4, "fuel_type": "Petrol"}},
    {"title": "Electric Scooter Jolta JE70", "category": "Vehicles", "condition": "Like New", "listing_type": "Rent", "sale_price": 0, "price_per_day": 600, "security_dep": 5000, "description": "Zero emission. Range 60km per charge. Great for campus.", "specs": {"frame_size": "Standard", "gear_count": 1, "fuel_type": "Electric"}},
    {"title": "Mountain Bike Trinx 27.5 inch", "category": "Vehicles", "condition": "Good", "listing_type": "Both", "sale_price": 22000, "price_per_day": 200, "security_dep": 3000, "description": "Hydraulic brakes, front suspension. Lightly used.", "specs": {"frame_size": "27.5 inch", "gear_count": 21, "fuel_type": "N/A"}},
    {"title": "Introduction to Algorithms CLRS 4th Ed", "category": "Textbooks", "condition": "Good", "listing_type": "Both", "sale_price": 3500, "price_per_day": 50, "security_dep": 500, "description": "Classic algorithms textbook. Some highlighting but all readable.", "specs": {}},
    {"title": "Engineering Mathematics by Stroud", "category": "Textbooks", "condition": "Like New", "listing_type": "Buy", "sale_price": 2800, "price_per_day": 0, "security_dep": 0, "description": "7th edition. Minimal use. Great for first year.", "specs": {}},
    {"title": "Computer Networking Kurose Ross 8th Ed", "category": "Textbooks", "condition": "Good", "listing_type": "Both", "sale_price": 3200, "price_per_day": 40, "security_dep": 400, "description": "Very good condition. All chapters intact.", "specs": {}},
    {"title": "Calculus by Howard Anton 10th Ed", "category": "Textbooks", "condition": "Fair", "listing_type": "Buy", "sale_price": 1800, "price_per_day": 0, "security_dep": 0, "description": "Some pages marked but complete. Great for quick study.", "specs": {}},
    {"title": "Digital Logic Design Morris Mano", "category": "Textbooks", "condition": "Good", "listing_type": "Buy", "sale_price": 1500, "price_per_day": 0, "security_dep": 0, "description": "5th edition. Good condition.", "specs": {}},
    {"title": "Study Table with Bookshelf", "category": "Furniture", "condition": "Good", "listing_type": "Both", "sale_price": 8000, "price_per_day": 100, "security_dep": 1000, "description": "Wooden study table with attached 3-shelf bookcase. Sturdy.", "specs": {}},
    {"title": "Single Bed with Mattress", "category": "Furniture", "condition": "Good", "listing_type": "Both", "sale_price": 12000, "price_per_day": 150, "security_dep": 2000, "description": "Hostel-grade single bed. Clean foam mattress included.", "specs": {}},
    {"title": "Plastic Chair Set of 4", "category": "Furniture", "condition": "Good", "listing_type": "Buy", "sale_price": 3200, "price_per_day": 0, "security_dep": 0, "description": "4 white plastic chairs, stackable. Perfect for room or balcony.", "specs": {}},
    {"title": "Steel Almirah 2-door", "category": "Furniture", "condition": "Good", "listing_type": "Both", "sale_price": 9500, "price_per_day": 120, "security_dep": 1500, "description": "2-door steel wardrobe with lock. Rust-free.", "specs": {}},
    {"title": "University Hoodie LUMS XL", "category": "Clothing", "condition": "Like New", "listing_type": "Buy", "sale_price": 2500, "price_per_day": 0, "security_dep": 0, "description": "Official LUMS hoodie, worn twice. Navy blue XL.", "specs": {}},
    {"title": "Lab Coat White Medium", "category": "Clothing", "condition": "Like New", "listing_type": "Both", "sale_price": 1200, "price_per_day": 80, "security_dep": 300, "description": "Formal lab coat for chemistry labs. Washed and clean.", "specs": {}},
    {"title": "Winter Jacket Unisex Size L", "category": "Clothing", "condition": "Good", "listing_type": "Buy", "sale_price": 3500, "price_per_day": 0, "security_dep": 0, "description": "Warm puffer jacket, dark green. Good for cold Islamabad winters.", "specs": {}},
    {"title": "Cricket Bat CA Plus 15000", "category": "Sports", "condition": "Good", "listing_type": "Both", "sale_price": 7500, "price_per_day": 200, "security_dep": 1000, "description": "Full-size willow bat. Grip replaced recently.", "specs": {}},
    {"title": "Badminton Racket Yonex Pair", "category": "Sports", "condition": "Like New", "listing_type": "Both", "sale_price": 4500, "price_per_day": 150, "security_dep": 500, "description": "Pair of Yonex rackets with carry bag. Used only 3 times.", "specs": {}},
    {"title": "Football Size 5 Adidas", "category": "Sports", "condition": "Good", "listing_type": "Buy", "sale_price": 2200, "price_per_day": 0, "security_dep": 0, "description": "Match-quality football, some scuffs on surface.", "specs": {}},
    {"title": "Gym Dumbbell Set 20kg", "category": "Sports", "condition": "Good", "listing_type": "Both", "sale_price": 6000, "price_per_day": 100, "security_dep": 1000, "description": "2x10kg dumbbells, rubber-coated. Great for hostel workouts.", "specs": {}},
    {"title": "Staedtler Geometry Box Set", "category": "Stationery", "condition": "New", "listing_type": "Buy", "sale_price": 850, "price_per_day": 0, "security_dep": 0, "description": "Full set: compass, protractor, rulers, divider. Sealed.", "specs": {}},
    {"title": "A3 Drawing Board with T-Square", "category": "Stationery", "condition": "Good", "listing_type": "Both", "sale_price": 1800, "price_per_day": 60, "security_dep": 300, "description": "Wooden drawing board A3. Includes T-square and set squares.", "specs": {}},
    {"title": "Rotring Isograph Technical Pen Set", "category": "Stationery", "condition": "Like New", "listing_type": "Buy", "sale_price": 2200, "price_per_day": 0, "security_dep": 0, "description": "3-pen set 0.25/0.35/0.5mm. Barely used. For engineering drawing.", "specs": {}},
    {"title": "Microwave Oven Dawlance 20L", "category": "Food", "condition": "Good", "listing_type": "Both", "sale_price": 12000, "price_per_day": 200, "security_dep": 2000, "description": "Working perfectly. Moving out of hostel, selling cheap.", "specs": {}},
    {"title": "Electric Kettle 1.8L", "category": "Food", "condition": "Like New", "listing_type": "Buy", "sale_price": 2800, "price_per_day": 0, "security_dep": 0, "description": "Fast boiling, auto-shutoff. Used only 2 months.", "specs": {}},
    {"title": "Rice Cooker National 1.8L", "category": "Food", "condition": "Good", "listing_type": "Both", "sale_price": 3500, "price_per_day": 80, "security_dep": 500, "description": "Works great. Perfect for hostel cooking.", "specs": {}},
    {"title": "Python and Data Science Tutoring", "category": "Tutoring", "condition": "New", "listing_type": "Rent", "sale_price": 0, "price_per_day": 500, "security_dep": 0, "description": "CS final-year student offering Python, pandas, ML basics.", "specs": {}},
    {"title": "Math and Calculus Tutoring", "category": "Tutoring", "condition": "New", "listing_type": "Rent", "sale_price": 0, "price_per_day": 400, "security_dep": 0, "description": "Engineering student offering calculus, linear algebra, statistics.", "specs": {}},
    {"title": "English Writing and IELTS Prep", "category": "Tutoring", "condition": "New", "listing_type": "Rent", "sale_price": 0, "price_per_day": 350, "security_dep": 0, "description": "IELTS 8.0 scorer. Helping with essays, speaking, listening skills.", "specs": {}},
    {"title": "Shared Ride to Gulberg Daily", "category": "Transport", "condition": "New", "listing_type": "Rent", "sale_price": 0, "price_per_day": 200, "security_dep": 0, "description": "Going to Gulberg, Lahore daily 8am. 2 seats available.", "specs": {}},
    {"title": "Car Rental Honda City 2019", "category": "Transport", "condition": "Good", "listing_type": "Rent", "sale_price": 0, "price_per_day": 3500, "security_dep": 20000, "description": "Self-drive or with driver. Fuel not included. Documents verified.", "specs": {}},
    {"title": "Extension Cord 4-Socket 3m", "category": "Misc", "condition": "Good", "listing_type": "Buy", "sale_price": 800, "price_per_day": 0, "security_dep": 0, "description": "Heavy duty with surge protection. 3 meter cable.", "specs": {}},
    {"title": "USB-C Hub 7-in-1", "category": "Misc", "condition": "Like New", "listing_type": "Buy", "sale_price": 3200, "price_per_day": 0, "security_dep": 0, "description": "HDMI, USB-A x3, SD card, PD charging. Great for MacBooks.", "specs": {}},
    {"title": "Desk Lamp LED Rechargeable", "category": "Misc", "condition": "Good", "listing_type": "Both", "sale_price": 1800, "price_per_day": 50, "security_dep": 300, "description": "3 brightness levels, rechargeable via USB. No flicker.", "specs": {}},
    {"title": "Portable Projector Mini HD", "category": "Misc", "condition": "Good", "listing_type": "Rent", "sale_price": 0, "price_per_day": 600, "security_dep": 5000, "description": "720p mini projector. Great for presentations and movie nights.", "specs": {}},
]


def seed():
    app = create_app()
    with app.app_context():
        lums = University.query.filter_by(name="LUMS").first()
        nust = University.query.filter_by(name="NUST").first()
        if not lums or not nust:
            print("ERROR: Run setup.py first.")
            return
        u1 = User.query.filter_by(email="ali@lums.edu.pk").first()
        if not u1:
            u1 = User(full_name="Ali Hassan", email="ali@lums.edu.pk",
                      student_id="L-2021-001", uni_affil=lums.uni_id,
                      role="Student", active_status="Active", phone="03111234567")
            u1.set_password("demo123")
            db.session.add(u1)
        u2 = User.query.filter_by(email="sara@nust.edu.pk").first()
        if not u2:
            u2 = User(full_name="Sara Ahmed", email="sara@nust.edu.pk",
                      student_id="N-2022-042", uni_affil=nust.uni_id,
                      role="Student", active_status="Active", phone="03219876543")
            u2.set_password("demo123")
            db.session.add(u2)
        db.session.commit()
        u1 = User.query.filter_by(email="ali@lums.edu.pk").first()
        u2 = User.query.filter_by(email="sara@nust.edu.pk").first()
        added = 0
        for idx, p in enumerate(PRODUCTS):
            if ItemRegistry.query.filter_by(title=p["title"]).first():
                continue
            owner = u1 if idx % 2 == 0 else u2
            item = ItemRegistry(
                owner_id=owner.user_id, title=p["title"],
                description=p.get("description", ""), category=p["category"],
                condition=p["condition"], listing_type=p["listing_type"],
                price_per_day=float(p.get("price_per_day", 0)),
                sale_price=float(p.get("sale_price", 0)),
                security_dep=float(p.get("security_dep", 0)),
                location_uni=owner.uni_affil,
            )
            db.session.add(item)
            db.session.flush()
            s = p.get("specs", {})
            cat = p["category"]
            if cat == "Electronics":
                db.session.add(Electronics(item_id=item.item_id, brand=s.get("brand"),
                    voltage=s.get("voltage"), battery_type=s.get("battery_type"), wattage=s.get("wattage")))
            elif cat == "Tools":
                db.session.add(Tools(item_id=item.item_id, tool_type=s.get("tool_type"),
                    power_source=s.get("power_source"), weight_kg=s.get("weight_kg")))
            elif cat == "Vehicles":
                db.session.add(Vehicles(item_id=item.item_id, frame_size=s.get("frame_size"),
                    gear_count=s.get("gear_count"), fuel_type=s.get("fuel_type")))
            db.session.add(ItemImage(item_id=item.item_id,
                image_url="https://placehold.co/400x300/e5e7eb/9ca3af?text=No+Image", is_primary=True))
            added += 1
        db.session.commit()
        print(f"Products seeded: {added} new  ({ItemRegistry.query.count()} total)")
        print("Demo: ali@lums.edu.pk / demo123  |  sara@nust.edu.pk / demo123")
        print("Admin: admin@unimarket.pk / admin123")
        print("Start server: python app.py")


if __name__ == "__main__":
    seed()

"""
models.py — PostgreSQL-native schema for UniMarket Pakistan

Key changes from SQLite/generic SQLAlchemy:
  1. All ENUMs are declared as PostgreSQL native CREATE TYPE enums (not VARCHAR CHECK).
     This gives proper type safety at the DB level and shows up correctly in pg_catalog.
  2. DateTime columns use TIMESTAMPTZ (timestamp with time zone) via
     db.DateTime(timezone=True). SQLite silently ignored timezone; PostgreSQL
     stores it correctly.
  3. autoincrement PKs use SERIAL/BIGSERIAL implicitly through SQLAlchemy's
     Integer PK — PostgreSQL maps this to SERIAL (sequence-backed).
  4. avg_rating is kept as NUMERIC(3,2) — correct for PostgreSQL, same as before.
  5. A DB-level CHECK constraint is added on reviews.rating (1–5).
  6. A DB-level CHECK constraint guards price fields against negative values.
  7. The avg_rating update in routes/reviews.py (Python-side aggregation) is
     replaced here with a PostgreSQL TRIGGER + FUNCTION for atomicity.
     See the event.listen block at the bottom.
  8. String lengths are enforced — PostgreSQL actually enforces VARCHAR(n),
     unlike SQLite which ignores it.
"""

import os
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy import event, text, Index
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

db = SQLAlchemy()
bcrypt = Bcrypt()


def now():
    return datetime.now(timezone.utc)


# =====================================================================
# PostgreSQL Native ENUM Types
# Declared with create_type=True so SQLAlchemy issues
# CREATE TYPE ... AS ENUM (...) before CREATE TABLE.
# Using named types means the enum is reusable and inspectable.
# =====================================================================

hec_status_enum = PG_ENUM(
    'Recognized', 'Not Recognized', 'Pending',
    name='hec_status_enum', create_type=True
)
role_enum = PG_ENUM(
    'Student', 'Admin',
    name='role_enum', create_type=True
)
active_status_enum = PG_ENUM(
    'Active', 'Suspended', 'Banned',
    name='active_status_enum', create_type=True
)
category_enum = PG_ENUM(
    'Electronics', 'Tools', 'Vehicles', 'Textbooks', 'Furniture',
    'Clothing', 'Sports', 'Stationery', 'Food', 'Tutoring', 'Transport', 'Misc',
    name='category_enum', create_type=True
)
condition_enum = PG_ENUM(
    'New', 'Like New', 'Good', 'Fair', 'Poor',
    name='condition_enum', create_type=True
)
listing_type_enum = PG_ENUM(
    'Buy', 'Rent', 'Both',
    name='listing_type_enum', create_type=True
)
avail_status_enum = PG_ENUM(
    'Available', 'Rented', 'Sold',
    name='avail_status_enum', create_type=True
)
rental_status_enum = PG_ENUM(
    'Pending', 'Active', 'Completed', 'Cancelled',
    name='rental_status_enum', create_type=True
)
txn_type_enum = PG_ENUM(
    'Payment', 'Refund', 'Security Deposit',
    name='txn_type_enum', create_type=True
)
method_enum = PG_ENUM(
    'EasyPaisa', 'JazzCash', 'Bank Transfer', 'Cash',
    name='method_enum', create_type=True
)
txn_status_enum = PG_ENUM(
    'Pending', 'Completed', 'Failed',
    name='txn_status_enum', create_type=True
)
order_status_enum = PG_ENUM(
    'Pending', 'Confirmed', 'Completed', 'Cancelled',
    name='order_status_enum', create_type=True
)

# Keep Python-side tuples for any route-level validation that needs them
HEC_STATUS_ENUM    = ('Recognized', 'Not Recognized', 'Pending')
ROLE_ENUM          = ('Student', 'Admin')
ACTIVE_STATUS_ENUM = ('Active', 'Suspended', 'Banned')
CATEGORY_ENUM      = ('Electronics', 'Tools', 'Vehicles', 'Textbooks', 'Furniture',
                      'Clothing', 'Sports', 'Stationery', 'Food', 'Tutoring', 'Transport', 'Misc')
CONDITION_ENUM     = ('New', 'Like New', 'Good', 'Fair', 'Poor')
LISTING_TYPE_ENUM  = ('Buy', 'Rent', 'Both')
AVAIL_STATUS_ENUM  = ('Available', 'Rented', 'Sold')
RENTAL_STATUS_ENUM = ('Pending', 'Active', 'Completed', 'Cancelled')
TXN_TYPE_ENUM      = ('Payment', 'Refund', 'Security Deposit')
METHOD_ENUM        = ('EasyPaisa', 'JazzCash', 'Bank Transfer', 'Cash')
TXN_STATUS_ENUM    = ('Pending', 'Completed', 'Failed')
ORDER_STATUS_ENUM  = ('Pending', 'Confirmed', 'Completed', 'Cancelled')


# =====================================================================
# University_Registry
# =====================================================================
class University(db.Model):
    __tablename__ = 'university_registry'

    uni_id       = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name         = db.Column(db.String(100), unique=True, nullable=False)
    city         = db.Column(db.String(100), nullable=False)
    province     = db.Column(db.String(100), nullable=False)
    # PostgreSQL ENUM — enforced at DB level, not just application level
    hec_status   = db.Column(hec_status_enum, nullable=False, default='Recognized')
    active_users = db.Column(db.Integer, default=0)

    users = db.relationship('User', back_populates='university')
    items = db.relationship('ItemRegistry', back_populates='location')

    def to_dict(self):
        return {
            'uni_id': self.uni_id, 'name': self.name, 'city': self.city,
            'province': self.province, 'hec_status': self.hec_status,
            'active_users': self.active_users
        }


# =====================================================================
# Users
# =====================================================================
class User(db.Model):
    __tablename__ = 'users'

    user_id       = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name     = db.Column(db.String(150), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    student_id    = db.Column(db.String(50), unique=True, nullable=False)
    uni_affil     = db.Column(db.Integer, db.ForeignKey('university_registry.uni_id', ondelete='RESTRICT'), nullable=False)
    role          = db.Column(role_enum, nullable=False, default='Student')
    phone         = db.Column(db.String(20))
    avg_rating    = db.Column(db.Numeric(3, 2), default=0.0)
    active_status = db.Column(active_status_enum, nullable=False, default='Active')
    # TIMESTAMPTZ — PostgreSQL stores this with UTC offset. Always use timezone=True.
    created_at    = db.Column(db.DateTime(timezone=True), default=now)

    university  = db.relationship('University', back_populates='users')
    items_owned = db.relationship('ItemRegistry', foreign_keys='ItemRegistry.owner_id', back_populates='owner')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'user_id': self.user_id, 'full_name': self.full_name, 'email': self.email,
            'student_id': self.student_id, 'uni_affil': self.uni_affil, 'role': self.role,
            'phone': self.phone,
            'avg_rating': float(self.avg_rating) if self.avg_rating else 0.0,
            'active_status': self.active_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'university': self.university.to_dict() if self.university else None
        }


# =====================================================================
# Item_Registry (Superclass / parent table in EER)
# =====================================================================
class ItemRegistry(db.Model):
    __tablename__ = 'item_registry'

    # PostgreSQL table-level CHECK constraints for price integrity
    __table_args__ = (
        db.CheckConstraint('price_per_day >= 0', name='chk_price_per_day_positive'),
        db.CheckConstraint('sale_price >= 0',    name='chk_sale_price_positive'),
        db.CheckConstraint('security_dep >= 0',  name='chk_security_dep_positive'),
        # Performance indexes for common query patterns in list_items()
        Index('idx_item_title_lower', text('lower(title)')),   # case-insensitive ILIKE search
        Index('idx_item_category',    'category'),              # category filter
        Index('idx_item_avail_status','avail_status'),          # Available filter
        Index('idx_item_listed_at',   'listed_at'),             # ORDER BY listed_at DESC
    )

    item_id       = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id      = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    title         = db.Column(db.String(200), nullable=False)
    description   = db.Column(db.Text)
    category      = db.Column(category_enum, nullable=False)
    condition     = db.Column(condition_enum, nullable=False)
    listing_type  = db.Column(listing_type_enum, nullable=False)
    avail_status  = db.Column(avail_status_enum, nullable=False, default='Available')
    price_per_day = db.Column(db.Numeric(10, 2), default=0.0)
    sale_price    = db.Column(db.Numeric(10, 2), default=0.0)
    security_dep  = db.Column(db.Numeric(10, 2), default=0.0)
    location_uni  = db.Column(db.Integer, db.ForeignKey('university_registry.uni_id', ondelete='RESTRICT'), nullable=False)
    listed_at     = db.Column(db.DateTime(timezone=True), default=now)

    owner            = db.relationship('User', back_populates='items_owned')
    location         = db.relationship('University', back_populates='items')
    images           = db.relationship('ItemImage', back_populates='item', cascade='all, delete-orphan')
    rentals          = db.relationship('Rental', back_populates='item', cascade='all, delete-orphan')
    electronics_spec = db.relationship('Electronics', back_populates='item', uselist=False, cascade='all, delete-orphan')
    tools_spec       = db.relationship('Tools', back_populates='item', uselist=False, cascade='all, delete-orphan')
    vehicles_spec    = db.relationship('Vehicles', back_populates='item', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        primary_img = next((i.image_url for i in self.images if i.is_primary), None)
        specs = None
        if self.category == 'Electronics' and self.electronics_spec:
            specs = self.electronics_spec.to_dict()
        elif self.category == 'Tools' and self.tools_spec:
            specs = self.tools_spec.to_dict()
        elif self.category == 'Vehicles' and self.vehicles_spec:
            specs = self.vehicles_spec.to_dict()

        return {
            'item_id': self.item_id, 'owner_id': self.owner_id, 'title': self.title,
            'description': self.description, 'category': self.category,
            'condition': self.condition, 'listing_type': self.listing_type,
            'avail_status': self.avail_status,
            'price_per_day': float(self.price_per_day) if self.price_per_day else 0,
            'sale_price': float(self.sale_price) if self.sale_price else 0,
            'security_dep': float(self.security_dep) if self.security_dep else 0,
            'location_uni': self.location_uni,
            'listed_at': self.listed_at.isoformat() if self.listed_at else None,
            'owner': {'full_name': self.owner.full_name, 'avg_rating': float(self.owner.avg_rating)} if self.owner else None,
            'location': self.location.name if self.location else None,
            'primary_image': primary_img,
            'images': [i.to_dict() for i in self.images],
            'specs': specs
        }


class ItemImage(db.Model):
    __tablename__ = 'item_images'
    id        = db.Column(db.Integer, primary_key=True)
    item_id   = db.Column(db.Integer, db.ForeignKey('item_registry.item_id', ondelete='CASCADE'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    item      = db.relationship('ItemRegistry', back_populates='images')

    def to_dict(self):
        return {'id': self.id, 'image_url': self.image_url, 'is_primary': self.is_primary}


# =====================================================================
# EER Subclasses (specialization of ItemRegistry)
# Each table holds category-specific attributes, linked 1:1 to item_registry
# =====================================================================
class Electronics(db.Model):
    __tablename__ = 'electronics'
    spec_id      = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id      = db.Column(db.Integer, db.ForeignKey('item_registry.item_id', ondelete='CASCADE'), unique=True, nullable=False)
    brand        = db.Column(db.String(100))
    voltage      = db.Column(db.String(50))
    battery_type = db.Column(db.String(50))
    wattage      = db.Column(db.String(50))
    item         = db.relationship('ItemRegistry', back_populates='electronics_spec')

    def to_dict(self):
        return {'brand': self.brand, 'voltage': self.voltage,
                'battery_type': self.battery_type, 'wattage': self.wattage}


class Tools(db.Model):
    __tablename__ = 'tools'
    spec_id      = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id      = db.Column(db.Integer, db.ForeignKey('item_registry.item_id', ondelete='CASCADE'), unique=True, nullable=False)
    power_source = db.Column(db.String(100))
    weight_kg    = db.Column(db.Numeric(5, 2))
    tool_type    = db.Column(db.String(100))
    item         = db.relationship('ItemRegistry', back_populates='tools_spec')

    def to_dict(self):
        return {'power_source': self.power_source,
                'weight_kg': float(self.weight_kg) if self.weight_kg else None,
                'tool_type': self.tool_type}


class Vehicles(db.Model):
    __tablename__ = 'vehicles'
    spec_id    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id    = db.Column(db.Integer, db.ForeignKey('item_registry.item_id', ondelete='CASCADE'), unique=True, nullable=False)
    frame_size = db.Column(db.String(50))
    gear_count = db.Column(db.Integer)
    fuel_type  = db.Column(db.String(50))
    item       = db.relationship('ItemRegistry', back_populates='vehicles_spec')

    def to_dict(self):
        return {'frame_size': self.frame_size, 'gear_count': self.gear_count,
                'fuel_type': self.fuel_type}


# =====================================================================
# Rentals
# =====================================================================
class Rental(db.Model):
    __tablename__ = 'rentals'

    __table_args__ = (
        db.CheckConstraint('end_time > start_time', name='chk_rental_time_order'),
        db.CheckConstraint('total_cost >= 0',        name='chk_rental_cost_positive'),
    )

    rental_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id     = db.Column(db.Integer, db.ForeignKey('item_registry.item_id', ondelete='CASCADE'), nullable=False)
    borrower_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    owner_id    = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    start_time  = db.Column(db.DateTime(timezone=True), nullable=False)
    end_time    = db.Column(db.DateTime(timezone=True), nullable=False)
    total_cost  = db.Column(db.Numeric(10, 2), nullable=False)
    status      = db.Column(rental_status_enum, default='Pending')

    item         = db.relationship('ItemRegistry', back_populates='rentals')
    borrower     = db.relationship('User', foreign_keys=[borrower_id])
    owner        = db.relationship('User', foreign_keys=[owner_id])
    transactions = db.relationship('Transaction', back_populates='rental', cascade='all, delete-orphan')
    review       = db.relationship('Review', back_populates='rental', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'rental_id': self.rental_id, 'item_id': self.item_id,
            'borrower_id': self.borrower_id, 'owner_id': self.owner_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_cost': float(self.total_cost), 'status': self.status,
            'item': self.item.to_dict() if self.item else None,
            'borrower': self.borrower.full_name if self.borrower else None,
            'owner': self.owner.full_name if self.owner else None,
        }


# =====================================================================
# Transactions (Weak Entity — depends on Rental for identity)
# =====================================================================
class Transaction(db.Model):
    __tablename__ = 'transactions'

    __table_args__ = (
        db.CheckConstraint('amount > 0', name='chk_txn_amount_positive'),
    )

    txn_id    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rental_id = db.Column(db.Integer, db.ForeignKey('rentals.rental_id', ondelete='CASCADE'), nullable=False)
    amount    = db.Column(db.Numeric(10, 2), nullable=False)
    txn_type  = db.Column(txn_type_enum, nullable=False)
    method    = db.Column(method_enum, nullable=False)
    txn_date  = db.Column(db.DateTime(timezone=True), default=now)
    status    = db.Column(txn_status_enum, default='Completed')

    rental = db.relationship('Rental', back_populates='transactions')


# =====================================================================
# Reviews (Weak Entity — depends on Rental, one-per-rental)
# =====================================================================
class Review(db.Model):
    __tablename__ = 'reviews'

    # DB-level enforcement: rating must be 1–5
    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='chk_rating_range'),
    )

    review_id    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rental_id    = db.Column(db.Integer, db.ForeignKey('rentals.rental_id', ondelete='CASCADE'), unique=True, nullable=False)
    reviewer_id  = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    reviewed_uid = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    rating       = db.Column(db.Integer, nullable=False)
    comment_text = db.Column(db.Text)
    reviewed_date = db.Column(db.DateTime(timezone=True), default=now)

    rental   = db.relationship('Rental', back_populates='review')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id])
    reviewed = db.relationship('User', foreign_keys=[reviewed_uid])


# =====================================================================
# Orders (Direct Purchases)
# =====================================================================
class Order(db.Model):
    __tablename__ = 'orders'

    __table_args__ = (
        db.CheckConstraint('amount > 0', name='chk_order_amount_positive'),
    )

    order_id       = db.Column(db.Integer, primary_key=True, autoincrement=True)
    buyer_id       = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    seller_id      = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    item_id        = db.Column(db.Integer, db.ForeignKey('item_registry.item_id', ondelete='RESTRICT'), nullable=False)
    amount         = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(method_enum, nullable=False, default='Cash')
    status         = db.Column(order_status_enum, nullable=False, default='Pending')
    created_at     = db.Column(db.DateTime(timezone=True), default=now)

    buyer  = db.relationship('User', foreign_keys=[buyer_id])
    seller = db.relationship('User', foreign_keys=[seller_id])
    item   = db.relationship('ItemRegistry')

    def to_dict(self):
        return {
            'order_id': self.order_id, 'buyer_id': self.buyer_id,
            'seller_id': self.seller_id, 'item_id': self.item_id,
            'amount': float(self.amount), 'payment_method': self.payment_method,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'buyer': self.buyer.full_name if self.buyer else None,
            'seller': self.seller.full_name if self.seller else None,
            'item': self.item.to_dict() if self.item else None,
        }


# =====================================================================
# PostgreSQL TRIGGER: auto-update avg_rating on INSERT/UPDATE/DELETE of reviews
#
# Why a trigger instead of Python-side aggregation (as in the original reviews.py)?
# — Atomicity: the trigger fires within the same transaction as the INSERT.
#   Python-side aggregation requires a second db.session.commit(), which
#   creates a window where the avg_rating is stale.
# — Correctness on DELETE/UPDATE: the original code only handled INSERT.
#   If a review is deleted or updated, the Python code would never recalculate.
# — Concurrency: two simultaneous reviews could race in Python; the trigger
#   runs inside the DB's own locking model.
# =====================================================================

AVG_RATING_TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION update_avg_rating()
RETURNS TRIGGER AS $$
DECLARE
    target_uid INTEGER;
BEGIN
    -- Determine which user's rating needs recalculation
    IF TG_OP = 'DELETE' THEN
        target_uid := OLD.reviewed_uid;
    ELSE
        target_uid := NEW.reviewed_uid;
    END IF;

    UPDATE users
    SET avg_rating = (
        SELECT COALESCE(AVG(rating::NUMERIC), 0.0)
        FROM reviews
        WHERE reviewed_uid = target_uid
    )
    WHERE user_id = target_uid;

    RETURN NULL;  -- AFTER trigger; return value is ignored for row-level
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_avg_rating ON reviews;

CREATE TRIGGER trg_avg_rating
AFTER INSERT OR UPDATE OR DELETE ON reviews
FOR EACH ROW EXECUTE FUNCTION update_avg_rating();
"""


def create_triggers(engine):
    """
    Call this once after db.create_all() to install the avg_rating trigger.
    The trigger is idempotent (DROP TRIGGER IF EXISTS + CREATE OR REPLACE).
    """
    with engine.connect() as conn:
        conn.execute(text(AVG_RATING_TRIGGER_SQL))
        conn.commit()

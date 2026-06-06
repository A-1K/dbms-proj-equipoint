"""
rentals.py — /api/rentals

Changes for PostgreSQL:
  - datetime.fromisoformat() now explicitly attaches UTC timezone if the
    incoming string has no offset. PostgreSQL's TIMESTAMPTZ column will
    reject or misinterpret naive datetimes depending on the server timezone.
  - Query.get() replaced with db.session.get() / db.get_or_404().
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Rental, Transaction, ItemRegistry
from datetime import datetime, timezone

rentals_bp = Blueprint('rentals', __name__, url_prefix='/api/rentals')


def err(msg, code=400): return jsonify({'success': False, 'message': msg}), code
def ok(data, msg='', code=200): return jsonify({'success': True, 'message': msg, 'data': data}), code


def parse_dt(s: str) -> datetime:
    """
    Parse an ISO-8601 datetime string and ensure it is timezone-aware (UTC).
    PostgreSQL TIMESTAMPTZ requires this; naive datetimes cause subtle bugs.
    """
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@rentals_bp.route('/', methods=['POST'])
@jwt_required()
def book_rental():
    user_id = int(get_jwt_identity())
    body = request.get_json() or {}

    item_id        = body.get('item_id')
    start_time_str = body.get('start_time')
    end_time_str   = body.get('end_time')
    method         = body.get('method', 'Cash')

    if not all([item_id, start_time_str, end_time_str]):
        return err('Missing required fields')

    start_time = parse_dt(start_time_str)
    end_time   = parse_dt(end_time_str)

    if end_time <= start_time:
        return err('end_time must be after start_time')

    item = db.get_or_404(ItemRegistry, item_id)
    if item.avail_status != 'Available':
        return err('Item is not available')
    if item.listing_type not in ('Rent', 'Both'):
        return err('This item is not available for rent')

    days = (end_time - start_time).days or 1
    total_cost = (float(item.price_per_day) * days) + float(item.security_dep)

    rental = Rental(
        item_id=item_id,
        borrower_id=user_id,
        owner_id=item.owner_id,
        start_time=start_time,
        end_time=end_time,
        total_cost=total_cost,
        status='Active'
    )
    db.session.add(rental)
    db.session.flush()

    txn = Transaction(
        rental_id=rental.rental_id,
        amount=total_cost,
        txn_type='Payment',
        method=method
    )
    db.session.add(txn)
    item.avail_status = 'Rented'
    db.session.commit()

    return ok(rental.to_dict(), 'Rental booked successfully')


@rentals_bp.route('/my_rentals', methods=['GET'])
@jwt_required()
def my_rentals():
    user_id = int(get_jwt_identity())
    rentals = Rental.query.filter_by(borrower_id=user_id).all()
    return ok([r.to_dict() for r in rentals])


@rentals_bp.route('/my_items_rented', methods=['GET'])
@jwt_required()
def my_items_rented():
    user_id = int(get_jwt_identity())
    rentals = Rental.query.filter_by(owner_id=user_id).all()
    return ok([r.to_dict() for r in rentals])

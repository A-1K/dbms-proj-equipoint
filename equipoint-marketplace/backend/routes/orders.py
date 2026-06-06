"""
Orders Routes — /api/orders

Changes for PostgreSQL:
  - Query.get() replaced with db.get_or_404() / db.session.get().
  - No other logic changes needed; order status machine is application-level.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Order, ItemRegistry, User

orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')


def err(msg, code=400):
    return jsonify({'success': False, 'message': msg}), code

def ok(data, msg='', code=200):
    return jsonify({'success': True, 'message': msg, 'data': data}), code


@orders_bp.route('/buy', methods=['POST'])
@jwt_required()
def buy_item():
    uid  = int(get_jwt_identity())
    body = request.get_json() or {}

    item_id        = body.get('item_id')
    payment_method = body.get('payment_method', 'Cash')

    if not item_id:
        return err('item_id is required')

    item = db.get_or_404(ItemRegistry, item_id)

    if item.owner_id == uid:
        return err('You cannot buy your own item')
    if item.listing_type not in ('Buy', 'Both'):
        return err('This item is not listed for sale')
    if item.avail_status != 'Available':
        return err('Item is no longer available')
    if not item.sale_price or float(item.sale_price) <= 0:
        return err('Item has no sale price set')

    order = Order(
        buyer_id       = uid,
        seller_id      = item.owner_id,
        item_id        = item.item_id,
        amount         = item.sale_price,
        payment_method = payment_method,
        status         = 'Pending',
    )
    db.session.add(order)
    item.avail_status = 'Sold'
    db.session.commit()

    return ok(order.to_dict(), 'Order placed successfully', 201)


@orders_bp.route('', methods=['GET'])
@jwt_required()
def my_orders():
    uid    = int(get_jwt_identity())
    orders = Order.query.filter_by(buyer_id=uid).order_by(Order.created_at.desc()).all()
    return ok([o.to_dict() for o in orders])


@orders_bp.route('/selling', methods=['GET'])
@jwt_required()
def my_sales():
    uid    = int(get_jwt_identity())
    orders = Order.query.filter_by(seller_id=uid).order_by(Order.created_at.desc()).all()
    return ok([o.to_dict() for o in orders])


@orders_bp.route('/<int:oid>/status', methods=['PUT'])
@jwt_required()
def update_order_status(oid):
    uid   = int(get_jwt_identity())
    order = db.get_or_404(Order, oid)
    body  = request.get_json() or {}
    new_status = body.get('status')

    allowed = {
        'Pending':   ['Confirmed', 'Cancelled'],
        'Confirmed': ['Completed', 'Cancelled'],
        'Completed': [],
        'Cancelled': [],
    }

    if order.seller_id == uid:
        if new_status not in allowed.get(order.status, []):
            return err(f'Cannot transition from {order.status} to {new_status}')
    elif order.buyer_id == uid:
        if not (new_status == 'Cancelled' and order.status == 'Pending'):
            return err('Forbidden', 403)
    else:
        return err('Forbidden', 403)

    if new_status == 'Cancelled':
        item = db.session.get(ItemRegistry, order.item_id)
        if item:
            item.avail_status = 'Available'

    order.status = new_status
    db.session.commit()
    return ok(order.to_dict(), f'Order status updated to {new_status}')

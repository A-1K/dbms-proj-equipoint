"""
products.py — /api/products

Changes for PostgreSQL:
  - .ilike() works natively and efficiently in PostgreSQL (uses indexes on
    lower(title) if you create one). No change needed there.
  - Query.get() replaced with db.session.get() for SQLAlchemy 2.x compatibility.
  - get_or_404 kept as-is (Flask-SQLAlchemy helper).
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, ItemRegistry, ItemImage, Electronics, Tools, Vehicles, User, CATEGORY_ENUM

products_bp = Blueprint('products', __name__, url_prefix='/api/products')


def err(msg, code=400): return jsonify({'success': False, 'message': msg}), code
def ok(data, msg='', code=200): return jsonify({'success': True, 'message': msg, 'data': data}), code


@products_bp.route('/', methods=['GET'])
def list_items():
    query = ItemRegistry.query.filter(ItemRegistry.avail_status == 'Available')

    cat = request.args.get('category')
    if cat:
        query = query.filter(ItemRegistry.category == cat)

    uni = request.args.get('university')
    if uni:
        query = query.filter(ItemRegistry.location_uni == uni)

    search = request.args.get('search')
    if search:
        # ilike on PostgreSQL is case-insensitive and leverages a functional index
        # if you create: CREATE INDEX idx_item_title ON item_registry (lower(title));
        query = query.filter(ItemRegistry.title.ilike(f'%{search}%'))

    listing_type = request.args.get('listing_type')
    if listing_type:
        query = query.filter(
            (ItemRegistry.listing_type == listing_type) |
            (ItemRegistry.listing_type == 'Both')
        )

    condition = request.args.get('condition')
    if condition:
        query = query.filter(ItemRegistry.condition == condition)

    # Pagination — ?page=1&per_page=20 (defaults: page 1, 20 items)
    page     = request.args.get('page',     1,  type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # cap at 100 to prevent abuse

    pagination = query.order_by(ItemRegistry.listed_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return ok({
        'items':      [i.to_dict() for i in pagination.items],
        'total':      pagination.total,
        'page':       pagination.page,
        'per_page':   pagination.per_page,
        'pages':      pagination.pages,
        'has_next':   pagination.has_next,
        'has_prev':   pagination.has_prev,
    })


@products_bp.route('/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = db.get_or_404(ItemRegistry, item_id)
    return ok(item.to_dict())


@products_bp.route('/', methods=['POST'])
@jwt_required()
def create_item():
    user_id = int(get_jwt_identity())
    body = request.get_json() or {}

    required = ['title', 'category', 'condition', 'listing_type']
    for f in required:
        if not body.get(f):
            return err(f'Missing field: {f}')

    user = db.get_or_404(User, user_id)
    location_uni = body.get('location_uni') or user.uni_affil

    item = ItemRegistry(
        owner_id=user_id,
        title=body['title'],
        description=body.get('description', ''),
        category=body['category'],
        condition=body['condition'],
        listing_type=body['listing_type'],
        price_per_day=float(body.get('price_per_day', 0)),
        sale_price=float(body.get('sale_price', 0)),
        security_dep=float(body.get('security_dep', 0)),
        location_uni=location_uni,
    )
    db.session.add(item)
    db.session.flush()  # get item.item_id before committing

    cat = body['category']
    specs = body.get('specs', {})
    if cat == 'Electronics':
        db.session.add(Electronics(
            item_id=item.item_id,
            brand=specs.get('brand'), voltage=specs.get('voltage'),
            battery_type=specs.get('battery_type'), wattage=specs.get('wattage')
        ))
    elif cat == 'Tools':
        db.session.add(Tools(
            item_id=item.item_id,
            power_source=specs.get('power_source'), weight_kg=specs.get('weight_kg'),
            tool_type=specs.get('tool_type')
        ))
    elif cat == 'Vehicles':
        db.session.add(Vehicles(
            item_id=item.item_id,
            frame_size=specs.get('frame_size'), gear_count=specs.get('gear_count'),
            fuel_type=specs.get('fuel_type')
        ))

    images = body.get('images', [])
    if images:
        for idx, img_url in enumerate(images):
            db.session.add(ItemImage(item_id=item.item_id, image_url=img_url, is_primary=(idx == 0)))
    else:
        db.session.add(ItemImage(
            item_id=item.item_id,
            image_url='https://placehold.co/400x300/e5e7eb/9ca3af?text=No+Image',
            is_primary=True
        ))

    db.session.commit()
    return ok(item.to_dict(), 'Item listed successfully', 201)


@products_bp.route('/categories', methods=['GET'])
def get_categories():
    return ok([{'id': c, 'name': c} for c in CATEGORY_ENUM])

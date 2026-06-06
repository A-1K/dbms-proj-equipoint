"""
auth.py — /api/auth

Changes for PostgreSQL / SQLAlchemy 2.x:
  - Query.get() is deprecated in SQLAlchemy 2.x; replaced with db.session.get().
  - get_or_404 is kept via Flask-SQLAlchemy's helper which still works.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, University

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def err(msg, code=400): return jsonify({'success': False, 'message': msg}), code
def ok(data, msg='', code=200): return jsonify({'success': True, 'message': msg, 'data': data}), code


@auth_bp.route('/register', methods=['POST'])
def register():
    body = request.get_json() or {}
    required = ['full_name', 'email', 'student_id', 'uni_affil', 'password']
    for f in required:
        if not body.get(f):
            return err(f'Missing field: {f}')

    email = body['email'].lower().strip()

    # Use db.session.get() — the SQLAlchemy 2.x recommended pattern
    uni = db.session.get(University, body['uni_affil'])
    if not uni:
        return err('University not found')
    if User.query.filter_by(email=email).first():
        return err('Email already registered')
    if User.query.filter_by(student_id=body['student_id']).first():
        return err('Student ID already registered')

    user = User(
        full_name=body['full_name'].strip(),
        email=email,
        student_id=body['student_id'].strip(),
        uni_affil=uni.uni_id,
        phone=body.get('phone', ''),
        role='Student',
        active_status='Active'
    )
    user.set_password(body['password'])
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.user_id))
    return ok({'token': token, 'user': user.to_dict()}, 'Registration successful', 201)


@auth_bp.route('/login', methods=['POST'])
def login():
    body = request.get_json() or {}
    email = body.get('email', '').lower().strip()
    password = body.get('password', '')
    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return err('Invalid email or password', 401)
    if user.active_status != 'Active':
        return err('Account suspended', 403)

    token = create_access_token(identity=str(user.user_id))
    return ok({'token': token, 'user': user.to_dict()}, 'Login successful')


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user = db.get_or_404(User, int(get_jwt_identity()))
    return ok(user.to_dict())


@auth_bp.route('/universities', methods=['GET'])
def list_universities():
    unis = University.query.order_by(University.name).all()
    return ok([u.to_dict() for u in unis])

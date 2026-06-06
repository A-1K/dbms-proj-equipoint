"""
tests/test_api.py — UniMarket Pakistan API Tests

Run:
    cd uni-marketplace/backend
    pytest ../../tests/test_api.py -v

Requires:
    - A running PostgreSQL instance with a test database.
    - Set TEST_DATABASE_URL in your environment, e.g.:
        TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/uni_marketplace_test

    Or run against the default dev DB (tests roll back after each test, so
    existing data is never touched — but the ENUMs must already be created).

What is tested:
    - Health endpoint
    - University listing
    - User registration (success + duplicate prevention)
    - User login (success + wrong password)
    - Product listing with pagination
    - Product creation (auth required)
    - Category listing
"""

import os
import pytest

# ---------------------------------------------------------------------------
# App factory — point at a test DB if TEST_DATABASE_URL is set
# ---------------------------------------------------------------------------
os.environ.setdefault(
    'DATABASE_URL',
    os.environ.get(
        'TEST_DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/uni_marketplace_test'
    )
)

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'uni-marketplace', 'backend'))

from app import create_app
from models import db as _db, University, User, create_triggers


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def app():
    """Create app once per test session with an isolated test database."""
    application = create_app()
    application.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': os.environ['DATABASE_URL'],
    })

    with application.app_context():
        _db.create_all()
        create_triggers(_db.engine)

        # Seed one university so registration tests have a valid uni_id
        if not University.query.filter_by(name='Test University').first():
            uni = University(
                name='Test University',
                city='Lahore',
                province='Punjab',
                hec_status='Recognized'
            )
            _db.session.add(uni)
            _db.session.commit()

    yield application

    # Teardown: drop everything after the full test session
    with application.app_context():
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(scope='session')
def uni_id(app):
    """Return the seeded test university's ID."""
    with app.app_context():
        uni = University.query.filter_by(name='Test University').first()
        return uni.uni_id


@pytest.fixture(scope='session')
def auth_token(app, uni_id):
    """Register a test user and return their JWT access token."""
    with app.test_client() as c:
        resp = c.post('/api/auth/register', json={
            'full_name':  'Test Student',
            'email':      'test.student@unimarket.pk',
            'student_id': 'TEST-001',
            'uni_affil':  uni_id,
            'password':   'testpass123',
        })
        data = resp.get_json()
        # If already registered from a previous run, fall back to login
        if not data.get('success'):
            resp = c.post('/api/auth/login', json={
                'email':    'test.student@unimarket.pk',
                'password': 'testpass123',
            })
            data = resp.get_json()
        return data['data']['token']


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get('/api/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ok'
        assert 'UniMarket' in data['app']


# ---------------------------------------------------------------------------
# Universities
# ---------------------------------------------------------------------------

class TestUniversities:
    def test_list_universities_returns_list(self, client):
        resp = client.get('/api/auth/universities')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert isinstance(data['data'], list)
        assert len(data['data']) >= 1

    def test_university_has_required_fields(self, client):
        resp = client.get('/api/auth/universities')
        uni = resp.get_json()['data'][0]
        for field in ('uni_id', 'name', 'city', 'province', 'hec_status'):
            assert field in uni, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# Auth — Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_register_missing_fields_returns_400(self, client):
        resp = client.post('/api/auth/register', json={'email': 'x@x.com'})
        assert resp.status_code == 400
        assert resp.get_json()['success'] is False

    def test_register_invalid_university_returns_400(self, client, uni_id):
        resp = client.post('/api/auth/register', json={
            'full_name':  'Ghost User',
            'email':      'ghost@unimarket.pk',
            'student_id': 'GHOST-001',
            'uni_affil':  999999,          # non-existent university
            'password':   'pass123',
        })
        assert resp.status_code == 400

    def test_register_duplicate_email_returns_400(self, client, uni_id, auth_token):
        # The test user was registered in the auth_token fixture; try again
        resp = client.post('/api/auth/register', json={
            'full_name':  'Duplicate',
            'email':      'test.student@unimarket.pk',
            'student_id': 'DUP-001',
            'uni_affil':  uni_id,
            'password':   'pass123',
        })
        assert resp.status_code == 400
        assert 'already' in resp.get_json()['message'].lower()


# ---------------------------------------------------------------------------
# Auth — Login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_success(self, client):
        resp = client.post('/api/auth/login', json={
            'email':    'test.student@unimarket.pk',
            'password': 'testpass123',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'token' in data['data']

    def test_login_wrong_password_returns_401(self, client):
        resp = client.post('/api/auth/login', json={
            'email':    'test.student@unimarket.pk',
            'password': 'wrongpassword',
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user_returns_401(self, client):
        resp = client.post('/api/auth/login', json={
            'email':    'nobody@unimarket.pk',
            'password': 'anything',
        })
        assert resp.status_code == 401

    def test_me_endpoint_requires_auth(self, client):
        resp = client.get('/api/auth/me')
        assert resp.status_code == 401

    def test_me_endpoint_with_token(self, client, auth_token):
        resp = client.get('/api/auth/me',
                          headers={'Authorization': f'Bearer {auth_token}'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['email'] == 'test.student@unimarket.pk'


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

class TestProducts:
    def test_list_products_returns_paginated_response(self, client):
        resp = client.get('/api/products/')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        # Pagination envelope
        for key in ('items', 'total', 'page', 'per_page', 'pages', 'has_next', 'has_prev'):
            assert key in data['data'], f"Pagination key missing: {key}"

    def test_pagination_page_param(self, client):
        resp = client.get('/api/products/?page=1&per_page=5')
        assert resp.status_code == 200
        data = resp.get_json()['data']
        assert data['per_page'] == 5
        assert data['page'] == 1

    def test_per_page_capped_at_100(self, client):
        resp = client.get('/api/products/?per_page=999')
        assert resp.status_code == 200
        data = resp.get_json()['data']
        assert data['per_page'] <= 100

    def test_category_filter(self, client):
        resp = client.get('/api/products/?category=Electronics')
        assert resp.status_code == 200
        items = resp.get_json()['data']['items']
        for item in items:
            assert item['category'] == 'Electronics'

    def test_categories_endpoint(self, client):
        resp = client.get('/api/products/categories')
        assert resp.status_code == 200
        cats = resp.get_json()['data']
        names = [c['name'] for c in cats]
        assert 'Electronics' in names
        assert 'Textbooks' in names

    def test_create_product_requires_auth(self, client):
        resp = client.post('/api/products/', json={
            'title': 'Unauthenticated Item',
            'category': 'Electronics',
            'condition': 'New',
            'listing_type': 'Buy',
        })
        assert resp.status_code == 401

    def test_create_product_success(self, client, auth_token, uni_id):
        resp = client.post('/api/products/',
            json={
                'title':        'Calculus Textbook 9th Ed',
                'description':  'Good condition, minimal highlighting',
                'category':     'Textbooks',
                'condition':    'Good',
                'listing_type': 'Buy',
                'sale_price':   800,
                'location_uni': uni_id,
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['title'] == 'Calculus Textbook 9th Ed'

    def test_create_product_missing_fields_returns_400(self, client, auth_token):
        resp = client.post('/api/products/',
            json={'title': 'Incomplete Item'},
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert resp.status_code == 400

    def test_get_single_product(self, client, auth_token, uni_id):
        # Create one first
        create_resp = client.post('/api/products/',
            json={
                'title':        'Test Laptop',
                'category':     'Electronics',
                'condition':    'Like New',
                'listing_type': 'Rent',
                'price_per_day': 200,
                'location_uni': uni_id,
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        item_id = create_resp.get_json()['data']['item_id']

        resp = client.get(f'/api/products/{item_id}')
        assert resp.status_code == 200
        assert resp.get_json()['data']['item_id'] == item_id

    def test_get_nonexistent_product_returns_404(self, client):
        resp = client.get('/api/products/999999')
        assert resp.status_code == 404

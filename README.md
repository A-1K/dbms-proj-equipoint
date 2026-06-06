# UniMarket Pakistan 🎓

A full-stack **inter-university equipment marketplace** for Pakistani students — built with Flask, PostgreSQL, and vanilla JS. Students can list, rent, and purchase equipment across HEC-recognized universities.

---

## Tech Stack

| Layer       | Technology                                      |
|-------------|--------------------------------------------------|
| Backend     | Python 3.11 · Flask 3.0 · Flask-SQLAlchemy 3.1  |
| Database    | PostgreSQL 16 (native ENUMs, triggers, indexes)  |
| Auth        | Flask-JWT-Extended (HS256 access tokens)         |
| Frontend    | Vanilla JS · HTML5 · CSS3 (single-page app)      |
| Dev Tools   | Docker · Flask-Migrate · pytest                  |

---

## Features

- **Authentication** — JWT-based register/login, bcrypt password hashing
- **Listings** — Create, browse, and filter items by category, condition, listing type, university, and keyword (paginated)
- **Rentals** — Book items for a date range; automatic cost calculation; security deposit tracking
- **Orders** — Direct purchase flow with a seller-driven status machine (Pending → Confirmed → Completed)
- **Reviews** — One review per completed rental; star rating (1–5)
- **Transactions** — Payment records linked to rentals (EasyPaisa, JazzCash, Bank Transfer, Cash)
- **Admin** — Default admin account seeded on first run

---

## Database Design Highlights

> This project uses several PostgreSQL-specific features intentionally, not just as a Flask default.

### Native ENUM Types
All status/category fields use `CREATE TYPE ... AS ENUM (...)` — enforced at the storage level, not just the application layer. Invalid values are rejected by PostgreSQL itself.

### PostgreSQL Trigger — `trg_avg_rating`
`users.avg_rating` is updated atomically via an `AFTER INSERT OR UPDATE OR DELETE` trigger on `reviews`. The original Python-side approach was non-atomic (required a second commit) and silently failed on DELETE/UPDATE. The trigger fires within the same transaction as the review change.

```sql
CREATE TRIGGER trg_avg_rating
AFTER INSERT OR UPDATE OR DELETE ON reviews
FOR EACH ROW EXECUTE FUNCTION update_avg_rating();
```

### EER Specialization
`item_registry` is the parent (superclass) table. `electronics`, `tools`, and `vehicles` are specialization tables with a 1:1 FK — an Extended Entity-Relationship pattern that avoids sparse columns and allows category-specific constraints.

### FK Cascade Strategy
- `ondelete='CASCADE'` — child rows deleted with parent (item images, rental reviews, spec tables)
- `ondelete='RESTRICT'` — deletion blocked if children exist (users with orders, universities with users)

### CHECK Constraints
DB-level guards on `price_per_day >= 0`, `sale_price >= 0`, `total_cost >= 0`, `amount > 0`, `rating BETWEEN 1 AND 5`, `end_time > start_time`.

### Performance Indexes
```python
Index('idx_item_title_lower', text('lower(title)'))  # ILIKE search
Index('idx_item_category',    'category')             # category filter
Index('idx_item_avail_status','avail_status')          # Available filter
Index('idx_item_listed_at',   'listed_at')             # ORDER BY
```

### ER Diagram

![ER Diagram](docs/erd.svg)

---

## Quickstart — Docker (recommended)

```bash
git clone https://github.com/<your-username>/unimarket-pk.git
cd unimarket-pk

docker compose up --build
```

The container runs `setup.py` on first boot (creates tables, installs trigger, seeds 15 universities and an admin account), then starts the Flask dev server.

Open **http://localhost:5000** in your browser.

**Default admin credentials:**
```
Email:    admin@unimarket.pk
Password: admin123
```

---

## Quickstart — Manual

### Prerequisites
- Python 3.11+
- PostgreSQL 16 running locally

```bash
# 1. Create the database
psql -U postgres -c "CREATE DATABASE uni_marketplace;"

# 2. Clone and enter backend
git clone https://github.com/<your-username>/unimarket-pk.git
cd unimarket-pk/uni-marketplace/backend

# 3. Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and set DATABASE_URL, JWT_SECRET_KEY, SECRET_KEY

# 5. Run setup (tables + trigger + seed data)
python setup.py

# 6. (Optional) Seed 50 sample products
python seed_50_products.py

# 7. Start the server
python app.py
```

Server starts at **http://localhost:5000**

---

## API Reference

### Auth
| Method | Endpoint              | Auth | Description           |
|--------|-----------------------|------|-----------------------|
| POST   | `/api/auth/register`  | No   | Register new student  |
| POST   | `/api/auth/login`     | No   | Login, get JWT token  |
| GET    | `/api/auth/me`        | JWT  | Current user profile  |
| GET    | `/api/auth/universities` | No | List all universities |

### Products
| Method | Endpoint                | Auth | Description                         |
|--------|-------------------------|------|-------------------------------------|
| GET    | `/api/products/`        | No   | List items (paginated, filterable)  |
| POST   | `/api/products/`        | JWT  | Create a new listing                |
| GET    | `/api/products/<id>`    | No   | Get single item                     |
| GET    | `/api/products/categories` | No | List all categories              |

**Pagination & Filters** (`GET /api/products/`):
```
?page=1&per_page=20
?category=Electronics
?listing_type=Rent
?condition=Good
?search=calculator
?university=1
```

### Rentals
| Method | Endpoint                     | Auth | Description         |
|--------|------------------------------|------|---------------------|
| POST   | `/api/rentals/`              | JWT  | Book a rental       |
| GET    | `/api/rentals/my_rentals`    | JWT  | My booked rentals   |
| GET    | `/api/rentals/my_items_rented` | JWT | Items I've rented out |

### Orders
| Method | Endpoint                      | Auth | Description           |
|--------|-------------------------------|------|-----------------------|
| POST   | `/api/orders/buy`             | JWT  | Purchase an item      |
| GET    | `/api/orders`                 | JWT  | My purchase history   |
| GET    | `/api/orders/selling`         | JWT  | Items I've sold       |
| PUT    | `/api/orders/<id>/status`     | JWT  | Update order status   |

### Reviews
| Method | Endpoint       | Auth | Description                  |
|--------|----------------|------|------------------------------|
| POST   | `/api/reviews/` | JWT | Post a review for a rental   |

---

## Running Tests

```bash
cd uni-marketplace/backend

# Set test DB (separate from dev DB)
export TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/uni_marketplace_test

pytest ../../tests/test_api.py -v
```

Tests cover: health check, university listing, registration (success + duplicates), login (success + wrong password), JWT-protected routes, product listing with pagination, product creation, and 404 handling — **25 test cases total**.

---

## Project Structure

```
unimarket-pk/
├── docker-compose.yml
├── docs/
│   └── erd.svg                    # Entity-Relationship Diagram
├── tests/
│   └── test_api.py                # pytest test suite (25 cases)
└── uni-marketplace/
    ├── backend/
    │   ├── Dockerfile
    │   ├── requirements.txt       # pinned versions
    │   ├── .env.example
    │   ├── app.py                 # Flask app factory
    │   ├── config.py              # PostgreSQL pool config
    │   ├── models.py              # SQLAlchemy models + trigger SQL
    │   ├── setup.py               # DB init + university seed
    │   ├── seed_50_products.py    # 50 sample listings
    │   └── routes/
    │       ├── auth.py
    │       ├── products.py        # with pagination
    │       ├── rentals.py
    │       ├── orders.py
    │       └── reviews.py
    └── frontend/
        └── index.html             # Single-page frontend
```

---

## Author

**Abdul Kabeer** · Data Science · GIK Institute of Engineering Sciences and Technology  
Student ID: 2024288

---

## License

MIT

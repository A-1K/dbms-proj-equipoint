
/* ================================================================
   1. Marketplace Overview KPIs
   ================================================================ */

-- Total users, active students, admins, universities, listings, rentals, orders, and reviews.
SELECT
    (SELECT COUNT(*) FROM users) AS total_users,
    (SELECT COUNT(*) FROM users WHERE active_status = 'Active') AS active_users,
    (SELECT COUNT(*) FROM users WHERE role = 'Student') AS total_students,
    (SELECT COUNT(*) FROM users WHERE role = 'Admin') AS total_admins,
    (SELECT COUNT(*) FROM university_registry) AS total_universities,
    (SELECT COUNT(*) FROM item_registry) AS total_listings,
    (SELECT COUNT(*) FROM item_registry WHERE avail_status = 'Available') AS available_listings,
    (SELECT COUNT(*) FROM rentals) AS total_rentals,
    (SELECT COUNT(*) FROM orders) AS total_orders,
    (SELECT COUNT(*) FROM reviews) AS total_reviews;

-- Marketplace revenue summary from completed/pending orders and rental transactions.
SELECT
    COALESCE((SELECT SUM(amount) FROM orders WHERE status IN ('Confirmed', 'Completed')), 0) AS order_revenue,
    COALESCE((SELECT SUM(total_cost) FROM rentals WHERE status IN ('Active', 'Completed')), 0) AS rental_revenue,
    COALESCE((SELECT SUM(amount) FROM transactions WHERE status = 'Completed'), 0) AS completed_transaction_value;


/* ================================================================
   2. Listing and Inventory Analytics
   ================================================================ */

-- Listings by category, with status breakdown.
SELECT
    category,
    COUNT(*) AS total_listings,
    COUNT(*) FILTER (WHERE avail_status = 'Available') AS available,
    COUNT(*) FILTER (WHERE avail_status = 'Rented') AS rented,
    COUNT(*) FILTER (WHERE avail_status = 'Sold') AS sold,
    ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM item_registry), 0), 2) AS category_share_percent
FROM item_registry
GROUP BY category
ORDER BY total_listings DESC, category;

-- Listings by listing type: Buy, Rent, Both.
SELECT
    listing_type,
    COUNT(*) AS total_listings,
    ROUND(AVG(sale_price), 2) AS avg_sale_price,
    ROUND(AVG(price_per_day), 2) AS avg_rental_price_per_day,
    ROUND(AVG(security_dep), 2) AS avg_security_deposit
FROM item_registry
GROUP BY listing_type
ORDER BY total_listings DESC;

-- Price statistics by category.
SELECT
    category,
    COUNT(*) AS listings,
    ROUND(MIN(NULLIF(sale_price, 0)), 2) AS min_sale_price,
    ROUND(AVG(NULLIF(sale_price, 0)), 2) AS avg_sale_price,
    ROUND(MAX(NULLIF(sale_price, 0)), 2) AS max_sale_price,
    ROUND(MIN(NULLIF(price_per_day, 0)), 2) AS min_rent_per_day,
    ROUND(AVG(NULLIF(price_per_day, 0)), 2) AS avg_rent_per_day,
    ROUND(MAX(NULLIF(price_per_day, 0)), 2) AS max_rent_per_day
FROM item_registry
GROUP BY category
ORDER BY listings DESC, category;

-- Oldest active listings: useful for finding stale inventory.
SELECT
    i.item_id,
    i.title,
    i.category,
    i.listing_type,
    i.avail_status,
    u.full_name AS seller_name,
    uni.name AS university,
    i.listed_at,
    CURRENT_DATE - i.listed_at::DATE AS days_since_listed
FROM item_registry i
JOIN users u ON i.owner_id = u.user_id
JOIN university_registry uni ON i.location_uni = uni.uni_id
WHERE i.avail_status = 'Available'
ORDER BY days_since_listed DESC, i.listed_at ASC
LIMIT 20;


/* ================================================================
   3. University-Level Marketplace Activity
   ================================================================ */

-- Marketplace activity by university.
SELECT
    uni.uni_id,
    uni.name AS university,
    uni.city,
    uni.province,
    COUNT(DISTINCT u.user_id) AS registered_users,
    COUNT(DISTINCT i.item_id) AS total_listings,
    COUNT(DISTINCT r.rental_id) AS total_rentals,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COALESCE(SUM(DISTINCT o.amount) FILTER (WHERE o.status IN ('Confirmed', 'Completed')), 0) AS order_revenue
FROM university_registry uni
LEFT JOIN users u ON u.uni_affil = uni.uni_id
LEFT JOIN item_registry i ON i.location_uni = uni.uni_id
LEFT JOIN rentals r ON r.item_id = i.item_id
LEFT JOIN orders o ON o.item_id = i.item_id
GROUP BY uni.uni_id, uni.name, uni.city, uni.province
ORDER BY total_listings DESC, registered_users DESC;

-- Top universities by available inventory.
SELECT
    uni.name AS university,
    uni.city,
    COUNT(i.item_id) AS available_items
FROM university_registry uni
JOIN item_registry i ON i.location_uni = uni.uni_id
WHERE i.avail_status = 'Available'
GROUP BY uni.name, uni.city
ORDER BY available_items DESC
LIMIT 10;


/* ================================================================
   4. Rental Analytics
   ================================================================ */

-- Rental status distribution.
SELECT
    status,
    COUNT(*) AS total_rentals,
    COALESCE(SUM(total_cost), 0) AS total_rental_value,
    ROUND(AVG(total_cost), 2) AS avg_rental_value
FROM rentals
GROUP BY status
ORDER BY total_rentals DESC;

-- Rental revenue by category.
SELECT
    i.category,
    COUNT(r.rental_id) AS total_rentals,
    COALESCE(SUM(r.total_cost), 0) AS total_revenue,
    ROUND(AVG(r.total_cost), 2) AS avg_rental_value,
    ROUND(AVG(EXTRACT(EPOCH FROM (r.end_time - r.start_time)) / 86400.0), 2) AS avg_rental_days
FROM rentals r
JOIN item_registry i ON r.item_id = i.item_id
WHERE r.status IN ('Active', 'Completed')
GROUP BY i.category
ORDER BY total_revenue DESC, total_rentals DESC;

-- Monthly rental trend.
SELECT
    DATE_TRUNC('month', r.start_time)::DATE AS month,
    COUNT(*) AS total_rentals,
    COALESCE(SUM(r.total_cost), 0) AS rental_revenue,
    ROUND(AVG(r.total_cost), 2) AS avg_rental_value
FROM rentals r
GROUP BY DATE_TRUNC('month', r.start_time)
ORDER BY month;

-- Most rented items.
SELECT
    i.item_id,
    i.title,
    i.category,
    owner.full_name AS owner_name,
    COUNT(r.rental_id) AS times_rented,
    COALESCE(SUM(r.total_cost), 0) AS total_revenue
FROM item_registry i
JOIN users owner ON i.owner_id = owner.user_id
JOIN rentals r ON i.item_id = r.item_id
WHERE r.status IN ('Active', 'Completed')
GROUP BY i.item_id, i.title, i.category, owner.full_name
ORDER BY times_rented DESC, total_revenue DESC
LIMIT 15;


/* ================================================================
   5. Order / Purchase Analytics
   ================================================================ */

-- Order status distribution.
SELECT
    status,
    COUNT(*) AS total_orders,
    COALESCE(SUM(amount), 0) AS total_order_value,
    ROUND(AVG(amount), 2) AS avg_order_value
FROM orders
GROUP BY status
ORDER BY total_orders DESC;

-- Sales revenue by category.
SELECT
    i.category,
    COUNT(o.order_id) AS total_orders,
    COALESCE(SUM(o.amount), 0) AS sales_revenue,
    ROUND(AVG(o.amount), 2) AS avg_sale_value
FROM orders o
JOIN item_registry i ON o.item_id = i.item_id
WHERE o.status IN ('Confirmed', 'Completed')
GROUP BY i.category
ORDER BY sales_revenue DESC, total_orders DESC;

-- Monthly order trend.
SELECT
    DATE_TRUNC('month', o.created_at)::DATE AS month,
    COUNT(*) AS total_orders,
    COALESCE(SUM(o.amount), 0) AS order_revenue,
    ROUND(AVG(o.amount), 2) AS avg_order_value
FROM orders o
GROUP BY DATE_TRUNC('month', o.created_at)
ORDER BY month;

-- Payment method usage across direct purchases.
SELECT
    payment_method,
    COUNT(*) AS total_orders,
    COALESCE(SUM(amount), 0) AS total_amount,
    ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM orders), 0), 2) AS usage_percent
FROM orders
GROUP BY payment_method
ORDER BY total_orders DESC;


/* ================================================================
   6. Seller / User Performance Analytics
   ================================================================ */

-- Top sellers by combined marketplace activity.
SELECT
    seller.user_id,
    seller.full_name AS seller_name,
    seller.email,
    seller.avg_rating,
    COUNT(DISTINCT i.item_id) AS listings_created,
    COUNT(DISTINCT o.order_id) AS sales_count,
    COALESCE(SUM(o.amount) FILTER (WHERE o.status IN ('Confirmed', 'Completed')), 0) AS sales_revenue,
    COUNT(DISTINCT r.rental_id) AS rentals_count,
    COALESCE(SUM(r.total_cost) FILTER (WHERE r.status IN ('Active', 'Completed')), 0) AS rental_revenue
FROM users seller
LEFT JOIN item_registry i ON seller.user_id = i.owner_id
LEFT JOIN orders o ON seller.user_id = o.seller_id
LEFT JOIN rentals r ON seller.user_id = r.owner_id
WHERE seller.role = 'Student'
GROUP BY seller.user_id, seller.full_name, seller.email, seller.avg_rating
ORDER BY (COALESCE(SUM(o.amount), 0) + COALESCE(SUM(r.total_cost), 0)) DESC,
         listings_created DESC
LIMIT 20;

-- Top-rated users with at least one review.
SELECT
    reviewed.user_id,
    reviewed.full_name AS seller_name,
    reviewed.avg_rating,
    COUNT(rv.review_id) AS review_count,
    ROUND(AVG(rv.rating), 2) AS calculated_avg_rating
FROM users reviewed
JOIN reviews rv ON reviewed.user_id = rv.reviewed_uid
GROUP BY reviewed.user_id, reviewed.full_name, reviewed.avg_rating
HAVING COUNT(rv.review_id) >= 1
ORDER BY reviewed.avg_rating DESC, review_count DESC
LIMIT 20;

-- Most active buyers/borrowers.
SELECT
    u.user_id,
    u.full_name,
    COUNT(DISTINCT o.order_id) AS orders_placed,
    COUNT(DISTINCT r.rental_id) AS rentals_requested,
    COALESCE(SUM(o.amount), 0) AS total_purchase_spend,
    COALESCE(SUM(r.total_cost), 0) AS total_rental_spend
FROM users u
LEFT JOIN orders o ON u.user_id = o.buyer_id
LEFT JOIN rentals r ON u.user_id = r.borrower_id
GROUP BY u.user_id, u.full_name
ORDER BY (COUNT(DISTINCT o.order_id) + COUNT(DISTINCT r.rental_id)) DESC,
         (COALESCE(SUM(o.amount), 0) + COALESCE(SUM(r.total_cost), 0)) DESC
LIMIT 20;


/* ================================================================
   7. Reviews and Trust Analytics
   ================================================================ */

-- Rating distribution.
SELECT
    rating,
    COUNT(*) AS total_reviews,
    ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM reviews), 0), 2) AS review_share_percent
FROM reviews
GROUP BY rating
ORDER BY rating DESC;

-- Recent review feed.
SELECT
    rv.review_id,
    reviewer.full_name AS reviewer_name,
    reviewed.full_name AS reviewed_user,
    i.title AS item_title,
    rv.rating,
    rv.comment_text,
    rv.reviewed_date
FROM reviews rv
JOIN users reviewer ON rv.reviewer_id = reviewer.user_id
JOIN users reviewed ON rv.reviewed_uid = reviewed.user_id
JOIN rentals r ON rv.rental_id = r.rental_id
JOIN item_registry i ON r.item_id = i.item_id
ORDER BY rv.reviewed_date DESC
LIMIT 20;

-- Users whose stored avg_rating differs from actual review average.
-- Useful for checking whether the PostgreSQL trigger is working correctly.
SELECT
    u.user_id,
    u.full_name,
    u.avg_rating AS stored_avg_rating,
    ROUND(AVG(rv.rating)::NUMERIC, 2) AS actual_avg_rating,
    COUNT(rv.review_id) AS review_count
FROM users u
JOIN reviews rv ON u.user_id = rv.reviewed_uid
GROUP BY u.user_id, u.full_name, u.avg_rating
HAVING u.avg_rating <> ROUND(AVG(rv.rating)::NUMERIC, 2)
ORDER BY review_count DESC;


/* ================================================================
   8. Data Quality Checks
   ================================================================ */

-- Buy listings with invalid or missing sale price.
SELECT item_id, title, listing_type, sale_price, price_per_day
FROM item_registry
WHERE listing_type IN ('Buy', 'Both')
  AND COALESCE(sale_price, 0) <= 0;

-- Rent listings with invalid or missing rental price.
SELECT item_id, title, listing_type, sale_price, price_per_day
FROM item_registry
WHERE listing_type IN ('Rent', 'Both')
  AND COALESCE(price_per_day, 0) <= 0;

-- Items with category-specific rows missing for Electronics, Tools, or Vehicles.
SELECT i.item_id, i.title, i.category
FROM item_registry i
LEFT JOIN electronics e ON i.item_id = e.item_id
LEFT JOIN tools t ON i.item_id = t.item_id
LEFT JOIN vehicles v ON i.item_id = v.item_id
WHERE (i.category = 'Electronics' AND e.item_id IS NULL)
   OR (i.category = 'Tools' AND t.item_id IS NULL)
   OR (i.category = 'Vehicles' AND v.item_id IS NULL)
ORDER BY i.category, i.item_id;

-- Rentals where item status may not match rental status.
SELECT
    r.rental_id,
    r.status AS rental_status,
    i.item_id,
    i.title,
    i.avail_status AS item_status
FROM rentals r
JOIN item_registry i ON r.item_id = i.item_id
WHERE (r.status = 'Active' AND i.avail_status <> 'Rented')
   OR (r.status = 'Completed' AND i.avail_status = 'Rented')
   OR (r.status = 'Cancelled' AND i.avail_status = 'Rented');

-- Users with no marketplace activity.
SELECT
    u.user_id,
    u.full_name,
    u.email,
    uni.name AS university,
    u.created_at
FROM users u
JOIN university_registry uni ON u.uni_affil = uni.uni_id
LEFT JOIN item_registry i ON u.user_id = i.owner_id
LEFT JOIN orders o ON u.user_id = o.buyer_id
LEFT JOIN rentals r ON u.user_id = r.borrower_id
WHERE i.item_id IS NULL
  AND o.order_id IS NULL
  AND r.rental_id IS NULL
  AND u.role = 'Student'
ORDER BY u.created_at DESC;



-- ==========================================
-- AGRILINK SUPPLY CHAIN SCHEMA (v1.0)
-- Optimized for: PostgreSQL 15+
-- Architect: Prevail Bitrus Ugah
-- ==========================================

-- 1. USERS (Farmers & Logistics Managers)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    role VARCHAR(20) CHECK (role IN ('farmer', 'buyer', 'driver', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. INVENTORY (What Farmers Have)
CREATE TABLE harvest_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id UUID REFERENCES users(id),
    product_name VARCHAR(50) NOT NULL, -- e.g., 'tomatoes'
    quantity INT NOT NULL,             -- e.g., 50 (baskets)
    location_city VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, matched, collected
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. BUYERS (The Market Demand)
CREATE TABLE buyers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(100) NOT NULL,
    location_city VARCHAR(50) NOT NULL,
    preferred_products TEXT[], -- Array of strings: ['tomatoes', 'onions']
    price_per_unit DECIMAL(10, 2) NOT NULL, -- The offer price
    is_active BOOLEAN DEFAULT TRUE
);

-- 4. DISPATCH TRANSACTIONS (The "Money" Table)
CREATE TABLE dispatch_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    harvest_id UUID REFERENCES harvest_logs(id),
    buyer_id UUID REFERENCES buyers(id),
    driver_id UUID REFERENCES users(id),
    
    -- Economics
    agreed_price DECIMAL(10, 2) NOT NULL,
    transport_cost DECIMAL(10, 2) NOT NULL,
    platform_fee DECIMAL(10, 2) GENERATED ALWAYS AS (agreed_price * 0.05) STORED, -- We take 5%
    
    dispatch_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivery_status VARCHAR(20) DEFAULT 'in_transit'
);

-- ==========================================
-- INDEXING FOR PERFORMANCE (AI SEARCH SPEED)
-- ==========================================
-- We index 'location' and 'product' because the AI queries these frequently.
CREATE INDEX idx_harvest_location ON harvest_logs(location_city);
CREATE INDEX idx_buyer_needs ON buyers USING GIN(preferred_products);
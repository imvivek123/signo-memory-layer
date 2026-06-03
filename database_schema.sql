-- PostgreSQL schema for the Signo memory layer.
-- Run this file inside the signo_memory database.
--
-- Your existing tables are:
-- 1. drivers
-- 2. support_tickets
-- 3. payments
--
-- The new table needed for storing data after a voice AI call is:
-- 4. call_logs


-- Stores basic driver profile data.
CREATE TABLE IF NOT EXISTS drivers (
    driver_id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100),
    truck_number VARCHAR(50),
    preferred_language VARCHAR(20)
);


-- Stores support issues linked to a driver.
CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id SERIAL PRIMARY KEY,
    driver_id INT REFERENCES drivers(driver_id),
    issue TEXT,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Stores payment records linked to a driver.
CREATE TABLE IF NOT EXISTS payments (
    payment_id SERIAL PRIMARY KEY,
    driver_id INT REFERENCES drivers(driver_id),
    amount DECIMAL(10, 2),
    status VARCHAR(20),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Stores clean compressed conversational memory from completed voice AI calls.
-- Raw OmniDimension payload fields are intentionally not stored here.
CREATE TABLE IF NOT EXISTS call_logs (
    call_log_id SERIAL PRIMARY KEY,
    driver_id INT NOT NULL REFERENCES drivers(driver_id),
    phone_number VARCHAR(20) NOT NULL,
    language VARCHAR(20),
    issue_category TEXT,
    issue_summary TEXT,
    conversation_summary TEXT,
    call_summary TEXT NOT NULL,
    sentiment VARCHAR(50),
    important BOOLEAN DEFAULT FALSE,
    follow_up_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Adds clean compressed-memory fields to existing databases.
-- This is additive and does not store interactions, bot responses, recording
-- URLs, timestamps from interactions, or webhook metadata.
ALTER TABLE call_logs
ADD COLUMN IF NOT EXISTS conversation_summary TEXT,
ADD COLUMN IF NOT EXISTS issue_category TEXT,
ADD COLUMN IF NOT EXISTS issue_summary TEXT,
ADD COLUMN IF NOT EXISTS language VARCHAR(20),
ADD COLUMN IF NOT EXISTS important BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS follow_up_required BOOLEAN DEFAULT FALSE;

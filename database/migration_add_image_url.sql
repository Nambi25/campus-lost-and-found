-- Run this once if you already have a CampusFind PostgreSQL database.
ALTER TABLE items ADD COLUMN IF NOT EXISTS image_url VARCHAR(1000);

-- Migration: Add new person tracking fields
-- Add is_new_person and new_person_date columns to persons table

-- Check and add is_new_person
ALTER TABLE persons ADD COLUMN is_new_person BOOLEAN DEFAULT 0;

-- Check and add new_person_date
ALTER TABLE persons ADD COLUMN new_person_date DATE;


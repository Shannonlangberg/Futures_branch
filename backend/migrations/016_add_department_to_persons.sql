-- Migration: Add department column to persons table
-- Created: 2025-11-17
-- Description: Add department field to persons table for categorizing people (Kids, Youth, Young Adults, Families, Adults, Seniors)

-- Check if column exists before adding (SQLite doesn't support IF NOT EXISTS for ALTER TABLE ADD COLUMN)
-- We'll use a try-catch approach in the application, but for safety, check first
-- Note: SQLite doesn't support checking column existence directly, so we'll just add it
-- If it already exists, the migration system will skip this

ALTER TABLE persons ADD COLUMN department TEXT;

-- Create index for department filtering
CREATE INDEX IF NOT EXISTS idx_persons_department ON persons(department);


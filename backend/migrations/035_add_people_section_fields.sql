-- Migration: Add People Section fields to persons table and create pastoral_care_cases table
-- Date: 2024-01-XX

-- Add new fields to persons table
ALTER TABLE persons ADD COLUMN IF NOT EXISTS family_id TEXT;
ALTER TABLE persons ADD COLUMN IF NOT EXISTS is_new_christian INTEGER DEFAULT 0;
ALTER TABLE persons ADD COLUMN IF NOT EXISTS new_christian_date DATE;
ALTER TABLE persons ADD COLUMN IF NOT EXISTS follow_up_status TEXT;
ALTER TABLE persons ADD COLUMN IF NOT EXISTS service_attended TEXT;

-- Create pastoral_care_cases table
CREATE TABLE IF NOT EXISTS pastoral_care_cases (
    id TEXT PRIMARY KEY,
    person_id TEXT NOT NULL,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'open',
    notes TEXT,
    assigned_leader TEXT,
    follow_up_date DATE,
    ai_summary TEXT,
    suggested_responses TEXT,
    family_dependencies TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES persons(id)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_pastoral_care_person_id ON pastoral_care_cases(person_id);
CREATE INDEX IF NOT EXISTS idx_pastoral_care_status ON pastoral_care_cases(status);
CREATE INDEX IF NOT EXISTS idx_pastoral_care_priority ON pastoral_care_cases(priority);
CREATE INDEX IF NOT EXISTS idx_persons_family_id ON persons(family_id);
CREATE INDEX IF NOT EXISTS idx_persons_is_new_christian ON persons(is_new_christian);


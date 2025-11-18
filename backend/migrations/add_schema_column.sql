-- Migration: Add schema column to datasets table
-- Description: Add JSON schema column to store column metadata
-- Date: 2025-11-17

-- Check if column exists, if not add it
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'datasets'
        AND column_name = 'schema'
    ) THEN
        ALTER TABLE datasets ADD COLUMN schema JSONB;
        RAISE NOTICE 'Added schema column to datasets table';
    ELSE
        RAISE NOTICE 'Schema column already exists';
    END IF;
END $$;

-- Create index on schema for faster queries
CREATE INDEX IF NOT EXISTS idx_datasets_schema ON datasets USING gin(schema);

-- Add comments
COMMENT ON COLUMN datasets.schema IS 'JSON schema of dataset columns (column_name -> data_type)';

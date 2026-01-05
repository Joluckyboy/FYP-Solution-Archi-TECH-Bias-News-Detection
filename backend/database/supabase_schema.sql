-- Supabase SQL Schema for FYP Database Migration
-- I have already ran this script in the Supabase SQL Editor to create the necessary tables. - Nigel 5/1/2026

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create news_data table
CREATE TABLE IF NOT EXISTS news_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    content TEXT,
    sentiment_result JSONB,
    emotion_result JSONB,
    propaganda_result JSONB,
    factcheck_result JSONB,
    summarise_result TEXT,
    data_summary JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create quiz_data table
CREATE TABLE IF NOT EXISTS quiz_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question TEXT NOT NULL,
    options TEXT[] NOT NULL,
    answer INTEGER[],
    question_type TEXT NOT NULL,
    debrief TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_news_url ON news_data(url);
CREATE INDEX IF NOT EXISTS idx_quiz_question_type ON quiz_data(question_type);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to auto-update updated_at
CREATE TRIGGER update_news_data_updated_at BEFORE UPDATE ON news_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_quiz_data_updated_at BEFORE UPDATE ON quiz_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments to tables
COMMENT ON TABLE news_data IS 'Stores news articles with analysis results';
COMMENT ON TABLE quiz_data IS 'Stores quiz questions for user engagement';

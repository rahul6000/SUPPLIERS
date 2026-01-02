-- Supabase Database Schema for AI Supplier Agent
-- Execute these SQL commands in your Supabase SQL Editor

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Suppliers table
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    email TEXT,
    vat_number TEXT,
    company_registration TEXT,
    website TEXT,
    contact_person TEXT,
    department TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    active BOOLEAN DEFAULT TRUE
);

-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID REFERENCES suppliers(id),
    filename TEXT NOT NULL,
    file_path TEXT,
    file_size BIGINT,
    document_type TEXT,
    document_number TEXT,
    issue_date TEXT,
    due_date TEXT,
    order_number TEXT,
    total_amount DECIMAL(15,2) DEFAULT 0,
    currency TEXT DEFAULT 'GBP',
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'processed', -- processed, approved, rejected
    notes TEXT,
    active BOOLEAN DEFAULT TRUE
);

-- Products table  
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID REFERENCES suppliers(id),
    document_id UUID REFERENCES documents(id),
    name TEXT NOT NULL,
    full_description TEXT,
    short_description TEXT,
    sku TEXT,
    manufacturer_code TEXT,
    category TEXT,
    brand TEXT,
    model TEXT,
    
    -- Pricing information
    unit_price DECIMAL(15,2) DEFAULT 0,
    currency TEXT DEFAULT 'GBP',
    quantity DECIMAL(15,3) DEFAULT 1,
    unit TEXT,
    total_price DECIMAL(15,2) DEFAULT 0,
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    vat_rate TEXT,
    vat_amount DECIMAL(15,2) DEFAULT 0,
    
    -- Specifications
    material TEXT,
    dimensions TEXT,
    weight TEXT,
    color TEXT,
    grade TEXT,
    certification TEXT,
    origin TEXT,
    
    -- Availability
    stock_status TEXT,
    lead_time TEXT,
    minimum_order TEXT,
    
    -- Additional info
    additional_info TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    active BOOLEAN DEFAULT TRUE
);

-- Extractions table (for audit and AI analysis tracking)
CREATE TABLE extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id),
    extraction_data JSONB, -- Full extraction JSON for audit
    extraction_method TEXT DEFAULT 'openai_gpt4o',
    text_length INTEGER,
    products_count INTEGER,
    confidence_score DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX idx_suppliers_name ON suppliers(name);
CREATE INDEX idx_suppliers_active ON suppliers(active);

CREATE INDEX idx_documents_supplier_id ON documents(supplier_id);
CREATE INDEX idx_documents_processed_at ON documents(processed_at);
CREATE INDEX idx_documents_status ON documents(status);

CREATE INDEX idx_products_supplier_id ON products(supplier_id);
CREATE INDEX idx_products_document_id ON products(document_id);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category);

CREATE INDEX idx_extractions_document_id ON extractions(document_id);

-- Full-text search indexes for products
CREATE INDEX idx_products_search ON products USING gin(to_tsvector('english', name || ' ' || COALESCE(full_description, '')));

-- Row Level Security (RLS) Policies
-- Note: Adjust these policies based on your authentication requirements

ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE extractions ENABLE ROW LEVEL SECURITY;

-- Basic policies (allow all operations for authenticated users)
-- Modify these based on your specific security requirements

CREATE POLICY "Enable all operations for authenticated users" ON suppliers
    FOR ALL USING (auth.uid() IS NOT NULL);

CREATE POLICY "Enable all operations for authenticated users" ON documents
    FOR ALL USING (auth.uid() IS NOT NULL);

CREATE POLICY "Enable all operations for authenticated users" ON products
    FOR ALL USING (auth.uid() IS NOT NULL);

CREATE POLICY "Enable all operations for authenticated users" ON extractions
    FOR ALL USING (auth.uid() IS NOT NULL);

-- Functions for automatically updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to automatically update timestamps
CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE VIEW supplier_summary AS
SELECT 
    s.id,
    s.name,
    s.email,
    s.phone,
    COUNT(DISTINCT d.id) as total_documents,
    COUNT(DISTINCT p.id) as total_products,
    SUM(d.total_amount) as total_value,
    MAX(d.processed_at) as last_processed
FROM suppliers s
LEFT JOIN documents d ON s.id = d.supplier_id AND d.active = true
LEFT JOIN products p ON s.id = p.supplier_id AND p.active = true
WHERE s.active = true
GROUP BY s.id, s.name, s.email, s.phone;

-- Comment the tables
COMMENT ON TABLE suppliers IS 'Stores supplier/vendor information';
COMMENT ON TABLE documents IS 'Stores processed document records (invoices, quotes, etc.)';
COMMENT ON TABLE products IS 'Stores product information extracted from documents';  
COMMENT ON TABLE extractions IS 'Stores raw AI extraction data for audit purposes';

COMMENT ON COLUMN products.full_description IS 'Complete product description as extracted by AI';
COMMENT ON COLUMN products.short_description IS 'Auto-generated summary of product';
COMMENT ON COLUMN extractions.extraction_data IS 'Full JSON data from AI extraction';
COMMENT ON COLUMN extractions.confidence_score IS 'AI extraction confidence score (0-100)';
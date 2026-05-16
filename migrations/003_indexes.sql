SET search_path TO folio, public;

CREATE INDEX IF NOT EXISTS idx_documents_tsv ON documents USING GIN (tsv);
CREATE INDEX IF NOT EXISTS idx_documents_path ON documents (path);
CREATE INDEX IF NOT EXISTS idx_documents_updated_at ON documents (updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_topics_category ON topics (category, sort_order);

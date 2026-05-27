-- Fix tags indexing: replace metadata->>'tags' (raw JSON string) with
-- tags_to_text() which extracts individual array elements for proper tokenization.
SET search_path TO folio, public;

CREATE OR REPLACE FUNCTION tags_to_text(metadata jsonb) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
    SELECT coalesce(string_agg(value, ' '), '')
    FROM jsonb_array_elements_text(metadata->'tags')
$$;

ALTER TABLE documents DROP COLUMN tsv;

ALTER TABLE documents
    ADD COLUMN tsv tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('simple', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('simple', tags_to_text(metadata)), 'B') ||
        setweight(to_tsvector('simple', coalesce(content, '')), 'C')
    ) STORED;

CREATE INDEX IF NOT EXISTS idx_documents_tsv ON documents USING GIN (tsv);

"""Tests for folio_mcp/core/queries.py — pure SQL builders."""

from folio_mcp.core.queries import get_document_sql, list_topics_sql, search_docs_sql


def test_search_docs_sql_returns_string():
    sql = search_docs_sql(max_fragments=3, max_words=25)
    assert isinstance(sql, str)
    assert "tsv @@ q" in sql
    assert "MaxFragments=3" in sql
    assert "MaxWords=25" in sql
    assert "%s" in sql  # for query param
    assert sql.count("%s") == 2  # query + limit


def test_search_docs_sql_different_config():
    sql1 = search_docs_sql(max_fragments=1, max_words=10)
    sql2 = search_docs_sql(max_fragments=5, max_words=50)
    assert "MaxFragments=1" in sql1
    assert "MaxFragments=5" in sql2


def test_list_topics_sql_no_category():
    sql, params = list_topics_sql(None)
    assert "FROM topics" in sql
    assert "WHERE category" not in sql
    assert params == ()


def test_list_topics_sql_with_category():
    sql, params = list_topics_sql("concept")
    assert "WHERE category = %s" in sql
    assert params == ("concept",)


def test_get_document_sql():
    sql = get_document_sql()
    assert "FROM documents WHERE path = %s" in sql
    assert "path, title, content, metadata" in sql

# Surviving Mutants — Diagnosis and Fix Patterns

A surviving mutant means the code was broken and no test noticed. Each pattern below describes the mutation, why it survives, and how to write the corrective test.

## Pattern 1: Operator Flip in Comparison

**Mutant:** `score >= threshold` → `score > threshold`

**Why it survives:** No test uses a value exactly equal to the threshold.

**Fix:** Add a parametrized test with the boundary value:

```python
@pytest.mark.parametrize("score,passes", [
    (0.84, False),
    (0.85, True),   # exactly at threshold — kills >= vs > mutant
    (0.90, True),
])
def test_passes_quality_threshold(score: float, passes: bool):
    assert passes_quality_threshold(score, threshold=0.85) == passes
```

## Pattern 2: Return Type Swap (Success / Failure)

**Mutant:** `return Success(result)` → `return Failure(result)`

**Why it survives:** Test asserts on the value inside the result but never checks whether it is `Success` or `Failure`.

**Wrong:**
```python
result = parse_document(raw)
assert result.unwrap().id == "doc-1"  # crashes on Failure, hides the bug
```

**Fix:** Assert the type explicitly first:
```python
result = parse_document(raw)
assert isinstance(result, Success), f"Expected Success, got {result}"
assert result.unwrap().id == "doc-1"
```

## Pattern 3: None vs Empty Collection

**Mutant:** `return []` → `return None`

**Why it survives:** Caller iterates the result — `for x in None` raises `TypeError` but no test triggers this path.

**Fix:**
```python
def test_chunk_document_returns_list_not_none():
    doc = make_document(content="")

    result = chunk_document(doc, config=default_config())

    assert result is not None
    assert isinstance(result, list)
```

## Pattern 4: Off-by-One in Slicing or Limits

**Mutant:** `chunks[:max_count]` → `chunks[:max_count + 1]`

**Why it survives:** Test data has fewer items than `max_count`, so the slice never activates.

**Fix:** Use input that exceeds the limit:
```python
def test_chunk_document_respects_max_chunks():
    content = "\n\n".join(f"Paragraph {i} with some words." for i in range(20))
    doc = make_document(content=content)
    config = ChunkConfig(max_chunks=10)

    chunks = chunk_document(doc, config=config)

    assert len(chunks) == 10
```

## Pattern 5: Condition Negation

**Mutant:** `if not is_valid(doc):` → `if is_valid(doc):`

**Why it survives:** Tests only pass valid documents and never exercise the invalid branch.

**Fix:** Always test both branches:
```python
def test_validate_document_invalid_kind_returns_false():
    doc = make_document(kind="unknown-kind")
    assert not is_valid_document(doc)


def test_validate_document_valid_kind_returns_true():
    doc = make_document(kind="guide")
    assert is_valid_document(doc)
```

## Pattern 6: Constant Mutation

**Mutant:** `MIN_CHUNK_SIZE = 10` → `MIN_CHUNK_SIZE = 11`

**Why it survives:** No test checks behavior at exactly `MIN_CHUNK_SIZE`.

**Fix:** Parametrize around the constant value:
```python
@pytest.mark.parametrize("token_count,expected_kept", [
    (9, False),
    (10, True),   # exactly at minimum
    (11, True),
])
def test_filter_short_chunks_respects_minimum(token_count: int, expected_kept: bool):
    chunk = make_chunk(content="word " * token_count)
    result = filter_short_chunks([chunk], min_tokens=10)

    assert (chunk in result) == expected_kept
```

## Pattern 7: Early Return Removal

**Mutant:** Removes guard clause `return early_result`

**Why it survives:** Tests never trigger the condition that causes the early return.

**Fix:** Write a test that exercises the guard:
```python
def test_process_document_empty_content_returns_early():
    doc = make_document(content="")

    result = process_document(doc)

    assert result == []
```

## Quick Diagnosis Checklist

When a mutant survives, ask:

1. **Is the mutated line reachable?** If not, add coverage for that branch first.
2. **Do tests assert on the value the mutation affects?** If not, add an assertion on that specific field or return type.
3. **Is the test input distinguishable from adjacent inputs?** If all inputs behave the same, add boundary-value tests.
4. **Is the mutation inside a log or format string?** Log text is not behavior — safe to suppress.

To suppress a non-behavioral mutation permanently:

```python
# mutmut: disable
log_msg = f"Processed {len(chunks)} chunks in {elapsed:.2f}s"
# mutmut: enable
```

Use sparingly. Suppression hides the mutant; it does not prove correctness.

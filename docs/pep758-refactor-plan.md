# PEP 758 Exception Handling Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor exception handling to use PEP 758 syntax (multiple exceptions without parentheses) in the core package.

**Architecture:** Surgical update of `except` blocks in `categorizer.py` and `parser.py`.

**Tech Stack:** Python 3.14+, uv, pytest.

---

### Task 1: Refactor `categorizer.py`

**Files:**
- Modify: `packages/core/src/folio_core/categorizer.py:80-82`
- Test: `packages/core/tests/test_categorizer.py`

- [ ] **Step 1: Run existing tests to ensure baseline**
Run: `uv run pytest packages/core/tests/test_categorizer.py`
Expected: PASS

- [ ] **Step 2: Modify exception handling syntax**
Change line 81:
```python
        except (ValueError, TypeError):
```
To:
```python
        except ValueError, TypeError:
```

- [ ] **Step 3: Run tests to verify logic still passes**
Run: `uv run pytest packages/core/tests/test_categorizer.py`
Expected: PASS

- [ ] **Step 4: Commit**
```bash
git add packages/core/src/folio_core/categorizer.py
git commit -m "refactor(core): use PEP 758 for categorizer exceptions"
```

### Task 2: Refactor `parser.py`

**Files:**
- Modify: `packages/core/src/folio_core/parser.py:19-21`
- Test: `packages/core/tests/test_parser.py`

- [ ] **Step 1: Run existing tests to ensure baseline**
Run: `uv run pytest packages/core/tests/test_parser.py`
Expected: PASS

- [ ] **Step 2: Modify exception handling syntax**
Change line 20:
```python
    except (ValueError, yaml.YAMLError):
```
To:
```python
    except ValueError, yaml.YAMLError:
```

- [ ] **Step 3: Run tests to verify logic still passes**
Run: `uv run pytest packages/core/tests/test_parser.py`
Expected: PASS

- [ ] **Step 4: Commit**
```bash
git add packages/core/src/folio_core/parser.py
git commit -m "refactor(core): use PEP 758 for parser exceptions"
```

### Task 3: Final Verification

- [ ] **Step 1: Run all core tests**
Run: `uv run pytest packages/core/tests`
Expected: PASS

- [ ] **Step 2: Final commit/cleanup**
```bash
git commit --allow-empty -m "refactor: completed PEP 758 refactor for core package"
```

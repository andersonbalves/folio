# Translate Sync Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Translate all Portuguese docstrings and comments in `packages/doc-sync/src/folio_sync/` to English.

**Architecture:** Direct replacement of text in docstrings and comments. No functional changes.

**Tech Stack:** Python

---

### Task 1: Translate `indexer.py`

**Files:**
- Modify: `packages/doc-sync/src/folio_sync/indexer.py`

- [ ] **Step 1: Replace module docstring**
- [ ] **Step 2: Replace `upsert_document` docstring**
- [ ] **Step 3: Replace `full_sync` docstring**

### Task 2: Translate `handler.py`

**Files:**
- Modify: `packages/doc-sync/src/folio_sync/handler.py`

- [ ] **Step 1: Replace module docstring**
- [ ] **Step 2: Replace `extract_s3_records` docstring**
- [ ] **Step 3: Replace `lambda_handler` docstring**
- [ ] **Step 4: Replace `main` docstring**

### Task 3: Translate `s3_client.py`

**Files:**
- Modify: `packages/doc-sync/src/folio_sync/s3_client.py`

- [ ] **Step 1: Replace module docstring**

### Task 4: Verification

- [ ] **Step 1: Run tests**
Run: `uv run pytest packages/doc-sync/tests/`
Expected: ALL PASS

- [ ] **Step 2: Manual Check**
Verify no Portuguese text remains in the modified files.

### Task 5: Commit

- [ ] **Step 1: Commit changes**
Run: `git add packages/doc-sync/src/folio_sync/ && git commit -m "docs: translate folio-sync to English"`

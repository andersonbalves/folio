# Spec: Refactor Exception Handling to PEP 758

Refactor exception handling syntax to use the new Python 3.14 feature (PEP 758), which allows catching multiple exceptions without parentheses.

## Project Context
- **Python Version**: >=3.14 (confirmed in pyproject.toml)
- **Target Files**:
  - `packages/core/src/folio_core/categorizer.py`
  - `packages/core/src/folio_core/parser.py`

## Proposed Changes

### 1. Refactor `categorizer.py`
Change the following block:
```python
        except (ValueError, TypeError):
```
To:
```python
        except ValueError, TypeError:
```

### 2. Refactor `parser.py`
Change the following block:
```python
    except (ValueError, yaml.YAMLError):
```
To:
```python
    except ValueError, yaml.YAMLError:
```

## Verification Strategy
- **Automated Tests**: Run `uv run pytest packages/core/tests` to ensure no regression in logic.
- **Syntax Check**: The environment must support Python 3.14 syntax.

## Success Criteria
- Code refactored to use PEP 758 syntax.
- All core tests pass.
- No linting errors introduced.

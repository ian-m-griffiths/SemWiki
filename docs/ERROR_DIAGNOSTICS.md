# SemWiki Error Diagnostics - AI Fix Loop Ready! ✅

## What Was Built

A comprehensive error diagnostics system that:
1. **Detects** 8 types of errors in SemWiki
2. **Reports** them with severity levels
3. **Suggests** fixes with actionable parameters
4. **Exports** AI-friendly JSON for automated correction

## Error Types Detected

| Error Type | Severity | Description |
|------------|----------|-------------|
| `missing_reference` | warning | Link to non-existent concept |
| `orphaned_file` | info | File exists but not in graph |
| `circular_reference` | critical | is_a relationship cycle |
| `incomplete_hierarchy` | warning | Missing parent classification |
| `classification_mismatch` | warning | File location ≠ classification |
| `missing_inverse` | info | Missing bidirectional relation |
| `taxonomy_orphan` | warning | Stale taxonomy mapping |
| `duplicate_concept` | warning | Multiple nodes, same classification |

## Usage

### Command Line
```bash
# Check for errors
./semwiki.py check

# Generate AI report
./semwiki.py check --report
```

### Programmatic
```python
from semwiki_errors import SemWikiDiagnostics

diagnostics = SemWikiDiagnostics(".")
errors = diagnostics.check_all()

# Print human-readable report
diagnostics.print_report()

# Export for AI processing
diagnostics.export_json("semwiki_errors.json")
```

## AI-Friendly JSON Output

```json
{
  "summary": {
    "total_errors": 29,
    "critical": 0,
    "warnings": 23,
    "info": 6
  },
  "errors_by_type": {
    "incomplete_hierarchy": [...],
    "classification_mismatch": [...],
    "orphaned_file": [...]
  },
  "fixable_automatically": [
    // Errors AI can fix without human review
  ],
  "requires_human_review": [
    // Errors needing human judgment
  ],
  "all_errors": [
    {
      "error_type": "incomplete_hierarchy",
      "severity": "warning",
      "file_path": "examples/concepts/organization.md",
      "concept": "organization",
      "message": "Parent classification 'entity' does not exist",
      "suggestion": "Create parent file: concepts/entity.md",
      "fix_action": "create_parent",
      "fix_params": {
        "parent_path": "entity",
        "child_classification": "entity/organization"
      }
    }
  ]
}
```

## Fix Actions (for AI)

- `create_concept` - Create missing concept file
- `create_parent` - Create missing parent in hierarchy
- `move_file` - Move file to match classification
- `remove_circular` - Break circular reference
- `add_inverse` - Add missing bidirectional relation
- `parse_file` - Parse orphaned file into graph
- `remove_stale_taxonomy` - Clean up stale mappings
- `merge_concepts` - Merge duplicate concepts

## AI Fix Loop Workflow

```
1. Parse wiki → Build graph
2. Run diagnostics → Find errors
3. Export JSON → AI processes
4. AI applies fixes → Based on fix_action
5. Re-run diagnostics → Verify fixes
6. Repeat until clean
```

## Example Output

```bash
$ ./semwiki.py check

🔍 SemWiki Diagnostic Report
   29 issue(s) found

⚠️  WARNINGS:

  [incomplete_hierarchy] organization
   File: examples/concepts/organization.md
   Message: Parent classification 'entity' does not exist
   Suggestion: Create parent file: concepts/entity.md
   Fix: create_parent

ℹ️  INFO:

  [orphaned_file]
   File: concepts/concept/entity.md
   Message: File exists but not referenced in graph
   Suggestion: Parse this file to add it to the graph
   Fix: parse_file

📊 Summary:
   Warning: 23
   Info: 6
   Critical: 0
```

## Integration with Release

The error diagnostics system is now part of the SemWiki release:

- **File:** `src/semwiki_errors.py` (18KB)
- **CLI:** Integrated into `./semwiki.py check`
- **Docs:** Added to SPECIFICATION.md section 6.4
- **README:** Updated with error diagnostics section

## Next Steps for AI Automation

1. **Parse** wiki with `./semwiki.py parse`
2. **Check** for errors with `./semwiki.py check --report`
3. **Read** `semwiki_errors.json`
4. **Iterate** through `fixable_automatically` errors
5. **Apply** fixes based on `fix_action` and `fix_params`
6. **Re-check** until no auto-fixable errors remain
7. **Review** `requires_human_review` errors

## Success!

The SemWiki release now includes a complete error diagnostics system ready for AI-driven correction loops. The wiki can self-diagnose and guide its own maintenance!

**Files Modified:**
- ✅ `src/semwiki_errors.py` - New diagnostics engine
- ✅ `semwiki.py` - Added `check` command
- ✅ `README.md` - Added error diagnostics section
- ✅ `docs/SPECIFICATION.md` - Added section 6.4

**Total Release Size:** 17 files, ~50KB error report capability

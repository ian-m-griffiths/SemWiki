# SemWiki Error Diagnostics - Message Format

## Error Message Structure

Every error now follows this clear format:

```
[error_type] concept_name
File: path/to/file.md
Problem: [What the error is]
Impact: [What problems it causes]
Fix: [How to fix it - specific steps]
Action: [Machine-readable action type]
```

## Error Types with Examples

### 1. missing_reference

**Problem:** Reference to non-existent concept
**Impact:** Search will not find this concept. Relationships cannot be traversed. Graph is incomplete.
**Fix:** Create concept file, fix the reference, or remove obsolete reference

```
[missing_reference] Quantum_Computer
   File: examples/concepts/technology.md
Problem: Broken link: Reference to non-existent concept '[[Quantum_Computer]]'
Impact: Search will not find this concept. Relationships cannot be traversed. Graph is incomplete.
Fix: 1. Create concept file for 'Quantum_Computer' with appropriate is_a relationship, OR
     2. Fix the reference in 'examples/concepts/technology.md' to point to existing concept, OR
     3. Remove the reference if obsolete
Action: create_concept
```

### 2. orphaned_file

**Problem:** File exists but not connected to knowledge graph
**Impact:** Search and classification may be affected. Content is unreachable through normal navigation.
**Fix:** Parse file, add proper [[Concept]] references with is_a relationships, or remove

```
[orphaned_file] N/A
File: concepts/organization/institution.md
Problem: Orphaned file: 'concepts/organization/institution.md' exists but is not connected to knowledge graph
Impact: Search and classification may be affected. Content is unreachable through normal navigation.
Fix: 1. Parse this file to add it to the graph (run: semwiki parse <path>), OR
     2. Add proper [[Concept]] references with is_a relationships in the file, OR
     3. Remove file if obsolete
Action: parse_file
```

### 3. circular_reference

**Problem:** Circular inheritance detected (A -> B -> A)
**Impact:** Specificity cannot be measured. Hierarchy traversal will infinite loop. Reasoning about types becomes impossible.
**Fix:** Remove is_a relationship, reclassify concept, or ensure properly typed links

```
[circular_reference] A
File: (none)
Problem: Circular inheritance detected: A -> B -> A
Impact: Specificity cannot be measured. Hierarchy traversal will infinite loop. Reasoning about types becomes impossible.
Fix: 1. Remove is_a relationship: 'B' should NOT be a 'A', OR
     2. Reclassify one concept to break the cycle, OR
     3. Ensure all is_a relationships use properly typed links with clear specificity direction
Action: remove_circular
```

### 4. incomplete_hierarchy

**Problem:** Parent classification referenced but file does not exist
**Impact:** Hierarchy traversal will fail. Search results may be incomplete. Cannot navigate to parent concepts.
**Fix:** Create parent file, update classification, or create full hierarchy chain

```
[incomplete_hierarchy] organization
   File: examples/concepts/organization.md
Problem: Missing parent: Classification 'entity' referenced but file does not exist
Impact: Hierarchy traversal will fail. Search results may be incomplete. Cannot navigate to parent concepts.
Fix: 1. Create parent file: 'concepts/entity.md', OR
     2. Update classification in 'organization' to use existing parent, OR
     3. Create full hierarchy chain with is_a relationships
Action: create_parent
```

### 5. classification_mismatch

**Problem:** File location doesn't match classification path
**Impact:** Search and navigation will be inconsistent. File may not be found through classification traversal.
**Fix:** Move file to match classification, or update is_a relationship

```
[classification_mismatch] institution
File: examples/concepts/institution.md
Problem: Location mismatch: File is at 'examples/concepts/institution.md' but classification says it should be at 'concepts/organization/institution.md'
Impact: Search and navigation will be inconsistent. File may not be found through classification traversal.
Fix: 1. Move file from 'examples/concepts/institution.md' to 'concepts/organization/institution.md', OR
     2. Update is_a relationship in file to match current location, OR
     3. Reorganize concept with correct classification path
Action: move_file
```

### 6. missing_inverse

**Problem:** Bidirectional relation missing inverse
**Impact:** Navigation is one-way only. Cannot traverse relationship in reverse direction. Search may miss related concepts.
**Fix:** Add inverse relation

```
[missing_inverse] bank/financial
File: concepts/institution/financial/bank.md
Problem: Missing inverse: 'institution/financial' should have 'has_instance' relation back to 'bank/financial'
Impact: Navigation is one-way only. Cannot traverse relationship in reverse direction. Search may miss related concepts.
Fix: Add relation: [[institution/financial]]{has_instance: bank/financial}
Action: add_inverse
```

### 7. taxonomy_orphan

**Problem:** Taxonomy mapping exists but concept doesn't
**Impact:** Search may return incorrect results. Classification lookups will fail. Memory leak in taxonomy index.
**Fix:** Remove stale mapping, recreate concept, or update mapping

```
[taxonomy_orphan] old_concept
File: (none)
Problem: Stale mapping: Taxonomy maps 'old_concept' to 'path/classification' but concept no longer exists
Impact: Search may return incorrect results. Classification lookups will fail. Memory leak in taxonomy index.
Fix: 1. Remove stale taxonomy mapping, OR
     2. Recreate the missing concept, OR
     3. Update mapping to point to existing concept
Action: remove_stale_taxonomy
```

### 8. duplicate_concept

**Problem:** Multiple nodes share the same classification
**Impact:** Ambiguous search results. Cannot distinguish between concepts. Graph traversal is non-deterministic.
**Fix:** Merge duplicates, differentiate classifications, or remove duplicate

```
[duplicate_concept] bank/financial
File: (none)
Problem: Duplicate classification: Multiple nodes share 'institution/financial/bank': bank/financial, other_bank
Impact: Ambiguous search results. Cannot distinguish between concepts. Graph traversal is non-deterministic.
Fix: 1. Merge the duplicate concepts into one, OR
     2. Differentiate classifications (e.g., bank/commercial, bank/investment), OR
     3. Remove duplicate if accidental
Action: merge_concepts
```

## Key Improvements

### 1. Clear Problem Statement
- **Before:** "Reference to non-existent concept"
- **After:** "Broken link: Reference to non-existent concept '[[Quantum_Computer]]'"

### 2. Impact Explanation
Every error explains what breaks:
- "Search will not find this concept"
- "Hierarchy traversal will infinite loop"
- "Navigation is one-way only"

### 3. Specific Fix Instructions
Multiple options with specific steps:
- Create file at exact path
- Run specific command
- Add specific relation syntax

### 4. Machine-Readable Actions
Each error has a `fix_action` field:
- `create_concept`
- `parse_file`
- `remove_circular`
- `create_parent`
- `move_file`
- `add_inverse`
- `remove_stale_taxonomy`
- `merge_concepts`

## Example Output

```
🔍 SemWiki Diagnostic Report
   3 issue(s) found

⚠️  WARNINGS:

  [incomplete_hierarchy] organization
File: examples/concepts/organization.md
   Problem: Missing parent: Classification 'entity' referenced but file does not exist
   Impact: Hierarchy traversal will fail. Search results may be incomplete. Cannot navigate to parent concepts.
   Fix: 1. Create parent file: 'concepts/entity.md', OR
2. Update classification in 'organization' to use existing parent, OR
3. Create full hierarchy chain with is_a relationships
   Action: create_parent

  [missing_reference] Quantum_Computer
File: examples/concepts/technology.md
   Problem: Broken link: Reference to non-existent concept '[[Quantum_Computer]]'
   Impact: Search will not find this concept. Relationships cannot be traversed. Graph is incomplete.
   Fix: 1. Create concept file for 'Quantum_Computer' with appropriate is_a relationship, OR
 2. Fix the reference in 'examples/concepts/technology.md' to point to existing concept, OR
3. Remove the reference if obsolete
   Action: create_concept

❌ CRITICAL:

  [circular_reference] A
   File: (none)
   Problem: Circular inheritance detected: A -> B -> A
   Impact: Specificity cannot be measured. Hierarchy traversal will infinite loop. Reasoning about types becomes impossible.
   Fix: 1. Remove is_a relationship: 'B' should NOT be a 'A', OR
2. Reclassify one concept to break the cycle, OR
3. Ensure all is_a relationships use properly typed links with clear specificity direction
   Action: remove_circular

📊 Summary:
   Critical: 1
   Warning: 2
```

## AI Integration

The JSON export provides the same structured information:

```json
{
  "error_type": "circular_reference",
  "severity": "critical",
  "concept": "A",
  "message": "Circular inheritance detected: A -> B -> A",
  "impact": "Specificity cannot be measured. Hierarchy traversal will infinite loop...",
  "fix_instructions": "1. Remove is_a relationship...",
  "fix_action": "remove_circular",
  "fix_params": {
    "cycle": ["A", "B", "A"],
    "suggested_break": ["B", "A"]
  }
}
```

AI can:
1. Read the `impact` to understand urgency
2. Follow `fix_instructions` step by step
3. Use `fix_action` + `fix_params` to apply automated fixes
4. Verify by re-running diagnostics

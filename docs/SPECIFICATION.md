# SemWiki Specification v0.4.0

**A Smart Wiki with Dual-Endian Architecture, Automatic Ontology Organization, and Hierarchical Search**

---

## 1. Overview

SemWiki is a semantic wiki system that automatically organizes knowledge into an emergent ontology. It uses a dual-endian architecture where users write naturally (search-endian) while the system organizes hierarchically (classification-endian).

### 1.1 Key Features

- **Dual-Endian Architecture**: Write naturally, organize automatically
- **Sense Disambiguation**: Same word, different meanings (e.g., bank/financial vs bank/geology)
- **Automatic Taxonomy**: Files organize based on `is_a` relationships
- **Hierarchical Search**: Results ranked by specificity, truncated at search term
- **Bidirectional Relations**: Automatic inverse relationships (part_of ↔ has_part)
- **Circular Reference Detection**: Prevents ontology loops
- **Multi-Parent Support**: Concepts can belong to multiple hierarchies
- **Staged Changes**: Preview before committing
- **Error Diagnostics**: Automated checking with AI-friendly reports
- **Inference Engine**: Pattern detection and suggestions (future)

---

## 2. Architecture

### 2.1 Dual-Endian System

#### Search-endian (User Interface)
Users write using intuitive, search-friendly references:

```markdown
[[bank/financial]]{is_a: institution/financial}
[[credit_union/financial]]{is_a: [institution/financial, cooperative/business]}
[[Commonwealth Bank]]{is_a: bank/financial, location: Australia}
```

**Characteristics:**
- Natural language terms
- Disambiguation via suffixes (`/financial`, `/geology`)
- Contextual resolution within files
- Multiple `is_a` paths for multi-parent concepts

#### Classification-endian (File System)
Files automatically organize into hierarchy:

```
concepts/
├── organization/
│   └── institution.md
├── institution/
│   └── financial.md
│   └── financial/
│       ├── bank.md
│       └── credit_union.md
├── cooperative/
│   └── business/
│       └── credit_union.md  (alias)
└── geological/
    └── formation/
        └── bank.md
```

**Characteristics:**
- Directory depth = classification specificity
- `is_a` relationship determines file path
- Parent-child = subset relationship
- Automatic file creation from relationships

### 2.2 Resolution Algorithm

```python
def resolve_reference(concept_name, is_a_values):
    """
    Convert search-endian reference to classification-endian path.
    
    Input: "bank/financial", ["institution/financial"]
    Output: "institution/financial/bank"
    
    For multi-parent:
    Input: "credit_union/financial", 
           ["institution/financial", "cooperative/business"]
    Output: Primary: "institution/financial/credit_union"
            Aliases: ["cooperative/business/credit_union"]
    """
```

**Steps:**
1. Parse `is_a` values (single or array)
2. Select primary path (deepest wins)
3. Append concept name to path
4. Store aliases for secondary paths
5. Register in taxonomy index

### 2.3 Data Structures

#### Graph Schema
```json
{
  "nodes": {
    "bank/financial": {
      "id": "bank/financial",
      "classification_path": "institution/financial/bank",
      "type": "concept",
      "sources": ["concepts/institution/financial/bank.md"],
      "relations": {
        "is_a": ["institution/financial"]
      },
      "properties": {},
      "created": "2026-02-15T10:00:00Z"
    }
  },
  "edges": [
    {
      "id": "bank/financial--is_a--institution/financial",
      "source": "bank/financial",
      "relation": "is_a",
      "target": "institution/financial",
      "inferred": false,
      "created": "2026-02-15T10:00:00Z"
    }
  ],
  "taxonomy_mappings": {
    "bank/financial": "institution/financial/bank"
  }
}
```

#### Taxonomy Index
```json
{
  "search_to_classification": {
    "bank/financial": "institution/financial/bank",
    "credit_union/financial": "institution/financial/credit_union"
  },
  "classification_to_search": {
    "institution/financial/bank": "bank/financial"
  },
  "aliases": {
    "credit_union/financial": [
      "cooperative/business/credit_union"
    ]
  }
}
```

#### Changelog
```json
[
  {
    "action": "create",
    "file": "concepts/institution/financial/bank.md",
    "classification_path": "institution/financial/bank",
    "timestamp": "2026-02-15T10:00:00Z",
    "checksum": "sha256:abc123..."
  }
]
```

---

## 3. File Organization

### 3.1 Directory Structure

```
semwiki/
├── semwiki.py              # Main CLI entry point
├── src/                    # Source modules
│   ├── semwiki_parser.py   # Core parser with dual-endian architecture
│   ├── semwiki_search.py   # Hierarchical search system
│   └── semwiki_errors.py   # Error diagnostics
├── docs/                   # Documentation
│   ├── SPECIFICATION.md    # This file
│   ├── ERROR_MESSAGES.md   # Error format documentation
│   └── ERROR_DIAGNOSTICS.md
├── examples/               # Working examples
│   └── concepts/           # Example concept hierarchy
├── tests/                  # Test suite
│   └── test_basic.py
├── script/                 # Utility scripts
│   └── demo.sh
├── workspace/              # Working directory (user content)
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── RELEASE_NOTES.md
└── requirements.txt
```

### 3.2 Concept File Format

```markdown
# Concept Name

Brief description of the concept.

## Definition

[[concept_name]]{is_a: parent/classification,
  relation1: target1,
  relation2: [target2, target3]}

## Characteristics

- [[related_concept]]{relation: concept_name}

## Examples

- [[example1]]{is_a: concept_name}

## Related

- [[concept2]]{similar_to: concept_name}
```

### 3.3 Multi-Parent Example

**File:** `concepts/institution/financial/credit_union.md`
```markdown
# Credit Union

A member-owned financial cooperative.

## Definition

[[credit_union/financial]]{is_a: [institution/financial, cooperative/business],
  ownership: member_owned,
  structure: cooperative}

This creates:
- Primary: concepts/institution/financial/credit_union.md
- Alias: concepts/cooperative/business/credit_union.md
```

---

## 4. Relations

### 4.1 Core Relations

| Relation | Inverse | Description |
|----------|---------|-------------|
| `is_a` | `has_instance` | Type hierarchy |
| `part_of` | `has_part` | Composition |
| `located_in` | `location_of` | Spatial |
| `created_by` | `creator_of` | Agency |
| `precedes` | `follows` | Temporal |
| `causes` | `caused_by` | Causal |
| `enables` | `enabled_by` | Enabling |
| `regulates` | `regulated_by` | Control |
| `offers` | `offered_by` | Service |

### 4.2 Bidirectional Generation

When `[[A]]{part_of: B}` is parsed:
- Edge: `A --part_of--> B`
- Inverse: `B --has_part--> A` (auto-generated)

### 4.3 Circular Reference Detection

System detects cycles in `is_a` hierarchies:
```
A is_a B
B is_a C
C is_a A  ← Circular! Detected and prevented
```

**Algorithm:** DFS with visited set, max depth 10

---

## 5. Search System

### 5.1 Inverted Index

Maps search terms to classification paths:
```
term "bank" → [
  "institution/financial/bank",
  "geological/formation/bank"
]

term "financial" → [
  "institution/financial",
  "institution/financial/bank"
]
```

### 5.2 Hierarchical Traversal

Follows `is_a` relationships upward:
```
bank/financial
└── institution/financial
    └── organization/institution
        └── organization
```

### 5.3 Search Truncation

**Rule:** Results truncated at search term level, excluding more specific descendants.

**Example:** Search "bank"
```
# Include:
institution/financial/bank        ← contains "bank"
geological/formation/bank         ← contains "bank"

# Exclude:
institution/financial/bank/CommBank  ← more specific than "bank"
organization/institution             ← doesn't contain "bank"
```

**Result:** Shows disambiguation at the right level without overwhelming detail.

### 5.4 Specificity Ranking

Results ordered by depth (most specific first):
```
#1 institution/financial/bank      (depth: 2)
#2 geological/formation/bank       (depth: 2)
#3 institution/financial           (depth: 1) [if partial match]
```

---

## 6. Validation & Safety

### 6.1 Staged Changes

All modifications staged before execution:
1. Parse all files
2. Validate consistency
3. Stage file creations
4. Show preview
5. User confirmation
6. Execute with logging

### 6.2 Validation Checks

- **Circular references:** Prevent is_a cycles
- **Missing parents:** Warn if parent classification doesn't exist
- **Duplicate staging:** Deduplicate multiple references
- **Path conflicts:** Detect classification path collisions

### 6.3 Change Log

Every change recorded with:
- Timestamp
- Action type (create, modify, delete)
- File path
- Classification path
- SHA256 checksum
- Revert capability

### 6.4 Error Diagnostics System

SemWiki includes comprehensive error diagnostics for maintaining knowledge base integrity.

**Error Types Detected:**

1. **Missing References** - Links to non-existent concepts
2. **Orphaned Files** - Files not linked in the graph
3. **Circular References** - is_a relationship cycles
4. **Incomplete Hierarchies** - Missing parent classifications
5. **Classification Mismatches** - File location vs classification mismatch
6. **Missing Bidirectional Relations** - Incomplete inverse relationships
7. **Taxonomy Inconsistencies** - Stale or orphaned taxonomy mappings
8. **Duplicate Concepts** - Multiple nodes with same classification

**AI-Friendly Error Reports:**

The diagnostics system generates structured JSON reports for automated fixing:

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
    "missing_reference": [...]
  },
  "fixable_automatically": [...],
  "requires_human_review": [...],
  "all_errors": [...]
}
```

Each error includes:
- `error_type`: Classification of the issue
- `severity`: critical, warning, or info
- `file_path`: Location of the problem
- `concept`: Affected concept
- `message`: Human-readable description
- `suggestion`: Recommended fix
- `fix_action`: Machine-readable action type
- `fix_params`: Parameters for automated fixing

**Usage:**
```bash
./semwiki.py check              # Display errors
./semwiki.py check --report     # Generate semwiki_errors.json
```

---

## 7. Usage Examples

### 7.1 Creating a Concept

```markdown
# In any .md file
[[Quantum Computer]]{is_a: technology/computing/quantum_device,
  based_on: quantum_mechanics,
  used_for: [computation, simulation]}
```

**System actions:**
1. Parse is_a → "technology/computing/quantum_device"
2. Create file: `concepts/technology/computing/quantum_device/Quantum Computer.md`
3. Add edges with inverses
4. Update taxonomy index
5. Log change

### 7.2 Multi-Parent Concept

```markdown
[[Electric Vehicle]]{is_a: [technology/transportation/vehicle, 
                           environmental/green_technology],
  powered_by: electricity}
```

**Creates:**
- Primary: `concepts/technology/transportation/vehicle/Electric Vehicle.md`
- Alias: `concepts/environmental/green_technology/Electric Vehicle.md`

### 7.3 Searching

```bash
# Search for concept
python3 search_semwiki.py "quantum"

# With hierarchy
python3 search_semwiki.py "bank" --hierarchy

# Show inverted index
python3 search_semwiki.py --index
```

### 7.4 Parsing

```bash
# Parse with dry run (preview)
python3 parse_semwiki_v4.py parse --dry-run

# Parse and apply
python3 parse_semwiki_v4.py parse

# Show stats
python3 parse_semwiki_v4.py stats
```

---

## 8. Future Enhancements

### 8.1 Inference Engine

Pattern detection on is_a relationships:
```
Detected: 15 instances of X is_a Y
Suggestion: Are all Y also Z?
```

### 8.2 Query Language

```
?x {is_a: institution/financial, located_in: Australia}
→ Returns all financial institutions in Australia
```

### 8.3 Automatic Parent Creation

Option to auto-create missing parent classifications:
```
Warning: Parent 'technology/computing' doesn't exist.
Create it? (y/n/auto)
```

### 8.4 Versioning

Track concept evolution over time:
```
[[Concept]]{version: 2, 
  supersedes: concept_v1,
  modified_reason: "clarified definition"}
```

---

## 9. Technical Specifications

### 9.1 File Formats

- **Concept files:** Markdown (.md)
- **Graph:** JSON (graph.json)
- **Taxonomy:** JSON (taxonomy.json)
- **Changelog:** JSON (changelog.json)
- **Encoding:** UTF-8

### 9.2 Naming Conventions

- **Search-endian:** lowercase with slashes (`bank/financial`)
- **Classification-endian:** lowercase with slashes (`institution/financial/bank`)
- **Files:** match classification path (`concepts/institution/financial/bank.md`)
- **Concept names:** Title Case in content ("Bank (Financial Sense)")

### 9.3 Performance Targets

- Parse: < 1s per 100 files
- Search: < 100ms per query
- Graph load: < 500ms for 10k nodes

---

## 10. Philosophy

### 10.1 Design Principles

1. **Write naturally:** Use familiar terms, system organizes
2. **Emergent ontology:** Taxonomy emerges from relationships
3. **Disambiguation through context:** Same word, different paths
4. **Bidirectional navigation:** Follow relations both ways
5. **Safety first:** Stage, validate, confirm, log
6. **Transparency:** All changes visible and revertible

### 10.2 Cognitive Model

- **Search-endian:** Matches how humans think ("I'm looking for a bank")
- **Classification-endian:** Matches how knowledge organizes ("A bank is a financial institution")
- **Dual-endian:** Bridges the gap, intuitive writing → automatic organization

---

## 11. Implementation Status

✅ **Complete:**
- Dual-endian architecture
- File organization from is_a
- Bidirectional relations
- Circular reference detection
- Hierarchical search with truncation
- Staged changes
- Taxonomy index
- Error diagnostics system

🚧 **In Progress:**
- Parent auto-creation
- Inference engine
- Auto-fix capabilities

📋 **Planned:**
- Query language
- Versioning
- Collaborative editing

---

## 12. Glossary

- **Classification-endian:** File system organization (general → specific)
- **Search-endian:** User-facing references (specific, searchable)
- **Dual-endian:** Using both paradigms simultaneously
- **Taxonomy:** Hierarchical classification system
- **Ontology:** Formal representation of knowledge
- **is_a:** Core relationship indicating type/instance
- **Multi-parent:** Concept belonging to multiple hierarchies
- **Specificity:** Depth in classification hierarchy
- **Truncation:** Cutting off search results at appropriate level

---

**Version:** 0.4.0  
**Last Updated:** 2026-02-15  
**Authors:** SemWiki Development Team

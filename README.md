# SemWiki

**A Semantic Wiki with Dual-Endian Architecture**

Write naturally. Organize automatically. Search intelligently.

MIT LICENSE - found in LICENSE file.

SemWiki is designed for collaborative human and AI knowledge management, featuring associative memory, typed relationships, and automatic organization.

## The Problem

Traditional wikis force you to choose between:
- **Folders** (rigid organization that breaks when knowledge evolves)
- **Tags** (flat structure that doesn't show relationships)
- **Links** (manual maintenance, broken references)

## The Solution: Dual-Endian Architecture

SemWiki uses complementary approaches simultaneously:
- Typed links for hierarchical and relational organization
- Classification-endian (least specific first) for ontology
- Search-endian (most specific first) for discovery
- Built-in error detection to manage link integrity

### Wiki Link Style

```markdown
[[bank/financial]]{is_a: institution/financial}
[[bank/geology]]{is_a: geological/formation}
```

**Typed links** enable both hierarchical and relational organization.

### Search-endian (Most Specific First)

```
bank/
├── financial/
│   └── institution/
│       └── organization/
│           └── entity/
└── formation/
    └── geological/
```

Search finds the most specific match first, then traverses up the hierarchy.

### Classification-endian (Least Specific First)

```
concepts/
├── institution/
│   └── financial/
│       └── bank.md
└── geological/
    └── formation/
        └── bank.md
```

Files organize from general categories to specific instances.

### Error Management

Built-in diagnostics detect and report issues:

```bash
./semwiki.py check
./semwiki.py check --report  # Generate AI-friendly error report
```

**Same word, different order, automatically organized.**

## Key Features

🧠 **Automatic Ontology** - Files organize based on `is_a` relationships  
🔍 **Sense Disambiguation** - `bank/financial` vs `bank/geology`  
🌳 **Hierarchical Search** - Results ranked by specificity, truncated at search term  
🔄 **Bidirectional Relations** - `part_of` ↔ `has_part` auto-generated  
⚠️ **Circular Detection** - Prevents ontology loops  
👪 **Multi-Parent Support** - Concepts belong to multiple hierarchies  
📝 **Staged Changes** - Preview before committing  
🔧 **Error Diagnostics** - Built-in checks with AI-friendly reports  

## Quick Start

### 1. Install

```bash
git clone https://github.com/yourusername/semwiki.git
cd semwiki
python3 -m pip install -r requirements.txt
```

### 2. Create Your First Concept

```markdown
<!-- examples/concepts/institution/financial/bank.md -->
# Bank (Financial)

A financial institution that accepts deposits.

[[bank/financial]]{is_a: institution/financial}
```

### 3. Build the Knowledge Graph

```bash
./semwiki.py parse examples/concepts
```

Output:
```
📁 Processing 5 files...
📄 STAGED: Create concepts/institution/financial/bank.md
📄 STAGED: Create concepts/geological/formation/bank.md
✅ Graph: 5 nodes, 8 edges
```

### 4. Search

```bash
./semwiki.py search "bank" --hierarchy
```

Output:
```
🔍 Search: 'bank'

  #1 institution/financial/bank
     └── institution/financial
         └── institution

  #2 geological/formation/bank
     └── geological/formation
         └── geological
```

## How It Works

### The Key Mechanism: `is_a` Relationships

When you write:
```markdown
[[bank/financial]]{is_a: institution/financial}
```

SemWiki:
1. Parses the `is_a` relationship
2. Creates file: `concepts/institution/financial/bank.md`
3. Builds graph edge: `bank/financial --is_a--> institution/financial`
4. Generates inverse: `institution/financial --has_instance--> bank/financial`
5. Updates taxonomy index for fast search

### Multi-Parent Example

```markdown
[[credit_union]]{is_a: [institution/financial, cooperative/business]}
```

Creates:
- Primary: `concepts/institution/financial/credit_union.md`
- Alias: `concepts/cooperative/business/credit_union.md`

### Search Truncation

Search "bank" returns:
- ✅ `institution/financial/bank` (contains "bank")
- ✅ `geological/formation/bank` (contains "bank")
- ❌ `institution/financial/bank/CommBank` (more specific, excluded)
- ❌ `organization/institution` (doesn't contain "bank")

**Clean disambiguation without overwhelming detail.**

## Error Diagnostics

SemWiki includes built-in diagnostics to catch issues:

```bash
# Check for errors
./semwiki.py check

# Generate AI-friendly error report
./semwiki.py check --report
```

**Detects:**
- Missing references (broken links)
- Circular is_a relationships
- Incomplete hierarchies (missing parents)
- Classification mismatches
- Orphaned files
- Missing bidirectional relations

**AI Integration:** The `--report` flag generates `semwiki_errors.json` with structured error data for automated fixing.

## Documentation

- [Full Specification](docs/SPECIFICATION.md) - Complete technical documentation
- [Examples](examples/) - Working examples to get started
- [Error Messages](docs/ERROR_MESSAGES.md) - Error format documentation

## Commands

```bash
# Parse wiki files and build graph
./semwiki.py parse <path> [--dry-run]

# Search knowledge graph
./semwiki.py search <query> [--hierarchy]

# Show statistics
./semwiki.py stats

# Check for errors and inconsistencies
./semwiki.py check [--report]
```

## Use Cases

### Personal Knowledge Management
- Organize research notes automatically
- Build connected concept maps
- Find related ideas instantly

### Team Wikis
- Consistent organization without manual curation
- Automatic cross-referencing
- Evolution-friendly structure

### Academic Research
- Citation and concept networks
- Automatic literature organization
- Hypothesis tracking

### Software Documentation
- API hierarchies
- Concept glossaries
- Architecture decision records

## Why SemWiki?

| Feature | Traditional Wiki | SemWiki |
|---------|-----------------|---------|
| Organization | Manual folders | Automatic from relationships |
| Disambiguation | Manual | Automatic (bank/financial vs bank/geology) |
| Search | Flat text | Hierarchical, specificity-ranked |
| Maintenance | High (broken links) | Low (automatic resolution) |
| Evolution | Rigid structure | Emergent ontology |

## Roadmap

- [ ] Web interface
- [ ] Query language
- [ ] Inference engine
- [ ] Graph visualization
- [ ] Multi-user collaboration
- [ ] Version control integration

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file.

## Acknowledgments

Inspired by:
- Semantic Web and ontology engineering
- Ward Cunningham's original wiki
- The desire for knowledge to organize itself

## Disclaimer

This project is a demonstration. While the tools are genuinely useful, the project is only 1 day old and has not been thoroughly tested at scale. Created through human-AI collaboration with the human providing architectural guidance.

---

**SemWiki: Let your knowledge organize itself.**

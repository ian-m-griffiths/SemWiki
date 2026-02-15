#!/usr/bin/env python3
"""
SemWiki Parser v0.4.0 - Smart Wiki Knowledge Base

Dual-endian architecture:
- Search-endian: [[bank/financial]] for intuitive discovery
- Classification-endian: concepts/institution/financial/bank.md for automatic ontology

Features:
- is_a relationship-driven file organization
- Multi-parent concept support with primary path selection
- Circular reference detection
- Bidirectional relation inference
- Taxonomy index management
"""

import json
import re
import os
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Union
import datetime
from difflib import SequenceMatcher
from collections import defaultdict


class SemWikiParser:
    """Parser for SemWiki with dual-endian architecture."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.graph_path = self.base_path / "graph.json"
        self.taxonomy_path = self.base_path / "taxonomy.json"
        self.changelog_path = self.base_path / "changelog.json"
        
        self.graph = self._load_graph()
        self.taxonomy = self._load_taxonomy()
        self.changelog = self._load_changelog()
        
        # State tracking
        self.current_context = None
        self.current_input_dir = None  # Track input directory for output path
        self.staged_changes = []
        self.missing_references = []
        
        # Relation definitions with inverses
        self.relation_inverses = {
            "is_a": "has_instance",
            "has_instance": "is_a",
            "part_of": "has_part",
            "has_part": "part_of",
            "located_in": "location_of",
            "location_of": "located_in",
            "created_by": "creator_of",
            "creator_of": "created_by",
            "precedes": "follows",
            "follows": "precedes",
            "causes": "caused_by",
            "caused_by": "causes",
            "enables": "enabled_by",
            "enabled_by": "enables",
            "regulates": "regulated_by",
            "regulated_by": "regulates",
            "offers": "offered_by",
            "offered_by": "offers",
        }
        
        # Regex patterns
        self.concept_pattern = re.compile(r"\[\[([^\]]+)\]\]")
        self.relation_block_pattern = re.compile(r"\[\[([^\]]+)\]\]\s*\{([^}]+)\}")
        
    def _load_graph(self) -> Dict:
        """Load or create graph structure."""
        if self.graph_path.exists():
            with open(self.graph_path, "r") as f:
                return json.load(f)
        return {
            "metadata": {
                "created": datetime.datetime.now().isoformat(),
                "version": "0.4.0",
                "description": "SemWiki smart knowledge graph",
            },
            "nodes": {},
            "edges": [],
            "taxonomy_mappings": {},  # search_path -> classification_path
        }
    
    def _load_taxonomy(self) -> Dict:
        """Load or create taxonomy index."""
        if self.taxonomy_path.exists():
            with open(self.taxonomy_path, "r") as f:
                return json.load(f)
        return {
            "search_to_classification": {},  # "bank/financial" -> "institution/financial/bank"
            "classification_to_search": {},  # "institution/financial/bank" -> "bank/financial"
            "aliases": {},  # Alternative paths for multi-parent
        }
    
    def _load_changelog(self) -> List[Dict]:
        """Load change history."""
        if self.changelog_path.exists():
            with open(self.changelog_path, "r") as f:
                return json.load(f)
        return []
    
    def _save_all(self):
        """Save all data structures."""
        # Update metadata
        self.graph["metadata"]["updated"] = datetime.datetime.now().isoformat()
        self.graph["metadata"]["nodes_count"] = len(self.graph["nodes"])
        self.graph["metadata"]["edges_count"] = len(self.graph["edges"])
        
        with open(self.graph_path, "w") as f:
            json.dump(self.graph, f, indent=2)
        
        with open(self.taxonomy_path, "w") as f:
            json.dump(self.taxonomy, f, indent=2)
        
        with open(self.changelog_path, "w") as f:
            json.dump(self.changelog, f, indent=2)
    
    def resolve_reference(self, concept_name: str, is_a_values: Optional[List[str]] = None) -> Tuple[str, str, List[str]]:
        """
        Resolve a concept reference using dual-endian architecture.
        
        Args:
            concept_name: The search-endian name (e.g., "bank" or "bank/financial")
            is_a_values: List of classification paths (e.g., ["institution/financial"])
        
        Returns:
            Tuple of (search_path, classification_path, all_paths)
        """
        # Check if already in taxonomy
        if concept_name in self.taxonomy["search_to_classification"]:
            classification_path = self.taxonomy["search_to_classification"][concept_name]
            return concept_name, classification_path, [classification_path]
        
        # Build from is_a relationships
        if is_a_values:
            # Multiple is_a values = multi-parent
            # Select primary: deepest path wins
            sorted_paths = sorted(is_a_values, key=lambda x: x.count("/"), reverse=True)
            primary_classification = sorted_paths[0]
            
            # Build full classification path
            concept_base = concept_name.split("/")[-1]  # "bank" from "bank/financial"
            classification_path = f"{primary_classification}/{concept_base}"
            
            # Store all paths (including aliases)
            all_paths = [f"{path}/{concept_base}" for path in is_a_values]
            
            # Register in taxonomy
            self.taxonomy["search_to_classification"][concept_name] = classification_path
            self.taxonomy["classification_to_search"][classification_path] = concept_name
            
            # Store aliases for multi-parent
            if len(all_paths) > 1:
                self.taxonomy["aliases"][concept_name] = all_paths[1:]
            
            return concept_name, classification_path, all_paths
        
        # No is_a, use context or simple name
        if self.current_context and "/" in str(self.current_context):
            # Inherit context from current file
            context_path = self._get_context_classification()
            concept_base = concept_name.split("/")[-1]
            classification_path = f"{context_path}/{concept_base}"
            return concept_name, classification_path, [classification_path]
        
        # Simple case: no classification hierarchy
        return concept_name, concept_name, [concept_name]
    
    def _get_context_classification(self) -> str:
        """Extract classification path from current context file."""
        if not self.current_context:
            return ""
        
        # Convert file path to classification path
        # workspace/concepts/institution/financial/bank.md -> institution/financial/bank
        rel_path = str(self.current_context)
        # Remove the base directory path (e.g., "workspace/concepts/" or "concepts/")
        if "concepts/" in rel_path:
            rel_path = rel_path.split("concepts/", 1)[1]
        rel_path = rel_path.replace(".md", "")
        return rel_path
    
    def classification_to_filepath(self, classification_path: str) -> Path:
        """Convert classification path to file path."""
        # Use the current input directory if available, otherwise default to "concepts"
        if self.current_input_dir:
            return self.base_path / self.current_input_dir / f"{classification_path}.md"
        return self.base_path / "concepts" / f"{classification_path}.md"
    
    def detect_circular_reference(self, source: str, target: str, relation: str) -> Optional[List[str]]:
        """
        Detect circular references in is_a hierarchy.
        
        Returns cycle path if circular, None if OK.
        """
        if relation != "is_a":
            return None
        
        # Build is_a graph
        is_a_graph = defaultdict(set)
        for edge in self.graph["edges"]:
            if edge["relation"] == "is_a":
                is_a_graph[edge["source"]].add(edge["target"])
        
        # Add proposed edge
        is_a_graph[source].add(target)
        
        # DFS to find cycle
        visited = set()
        path = []
        
        def dfs(node, path_stack):
            if node in path_stack:
                # Found cycle
                cycle_start = path_stack.index(node)
                return path_stack[cycle_start:] + [node]
            
            if node in visited:
                return None
            
            visited.add(node)
            path_stack.append(node)
            
            for neighbor in is_a_graph[node]:
                result = dfs(neighbor, path_stack)
                if result:
                    return result
            
            path_stack.pop()
            return None
        
        return dfs(source, [])
    
    def validate_classification_consistency(self, classification_path: str) -> List[str]:
        """
        Validate that classification path is consistent with existing taxonomy.
        
        Returns list of warnings.
        """
        warnings = []
        parts = classification_path.split("/")
        
        # Check parent existence
        for i in range(1, len(parts)):
            parent_path = "/".join(parts[:i])
            parent_file = self.classification_to_filepath(parent_path)
            
            if not parent_file.exists():
                # Parent doesn't exist as file
                # Check if it exists as inferred node
                if parent_path not in self.graph["nodes"]:
                    warnings.append(
                        f"Parent '{parent_path}' does not exist. "
                        f"Create it or check classification path."
                    )
        
        return warnings
    
    def stage_file_creation(self, classification_path: str, content: Optional[str] = None) -> Dict:
        """
        Stage a new file creation from classification path.
        
        Returns staged change entry.
        """
        file_path = self.classification_to_filepath(classification_path)
        
        # Generate default content if not provided
        if content is None:
            concept_name = classification_path.split("/")[-1]
            parent = "/".join(classification_path.split("/")[:-1])
            
            content = f"# {concept_name.replace('_', ' ').title()}\n\n"
            if parent:
                content += f"[[{concept_name}]]{{is_a: {parent}}}\n\n"
            content += f"## Definition\n\n"
            content += f"_{concept_name.replace('_', ' ')} is a concept._\n\n"
            content += f"## Related\n\n"
            content += f"<!-- Add related concepts here -->\n"
        
        # Compute checksum
        checksum = hashlib.sha256(content.encode()).hexdigest()
        
        change = {
            "type": "create",
            "file": str(file_path.relative_to(self.base_path)),
            "classification_path": classification_path,
            "content": content,
            "checksum": checksum,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        
        self.staged_changes.append(change)
        return change
    
    def apply_staged_changes(self, dry_run: bool = False) -> List[Dict]:
        """
        Apply all staged changes.
        
        Returns list of applied changes.
        """
        applied = []
        
        for change in self.staged_changes:
            if change["type"] == "create":
                file_path = self.base_path / change["file"]
                
                # Create parent directories
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                if not dry_run:
                    with open(file_path, "w") as f:
                        f.write(change["content"])
                
                applied.append(change)
                
                # Add to changelog
                self.changelog.append({
                    "action": "create",
                    "file": change["file"],
                    "classification_path": change["classification_path"],
                    "timestamp": change["timestamp"],
                    "checksum": change["checksum"],
                })
        
        if not dry_run:
            self.staged_changes = []
            self._save_all()
        
        return applied
    
    def parse_relations(self, rel_text: str) -> Dict[str, Union[str, List[str]]]:
        """
        Parse relation key:value pairs from text.
        
        Handles:
        - Single values: is_a: institution/financial
        - Arrays: is_a: [institution/financial, cooperative/business]
        - Concept references: [[target_concept]]
        """
        relations = {}
        
        # Pattern to match key: value pairs
        # Handles arrays [item1, item2] and concept refs [[concept]]
        kv_pattern = re.compile(
            r'(\w+):\s*'  # key:
            r'('  # value group
            r'\[\[[^\]]+\]\]'  # [[concept]]
            r'|\[[^\]]*\]'  # [array] or []
            r'|"[^"]*"'  # "quoted string"
            r"|'[^']*'"  # 'quoted string'
            r'|[^,\]]+'  # plain value
            r')'
        )
        
        for match in kv_pattern.finditer(rel_text):
            key = match.group(1)
            value = match.group(2).strip()
            
            # Handle concept references [[concept]]
            if value.startswith("[[") and value.endswith("]]"):
                value = value[2:-2]
                # Resolve if it has classification info
                if "/" in value or key == "is_a":
                    # For is_a, use the value directly as classification path
                    pass
            
            # Handle arrays [item1, item2]
            elif value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                if inner:
                    items = self._parse_array(inner)
                    value = items
                else:
                    value = []
            
            # Handle quoted strings
            elif (value.startswith('"') and value.endswith('"')) or \
                 (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            relations[key] = value
        
        return relations
    
    def _parse_array(self, text: str) -> List[str]:
        """Parse array contents, handling quotes and nested brackets."""
        items = []
        current = ""
        in_quote = False
        quote_char = None
        bracket_depth = 0
        
        for char in text:
            if char in ['"', "'"] and not in_quote:
                in_quote = True
                quote_char = char
                current += char
            elif char == quote_char and in_quote:
                in_quote = False
                current += char
            elif char == "[" and not in_quote:
                bracket_depth += 1
                current += char
            elif char == "]" and not in_quote:
                bracket_depth -= 1
                current += char
            elif char == "," and not in_quote and bracket_depth == 0:
                if current.strip():
                    items.append(self._clean_value(current.strip()))
                current = ""
            else:
                current += char
        
        if current.strip():
            items.append(self._clean_value(current.strip()))
        
        return items
    
    def _clean_value(self, value: str) -> str:
        """Clean a value by removing quotes and brackets."""
        value = value.strip()
        if value.startswith("[[") and value.endswith("]]"):
            return value[2:-2]
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        return value
    
    def parse_file(self, file_path: Path) -> List[Dict]:
        """
        Parse a SemWiki file and extract concepts with relations.
        
        Returns list of parsed concepts with metadata.
        """
        self.current_context = file_path.relative_to(self.base_path)
        content = file_path.read_text()
        
        parsed_concepts = []
        
        # Find all [[concept]]{relations} patterns
        for match in self.relation_block_pattern.finditer(content):
            concept_name = match.group(1)
            rel_text = match.group(2)
            
            # Parse relations
            relations = self.parse_relations(rel_text)
            
            # Extract is_a values (handle both single and array)
            is_a_values = relations.get("is_a", [])
            if isinstance(is_a_values, str):
                is_a_values = [is_a_values]
            
            # Resolve to dual-endian paths
            search_path, classification_path, all_paths = self.resolve_reference(
                concept_name, is_a_values if is_a_values else None
            )
            
            # Check for circular references
            for relation, target in relations.items():
                if relation == "is_a":
                    targets = [target] if isinstance(target, str) else target
                    for t in targets:
                        cycle = self.detect_circular_reference(search_path, t, "is_a")
                        if cycle:
                            print(f"⚠️  WARNING: Circular reference detected: {' -> '.join(cycle)}")
            
            # Validate classification consistency
            warnings = self.validate_classification_consistency(classification_path)
            for warning in warnings:
                print(f"⚠️  WARNING: {warning}")
            
            # Check if file exists, stage creation if not
            # Only stage creation for new concept definitions (those with is_a)
            file_path_resolved = self.classification_to_filepath(classification_path)
            if not file_path_resolved.exists() and classification_path != search_path and is_a_values:
                change = self.stage_file_creation(classification_path)
                print(f"📄 STAGED: Create {change['file']}")
            
            parsed_concepts.append({
                "search_path": search_path,
                "classification_path": classification_path,
                "all_paths": all_paths,
                "relations": relations,
                "source_file": str(self.current_context),
            })
        
        return parsed_concepts
    
    def add_to_graph(self, parsed_concepts: List[Dict]):
        """Add parsed concepts to the graph."""
        for concept in parsed_concepts:
            search_path = concept["search_path"]
            classification_path = concept["classification_path"]
            
            # Create or update node
            if search_path not in self.graph["nodes"]:
                self.graph["nodes"][search_path] = {
                    "id": search_path,
                    "type": "concept",
                    "classification_path": classification_path,
                    "created": datetime.datetime.now().isoformat(),
                    "sources": [concept["source_file"]],
                    "relations": {},
                    "properties": {},
                }
            else:
                if concept["source_file"] not in self.graph["nodes"][search_path]["sources"]:
                    self.graph["nodes"][search_path]["sources"].append(concept["source_file"])
            
            # Store taxonomy mapping
            self.graph["taxonomy_mappings"][search_path] = classification_path
            
            # Add relations
            for rel_type, target in concept["relations"].items():
                if isinstance(target, list):
                    for t in target:
                        self._add_relation(search_path, rel_type, t, concept["source_file"])
                else:
                    self._add_relation(search_path, rel_type, target, concept["source_file"])
    
    def _add_relation(self, source: str, rel_type: str, target: str, source_file: str):
        """Add a relation with automatic inverse."""
        # Check for circular references
        if rel_type == "is_a":
            cycle = self.detect_circular_reference(source, target, "is_a")
            if cycle:
                print(f"⚠️  Skipping circular relation: {' -> '.join(cycle)}")
                return
        
        # Create edge
        edge_id = f"{source}--{rel_type}--{target}"
        edge = {
            "id": edge_id,
            "source": source,
            "relation": rel_type,
            "target": target,
            "source_file": source_file,
            "created": datetime.datetime.now().isoformat(),
        }
        
        # Check for duplicates
        existing = next((e for e in self.graph["edges"] if e["id"] == edge_id), None)
        if not existing:
            self.graph["edges"].append(edge)
            
            # Update node relations
            if source in self.graph["nodes"]:
                if rel_type not in self.graph["nodes"][source]["relations"]:
                    self.graph["nodes"][source]["relations"][rel_type] = []
                if target not in self.graph["nodes"][source]["relations"][rel_type]:
                    self.graph["nodes"][source]["relations"][rel_type].append(target)
            
            # Add inverse relation
            self._add_inverse_relation(source, rel_type, target, source_file)
    
    def _add_inverse_relation(self, source: str, rel_type: str, target: str, source_file: str):
        """Add inverse relation."""
        inverse_type = self.relation_inverses.get(rel_type)
        if not inverse_type:
            return
        
        edge_id = f"{target}--{inverse_type}--{source}"
        edge = {
            "id": edge_id,
            "source": target,
            "relation": inverse_type,
            "target": source,
            "source_file": source_file,
            "created": datetime.datetime.now().isoformat(),
        }
        
        existing = next((e for e in self.graph["edges"] if e["id"] == edge_id), None)
        if not existing:
            self.graph["edges"].append(edge)
            
            if target in self.graph["nodes"]:
                if inverse_type not in self.graph["nodes"][target]["relations"]:
                    self.graph["nodes"][target]["relations"][inverse_type] = []
                if source not in self.graph["nodes"][target]["relations"][inverse_type]:
                    self.graph["nodes"][target]["relations"][inverse_type].append(source)
    
    def process_directory(self, directory: str, dry_run: bool = False, auto_apply: bool = False):
        """Process all files in a directory."""
        target_dir = self.base_path / directory
        if not target_dir.exists():
            print(f"Directory not found: {target_dir}")
            return
        
        self.current_input_dir = directory
        
        files = list(target_dir.rglob("*.md"))
        print(f"\n📁 Processing {len(files)} files from {directory}/\n")
        
        for file_path in files:
            print(f"  📄 {file_path.relative_to(self.base_path)}")
            parsed = self.parse_file(file_path)
            for concept in parsed:
                print(f"     → {concept['search_path']} → {concept['classification_path']}")
            self.add_to_graph(parsed)
        
        if self.staged_changes:
            print(f"\n📋 Staged Changes: {len(self.staged_changes)}")
            for change in self.staged_changes:
                print(f"   Create: {change['file']}")
            
            if not dry_run:
                if auto_apply:
                    applied = self.apply_staged_changes()
                    print(f"\n✅ Applied {len(applied)} changes")
                else:
                    confirm = input("\nApply changes? (y/n): ").lower().strip()
                    if confirm == 'y':
                        applied = self.apply_staged_changes()
                        print(f"\n✅ Applied {len(applied)} changes")
                    else:
                        print("\n⏸️  Changes staged but not applied")
                        print("   Run with --apply to confirm")
        
        if not dry_run:
            self._save_all()
        
        print(f"\n📊 Graph Stats: {len(self.graph['nodes'])} nodes, {len(self.graph['edges'])} edges")

    def print_stats(self):
        """Print graph statistics."""
        print(f"Nodes: {len(self.graph['nodes'])}")
        print(f"Edges: {len(self.graph['edges'])}")
        print(f"Taxonomy mappings: {len(self.taxonomy['search_to_classification'])}")
        print(f"Changelog entries: {len(self.changelog)}")


def main():
    """Main entry point."""
    import sys
    
    base_path = "."
    parser = SemWikiParser(base_path)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "parse":
            dry_run = "--dry-run" in sys.argv
            parser.process_directory("concepts", dry_run=dry_run)
            parser.process_directory("pages", dry_run=dry_run)
        
        elif command == "apply":
            # Apply previously staged changes
            if parser.staged_changes:
                applied = parser.apply_staged_changes()
                print(f"Applied {len(applied)} changes")
            else:
                print("No staged changes to apply")
        
        elif command == "stats":
            print(f"Nodes: {len(parser.graph['nodes'])}")
            print(f"Edges: {len(parser.graph['edges'])}")
            print(f"Taxonomy mappings: {len(parser.taxonomy['search_to_classification'])}")
            print(f"Changelog entries: {len(parser.changelog)}")
        
        else:
            print("Usage: python parse_semwiki.py [parse|apply|stats] [--dry-run]")
    else:
        print("SemWiki Parser v0.4.0")
        print("Commands:")
        print("  parse [--dry-run]  - Parse all files and stage changes")
        print("  apply              - Apply staged changes")
        print("  stats              - Show graph statistics")


if __name__ == "__main__":
    main()

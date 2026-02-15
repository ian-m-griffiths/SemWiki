#!/usr/bin/env python3
"""
SemWiki Error Diagnostic System

Analyzes SemWiki for errors and provides structured reports for AI fixing.
Designed for automated correction loops.

Error Message Format:
- What the error is
- What problem it causes
- How to fix it

Usage:
    python3 semwiki_errors.py check           # Check for all errors
    python3 semwiki_errors.py fix --dry-run   # Preview fixes
    python3 semwiki_errors.py fix             # Apply fixes
    python3 semwiki_errors.py report          # Generate AI report
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
import argparse


@dataclass
class SemWikiError:
    """Represents a single error with fix information."""
    error_type: str
    severity: str  # critical, warning, info
    file_path: str
    concept: str
    message: str
    impact: str  # What problems this causes
    fix_instructions: str  # Specific steps to fix
    fix_action: str  # create_file, add_relation, remove_circular, etc.
    fix_params: Dict  # Parameters needed to apply the fix
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SemWikiDiagnostics:
    """Diagnostic engine for SemWiki."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.graph_path = self.base_path / "graph.json"
        self.taxonomy_path = self.base_path / "taxonomy.json"
        
        self.graph = self._load_json(self.graph_path, {"nodes": {}, "edges": []})
        self.taxonomy = self._load_json(self.taxonomy_path, {})
        
        self.errors: List[SemWikiError] = []
        
    def _load_json(self, path: Path, default: Dict) -> Dict:
        """Load JSON file or return default."""
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return default
    
    def check_all(self) -> List[SemWikiError]:
        """Run all diagnostic checks."""
        self.errors = []
        
        self._check_missing_references()
        self._check_orphaned_files()
        self._check_circular_references()
        self._check_incomplete_hierarchies()
        self._check_classification_mismatches()
        self._check_bidirectional_missing()
        self._check_taxonomy_consistency()
        self._check_duplicate_concepts()
        
        # Sort by severity
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        self.errors.sort(key=lambda e: severity_order.get(e.severity, 3))
        
        return self.errors
    
    def _check_missing_references(self):
        """Check for references to non-existent concepts."""
        missing_refs = self.graph.get("missing_references", [])
        
        for ref in missing_refs:
            concept = ref.get("reference", "unknown")
            source = ref.get("context", "unknown")
            
            error = SemWikiError(
                error_type="missing_reference",
                severity="warning",
                file_path=source,
                concept=concept,
                message=f"Broken link: Reference to non-existent concept '[[{concept}]]'",
                impact="Search will not find this concept. Relationships cannot be traversed. Graph is incomplete.",
                fix_instructions=f"1. Create concept file for '{concept}' with appropriate is_a relationship, OR\n2. Fix the reference in '{source}' to point to existing concept, OR\n3. Remove the reference if obsolete",
                fix_action="create_concept",
                fix_params={
                    "concept_name": concept,
                    "source_file": source,
                    "suggestions": ref.get("suggestions", [])
                }
            )
            self.errors.append(error)
    
    def _check_orphaned_files(self):
        """Check for files not linked in the graph."""
        concepts_dir = self.base_path / "concepts"
        if not concepts_dir.exists():
            return
        
        all_files = set()
        for f in concepts_dir.rglob("*.md"):
            rel_path = str(f.relative_to(self.base_path))
            all_files.add(rel_path)
        
        # Get files referenced in graph
        referenced_files = set()
        for node_id, node in self.graph.get("nodes", {}).items():
            for source in node.get("sources", []):
                referenced_files.add(source)
        
        # Find orphaned files
        orphaned = all_files - referenced_files
        for file_path in orphaned:
            # Check if it's an index file
            if ".index.md" in file_path:
                continue
                
            error = SemWikiError(
                error_type="orphaned_file",
                severity="info",
                file_path=file_path,
                concept="",
                message=f"Orphaned file: '{file_path}' exists but is not connected to knowledge graph",
                impact="Search and classification may be affected. Content is unreachable through normal navigation.",
                fix_instructions="1. Parse this file to add it to the graph (run: semwiki parse <path>), OR\n2. Add proper [[Concept]] references with is_a relationships in the file, OR\n3. Remove file if obsolete",
                fix_action="parse_file",
                fix_params={"file_path": file_path}
            )
            self.errors.append(error)
    
    def _check_circular_references(self):
        """Check for circular is_a relationships."""
        # Build is_a graph with proper typing
        is_a_graph = defaultdict(set)
        for edge in self.graph.get("edges", []):
            if edge["relation"] == "is_a":
                is_a_graph[edge["source"]].add(edge["target"])
        
        # Find cycles using DFS
        def find_cycle(node: str, visited: Set, path: List) -> Optional[List]:
            if node in path:
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]
            
            if node in visited:
                return None
            
            visited.add(node)
            path.append(node)
            
            for target in is_a_graph[node]:
                cycle = find_cycle(target, visited, path)
                if cycle:
                    return cycle
            
            path.pop()
            return None
        
        checked = set()
        for node in list(is_a_graph.keys()):
            if node not in checked:
                cycle = find_cycle(node, set(), [])
                if cycle:
                    cycle_str = " -> ".join(cycle)
                    break_point = (cycle[-2], cycle[-1])
                    
                    error = SemWikiError(
                        error_type="circular_reference",
                        severity="critical",
                        file_path="",
                        concept=cycle[0],
                        message=f"Circular inheritance detected: {cycle_str}",
                        impact="Specificity cannot be measured. Hierarchy traversal will infinite loop. Reasoning about types becomes impossible.",
                        fix_instructions=f"1. Remove is_a relationship: '{break_point[0]}' should NOT be a '{break_point[1]}', OR\n2. Reclassify one concept to break the cycle, OR\n3. Ensure all is_a relationships use properly typed links with clear specificity direction",
                        fix_action="remove_circular",
                        fix_params={
                            "cycle": cycle,
                            "suggested_break": break_point
                        }
                    )
                    self.errors.append(error)
                    checked.update(cycle)
    
    def _check_incomplete_hierarchies(self):
        """Check for incomplete parent hierarchies."""
        for node_id, node in self.graph.get("nodes", {}).items():
            classification = node.get("classification_path", "")
            if not classification:
                continue
            
            parts = classification.split("/")
            for i in range(1, len(parts)):
                parent_path = "/".join(parts[:i])
                parent_file = self.base_path / "concepts" / f"{parent_path}.md"
                
                if not parent_file.exists():
                    source = node.get("sources", [""])[0] if node.get("sources") else ""
                    
                    error = SemWikiError(
                        error_type="incomplete_hierarchy",
                        severity="warning",
                        file_path=source,
                        concept=node_id,
                        message=f"Missing parent: Classification '{parent_path}' referenced but file does not exist",
                        impact="Hierarchy traversal will fail. Search results may be incomplete. Cannot navigate to parent concepts.",
                        fix_instructions=f"1. Create parent file: 'concepts/{parent_path}.md', OR\n2. Update classification in '{node_id}' to use existing parent, OR\n3. Create full hierarchy chain with is_a relationships",
                        fix_action="create_parent",
                        fix_params={
                            "parent_path": parent_path,
                            "child_classification": classification,
                            "child_file": source
                        }
                    )
                    self.errors.append(error)
    
    def _check_classification_mismatches(self):
        """Check for mismatches between file location and classification."""
        for node_id, node in self.graph.get("nodes", {}).items():
            classification = node.get("classification_path", "")
            sources = node.get("sources", [])
            
            if not sources or not classification:
                continue
            
            for source in sources:
                # Expected location based on classification
                expected = f"concepts/{classification}.md"
                if source != expected:
                    error = SemWikiError(
                        error_type="classification_mismatch",
                        severity="warning",
                        file_path=source,
                        concept=node_id,
                        message=f"Location mismatch: File is at '{source}' but classification says it should be at '{expected}'",
                        impact="Search and navigation will be inconsistent. File may not be found through classification traversal.",
                        fix_instructions=f"1. Move file from '{source}' to '{expected}', OR\n2. Update is_a relationship in file to match current location, OR\n3. Reorganize concept with correct classification path",
                        fix_action="move_file",
                        fix_params={
                            "current_path": source,
                            "expected_path": expected,
                            "classification": classification
                        }
                    )
                    self.errors.append(error)
    
    def _check_bidirectional_missing(self):
        """Check for missing bidirectional relations."""
        relation_inverses = {
            "is_a": "has_instance",
            "part_of": "has_part",
            "located_in": "location_of",
            "created_by": "creator_of",
        }
        
        edges = self.graph.get("edges", [])
        edge_set = set((e["source"], e["relation"], e["target"]) for e in edges)
        
        for edge in edges:
            rel = edge["relation"]
            if rel in relation_inverses:
                inverse = relation_inverses[rel]
                expected = (edge["target"], inverse, edge["source"])
                
                if expected not in edge_set:
                    source_file = edge.get("source_file", "")
                    
                    error = SemWikiError(
                        error_type="missing_inverse",
                        severity="info",
                        file_path=source_file,
                        concept=edge["source"],
                        message=f"Missing inverse: '{edge['target']}' should have '{inverse}' relation back to '{edge['source']}'",
                        impact="Navigation is one-way only. Cannot traverse relationship in reverse direction. Search may miss related concepts.",
                        fix_instructions=f"Add relation: [[{edge['target']}]]{{{inverse}: {edge['source']}}}",
                        fix_action="add_inverse",
                        fix_params={
                            "source": edge["target"],
                            "relation": inverse,
                            "target": edge["source"]
                        }
                    )
                    self.errors.append(error)
    
    def _check_taxonomy_consistency(self):
        """Check for inconsistencies in taxonomy mappings."""
        mappings = self.graph.get("taxonomy_mappings", {})
        
        for search_path, classification in mappings.items():
            # Check if node exists
            if search_path not in self.graph.get("nodes", {}):
                error = SemWikiError(
                    error_type="taxonomy_orphan",
                    severity="warning",
                    file_path="",
                    concept=search_path,
                    message=f"Stale mapping: Taxonomy maps '{search_path}' to '{classification}' but concept no longer exists",
                    impact="Search may return incorrect results. Classification lookups will fail. Memory leak in taxonomy index.",
                    fix_instructions="1. Remove stale taxonomy mapping, OR\n2. Recreate the missing concept, OR\n3. Update mapping to point to existing concept",
                    fix_action="remove_stale_taxonomy",
                    fix_params={"search_path": search_path, "classification": classification}
                )
                self.errors.append(error)
    
    def _check_duplicate_concepts(self):
        """Check for duplicate concepts with different names."""
        classifications = defaultdict(list)
        
        for node_id, node in self.graph.get("nodes", {}).items():
            classification = node.get("classification_path", "")
            if classification:
                classifications[classification].append(node_id)
        
        for classification, nodes in classifications.items():
            if len(nodes) > 1:
                nodes_str = ", ".join(nodes)
                
                error = SemWikiError(
                    error_type="duplicate_concept",
                    severity="warning",
                    file_path="",
                    concept=nodes[0],
                    message=f"Duplicate classification: Multiple nodes share '{classification}': {nodes_str}",
                    impact="Ambiguous search results. Cannot distinguish between concepts. Graph traversal is non-deterministic.",
                    fix_instructions="1. Merge the duplicate concepts into one, OR\n2. Differentiate classifications (e.g., concept/type1, concept/type2), OR\n3. Remove duplicate if accidental",
                    fix_action="merge_concepts",
                    fix_params={
                        "classification": classification,
                        "nodes": nodes
                    }
                )
                self.errors.append(error)
    
    def generate_ai_report(self) -> Dict:
        """Generate structured report for AI processing."""
        report = {
            "summary": {
                "total_errors": len(self.errors),
                "critical": len([e for e in self.errors if e.severity == "critical"]),
                "warnings": len([e for e in self.errors if e.severity == "warning"]),
                "info": len([e for e in self.errors if e.severity == "info"]),
            },
            "errors_by_type": defaultdict(list),
            "fixable_automatically": [],
            "requires_human_review": [],
            "all_errors": []
        }
        
        for error in self.errors:
            report["errors_by_type"][error.error_type].append(error.to_dict())
            report["all_errors"].append(error.to_dict())
            
            # Categorize fixability
            auto_fixable = [
                "missing_inverse",
                "taxonomy_orphan"
            ]
            
            if error.error_type in auto_fixable:
                report["fixable_automatically"].append(error.to_dict())
            else:
                report["requires_human_review"].append(error.to_dict())
        
        return report
    
    def print_report(self):
        """Print human-readable error report."""
        if not self.errors:
            print("✅ No errors found! SemWiki is clean.")
            return
        
        print(f"\n🔍 SemWiki Diagnostic Report")
        print(f"   {len(self.errors)} issue(s) found\n")
        
        by_severity = defaultdict(list)
        for error in self.errors:
            by_severity[error.severity].append(error)
        
        # Print critical first
        if by_severity["critical"]:
            print("❌ CRITICAL ISSUES:")
            for error in by_severity["critical"]:
                self._print_error(error)
            print()
        
        if by_severity["warning"]:
            print("⚠️  WARNINGS:")
            for error in by_severity["warning"]:
                self._print_error(error)
            print()
        
        if by_severity["info"]:
            print("ℹ️  INFO:")
            for error in by_severity["info"]:
                self._print_error(error)
            print()
        
        # Summary
        print("📊 Summary:")
        for severity, errors in by_severity.items():
            print(f"   {severity.capitalize()}: {len(errors)}")
    
    def _print_error(self, error: SemWikiError):
        """Print a single error with full context."""
        print(f"\n  [{error.error_type}] {error.concept or 'N/A'}")
        if error.file_path:
            print(f"   File: {error.file_path}")
        print(f"   Problem: {error.message}")
        print(f"   Impact: {error.impact}")
        print(f"   Fix: {error.fix_instructions}")
        print(f"   Action: {error.fix_action}")
    
    def export_json(self, output_path: str):
        """Export error report to JSON for AI processing."""
        report = self.generate_ai_report()
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"📄 Report exported to: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SemWiki Error Diagnostics for AI Fix Loop"
    )
    parser.add_argument(
        "--base-path",
        default=".",
        help="Base path for SemWiki (default: current directory)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check for errors")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate AI report")
    report_parser.add_argument("--output", "-o", default="semwiki_errors.json",
                              help="Output JSON file (default: semwiki_errors.json)")
    
    # Fix command (placeholder for future)
    fix_parser = subparsers.add_parser("fix", help="Fix errors (coming soon)")
    fix_parser.add_argument("--dry-run", action="store_true",
                           help="Preview fixes without applying")
    
    args = parser.parse_args()
    
    diagnostics = SemWikiDiagnostics(args.base_path)
    
    if args.command == "check":
        diagnostics.check_all()
        diagnostics.print_report()
    
    elif args.command == "report":
        diagnostics.check_all()
        diagnostics.export_json(args.output)
    
    elif args.command == "fix":
        print("🔧 Auto-fix coming in v0.5.0!")
        print("   For now, use the report to guide manual fixes.")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

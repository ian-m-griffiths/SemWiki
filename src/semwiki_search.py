#!/usr/bin/env python3
"""
SemWiki Search System v0.1.0

Generates search map from classification-endian structure.
Traverses is_a hierarchy to find results from most to least specific.

Usage:
    python3 search_semwiki.py "credit_union"           # Search for concept
    python3 search_semwiki.py "bank" --hierarchy       # Show full hierarchy
    python3 search_semwiki.py "institution" --index    # Show inverted index
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import argparse


class SemWikiSearch:
    """Search system with hierarchical traversal."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.graph_path = self.base_path / "graph.json"
        self.taxonomy_path = self.base_path / "taxonomy.json"
        
        self.graph = self._load_graph()
        self.taxonomy = self._load_taxonomy()
        
        # Build search indices
        self.search_index = {}  # term -> list of (path, specificity)
        self.hierarchy_cache = {}  # path -> parent paths
        
    def _load_graph(self) -> Dict:
        """Load graph data."""
        if self.graph_path.exists():
            with open(self.graph_path, "r") as f:
                return json.load(f)
        return {"nodes": {}, "edges": []}
    
    def _load_taxonomy(self) -> Dict:
        """Load taxonomy mappings."""
        if self.taxonomy_path.exists():
            with open(self.taxonomy_path, "r") as f:
                return json.load(f)
        return {"search_to_classification": {}, "aliases": {}}
    
    def build_search_index(self):
        """
        Build inverted search index from classification paths.
        
        For each concept, index it and all its parent classifications.
        """
        self.search_index = defaultdict(list)
        
        # Process all nodes
        for node_id, node_data in self.graph.get("nodes", {}).items():
            classification_path = node_data.get("classification_path", node_id)
            
            # Extract concept name from end of path
            concept_name = classification_path.split("/")[-1]
            
            # Calculate specificity (depth in hierarchy)
            depth = classification_path.count("/")
            
            # Index by concept name
            self.search_index[concept_name.lower()].append({
                "search_path": node_id,
                "classification_path": classification_path,
                "depth": depth,
                "specificity": depth + 1,  # Higher = more specific
                "node": node_data
            })
            
            # Also index by full path components
            parts = classification_path.split("/")
            for i, part in enumerate(parts):
                partial_path = "/".join(parts[:i+1])
                self.search_index[part.lower()].append({
                    "search_path": node_id,
                    "classification_path": classification_path,
                    "depth": depth,
                    "specificity": i + 1,
                    "is_partial": i < len(parts) - 1,
                    "node": node_data
                })
    
    def get_parent_hierarchy(self, classification_path: str) -> List[str]:
        """
        Get parent hierarchy by traversing up is_a relationships.
        
        Returns list from most specific to least specific (root).
        """
        if classification_path in self.hierarchy_cache:
            return self.hierarchy_cache[classification_path]
        
        hierarchy = [classification_path]
        visited = {classification_path}
        
        # Find node for this classification
        search_path = None
        for node_id, node_data in self.graph.get("nodes", {}).items():
            if node_data.get("classification_path") == classification_path:
                search_path = node_id
                break
        
        if not search_path:
            # Try to find by splitting path
            parts = classification_path.split("/")
            for i in range(len(parts) - 1, 0, -1):
                parent_path = "/".join(parts[:i])
                if parent_path not in visited:
                    hierarchy.append(parent_path)
                    visited.add(parent_path)
            return hierarchy
        
        # Traverse is_a relationships
        current = search_path
        max_depth = 10  # Prevent infinite loops
        depth = 0
        
        while current and depth < max_depth:
            node = self.graph["nodes"].get(current, {})
            is_a_targets = node.get("relations", {}).get("is_a", [])
            
            if not is_a_targets:
                break
            
            # Get first is_a target
            target = is_a_targets[0] if isinstance(is_a_targets, list) else is_a_targets
            
            # Get classification path of target
            target_node = self.graph["nodes"].get(target, {})
            target_classification = target_node.get("classification_path", target)
            
            if target_classification not in visited:
                hierarchy.append(target_classification)
                visited.add(target_classification)
            
            current = target
            depth += 1
        
        self.hierarchy_cache[classification_path] = hierarchy
        return hierarchy
    
    def search(self, query: str, include_hierarchy: bool = False) -> List[Dict]:
        """
        Search for concepts by name.
        
        Only returns paths where the search term appears.
        Truncates at the search term level (excludes more specific descendants).
        Results ordered by specificity (most specific first).
        """
        query_lower = query.lower()
        results = []
        seen = set()
        
        for node_id, node_data in self.graph.get("nodes", {}).items():
            classification_path = node_data.get("classification_path", node_id)
            parts = classification_path.split("/")
            
            match_index = None
            matched_in_search_path = False
            
            for i, part in enumerate(parts):
                if query_lower in part.lower() or part.lower() in query_lower:
                    match_index = i
                    break
            
            if match_index is None:
                node_parts = node_id.split("/")
                for i, part in enumerate(node_parts):
                    if query_lower in part.lower() or part.lower() in query_lower:
                        match_index = len(parts) - 1
                        matched_in_search_path = True
                        break
            
            if match_index is not None:
                truncated_path = "/".join(parts[:match_index + 1])
                
                if truncated_path in seen:
                    continue
                seen.add(truncated_path)
                
                truncated_depth = match_index
                truncated_specificity = match_index + 1
                
                matched_term = parts[match_index] if match_index < len(parts) else node_id.split("/")[-1]
                
                results.append({
                    "search_path": node_id,
                    "classification_path": truncated_path,
                    "full_classification_path": classification_path,
                    "depth": truncated_depth,
                    "specificity": truncated_specificity,
                    "node": node_data,
                    "matched_term": matched_term
                })
        
        results.sort(key=lambda x: (-x["specificity"], x["classification_path"]))
        
        if include_hierarchy:
            for result in results:
                result["hierarchy"] = self.get_parent_hierarchy(result["classification_path"])
        
        return results
    
    def format_result(self, result: Dict, show_hierarchy: bool = False) -> str:
        """Format a search result for display."""
        lines = []
        
        search_path = result["search_path"]
        classification = result["classification_path"]
        depth = result["depth"]
        
        lines.append(f"  📄 {search_path}")
        lines.append(f"     📂 {classification}")
        lines.append(f"     📊 Specificity: {depth} (depth in hierarchy)")
        
        if show_hierarchy and "hierarchy" in result:
            lines.append(f"     🔗 Hierarchy:")
            for i, parent in enumerate(result["hierarchy"][:5]):  # Show top 5
                indent = "       " + "  " * i
                lines.append(f"{indent}└─ {parent}")
        
        # Show relations
        node = result.get("node", {})
        relations = node.get("relations", {})
        if relations:
            lines.append(f"     🔗 Relations:")
            for rel_type, targets in list(relations.items())[:3]:  # Top 3
                target_str = targets[0] if isinstance(targets, list) else targets
                lines.append(f"       • {rel_type}: {target_str}")
        
        return "\n".join(lines)
    
    def print_search_results(self, query: str, include_hierarchy: bool = False):
        """Print formatted search results."""
        print(f"\n🔍 Search: '{query}'\n")
        
        results = self.search(query, include_hierarchy=include_hierarchy)
        
        if not results:
            print("  No results found.")
            return
        
        print(f"  Found {len(results)} result(s):\n")
        
        for i, result in enumerate(results[:10], 1):  # Show top 10
            print(f"  #{i}")
            print(self.format_result(result, show_hierarchy=include_hierarchy))
            print()
    
    def print_inverted_index(self):
        """Print the inverted search index."""
        print("\n📚 Inverted Search Index\n")
        
        # Sort by term
        for term in sorted(self.search_index.keys()):
            entries = self.search_index[term]
            print(f"  {term}:")
            
            # Group by specificity
            by_specificity = defaultdict(list)
            for entry in entries:
                by_specificity[entry["specificity"]].append(entry)
            
            for specificity in sorted(by_specificity.keys(), reverse=True):
                for entry in by_specificity[specificity]:
                    print(f"    • {entry['classification_path']} (depth: {entry['depth']})")
    
    def print_hierarchy_tree(self, root: Optional[str] = None):
        """
        Print hierarchy tree from classification paths.
        
        Shows the full ontology structure.
        """
        print("\n🌳 Classification Hierarchy\n")
        
        # Build tree from all classification paths
        tree = defaultdict(lambda: defaultdict(list))
        all_paths = set()
        
        for node_id, node_data in self.graph.get("nodes", {}).items():
            classification = node_data.get("classification_path", node_id)
            all_paths.add(classification)
        
        # Build parent-child relationships
        for path in sorted(all_paths):
            parts = path.split("/")
            for i in range(len(parts) - 1):
                parent = "/".join(parts[:i+1])
                child = "/".join(parts[:i+2])
                if child != parent:
                    tree[parent]["children"].append(child)
        
        # Find roots (no parent)
        roots = []
        for path in all_paths:
            parts = path.split("/")
            if len(parts) == 1:
                roots.append(path)
        
        # Print tree
        def print_node(node_path: str, indent: int = 0):
            prefix = "  " * indent
            node_name = node_path.split("/")[-1]
            print(f"{prefix}└─ {node_name}")
            
            for child in sorted(tree[node_path]["children"]):
                print_node(child, indent + 1)
        
        if root:
            print_node(root)
        else:
            for root_node in sorted(roots):
                print_node(root_node)
                print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="SemWiki Search System")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--hierarchy", "-H", action="store_true", 
                       help="Include hierarchy in results")
    parser.add_argument("--index", "-i", action="store_true",
                       help="Show inverted index")
    parser.add_argument("--tree", "-t", action="store_true",
                       help="Show hierarchy tree")
    parser.add_argument("--base-path", default=".",
                       help="Base path for SemWiki")
    
    args = parser.parse_args()
    
    search = SemWikiSearch(args.base_path)
    search.build_search_index()
    
    if args.index:
        search.print_inverted_index()
    elif args.tree:
        search.print_hierarchy_tree()
    elif args.query:
        search.print_search_results(args.query, include_hierarchy=args.hierarchy)
    else:
        print("SemWiki Search System v0.1.0")
        print("\nUsage:")
        print("  python3 search_semwiki.py 'credit_union'        # Search")
        print("  python3 search_semwiki.py 'bank' --hierarchy    # With hierarchy")
        print("  python3 search_semwiki.py --index               # Show index")
        print("  python3 search_semwiki.py --tree                # Show tree")


if __name__ == "__main__":
    main()

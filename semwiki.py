#!/usr/bin/env python3
"""
SemWiki - Semantic Wiki with Dual-Endian Architecture

A smart wiki system that:
- Organizes knowledge automatically via is_a relationships
- Supports sense disambiguation (bank/financial vs bank/geology)
- Provides hierarchical search with specificity ranking

Usage:
    semwiki parse [path]     # Parse wiki files and build graph
    semwiki search [query]   # Search the knowledge graph
    semwiki serve            # Start web interface (future)
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from semwiki_parser import SemWikiParser
from semwiki_search import SemWikiSearch


def main():
    parser = argparse.ArgumentParser(
        description="SemWiki - Semantic Wiki System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s parse examples/concepts --dry-run    # Preview changes
  %(prog)s parse examples/concepts             # Build knowledge graph
  %(prog)s search "bank" --hierarchy           # Search with hierarchy
  %(prog)s stats                               # Show graph statistics
        """
    )
    
    parser.add_argument(
        "--base-path", 
        default=".",
        help="Base path for wiki (default: current directory)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Parse command
    parse_parser = subparsers.add_parser("parse", help="Parse wiki files")
    parse_parser.add_argument("path", help="Path to wiki directory")
    parse_parser.add_argument("--dry-run", action="store_true", 
                             help="Preview changes without applying")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search knowledge graph")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--hierarchy", "-H", action="store_true",
                              help="Show hierarchy in results")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check for errors")
    check_parser.add_argument("--report", "-r", action="store_true",
                             help="Generate AI report (semwiki_errors.json)")
    
    args = parser.parse_args()
    
    if args.command == "parse":
        base_path = Path(args.base_path)
        wiki_parser = SemWikiParser(str(base_path))
        wiki_parser.process_directory(args.path, dry_run=args.dry_run)
    
    elif args.command == "search":
        base_path = Path(args.base_path)
        search = SemWikiSearch(str(base_path))
        search.build_search_index()
        search.print_search_results(args.query, include_hierarchy=args.hierarchy)
    
    elif args.command == "stats":
        base_path = Path(args.base_path)
        wiki_parser = SemWikiParser(str(base_path))
        wiki_parser.print_stats()
    
    elif args.command == "check":
        from semwiki_errors import SemWikiDiagnostics
        base_path = Path(args.base_path)
        diagnostics = SemWikiDiagnostics(str(base_path))
        diagnostics.check_all()
        diagnostics.print_report()
        if args.report:
            diagnostics.export_json("semwiki_errors.json")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

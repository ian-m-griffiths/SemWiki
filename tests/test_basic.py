#!/usr/bin/env python3
"""
Quick test to verify SemWiki examples work.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from semwiki_parser import SemWikiParser
from semwiki_search import SemWikiSearch


def test_parse():
    """Test that parsing works."""
    print("🧪 Testing parser...")
    
    base_path = Path(__file__).parent.parent
    parser = SemWikiParser(str(base_path))
    
    parser.process_directory("examples/concepts", dry_run=False, auto_apply=True)
    
    print(f"✅ Parsed successfully")
    print(f"   Nodes: {len(parser.graph['nodes'])}")
    print(f"   Edges: {len(parser.graph['edges'])}")
    
    return True


def test_search():
    """Test that search works."""
    print("\n🔍 Testing search...")
    
    base_path = Path(__file__).parent.parent
    search = SemWikiSearch(str(base_path))
    search.build_search_index()
    
    # Test search
    results = search.search("bank")
    
    print(f"✅ Search working")
    print(f"   Results for 'bank': {len(results)}")
    
    for r in results:
        print(f"   - {r['classification_path']}")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("SemWiki Quick Test Suite")
    print("=" * 60)
    
    try:
        test_parse()
        test_search()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/bin/bash
# SemWiki Demo Script
# Run this to see SemWiki in action!

echo "=========================================="
echo "  SemWiki Demo - Dual-Endian Wiki System"
echo "=========================================="
echo ""

# Check Python version
python3 --version 2>/dev/null || { echo "❌ Python 3 not found"; exit 1; }

echo "✅ Python found"
echo ""

# Change to semwiki directory (script is in script/, go up one level)
cd "$(dirname "$0")/.."

echo "📁 Current directory: $(pwd)"
echo ""

# Step 1: Show the example concept files
echo "Step 1: Example Concept Files"
echo "------------------------------"
echo ""
echo "We have two 'bank' concepts:"
echo ""
echo "1. Financial Bank:"
echo "   File: examples/concepts/institution/financial/bank.md"
echo "   Content:"
cat examples/concepts/institution/financial/bank.md | head -10
echo ""
echo "2. Geological Bank:"
echo "   File: examples/concepts/geological/formation/bank.md"
echo "   Content:"
cat examples/concepts/geological/formation/bank.md | head -10
echo ""

# Step 2: Parse with dry run
echo "Step 2: Parse Concepts (Dry Run)"
echo "---------------------------------"
echo ""
./semwiki.py parse examples/concepts --dry-run 2>&1 | head -20
echo ""

# Step 3: Actual parse
echo "Step 3: Build Knowledge Graph"
echo "------------------------------"
echo ""
./semwiki.py parse examples/concepts <<< "y" 2>&1 | head -20
echo ""

# Step 4: Search
echo "Step 4: Search for 'bank'"
echo "-------------------------"
echo ""
./semwiki.py search "bank" --hierarchy 2>&1
echo ""

# Step 5: Show stats
echo "Step 5: Graph Statistics"
echo "------------------------"
echo ""
./semwiki.py stats 2>&1
echo ""

echo "=========================================="
echo "  ✅ Demo Complete!"
echo "=========================================="
echo ""
echo "What you saw:"
echo "  • Two senses of 'bank' - financial and geological"
echo "  • Automatic file organization based on is_a relationships"
echo "  • Hierarchical search that finds both senses"
echo "  • Knowledge graph with nodes and edges"
echo ""
echo "Try it yourself:"
echo "  ./semwiki.py parse examples/concepts"
echo "  ./semwiki.py search \"institution\" --hierarchy"
echo ""

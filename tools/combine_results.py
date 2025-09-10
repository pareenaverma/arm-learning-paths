#!/usr/bin/env python3
"""
Helper script to combine style and grammar check results.
"""

import json
import os
import sys

def combine_results(style_file, grammar_file, output_file):
    """Combine style and grammar check results."""
    # Load style suggestions
    style_suggestions = []
    if os.path.exists(style_file):
        with open(style_file, "r") as f:
            style_suggestions = json.load(f)

    # Load grammar suggestions
    grammar_suggestions = []
    if os.path.exists(grammar_file):
        with open(grammar_file, "r") as f:
            grammar_suggestions = json.load(f)

    # Combine suggestions
    combined_suggestions = style_suggestions + grammar_suggestions

    # Sort by line number
    combined_suggestions.sort(key=lambda x: x["line"])

    # Save combined suggestions
    with open(output_file, "w") as f:
        json.dump(combined_suggestions, f, indent=2)

    print(f"Combined {len(style_suggestions)} style suggestions and {len(grammar_suggestions)} grammar suggestions.")
    return len(combined_suggestions)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python combine_results.py <style_file> <grammar_file> <output_file>")
        sys.exit(1)
    
    style_file = sys.argv[1]
    grammar_file = sys.argv[2]
    output_file = sys.argv[3]
    
    combine_results(style_file, grammar_file, output_file)

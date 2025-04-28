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
        try:
            with open(style_file, "r") as f:
                style_suggestions = json.load(f)
                # Ensure each suggestion has a reason that includes "Style"
                for sugg in style_suggestions:
                    if "reason" in sugg and "Style" not in sugg["reason"]:
                        sugg["reason"] = f"Style: {sugg['reason']}"
        except json.JSONDecodeError:
            print(f"Error: {style_file} is not valid JSON")
        except Exception as e:
            print(f"Error loading {style_file}: {e}")
    else:
        print(f"Warning: Style file {style_file} does not exist")

    # Load grammar suggestions
    grammar_suggestions = []
    if os.path.exists(grammar_file):
        try:
            with open(grammar_file, "r") as f:
                grammar_suggestions = json.load(f)
                # Ensure each suggestion has a reason that includes "Grammar"
                for sugg in grammar_suggestions:
                    if "reason" in sugg and "Grammar" not in sugg["reason"]:
                        sugg["reason"] = f"Grammar: {sugg['reason']}"
        except json.JSONDecodeError:
            print(f"Error: {grammar_file} is not valid JSON")
        except Exception as e:
            print(f"Error loading {grammar_file}: {e}")
    else:
        print(f"Warning: Grammar file {grammar_file} does not exist")

    # Combine suggestions
    combined_suggestions = style_suggestions + grammar_suggestions

    # Sort by line number
    combined_suggestions.sort(key=lambda x: x.get("line", 0))

    # Debug output
    print(f"Style suggestions: {len(style_suggestions)}")
    print(f"Grammar suggestions: {len(grammar_suggestions)}")
    print(f"Combined suggestions: {len(combined_suggestions)}")

    # Save combined suggestions
    try:
        with open(output_file, "w") as f:
            json.dump(combined_suggestions, f, indent=2)
        print(f"Successfully wrote combined suggestions to {output_file}")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")
        return 0

    return len(combined_suggestions)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python combine_results.py <style_file> <grammar_file> <output_file>")
        sys.exit(1)
    
    style_file = sys.argv[1]
    grammar_file = sys.argv[2]
    output_file = sys.argv[3]
    
    # Print arguments for debugging
    print(f"Style file: {style_file}")
    print(f"Grammar file: {grammar_file}")
    print(f"Output file: {output_file}")
    
    # Check if files exist
    print(f"Style file exists: {os.path.exists(style_file)}")
    print(f"Grammar file exists: {os.path.exists(grammar_file)}")
    
    # Combine results
    total_suggestions = combine_results(style_file, grammar_file, output_file)
    
    # Exit with status code based on success
    sys.exit(0 if total_suggestions > 0 or (not os.path.exists(style_file) and not os.path.exists(grammar_file)) else 1)

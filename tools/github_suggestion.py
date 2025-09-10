#!/usr/bin/env python3
"""
GitHub suggestion formatter for Arm Learning Paths style checker.
This script takes the style suggestions JSON file and formats them as GitHub
review comments with proper suggestion syntax.
"""

import argparse
import json
import os
import sys
from pathlib import Path

def format_github_suggestions(suggestions):
    """Format suggestions as GitHub review comments."""
    github_comments = []
    
    # Group suggestions by file
    file_suggestions = {}
    for sugg in suggestions:
        file_path = sugg["file"]
        if file_path not in file_suggestions:
            file_suggestions[file_path] = []
        file_suggestions[file_path].append(sugg)
    
    # Format suggestions for each file
    for file_path, file_suggs in file_suggestions.items():
        print(f"\nSuggestions for {file_path}:")
        print("=" * 80)
        
        for sugg in file_suggs:
            comment = (
                f"**Style suggestion**: {sugg['reason']}\n\n"
                f"```suggestion\n{sugg['suggested']}\n```"
            )
            github_comments.append({
                "path": file_path,
                "line": sugg["line"],
                "body": comment
            })
            
            print(f"Line {sugg['line']}:")
            print(comment)
            print("-" * 80)
    
    return github_comments

def main():
    parser = argparse.ArgumentParser(description="Format style suggestions as GitHub review comments")
    parser.add_argument("--input", default="style_suggestions.json", help="Input JSON file with style suggestions")
    args = parser.parse_args()
    
    if not os.path.isfile(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    with open(args.input, "r", encoding="utf-8") as f:
        suggestions = json.load(f)
    
    if not suggestions:
        print("No style suggestions found in the input file.")
        sys.exit(0)
    
    github_comments = format_github_suggestions(suggestions)
    
    print(f"\nFormatted {len(github_comments)} GitHub review comments.")
    print("\nThese comments can be used in the GitHub API to create review comments.")
    print("In the GitHub Actions workflow, they will be submitted as a review on the PR.")

if __name__ == "__main__":
    main()

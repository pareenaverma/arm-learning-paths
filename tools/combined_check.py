#!/usr/bin/env python3
"""
Combined style and grammar checker for Arm Learning Paths content.
This script runs both style and grammar checks and combines the results.
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path

def run_style_check(file_path, rules_file, output_file):
    """Run the style checker on a file."""
    cmd = [
        "python3", "tools/enhanced_style_check.py",
        "--file", file_path,
        "--rules", rules_file,
        "--output", output_file
    ]
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        print(f"Error running style check on {file_path}")
        return False

def run_grammar_check(file_path, output_file):
    """Run the grammar checker on a file."""
    cmd = [
        "python3", "tools/grammar_check.py",
        "--file", file_path,
        "--output", output_file
    ]
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        print(f"Error running grammar check on {file_path}")
        return False

def combine_suggestions(style_file, grammar_file, output_file):
    """Combine style and grammar suggestions into a single file."""
    style_suggestions = []
    grammar_suggestions = []
    
    # Load style suggestions
    if os.path.exists(style_file):
        with open(style_file, "r") as f:
            style_suggestions = json.load(f)
    
    # Load grammar suggestions
    if os.path.exists(grammar_file):
        with open(grammar_file, "r") as f:
            grammar_suggestions = json.load(f)
    
    # Combine suggestions
    combined_suggestions = style_suggestions + grammar_suggestions
    
    # Sort by file and line number
    combined_suggestions.sort(key=lambda x: (x["file"], x["line"]))
    
    # Save combined suggestions
    with open(output_file, "w") as f:
        json.dump(combined_suggestions, f, indent=2)
    
    return len(combined_suggestions)

def print_summary(style_count, grammar_count, combined_count):
    """Print a summary of the checks."""
    print("\nCheck Summary:")
    print("=" * 80)
    print(f"Style issues found: {style_count}")
    print(f"Grammar issues found: {grammar_count}")
    print(f"Total issues found: {combined_count}")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="Run combined style and grammar checks")
    parser.add_argument("--file", help="Path to a specific markdown file to check")
    parser.add_argument("--dir", help="Directory containing markdown files to check")
    parser.add_argument("--rules", default="tools/style_rules.json", help="JSON file containing style rules")
    parser.add_argument("--output", default="combined_suggestions.json", help="Output file for combined suggestions")
    args = parser.parse_args()
    
    if not args.file and not args.dir:
        print("Error: Please provide either --file or --dir argument")
        sys.exit(1)
    
    style_count = 0
    grammar_count = 0
    combined_count = 0
    
    # Check a specific file
    if args.file:
        if not os.path.isfile(args.file):
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
        
        if not args.file.endswith((".md", ".mdx")):
            print(f"Warning: {args.file} is not a markdown file. Checking anyway.")
        
        # Run style check
        style_output = f"{args.file}.style.json"
        if run_style_check(args.file, args.rules, style_output):
            with open(style_output, "r") as f:
                style_suggestions = json.load(f)
                style_count = len(style_suggestions)
        
        # Run grammar check
        grammar_output = f"{args.file}.grammar.json"
        if run_grammar_check(args.file, grammar_output):
            with open(grammar_output, "r") as f:
                grammar_suggestions = json.load(f)
                grammar_count = len(grammar_suggestions)
        
        # Combine results
        combined_count = combine_suggestions(style_output, grammar_output, args.output)
        
        # Clean up temporary files
        if os.path.exists(style_output):
            os.remove(style_output)
        if os.path.exists(grammar_output):
            os.remove(grammar_output)
    
    # Check all markdown files in a directory
    if args.dir:
        if not os.path.isdir(args.dir):
            print(f"Error: Directory not found: {args.dir}")
            sys.exit(1)
        
        all_style_suggestions = []
        all_grammar_suggestions = []
        
        for root, _, files in os.walk(args.dir):
            for file in files:
                if file.endswith((".md", ".mdx")):
                    file_path = os.path.join(root, file)
                    
                    # Run style check
                    style_output = f"{file_path}.style.json"
                    if run_style_check(file_path, args.rules, style_output):
                        with open(style_output, "r") as f:
                            style_suggestions = json.load(f)
                            all_style_suggestions.extend(style_suggestions)
                    
                    # Run grammar check
                    grammar_output = f"{file_path}.grammar.json"
                    if run_grammar_check(file_path, grammar_output):
                        with open(grammar_output, "r") as f:
                            grammar_suggestions = json.load(f)
                            all_grammar_suggestions.extend(grammar_suggestions)
                    
                    # Clean up temporary files
                    if os.path.exists(style_output):
                        os.remove(style_output)
                    if os.path.exists(grammar_output):
                        os.remove(grammar_output)
        
        # Save all suggestions
        style_output = "all_style_suggestions.json"
        with open(style_output, "w") as f:
            json.dump(all_style_suggestions, f, indent=2)
        
        grammar_output = "all_grammar_suggestions.json"
        with open(grammar_output, "w") as f:
            json.dump(all_grammar_suggestions, f, indent=2)
        
        # Combine results
        combined_count = combine_suggestions(style_output, grammar_output, args.output)
        
        style_count = len(all_style_suggestions)
        grammar_count = len(all_grammar_suggestions)
        
        # Clean up temporary files
        if os.path.exists(style_output):
            os.remove(style_output)
        if os.path.exists(grammar_output):
            os.remove(grammar_output)
    
    # Print summary
    print_summary(style_count, grammar_count, combined_count)
    print(f"Combined suggestions saved to {args.output}")

if __name__ == "__main__":
    main()

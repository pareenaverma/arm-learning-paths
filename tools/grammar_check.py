#!/usr/bin/env python3
"""
Grammar checker for Arm Learning Paths content.
This script checks markdown files for grammar issues using the LanguageTool API.
"""

import argparse
import json
import os
import re
import sys
import requests
from pathlib import Path
import html
import markdown
from bs4 import BeautifulSoup

def is_in_code_block(lines, line_index):
    """Check if the line is within a code block."""
    code_block_count = 0
    for i in range(line_index):
        if re.match(r'^```', lines[i]):
            code_block_count += 1
    
    return code_block_count % 2 == 1  # Odd count means inside a code block

def is_in_yaml_frontmatter(lines, line_index):
    """Check if the line is within YAML frontmatter."""
    if line_index == 0 and lines[0].strip() == '---':
        return True
        
    frontmatter_markers = 0
    for i in range(line_index):
        if lines[i].strip() == '---':
            frontmatter_markers += 1
    
    # If we've seen an odd number of markers, we're in frontmatter
    return frontmatter_markers % 2 == 1

def extract_text_from_markdown(content):
    """Extract plain text from markdown, preserving line numbers."""
    lines = content.split('\n')
    text_lines = []
    line_map = {}  # Maps text line numbers to original markdown line numbers
    
    current_text_line = 0
    
    for i, line in enumerate(lines):
        # Skip code blocks, YAML frontmatter, and other non-prose content
        if (is_in_code_block(lines, i) or 
            is_in_yaml_frontmatter(lines, i) or 
            re.match(r'^#+\s', line) or  # Skip headings
            re.match(r'^[*-]\s', line) or  # Skip list items
            re.match(r'^\s*```', line) or  # Skip code block markers
            re.match(r'^\s*\[.*\]:\s*', line) or  # Skip link references
            not line.strip()):  # Skip empty lines
            continue
        
        # Convert markdown to plain text for this line
        html_content = markdown.markdown(line)
        soup = BeautifulSoup(html_content, 'html.parser')
        text_line = soup.get_text()
        
        if text_line.strip():
            text_lines.append(text_line)
            line_map[current_text_line] = i
            current_text_line += 1
    
    return '\n'.join(text_lines), line_map

def check_grammar(content, file_path):
    """Check content for grammar issues using LanguageTool API."""
    # Extract plain text from markdown
    text, line_map = extract_text_from_markdown(content)
    
    if not text.strip():
        return []
    
    # Call LanguageTool API
    url = "https://api.languagetool.org/v2/check"
    params = {
        'text': text,
        'language': 'en-US',
        'enabledOnly': 'false'
    }
    
    try:
        response = requests.post(url, data=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        result = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling LanguageTool API: {e}")
        return []
    
    # Process results
    suggestions = []
    lines = content.split('\n')
    
    for match in result.get('matches', []):
        # Get the offset in the plain text
        offset = match.get('offset', 0)
        length = match.get('length', 0)
        
        # Find the line number in the plain text
        text_line_num = text[:offset].count('\n')
        
        # Map back to the original markdown line number
        if text_line_num in line_map:
            md_line_num = line_map[text_line_num]
            
            # Get the original line
            original_line = lines[md_line_num]
            
            # Get the context from the match
            context = match.get('context', {})
            context_text = context.get('text', '')
            context_offset = context.get('offset', 0)
            context_length = context.get('length', 0)
            
            # Extract the problematic text
            error_text = context_text[context_offset:context_offset + context_length]
            
            # Get the suggested replacements
            replacements = match.get('replacements', [])
            suggested_text = replacements[0].get('value', '') if replacements else ''
            
            # Create a suggestion
            if suggested_text and error_text in original_line:
                suggested_line = original_line.replace(error_text, suggested_text)
                
                suggestions.append({
                    "file": file_path,
                    "line": md_line_num + 1,  # 1-based line numbers
                    "original": original_line,
                    "suggested": suggested_line,
                    "reason": f"Grammar: {match.get('message', 'Grammar issue')}",
                })
    
    return suggestions

def save_suggestions_to_file(suggestions, output_file="grammar_suggestions.json"):
    """Save suggestions to a JSON file."""
    with open(output_file, "w") as f:
        json.dump(suggestions, f, indent=2)
    print(f"Saved grammar suggestions to {output_file}")

def print_suggestions(suggestions):
    """Print suggestions in a readable format."""
    if not suggestions:
        print("No grammar issues found.")
        return
    
    print(f"\nFound {len(suggestions)} grammar issues:")
    print("=" * 80)
    
    for i, sugg in enumerate(suggestions, 1):
        print(f"Issue {i}:")
        print(f"File: {sugg['file']}")
        print(f"Line: {sugg['line']}")
        print(f"Reason: {sugg['reason']}")
        print(f"Original: {sugg['original']}")
        print(f"Suggested: {sugg['suggested']}")
        print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description="Check markdown files for grammar issues")
    parser.add_argument("--file", help="Path to a specific markdown file to check")
    parser.add_argument("--dir", help="Directory containing markdown files to check")
    parser.add_argument("--output", default="grammar_suggestions.json", help="Output file for suggestions")
    args = parser.parse_args()
    
    if not args.file and not args.dir:
        print("Error: Please provide either --file or --dir argument")
        sys.exit(1)
    
    all_suggestions = []
    
    # Check a specific file
    if args.file:
        if not os.path.isfile(args.file):
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
        
        if not args.file.endswith((".md", ".mdx")):
            print(f"Warning: {args.file} is not a markdown file. Checking anyway.")
        
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
        
        suggestions = check_grammar(content, args.file)
        all_suggestions.extend(suggestions)
        print(f"Checked {args.file}: Found {len(suggestions)} grammar issues")
    
    # Check all markdown files in a directory
    if args.dir:
        if not os.path.isdir(args.dir):
            print(f"Error: Directory not found: {args.dir}")
            sys.exit(1)
        
        for root, _, files in os.walk(args.dir):
            for file in files:
                if file.endswith((".md", ".mdx")):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    suggestions = check_grammar(content, file_path)
                    all_suggestions.extend(suggestions)
                    print(f"Checked {file_path}: Found {len(suggestions)} grammar issues")
    
    # Print and save suggestions
    print_suggestions(all_suggestions)
    save_suggestions_to_file(all_suggestions, args.output)

if __name__ == "__main__":
    main()

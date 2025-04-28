#!/usr/bin/env python3
"""
Style checker for Arm Learning Paths content.
This script checks PR content against writing style guidelines and provides
replacement suggestions as GitHub commit suggestions.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
import requests
import yaml
import markdown
from collections import defaultdict

# Style rules based on Arm Learning Paths writing guidelines
STYLE_RULES = [
    {
        "pattern": r"\b(?:utilize|utilization|utilizes|utilizing)\b",
        "replacement": "use",
        "reason": "Use 'use' instead of 'utilize' for simplicity."
    },
    {
        "pattern": r"\b(?:optimize|optimization|optimizes|optimizing)\b",
        "replacement": "improve",
        "reason": "Simplify language by replacing 'optimize' with 'improve'."
    },
    {
        "pattern": r"\bin order to\b",
        "replacement": "to",
        "reason": "Use 'to' instead of 'in order to' for conciseness."
    },
    {
        "pattern": r"\bplease note that\b",
        "replacement": "",
        "reason": "Remove 'please note that' for directness."
    },
    {
        "pattern": r"\bthe data (?:is|was) processed\b",
        "replacement": "processed the data",
        "reason": "Use active voice instead of passive voice."
    },
    {
        "pattern": r"\byou should\b",
        "replacement": "",
        "reason": "Be direct with instructions, avoid 'you should'."
    },
    # Add more style rules based on the guidelines
]

def get_changed_files(pr_number, repo, token):
    """Get the list of files changed in the PR."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return [file_info for file_info in response.json() 
            if file_info["filename"].endswith((".md", ".mdx"))]

def get_file_content(repo, file_path, ref, token):
    """Get the content of a file from GitHub."""
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={ref}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 404:
        return None
    
    response.raise_for_status()
    content = response.json()
    
    if content.get("type") == "file":
        import base64
        return base64.b64decode(content["content"]).decode("utf-8")
    
    return None

def check_style(content, file_path):
    """Check content against style rules and return suggestions."""
    suggestions = []
    lines = content.split("\n")
    
    for i, line in enumerate(lines):
        for rule in STYLE_RULES:
            matches = re.finditer(rule["pattern"], line, re.IGNORECASE)
            for match in matches:
                # Skip code blocks
                if is_in_code_block(lines, i):
                    continue
                
                # Create a suggestion
                original = line
                suggested = re.sub(rule["pattern"], rule["replacement"], line, flags=re.IGNORECASE)
                
                if original != suggested:
                    suggestions.append({
                        "file": file_path,
                        "line": i + 1,
                        "original": original,
                        "suggested": suggested,
                        "reason": rule["reason"],
                        "file_content": content
                    })
                    # Only one suggestion per line to avoid conflicts
                    break
    
    return suggestions

def is_in_code_block(lines, line_index):
    """Check if the line is within a code block."""
    code_block_count = 0
    for i in range(line_index):
        if re.match(r'^```', lines[i]):
            code_block_count += 1
    
    return code_block_count % 2 == 1  # Odd count means inside a code block

def create_review_comment(repo, pr_number, suggestions, head_sha, token):
    """Create review comments with suggestions on GitHub PR."""
    # Group suggestions by file
    file_suggestions = defaultdict(list)
    for suggestion in suggestions:
        file_suggestions[suggestion["file"]].append(suggestion)
    
    # Create review comments
    review_comments = []
    for file_path, file_suggs in file_suggestions.items():
        for sugg in file_suggs:
            comment = {
                "path": sugg["file"],
                "line": sugg["line"],
                "body": f"**Style suggestion**: {sugg['reason']}\n\n"
                        f"```suggestion\n{sugg['suggested']}\n```"
            }
            review_comments.append(comment)
    
    # Submit the review
    if review_comments:
        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
        headers = {"Authorization": f"token {token}"}
        data = {
            "commit_id": head_sha,
            "body": "## Style Check Results\n\nI found some style issues that could be improved based on our writing guidelines.",
            "event": "COMMENT",
            "comments": review_comments
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        print(f"Created {len(review_comments)} style suggestions.")
    else:
        print("No style issues found.")

def save_suggestions_to_file(suggestions, output_file="style_suggestions.json"):
    """Save suggestions to a JSON file for debugging."""
    with open(output_file, "w") as f:
        json.dump(suggestions, f, indent=2)
    print(f"Saved suggestions to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Check PR content for style issues")
    parser.add_argument("--pr", required=True, help="PR number")
    parser.add_argument("--head-sha", required=True, help="Head commit SHA")
    parser.add_argument("--repo", required=True, help="Repository name (owner/repo)")
    parser.add_argument("--output", default="style_suggestions.json", help="Output file for suggestions")
    args = parser.parse_args()
    
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    # Get changed files in the PR
    try:
        changed_files = get_changed_files(args.pr, args.repo, token)
    except Exception as e:
        print(f"Error getting changed files: {e}")
        sys.exit(1)
    
    all_suggestions = []
    
    # Check each changed file
    for file_info in changed_files:
        file_path = file_info["filename"]
        print(f"Checking {file_path}...")
        
        try:
            content = get_file_content(args.repo, file_path, args.head_sha, token)
            if content:
                suggestions = check_style(content, file_path)
                all_suggestions.extend(suggestions)
                print(f"Found {len(suggestions)} style issues in {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Save suggestions to file
    save_suggestions_to_file(all_suggestions, args.output)
    
    # Create review comments
    try:
        create_review_comment(args.repo, args.pr, all_suggestions, args.head_sha, token)
    except Exception as e:
        print(f"Error creating review comments: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

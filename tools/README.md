# Style Checking Tools for Arm Learning Paths

This directory contains tools for checking and enforcing the writing style guidelines for Arm Learning Paths content.

## Available Tools

1. **enhanced_style_check.py**: Check markdown files against writing style guidelines and provide suggestions.
2. **github_suggestion.py**: Format style suggestions as GitHub review comments.
3. **style_rules.json**: JSON file containing style rules and patterns.

## Local Testing

### Prerequisites

No special dependencies are required for basic functionality.

### Usage

#### Check a single file:

```bash
python3 tools/enhanced_style_check.py --file path/to/file.md
```

#### Check all markdown files in a directory:

```bash
python3 tools/enhanced_style_check.py --dir path/to/directory
```

#### Format suggestions as GitHub review comments:

```bash
python3 tools/github_suggestion.py --input style_suggestions.json
```

## GitHub Actions Integration

The style checker is integrated with GitHub Actions and can be run manually on a PR:

1. Go to the "Actions" tab in the GitHub repository
2. Select the "Style Check" workflow
3. Click "Run workflow"
4. Enter the PR number and click "Run workflow"

The workflow will check the PR content and add review comments with suggestions.

## Style Rules

Style rules are defined in `style_rules.json`. Each rule has:

- **pattern**: Regular expression pattern to match
- **replacement**: Text to replace the matched pattern
- **reason**: Explanation for the suggestion

To add or modify rules, edit the `style_rules.json` file.

## Example

Input:
```markdown
In order to utilize this feature, you should follow these steps.
```

Output suggestion:
```
Use 'use' instead of 'utilize' for simplicity.

```suggestion
To use this feature, follow these steps.
```
```

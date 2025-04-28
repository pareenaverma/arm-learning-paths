# Style Checking Tools for Arm Learning Paths

This directory contains tools for checking and enforcing the writing style guidelines for Arm Learning Paths content.

## Available Tools

1. **enhanced_style_check.py**: Check markdown files against writing style guidelines and provide suggestions. Uses both rule-based checks and NLP-based passive voice detection.
2. **github_suggestion.py**: Format style suggestions as GitHub review comments.
3. **style_rules.json**: JSON file containing style rules and patterns.

## Local Testing

### Prerequisites

For basic functionality, no special dependencies are required.

For advanced passive voice detection, you'll need:
- spaCy library
- English language model for spaCy

You can install these with:
```bash
pip install spacy
python -m spacy download en_core_web_sm
```

Or use the built-in installer:
```bash
python3 tools/enhanced_style_check.py --install-spacy
```

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

The workflow will check the PR content and add review comments with suggestions that you can directly commit or dismiss.

## Style Rules

Style rules are defined in `style_rules.json`. Each rule has:

- **pattern**: Regular expression pattern to match
- **replacement**: Text to replace the matched pattern
- **reason**: Explanation for the suggestion

To add or modify rules, edit the `style_rules.json` file.

### Types of Style Checks

The style checker performs several types of checks:

1. **Word Choice**: Replaces complex words with simpler alternatives (e.g., "utilize" → "use")
2. **Passive Voice**: Converts passive voice to active voice for clarity and directness
3. **Wordiness**: Simplifies wordy phrases (e.g., "in order to" → "to")
4. **Tone**: Replaces "we" with "you" to address the reader directly
5. **Neutrality**: Replaces phrases like "we recommend" with "it is recommended" for a more neutral tone

## Passive Voice Detection

The style checker uses two methods to detect passive voice:

1. **spaCy NLP (Advanced)**: Uses spaCy's dependency parsing to identify passive voice constructions and suggest active voice alternatives. This method is more accurate but requires additional dependencies.

2. **Regular Expressions (Basic)**: Falls back to regex patterns if spaCy is not available. This method is less accurate but has no dependencies.

## Examples

### Word Choice Example:
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

### Passive Voice Example:
Input:
```markdown
The data is processed by the system.
```

Output suggestion:
```
Convert passive voice to active voice for clarity and directness.

```suggestion
The system processes the data.
```
```

### Tone Example:
Input:
```markdown
We recommend using Amazon Q for development.
```

Output suggestion:
```
Use 'it is recommended' instead of 'we recommend' for a more neutral tone.

```suggestion
It is recommended using Amazon Q for development.
```
```

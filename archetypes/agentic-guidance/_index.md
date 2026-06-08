---
title: "{{ replace .Name "-" " " | title }}"
description: ""
weight: 1
layout: agenticall

author: ""

### Target hardware
armips:
operatingsystems:
tools_software_languages:

### Agentic metadata
agent_compatible:
    - GitHub Copilot Agent Mode
    - Claude Code
    - Codex CLI
task_type: ""               # migration | optimization | debugging | scaffolding
estimated_turns: 5
requires_tool_calls: true   # set false if the workflow is prompt-only
---

## Overview

<!-- What developer problem does this workflow solve? One paragraph. -->

## Files in this workflow

| File | Purpose |
|---|---|
| [prompt.md](prompt.md) | The structured prompt to paste into your agent |
| [workflow.md](workflow.md) | Step-by-step breakdown of what the agent does at each turn |

## How to use this guidance

1. Open your agent of choice
2. Open the target repository
3. Paste the contents of [prompt.md](prompt.md) as your first message
4. Follow the agent through the [workflow](workflow.md)

## Prerequisites

-

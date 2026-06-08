---
title: Migrate a containerized x86 workload to Arm Graviton
description: Agentic workflow and prompt files for using an AI coding agent to assess, adapt, and validate a Docker-based application for Arm Graviton (aarch64).
weight: 1
layout: agenticall

author: Pareena Verma

### Target hardware
subjects: Containers and Virtualization
armips:
    - Neoverse
operatingsystems:
    - Linux
tools_software_languages:
    - Docker
    - Python

### Agentic-guidance-specific metadata
agent_compatible:
    - GitHub Copilot Agent Mode
    - Claude Code
    - Codex CLI
    - Amazon Q Developer
task_type: migration
estimated_turns: 8
requires_tool_calls: true
---

## Overview

This workflow guides an AI coding agent through migrating a containerized x86 application to run natively on Arm Graviton. The agent audits the Dockerfile and dependencies, rebuilds for `linux/arm64`, and validates the result.

## Files in this workflow

| File | Purpose |
|---|---|
| [prompt.md](prompt.md) | The structured prompt to paste into your agent |
| [workflow.md](workflow.md) | Step-by-step breakdown of what the agent does at each turn |
| [validation-script.sh](files/validation-script.sh) | Shell script the agent runs to verify the migrated container |

## How to use this guidance

1. Open your agent of choice (GitHub Copilot agent mode, Claude Code, or similar)
2. Open the repository containing your x86 container application
3. Paste the contents of [prompt.md](prompt.md) as your first message
4. Follow the agent through the [workflow](workflow.md) — intervene only where flagged

## Prerequisites

- An Arm Graviton instance or local Arm machine with Docker installed
- The x86 application source code available locally or cloned
- [Install Docker on Arm](/install-guides/docker/docker-engine/)

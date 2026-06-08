---
title: "Prompt — {{ replace .Name "-" " " | title }}"
weight: 2
layout: agenticall
---

## Agent prompt

Copy the block below in full and paste it as your opening message to the agent.

```text
<!-- 
  Write the agent prompt here. Follow these principles:
  - State the target hardware explicitly (Arm aarch64, Graviton, Neoverse, etc.)
  - Define what the agent must NOT change (application logic, APIs, data models)
  - Give the agent a concrete success signal (a command to run, output to check)
  - End with: "Confirm you understand, then ask me for [specific input] before proceeding."
-->
```

## What the prompt does

<!-- Explain the key constraints and why each exists -->

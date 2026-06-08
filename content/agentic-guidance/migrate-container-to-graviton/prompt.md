---
title: Prompt — migrate a containerized x86 workload to Arm Graviton
weight: 2
layout: agenticall
---

## Agent prompt

Copy the block below in full and paste it as your opening message to the agent.

```text
You are helping migrate a containerized x86 application to run natively on Arm Graviton (linux/arm64).

Target environment:
- Architecture: aarch64 (AWS Graviton, Ampere Altra, or equivalent)
- OS: Ubuntu 24.04 or Amazon Linux 2023
- Container runtime: Docker (buildx with linux/arm64 support)

Repository context:
- The project root is the current working directory
- The primary Dockerfile is at the path I will confirm below

Your task:
1. Read the Dockerfile and identify any x86-specific base images, binaries, or build flags
2. Check package.json, requirements.txt, go.mod, or the equivalent dependency file for packages with known Arm compatibility issues
3. Propose a modified Dockerfile that targets linux/arm64. Use multi-arch base images where available (e.g., ubuntu:24.04, python:3.11-slim)
4. Rebuild the image using: docker buildx build --platform linux/arm64 -t <image-name>:arm64 .
5. Run the container and execute the validation script at tools/validation-script.sh
6. Report any failures with the exact error, the likely cause, and a proposed fix
7. Repeat steps 4–6 until the container runs cleanly

Do not modify application logic. Only change build configuration, base images, and platform-specific dependencies.

Confirm you understand the task, then ask me for the Dockerfile path before proceeding.
```

## What the prompt does

- Scopes the agent to build changes only — application logic is off-limits
- Forces the agent to ask for confirmation before modifying files
- Provides a concrete validation step so the agent has an objective success signal
- Keeps the agent in a loop until the build passes

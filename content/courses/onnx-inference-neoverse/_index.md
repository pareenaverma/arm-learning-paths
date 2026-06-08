---
title: Run ML inference on Arm Neoverse with ONNX Runtime
description: Learn how to prepare, optimize, and run an ONNX model on Arm Neoverse servers using ONNX Runtime, measuring latency and throughput at each stage.
weight: 1
layout: coursesall

minutes_to_complete: 90
level: Introductory
author: Pareena Verma

### Tags — same taxonomy as Learning Paths for cross-pillar filtering
subjects: ML
armips:
    - Neoverse
operatingsystems:
    - Linux
tools_software_languages:
    - Python
    - ONNX
    - GCC

### Course-specific metadata
modules:
    - module: 1
      title: Set up the Arm Neoverse environment
      file: module-1-setup.md
    - module: 2
      title: Load and inspect an ONNX model
      file: module-2-load-model.md
    - module: 3
      title: Run inference and measure performance
      file: module-3-inference.md
    - module: 4
      title: Apply ONNX Runtime optimizations for Arm
      file: module-4-optimize.md
---

This course walks you through running machine learning inference on an Arm Neoverse server using ONNX Runtime. You'll go from a raw model file to a tuned, benchmarked inference pipeline — all on Arm-native hardware.

## What you'll learn

- Set up ONNX Runtime on an aarch64 Linux server
- Load, inspect, and validate an ONNX model
- Measure baseline inference latency and throughput
- Apply Arm-specific execution provider optimizations

## Prerequisites

- An Arm Neoverse instance (AWS Graviton, Ampere Altra, or similar)
- Basic Python knowledge
- [Install Python](/install-guides/python/)

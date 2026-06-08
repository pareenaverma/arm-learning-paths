---
title: "Module 1: Set up the Arm Neoverse environment"
weight: 1
layout: coursesall
minutes_to_complete: 15
---

## Set up the Arm Neoverse environment

In this module you'll provision your Arm Neoverse instance and install the dependencies needed for the rest of the course.

### Provision an Arm Neoverse instance

Any of the following work:

- **AWS Graviton**: launch a `c7g.large` or larger EC2 instance with Amazon Linux 2023 or Ubuntu 24.04
- **Ampere Altra**: Ampere Developer Cloud or OCI Ampere A1
- **Local Arm hardware**: any aarch64 system running Ubuntu 22.04 or 24.04

Confirm the architecture before continuing:

```bash
uname -m
```

The expected output is:

```output
aarch64
```

### Install Python and pip

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv
```

### Create a virtual environment

```bash
python3 -m venv onnx-env
source onnx-env/bin/activate
```

### Install ONNX Runtime

{{% notice Note %}}
The following commands use ONNX Runtime version 1.18.0. The same commands work with other versions. To find the latest version, see [ONNX Runtime releases](https://github.com/microsoft/onnxruntime/releases).
{{% /notice %}}

```bash
pip install onnxruntime==1.18.0 onnx numpy
```

Verify the installation:

```bash
python3 -c "import onnxruntime; print(onnxruntime.__version__)"
```

The expected output is:

```output
1.18.0
```

## What you've learned and what's next

In this module you set up a working Python environment with ONNX Runtime on an Arm Neoverse server. In the next module you'll load and inspect an ONNX model to understand its structure before running inference.

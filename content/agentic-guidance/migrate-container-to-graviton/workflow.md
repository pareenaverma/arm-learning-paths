---
title: Workflow — migrate a containerized x86 workload to Arm Graviton
weight: 3
layout: agenticall
---

## Agentic workflow breakdown

This page describes what the agent does at each turn, what output to expect, and when to intervene.

### Turn 1 — Confirm task and request Dockerfile path

**Agent action**: Summarizes the task and asks for the Dockerfile path.

**Your response**: Provide the relative path, for example `./Dockerfile` or `services/api/Dockerfile`.

**Do not intervene if**: The agent correctly restates the goal (Arm migration, no logic changes).

---

### Turn 2 — Audit the Dockerfile

**Agent action**: Reads the Dockerfile. Reports:
- Base image and whether it has an official `linux/arm64` variant
- `RUN` steps that reference x86 binaries, `uname -m` checks, or hardcoded architecture strings
- Any `--platform` flags already present

**Expected output**:
```
Base image: node:18-alpine
Arm64 support: yes (multi-arch official image)
Issues found:
  - Line 12: curl download targets x86_64 binary
  - Line 19: RUN apt-get install libssl-dev — check Arm package availability
```

**Intervene if**: The agent proposes changing application code (routes, business logic, database queries).

---

### Turn 3 — Audit dependencies

**Agent action**: Reads the dependency file (`package.json`, `requirements.txt`, `go.mod`, etc.). Flags:
- Native extensions that need recompilation
- Packages pinned to x86-only wheels or binaries
- Known incompatible versions

**Expected output lists** flagged packages with a recommended fix or version bump.

---

### Turn 4 — Propose modified Dockerfile

**Agent action**: Produces a complete updated Dockerfile. Review the diff before approving.

**Approve if**: Changes are limited to:
- Base image tags updated to multi-arch or explicit `arm64` variants
- Architecture-conditional download URLs
- Build flags such as `GOARCH=arm64` or `TARGETARCH`

**Reject and clarify if**: The agent changes `CMD`, `ENTRYPOINT`, environment variables unrelated to the build, or application source files.

---

### Turn 5 — Build for linux/arm64

**Agent action**: Runs:

```bash
docker buildx build --platform linux/arm64 -t <image>:arm64 --load .
```

**Expected output**: Build log ending with a success line such as:

```output
=> exporting to image
=> => naming to docker.io/library/<image>:arm64
```

**If the build fails**: The agent should report the exact error line, diagnose the cause, and propose a fix. It loops back to Turn 4.

---

### Turn 6 — Run and validate

**Agent action**: Starts the container and runs the validation script:

```bash
docker run --rm <image>:arm64 /bin/sh -c "$(cat tools/validation-script.sh)"
```

**Expected output**: All checks pass:

```output
[PASS] Architecture: aarch64
[PASS] Application starts
[PASS] Health endpoint responds with HTTP 200
```

**If any check fails**: The agent diagnoses and loops back to Turn 4 or Turn 5 as appropriate.

---

### Turn 7 — Summary report

**Agent action**: Produces a migration summary:
- Changes made (files and line numbers)
- Packages updated and why
- Confirmed architecture at runtime
- Any manual follow-up items

Use this summary as the basis for your PR description.

---

## Intervention checklist

Before approving any agent action, confirm:

- [ ] No application logic was modified
- [ ] Base images have official `linux/arm64` support
- [ ] Native dependencies were recompiled, not removed
- [ ] The validation script passed on the Arm host, not an emulated environment

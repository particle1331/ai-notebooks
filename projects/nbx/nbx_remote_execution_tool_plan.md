# NBX: Remote Execution Tool (Design Plan)

## Overview

NBX is a CLI tool that allows users to execute notebooks, Python scripts, or entire projects on a remote machine (e.g., RunPod) while streaming logs in real time and retrieving outputs after execution.

---

## Goals

- Run `.ipynb`, `.py`, or full project folders remotely
- Support parameter injection
- Support environment variable injection
- Stream logs in real time to local dashboard
- Retrieve outputs/artifacts after execution
- Keep UX simple and developer-friendly

---

## CLI Design

### Basic Usage

```bash
nbx run notebook.ipynb
nbx run script.py
nbx run ./project --entry train.py
```

### With Parameters

```bash
nbx run train.py -- --epochs 10 --lr 0.001
nbx run notebook.ipynb --params epochs=10 lr=0.001
```

### With Environment Variables

```bash
nbx run train.py \
  --env CUDA_VISIBLE_DEVICES=0 \
  --env MODE=prod
```

### With Params File

```bash
nbx run train.py --params-file params.yaml
```

---

## Core Concepts

### Job Specification

All executions are normalized into a single job structure:

```json
{
  "type": "notebook | script | project",
  "entrypoint": "train.py",
  "path": "./project",
  "params": {},
  "env": {}
}
```

---

## Execution Types

### Notebook

- Executed using `papermill`
- Supports parameter injection

```bash
papermill input.ipynb output.ipynb -p key value
```

---

### Python Script

- Executed directly via Python

```bash
python script.py --arg value
```

---

### Project Folder

- Uploaded as archive
- Extracted remotely
- Entry point executed

```bash
python train.py
```

---

## Packaging Strategy

### MVP

- Archive project using tar.gz
- Upload via SCP or rsync

```bash
tar -czf job.tar.gz ./project
scp job.tar.gz remote:/workspace/
```

---

## Remote Execution Flow

1. Upload job archive
2. Extract on remote
3. Set environment variables
4. Execute based on job type
5. Stream logs
6. Save outputs

---

## Logging & Streaming

### Approach

Wrap execution and stream stdout/stderr:

```python
proc = subprocess.Popen(
    command,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

for line in proc.stdout:
    print(line, flush=True)
```

### Transport Options

- MVP: SSH stdout streaming
- Future: WebSockets

---

## Parameter Injection

### Scripts

- Pass through CLI arguments

### Notebooks

- Use papermill `-p` flags
- Require parameters cell

---

## Environment Variables

- Inject into subprocess environment

```python
env = {**os.environ, **custom_env}
```

---

## Artifact Handling

### Outputs

- Executed notebook
- Logs
- Generated files

### Retrieval

```bash
scp remote:/workspace/output ./local_output
```

---

## Local Dashboard (MVP)

### Option 1: Terminal UI

- Use `rich`
- Display logs in real time

### Option 2: Web UI (Future)

- FastAPI + WebSocket
- React frontend

---

## Project Structure

```bash
nbx/
  cli.py
  packager.py
  remote.py
  runner.py
  dashboard.py
  transport/
    ssh.py
```

---

## Runner Abstraction

```python
class Runner:
    def run(self): ...

class NotebookRunner(Runner): ...
class ScriptRunner(Runner): ...
class ProjectRunner(Runner): ...
```

---

## Advanced Features (Future)

### Dev Mode

```bash
nbx run ./project --entry train.py --watch
```

- Watches file changes
- Re-syncs and restarts job

---

### Docker Support

- Build image from project
- Run in container

---

### Multi-Provider Support

- RunPod
- AWS
- GCP

---

### Parallel Jobs

- Run multiple jobs concurrently

---

### Secret Management

- Mask sensitive env variables

---

## Edge Cases

### Large Outputs

- Truncate or chunk logs

### Dependency Issues

- Require preconfigured environment
- Future: auto install

### Relative Paths

- Preserve project structure exactly

### Long Running Jobs

- Add heartbeat logs

---

## MVP Scope

### Included

- Script execution
- Notebook execution
- Project execution
- Param injection
- Env injection
- SSH-based execution
- Stdout streaming
- Artifact download

### Excluded (for now)

- Web UI
- Docker builds
- Multi-node orchestration
- Job queueing

---

## Summary

NBX is a lightweight remote execution tool focused on:

- Simplicity
- Real-time feedback
- Flexibility across notebooks, scripts, and projects

It enables developers to offload heavy workloads to remote machines without losing visibility or control.


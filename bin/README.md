# 📁 Folder `bin/` — Utility Scripts

This folder contains the project's executable scripts to facilitate setup, testing, CI/CD, and other local operations.

## Available Scripts

| Script         | Description                                                                |
|----------------|---------------------------------------------------------------------------|
| `setup.sh`     | Sets up virtual environment, installs dependencies and pre-commit hooks    |
| `bootstrap.sh` | Prepares your local machine: installs Poetry, Docker, prerequisites        |

## How to use

```bash
chmod +x bin/*.sh  # Ensure permission
./bin/setup.sh
./bin/bootstrap.sh -e push -j lint
```
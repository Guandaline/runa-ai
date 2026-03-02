# 🚀 Onboarding Guide — athomic

This guide helps new developers quickly set up the development environment for the `athomic` project.

---

## ⚙️ Local Setup

1. Give execution permission to the setup script:

```bash
chmod +x bin/setup.sh
```

2. Run the script with Make:

```bash
make setup
```

This command will:
- Create a local `.venv` virtual environment with Poetry
- Activate the virtual environment (via `source`)
- Install project dependencies
- Create the `.env` file from `.env.example` (if needed)
- Load the `GH_TOKEN` or `CI_JOB_TOKEN` variable
- Start the application with `uvicorn`

> ℹ️ If you prefer to run manually:
> ```bash
> source bin/setup.sh
> ```

---

## 📦 Versioning with Semantic Release

This project uses `python-semantic-release` for automated version control.

### Run release manually:

```bash
make release
```

Or:

```bash
poetry run dotenv run -- poetry run semantic-release version
```

---

## 🔐 Setting up GH_TOKEN on GitHub

1. Go to: `Settings > Secrets and variables > Actions`
2. Click **New repository secret**
3. Name: `GH_TOKEN`
4. Value: your personal token with `repo`, `workflow`, `write:packages` scopes

---

## 💻 (Optional) Set up GH_TOKEN via GitHub CLI

```bash
gh auth login
gh secret set GH_TOKEN -b"your_token_here"
```

---

## 🛠️ Integration with GitLab CI/CD (future-ready)

In GitLab CI, the `CI_JOB_TOKEN` will be automatically used as `GH_TOKEN`.

---

## 🧰 Useful Make Commands

### 🔧 Local setup
```bash
make setup
```

---
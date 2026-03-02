#!/usr/bin/env bash
set -e

echo "🔧 Installing development prerequisites..."

# Install Poetry if not already installed
if ! command -v poetry &> /dev/null; then
  echo "📦 Installing Poetry..."
  curl -sSL https://install.python-poetry.org | python3 -
else
  echo "✅ Poetry already installed"
fi

# Install Docker if necessary (Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]] && ! command -v docker &> /dev/null; then
  echo "🐳 Installing Docker..."
  sudo apt-get update && sudo apt-get install -y docker.io
else
  echo "✅ Docker already installed (or not required)"
fi

echo "🧹 Updating pre-commit and dependencies..."
pip install --upgrade pre-commit

echo "🎉 Environment successfully prepared!"
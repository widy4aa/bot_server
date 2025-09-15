#!/usr/bin/env bash
set -euo pipefail

# Usage:
#  PYTHON=/path/to/python ./build.sh
# Default Python interpreter (override with PYTHON env var)
PYTHON=${PYTHON:-/home/widy4aa/py_for_code/bin/python}
APP=main.py
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="$PROJECT_ROOT/dist"
TMPDIR=$(mktemp -d)

echo "Project root: $PROJECT_ROOT"
echo "Temporary build dir: $TMPDIR"
echo "Using Python: $PYTHON"

# Ensure PyInstaller is available in the selected interpreter
if ! $PYTHON -m PyInstaller --version >/dev/null 2>&1; then
  echo "PyInstaller not found in $PYTHON, installing..."
  $PYTHON -m pip install --upgrade pyinstaller
fi

# Copy project to temporary dir while excluding sensitive files/folders
echo "Copying project to temporary build directory (excluding .env, user.csv, Downloads)..."
rsync -a --delete \
  --exclude='.git' \
  --exclude='venv' --exclude='.venv' --exclude='env' \
  --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='.gitignore' \
  --exclude='.env' \
  --exclude='user.csv' \
  --exclude='Downloads' \
  --exclude='dist' --exclude='build' --exclude='*.spec' \
  "$PROJECT_ROOT/" "$TMPDIR/"

cd "$TMPDIR"

# Clean previous PyInstaller outputs if any
rm -rf build dist *.spec || true

echo "Running PyInstaller (onefile)..."
$PYTHON -m PyInstaller --onefile --clean --noconfirm "$APP"

# Ensure output directory exists in original project
mkdir -p "$OUT_DIR"

# Copy built artifact(s) back to project out dir
echo "Copying artifacts to $OUT_DIR"
cp -v dist/* "$OUT_DIR/"

echo "Build finished. Artifacts available in: $OUT_DIR"

echo "Cleaning temporary build dir..."
cd "$PROJECT_ROOT"
rm -rf "$TMPDIR"

echo "Done."
#!/usr/bin/env bash
# Build script for unified deployment on Render / Railway
set -e

echo "=== Installing Python dependencies ==="
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "=== Building React frontend ==="
npm --prefix frontend install
npm --prefix frontend run build

echo "=== Build completed successfully ==="

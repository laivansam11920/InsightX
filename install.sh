#!/bin/bash

# ==============================================================================
# Script Name: install.sh
# Description: Automated environment setup for InsightX
# Author: Lại Văn Sâm
# Date: July 2026
# ==============================================================================

set -e # Exit immediately if a command exits with a non-zero status

echo "--- Initializing InsightX Environment Setup ---"

# 1. Identify Operating System
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo "[INFO] Detected OS: Linux (Ubuntu/Debian)"
    sudo apt update && sudo apt install -y python3 python3-venv python3-pip
    sudo dnf update && sudo dnf install python3
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    OS="windows"
    echo "[INFO] Detected OS: Windows"
    echo "[INFO] You should install python3 before proceeding."
else
    echo "[ERROR] Unsupported OS: $OSTYPE"
    exit 1
fi

# 2. Setup Python Environment
if [ ! -d ".venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv .venv
fi

# 3. Activate Virtual Environment
echo "[INFO] Activating virtual environment..."
if [ "$OS" == "linux" ]; then
    source .venv/bin/activate
else
    source .venv/Scripts/activate
fi

# 4. Install Dependencies
echo "[INFO] Upgrading pip and installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt


if [ -f .env ]; then
    echo "The .env file already exists. Skipping the creation step."
else
    echo "Creating a sample .env file..."

    cat << EOF > .env
PORT=5000
DEBUG=True
TEST=True

GITHUB_TOKEN=your_github_token_classic
NAME_GITHUB=your_github_name
MONGO_URI=your_mongodb_url

DB_NAME=your_db_name
DB_COLLECTION=your_db_collection_in_db_name

EOF

    echo "Successfully created the .env file!"
fi

echo "[SUCCESS] Environment setup complete. Launching InsightX..."
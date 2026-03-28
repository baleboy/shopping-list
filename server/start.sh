#!/bin/bash
set -e

DATA_DIR="${SHOPPING_DATA_DIR:-/data}"

if [ -d "$DATA_DIR/.git" ]; then
    echo "Pulling latest data..."
    git -C "$DATA_DIR" pull --ff-only || true
elif [ -d "$DATA_DIR" ]; then
    echo "Cloning data repo into existing directory..."
    git clone https://github.com/baleboy/shopping-list-data.git "$DATA_DIR/tmp_clone"
    mv "$DATA_DIR/tmp_clone/"* "$DATA_DIR/tmp_clone/".git "$DATA_DIR/" 2>/dev/null || true
    rm -rf "$DATA_DIR/tmp_clone"
else
    echo "Cloning data repo..."
    git clone https://github.com/baleboy/shopping-list-data.git "$DATA_DIR"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8080

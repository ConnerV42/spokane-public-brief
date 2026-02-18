#!/usr/bin/env bash
set -euo pipefail

# Spokane Public Brief — Build Script
# Packages Lambda functions + frontend for deployment
# Output: dist/api.zip, dist/ingestor.zip, dist/analyzer.zip, dist/frontend/

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="$PROJECT_DIR/dist"
BUILD_DIR="$PROJECT_DIR/.build"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[build]${NC} $*"; }
warn() { echo -e "${YELLOW}[build]${NC} $*"; }
err()  { echo -e "${RED}[build]${NC} $*" >&2; }

# Clean previous build
rm -rf "$DIST_DIR" "$BUILD_DIR"
mkdir -p "$DIST_DIR" "$BUILD_DIR"

# --- Lambda Packages ---

# Install dependencies into a shared layer directory
log "Installing Python dependencies..."
DEPS_DIR="$BUILD_DIR/deps"
pip install --quiet --target "$DEPS_DIR" \
    -r "$PROJECT_DIR/requirements.txt" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.12 \
    --only-binary=:all: \
    2>/dev/null || {
    warn "Cross-platform install failed, falling back to native pip install"
    pip install --quiet --target "$DEPS_DIR" -r "$PROJECT_DIR/requirements.txt"
}

# Copy source package
log "Copying source package..."
cp -r "$PROJECT_DIR/src/spokane_public_brief" "$DEPS_DIR/"

build_lambda() {
    local name="$1"
    local handler_file="$2"
    local zip_name="$3"

    log "Packaging $name → dist/$zip_name..."
    local staging="$BUILD_DIR/$name"
    mkdir -p "$staging"

    # Copy deps + source
    cp -r "$DEPS_DIR"/* "$staging/"

    # Copy handler to root
    cp "$PROJECT_DIR/$handler_file" "$staging/"

    # Create zip
    (cd "$staging" && zip -qr "$DIST_DIR/$zip_name" .)
}

build_lambda "api"      "lambda_handler.py"    "api.zip"
build_lambda "ingestor" "ingestor_handler.py"  "ingestor.zip"
build_lambda "analyzer" "analyzer_handler.py"  "analyzer.zip"

# Show sizes
log "Lambda packages:"
for z in "$DIST_DIR"/*.zip; do
    size=$(du -sh "$z" | cut -f1)
    echo "  $(basename "$z"): $size"
done

# --- Frontend ---

if [ -d "$FRONTEND_DIR" ]; then
    log "Building frontend..."
    (cd "$FRONTEND_DIR" && npm ci --silent 2>/dev/null && npm run build)
    if [ -d "$FRONTEND_DIR/dist" ]; then
        cp -r "$FRONTEND_DIR/dist" "$DIST_DIR/frontend"
        log "Frontend built → dist/frontend/"
    else
        err "Frontend build produced no output"
        exit 1
    fi
else
    warn "No frontend/ directory, skipping frontend build"
fi

log "Build complete! Output in dist/"
ls -la "$DIST_DIR/"

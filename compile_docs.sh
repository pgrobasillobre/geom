#!/bin/bash

# Script to clean and rebuild GEOM documentation

BUILD_DIR="docs/_build"

echo "🧹 Cleaning previous build..."
if [ -d "$BUILD_DIR" ]; then
    rm -rf "$BUILD_DIR"
    echo " Removed $BUILD_DIR"
else
    echo " No previous build found."
fi

echo "📚 Rebuilding documentation..."
sphinx-build -b html docs "$BUILD_DIR/html"

if [ $? -eq 0 ]; then
    echo " Documentation built successfully!"
    echo " Output located at $BUILD_DIR/html/index.html"
else
    echo "❌ Build failed."
fi


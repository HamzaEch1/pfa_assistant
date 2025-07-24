#!/bin/bash

echo "🔄 Starting Atlas to Qdrant synchronization..."

# Check if Atlas is running
if ! docker-compose ps | grep atlas | grep -q "Up"; then
    echo "❗ Atlas is not running. Please start it first with: docker-compose up -d"
    exit 1
fi

# Check if Qdrant is accessible (assuming it's running in main project)
echo "🔍 Checking Qdrant connectivity..."
if ! curl -s http://localhost:6333 > /dev/null; then
    echo "❗ Qdrant is not accessible at localhost:6333"
    echo "💡 Make sure your main project's Qdrant is running"
    echo "💡 You can also start a local Qdrant with: docker run -p 6333:6333 qdrant/qdrant"
    exit 1
fi

# Build script container if not exists
echo "📊 Building script container..."
docker build -f Dockerfile.scripts -t atlas-scripts .

echo "🔄 Running Atlas to Qdrant synchronization..."
docker run --rm --network host \
    -e ATLAS_URL=http://localhost:21000 \
    -e QDRANT_URL=http://localhost:6333 \
    -e QDRANT_COLLECTION_NAME=atlas_catalog \
    atlas-scripts python scripts/sync_atlas_to_qdrant.py

echo "✅ Synchronization completed!"
echo "📊 Data is now available in Qdrant collection: atlas_catalog"
echo "🔗 Qdrant dashboard: http://localhost:6333/dashboard" 
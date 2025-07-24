#!/bin/bash

echo "🚀 Starting Apache Atlas population from Excel catalog..."

# Check if Docker Compose services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "❗ Starting Apache Atlas services..."
    docker-compose up -d
    echo "⏳ Waiting for services to be ready..."
    sleep 60
fi

# Build and run the populate script
echo "📊 Building script container..."
docker build -f Dockerfile.scripts -t atlas-scripts .

echo "📋 Running Excel to Atlas population script..."
docker run --rm --network apache-atlas_atlas-network \
    -e ATLAS_URL=http://atlas:21000 \
    -e QDRANT_URL=http://localhost:6333 \
    atlas-scripts python scripts/populate_atlas_from_excel.py

echo "✅ Atlas population completed!"
echo "🌐 You can access Atlas at: http://localhost:21000"
echo "🔑 Username: admin, Password: admin" 
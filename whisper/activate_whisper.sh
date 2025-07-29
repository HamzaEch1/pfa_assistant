#!/bin/bash
# Whisper Environment Activation Script
# Usage: source activate_whisper.sh

echo "🎤 Activating Whisper Environment..."

# Activate the virtual environment
source whisper_env/bin/activate

# Show status
echo "✅ Whisper environment activated!"
echo "📋 Available commands:"
echo "   whisper --help           # Show help"
echo "   whisper audio.mp3        # Transcribe audio"
echo "   python test_whisper.py   # Run test script"
echo ""
echo "🎯 Quick examples:"
echo "   whisper audio.wav --model base"
echo "   whisper audio.mp3 --language French"
echo "   whisper audio.m4a --task translate"
echo ""
echo "💡 To deactivate: deactivate" 
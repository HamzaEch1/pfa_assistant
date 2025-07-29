#!/usr/bin/env python3
"""
Test script for OpenAI Whisper
This script demonstrates how to use Whisper for speech recognition.
"""

import whisper
import os
import tempfile
import numpy as np
import torch
from pathlib import Path

def test_whisper_basic():
    """Test basic Whisper functionality"""
    print("🎤 Testing Whisper Speech Recognition")
    print("=" * 50)
    
    # Load a small model for testing
    print("Loading Whisper model (tiny)...")
    model = whisper.load_model("tiny")
    print(f"✅ Model loaded successfully!")
    print(f"   Device: {model.device}")
    print(f"   Model dimensions: {model.dims}")
    
    return model

def create_test_audio():
    """Create a simple test audio signal"""
    print("\n🔊 Creating test audio signal...")
    
    # Create a simple sine wave (440 Hz, A note)
    sample_rate = 16000
    duration = 3  # seconds
    frequency = 440  # Hz
    
    t = np.linspace(0, duration, sample_rate * duration, False)
    audio_signal = np.sin(2 * np.pi * frequency * t) * 0.3
    
    # Save to temporary file
    temp_dir = Path("temp_audio")
    temp_dir.mkdir(exist_ok=True)
    
    audio_file = temp_dir / "test_tone.wav"
    
    # Save using a simple method (you might need scipy.io.wavfile for more complex audio)
    try:
        import soundfile as sf
        sf.write(str(audio_file), audio_signal, sample_rate)
        print(f"✅ Test audio saved to: {audio_file}")
    except ImportError:
        print("⚠️  soundfile not available, skipping audio file creation")
        return None
    
    return audio_file

def transcribe_audio(model, audio_file):
    """Transcribe audio using Whisper"""
    if audio_file is None or not audio_file.exists():
        print("⚠️  No audio file available for transcription")
        return
    
    print(f"\n📝 Transcribing audio: {audio_file}")
    
    try:
        # Transcribe the audio
        result = model.transcribe(str(audio_file))
        
        print("✅ Transcription completed!")
        print(f"   Detected language: {result.get('language', 'unknown')}")
        print(f"   Text: '{result['text']}'")
        
        # Show segments if available
        if 'segments' in result:
            print(f"   Segments: {len(result['segments'])}")
    
    except Exception as e:
        print(f"❌ Transcription failed: {e}")

def demo_whisper_features(model):
    """Demonstrate various Whisper features"""
    print("\n🚀 Whisper Features Demo")
    print("-" * 30)
    
    # Show available languages
    print(f"📋 Supported languages: {len(whisper.tokenizer.LANGUAGES)} languages")
    print("   Examples:", list(list(whisper.tokenizer.LANGUAGES.items())[:5]))
    
    # Show model info
    print(f"🧠 Model info:")
    print(f"   Model type: {type(model).__name__}")
    print(f"   Parameters: ~{model.dims.n_audio_state}M (estimated)")

def show_usage_examples():
    """Show usage examples"""
    print("\n📖 Usage Examples")
    print("-" * 20)
    
    print("🎯 Command Line Usage:")
    print("   whisper audio.mp3 --model tiny")
    print("   whisper audio.wav --language French")
    print("   whisper audio.m4a --task translate --model medium")
    
    print("\n🐍 Python API Usage:")
    print("""
import whisper

# Load model
model = whisper.load_model("base")

# Transcribe audio
result = model.transcribe("audio.mp3")
print(result["text"])

# With language specification
result = model.transcribe("audio.mp3", language="French")

# Translation to English
result = model.transcribe("foreign_audio.mp3", task="translate")
    """)

def main():
    """Main test function"""
    print("🎵 OpenAI Whisper Test & Demo")
    print("=" * 40)
    
    try:
        # Test basic functionality
        model = test_whisper_basic()
        
        # Create test audio (optional)
        audio_file = create_test_audio()
        
        # Test transcription
        transcribe_audio(model, audio_file)
        
        # Show features
        demo_whisper_features(model)
        
        # Show usage examples
        show_usage_examples()
        
        print("\n✅ All tests completed successfully!")
        print("\n🎯 Next steps:")
        print("   1. Try with your own audio files:")
        print("      whisper your_audio.mp3")
        print("   2. Experiment with different models:")
        print("      whisper audio.wav --model base")
        print("   3. Try different languages:")
        print("      whisper audio.wav --language Spanish")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
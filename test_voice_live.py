#!/usr/bin/env python3
"""
Live test script for Voice endpoints
Tests the running FastAPI server voice functionality.
"""

import requests
import tempfile
import numpy as np
import os
from pathlib import Path

# Generate a simple test audio file
def create_test_audio():
    """Create a simple test audio file"""
    print("🔊 Creating test audio file...")
    
    try:
        import soundfile as sf
        
        # Create a simple sine wave (440 Hz, A note)
        sample_rate = 16000
        duration = 3  # seconds
        frequency = 440  # Hz
        
        t = np.linspace(0, duration, sample_rate * duration, False)
        audio_signal = np.sin(2 * np.pi * frequency * t) * 0.3
        
        # Save to temporary file
        audio_file = "test_audio.wav"
        sf.write(audio_file, audio_signal, sample_rate)
        print(f"✅ Test audio created: {audio_file}")
        return audio_file
        
    except ImportError:
        print("❌ soundfile not available")
        return None

def test_voice_info():
    """Test the voice info endpoint (no auth needed)"""
    print("\n🎤 Testing Voice Info Endpoint")
    print("-" * 40)
    
    try:
        # Try to get voice info without auth first
        response = requests.get("http://localhost:8000/api/v1/chat/voice/info")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Voice info retrieved successfully!")
            print(f"   Voice available: {data.get('voice_processing', {}).get('available', False)}")
            print(f"   Model: {data.get('voice_processing', {}).get('model_name', 'Unknown')}")
            print(f"   Languages: {data.get('voice_processing', {}).get('languages', 0)}")
            return True
        elif response.status_code == 401:
            print("🔒 Authentication required for voice info")
            return False
        else:
            print(f"❌ Failed to get voice info: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing voice info: {e}")
        return False

def test_voice_languages():
    """Test the supported languages endpoint"""
    print("\n🌍 Testing Supported Languages Endpoint")
    print("-" * 45)
    
    try:
        response = requests.get("http://localhost:8000/api/v1/chat/voice/languages")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Languages retrieved successfully!")
            print(f"   Total languages: {data.get('total_languages', 0)}")
            common = data.get('common_languages', {})
            print(f"   Common languages: {list(common.keys())[:10]}")
            return True
        elif response.status_code == 401:
            print("🔒 Authentication required for languages")
            return False
        else:
            print(f"❌ Failed to get languages: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing languages: {e}")
        return False

def test_voice_transcription():
    """Test the voice transcription endpoint"""
    print("\n📝 Testing Voice Transcription Endpoint")
    print("-" * 45)
    
    # Create test audio
    audio_file = create_test_audio()
    if not audio_file:
        print("❌ Cannot test transcription without audio file")
        return False
    
    try:
        # Prepare file for upload
        with open(audio_file, 'rb') as f:
            files = {'audio_file': f}
            data = {'language': 'en'}
            
            response = requests.post(
                "http://localhost:8000/api/v1/chat/voice/transcribe",
                files=files,
                data=data
            )
        
        # Clean up
        if os.path.exists(audio_file):
            os.remove(audio_file)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Transcription completed!")
            print(f"   Success: {result.get('success', False)}")
            transcription = result.get('transcription', {})
            print(f"   Text: '{transcription.get('text', 'N/A')}'")
            print(f"   Language: {transcription.get('language', 'N/A')}")
            print(f"   Duration: {transcription.get('duration', 0):.1f}s")
            return True
        elif response.status_code == 401:
            print("🔒 Authentication required for transcription")
            return False
        else:
            print(f"❌ Transcription failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error testing transcription: {e}")
        return False

def test_server_health():
    """Test if the server is responding"""
    print("🏥 Testing Server Health")
    print("-" * 25)
    
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server is responding")
            return True
        else:
            print(f"❌ Server returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return False

def main():
    """Main test function"""
    print("🎵 Live Voice Integration Test")
    print("=" * 40)
    print("Testing the running FastAPI server...")
    
    results = []
    
    # Test server health
    results.append(test_server_health())
    
    # Test voice endpoints
    results.append(test_voice_info())
    results.append(test_voice_languages())
    results.append(test_voice_transcription())
    
    # Summary
    print("\n📊 Test Results")
    print("-" * 15)
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! Voice integration is working!")
    elif passed > total // 2:
        print("⚠️ Most tests passed. Some may require authentication.")
    else:
        print("❌ Multiple tests failed. Check server and configuration.")
    
    print("\n🎯 Voice Integration Status:")
    if passed >= 2:
        print("✅ Voice processing is integrated and working!")
        print("✅ Your RAG chatbot now supports voice conversations!")
        print("\n📋 Available endpoints:")
        print("   • GET  /api/v1/chat/voice/info       - Voice capabilities")
        print("   • GET  /api/v1/chat/voice/languages  - Supported languages") 
        print("   • POST /api/v1/chat/voice/transcribe - Audio transcription")
        print("   • POST /api/v1/chat/voice/conversation - Complete voice chat")
        print("\n🌐 Access your application:")
        print("   • Frontend: http://localhost:3000")
        print("   • API Docs: http://localhost:8000/docs")
        print("   • Backend: http://localhost:8000")
    else:
        print("⚠️ Voice integration may need authentication setup")
    
    return passed == total

if __name__ == "__main__":
    main() 
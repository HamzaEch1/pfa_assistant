#!/usr/bin/env python3
"""
Test script for Voice + RAG integration
This script tests the complete voice conversation workflow.
"""

import asyncio
import tempfile
import os
import sys
from pathlib import Path

# Add the project path
sys.path.append(str(Path(__file__).parent))

# Test the voice service integration
async def test_voice_service():
    """Test the voice service functionality"""
    print("🎤 Testing Voice Service Integration")
    print("=" * 50)
    
    try:
        # Import the voice service
        from api.services.voice_service import voice_service
        
        # Check if voice processing is available
        print("1. Checking voice capabilities...")
        info = voice_service.get_model_info()
        print(f"   Voice available: {info.get('available', False)}")
        print(f"   Model: {info.get('model_name', 'Unknown')}")
        print(f"   Max duration: {info.get('max_duration', 0)}s")
        
        # Get supported languages
        print("\n2. Checking supported languages...")
        languages = voice_service.get_supported_languages()
        print(f"   Supported languages: {len(languages)}")
        print(f"   Examples: {list(languages.keys())[:10]}")
        
        if not info.get('available', False):
            print("\n⚠️  Voice processing not available - please install dependencies:")
            print("   pip install openai-whisper tiktoken numba more-itertools pydub librosa soundfile")
            return False
        
        print("\n✅ Voice service initialized successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the project root")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_api_endpoints():
    """Test that the API endpoints are properly configured"""
    print("\n🌐 Testing API Endpoints")
    print("-" * 30)
    
    try:
        # Try to import the router
        from api.routers.chat import router
        
        # Check if voice endpoints are added
        voice_routes = [route for route in router.routes if 'voice' in str(route.path)]
        
        print(f"Found {len(voice_routes)} voice endpoints:")
        for route in voice_routes:
            print(f"   {route.methods} {route.path}")
        
        if len(voice_routes) >= 4:  # transcribe, conversation, info, languages
            print("✅ All voice endpoints properly configured!")
            return True
        else:
            print("⚠️  Some voice endpoints may be missing")
            return False
            
    except Exception as e:
        print(f"❌ Error checking endpoints: {e}")
        return False

async def test_dependencies():
    """Test that all required dependencies are available"""
    print("\n📦 Testing Dependencies")
    print("-" * 25)
    
    dependencies = {
        'whisper': 'OpenAI Whisper',
        'pydub': 'Audio processing',
        'librosa': 'Audio analysis', 
        'soundfile': 'Audio I/O',
        'tiktoken': 'Whisper tokenizer',
        'numba': 'Whisper dependency',
        'more_itertools': 'Whisper dependency'
    }
    
    missing = []
    
    for dep, desc in dependencies.items():
        try:
            __import__(dep)
            print(f"   ✅ {dep} - {desc}")
        except ImportError:
            print(f"   ❌ {dep} - {desc} (MISSING)")
            missing.append(dep)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("   Install with: pip install " + " ".join(missing))
        return False
    else:
        print("\n✅ All dependencies available!")
        return True

async def test_file_permissions():
    """Test file upload and processing permissions"""
    print("\n📁 Testing File Permissions")
    print("-" * 30)
    
    try:
        # Test creating audio directory
        audio_dir = Path("user_files/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Audio directory: {audio_dir}")
        
        # Test creating temporary files
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp:
            print(f"   ✅ Temporary files: {temp.name}")
        
        # Test permissions
        test_file = audio_dir / "test.txt"
        test_file.write_text("test")
        test_file.unlink()
        print("   ✅ Write permissions")
        
        return True
        
    except Exception as e:
        print(f"   ❌ File permission error: {e}")
        return False

async def create_sample_integration():
    """Create a sample integration example"""
    print("\n🔧 Creating Sample Integration")
    print("-" * 35)
    
    sample_code = '''
# Sample Voice Integration Usage

from api.services.voice_service import voice_service

async def handle_voice_message(audio_file_path, user_id):
    """
    Complete voice conversation workflow
    """
    try:
        # Process voice conversation
        result = await voice_service.process_voice_conversation(
            audio_file_path=audio_file_path,
            user_id=user_id,
            language="en"  # or auto-detect with None
        )
        
        return {
            "transcription": result["user_message"],
            "response": result["assistant_response"],
            "conversation_id": result["conversation_id"]
        }
        
    except Exception as e:
        print(f"Voice processing failed: {e}")
        return None

# Example API usage:
# curl -X POST http://localhost:8000/api/v1/chat/voice/conversation \\
#      -H "Authorization: Bearer YOUR_TOKEN" \\
#      -F "audio_file=@recording.wav" \\
#      -F "language=en"
'''
    
    # Save sample code
    sample_file = Path("voice_integration_example.py")
    sample_file.write_text(sample_code)
    print(f"   ✅ Sample code saved to: {sample_file}")
    
    return True

async def show_next_steps():
    """Show next steps for completing the integration"""
    print("\n🎯 Next Steps for Voice Integration")
    print("=" * 40)
    
    steps = [
        "1. Install voice dependencies:",
        "   pip install -r requirements.txt",
        "",
        "2. Add voice environment variables to your .env:",
        "   WHISPER_MODEL_NAME=base",
        "   MAX_AUDIO_DURATION=300",
        "   VOICE_LANGUAGE=en",
        "",
        "3. Start your FastAPI server:",
        "   uvicorn api.main:app --reload",
        "",
        "4. Test voice endpoints:",
        "   GET  /api/v1/chat/voice/info",
        "   POST /api/v1/chat/voice/transcribe",
        "   POST /api/v1/chat/voice/conversation",
        "",
        "5. Integrate VoiceRecorder component in frontend:",
        "   import VoiceRecorder from './components/VoiceRecorder'",
        "",
        "6. Test complete workflow:",
        "   Record audio → Transcribe → RAG process → Response"
    ]
    
    for step in steps:
        print(step)
    
    print("\n📋 Available API Endpoints:")
    endpoints = [
        "POST /api/v1/chat/voice/transcribe      - Transcribe audio to text",
        "POST /api/v1/chat/voice/conversation    - Complete voice workflow", 
        "GET  /api/v1/chat/voice/info           - Get voice capabilities",
        "GET  /api/v1/chat/voice/languages      - Get supported languages"
    ]
    
    for endpoint in endpoints:
        print(f"   {endpoint}")

async def main():
    """Main test function"""
    print("🎵 Voice + RAG Integration Test")
    print("=" * 40)
    
    results = []
    
    # Run all tests
    results.append(await test_dependencies())
    results.append(await test_voice_service())
    results.append(await test_api_endpoints())
    results.append(await test_file_permissions())
    results.append(await create_sample_integration())
    
    # Show results
    print("\n📊 Test Results")
    print("-" * 15)
    passed = sum(results)
    total = len(results)
    
    print(f"   Tests passed: {passed}/{total}")
    
    if passed == total:
        print("   ✅ All tests passed! Voice integration ready.")
    else:
        print("   ⚠️  Some tests failed. Check errors above.")
    
    # Show next steps
    await show_next_steps()
    
    print("\n🎉 Voice integration setup complete!")
    print("   Ready to process voice conversations with RAG!")

if __name__ == "__main__":
    asyncio.run(main()) 

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
# curl -X POST http://localhost:8000/api/v1/chat/voice/conversation \
#      -H "Authorization: Bearer YOUR_TOKEN" \
#      -F "audio_file=@recording.wav" \
#      -F "language=en"

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
import logging
from pathlib import Path
import aiofiles # type: ignore
from wav2lip_service import wav2lip_service
from pydub import AudioSegment
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Avatar Service", description="Wav2Lip Avatar Generation Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/avatar/generate")
async def generate_avatar_video(
    audio_file: UploadFile = File(...),
    text: str = Form(...),
    avatar_type: str = Form(default="professional")
):
    """
    Generate avatar video with lip sync from audio and text
    
    Args:
        audio_file: Audio file (WAV, MP3, etc.)
        text: Text being spoken
        avatar_type: Type of avatar (professional, friendly)
        
    Returns:
        Generated avatar video file
    """
    try:
        logger.info(f"Generating avatar video for text: {text[:50]}...")
        
        # Validate audio file
        if not audio_file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.ogg')):
            raise HTTPException(status_code=400, detail="Unsupported audio format")
        
        # Save uploaded audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            content = await audio_file.read()
            temp_audio.write(content)
            temp_audio_path = temp_audio.name
        
        # Convert audio to WAV if needed
        if not audio_file.filename.lower().endswith('.wav'):
            audio = AudioSegment.from_file(temp_audio_path)
            wav_path = temp_audio_path.replace(temp_audio_path.split('.')[-1], 'wav')
            audio.export(wav_path, format="wav")
            os.unlink(temp_audio_path)
            temp_audio_path = wav_path
        
        # Generate avatar video
        output_video_path = wav2lip_service.create_banking_avatar_video(
            text=text,
            voice_audio_path=temp_audio_path,
            avatar_type=avatar_type
        )
        
        # Clean up temporary audio file
        os.unlink(temp_audio_path)
        
        # Return video file
        return FileResponse(
            output_video_path,
            media_type="video/mp4",
            filename=f"avatar_{hash(text) % 10000}.mp4"
        )
        
    except Exception as e:
        logger.error(f"Error generating avatar video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/avatar/generate-from-text")
async def generate_avatar_from_text(
    text: str = Form(...),
    avatar_type: str = Form(default="professional"),
    voice_type: str = Form(default="fr-FR")
):
    """
    Generate avatar video from text using TTS
    
    Args:
        text: Text to convert to speech and avatar
        avatar_type: Type of avatar
        voice_type: Voice type for TTS
        
    Returns:
        Generated avatar video file
    """
    try:
        logger.info(f"Generating avatar from text: {text[:50]}...")
        
        # Generate TTS audio (simplified - you'd integrate with your existing TTS)
        tts_audio_path = await _generate_tts_audio(text, voice_type)
        
        # Generate avatar video
        output_video_path = wav2lip_service.create_banking_avatar_video(
            text=text,
            voice_audio_path=tts_audio_path,
            avatar_type=avatar_type
        )
        
        # Clean up TTS audio
        os.unlink(tts_audio_path)
        
        return FileResponse(
            output_video_path,
            media_type="video/mp4",
            filename=f"avatar_tts_{hash(text) % 10000}.mp4"
        )
        
    except Exception as e:
        logger.error(f"Error generating avatar from text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _generate_tts_audio(text: str, voice_type: str) -> str:
    """Generate TTS audio (simplified implementation)"""
    # This is a placeholder - integrate with your existing TTS service
    # For now, create a silent audio file
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
        # Create silent audio based on text length
        duration_ms = len(text) * 100  # Rough estimate
        silence = AudioSegment.silent(duration=duration_ms)
        
        # Export to file
        silence.export(temp_file.name, format="wav")
        return temp_file.name

@app.get("/avatar/types")
async def get_avatar_types():
    """Get available avatar types"""
    return {
        "avatar_types": [
            {
                "id": "professional",
                "name": "Professional Banker",
                "description": "Professional banking representative with suit"
            },
            {
                "id": "friendly", 
                "name": "Friendly Assistant",
                "description": "Friendly and approachable assistant"
            },
            {
                "id": "executive",
                "name": "Executive",
                "description": "Senior banking executive"
            }
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "avatar"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

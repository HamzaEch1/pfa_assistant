"""
Avatar service for text-to-speech with lip sync
"""
import requests
import logging
import tempfile
import os
from typing import Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class AvatarService:
    def __init__(self, avatar_service_url: str = "http://avatar:8003"):
        self.avatar_service_url = avatar_service_url
        
    async def generate_avatar_video(
        self, 
        text: str, 
        audio_file_path: str,
        avatar_type: str = "professional"
    ) -> str:
        """
        Generate avatar video with lip sync
        
        Args:
            text: Text being spoken
            audio_file_path: Path to audio file
            avatar_type: Type of avatar
            
        Returns:
            URL to generated video
        """
        try:
            # Prepare files for upload
            files = {
                'audio_file': open(audio_file_path, 'rb')
            }
            
            data = {
                'text': text,
                'avatar_type': avatar_type
            }
            
            # Call avatar service
            response = requests.post(
                f"{self.avatar_service_url}/avatar/generate",
                files=files,
                data=data,
                timeout=300  # 5 minutes timeout
            )
            
            files['audio_file'].close()
            
            if response.status_code == 200:
                # Save video to temporary file
                temp_video = tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix='.mp4',
                    dir='/tmp'
                )
                
                temp_video.write(response.content)
                temp_video.close()
                
                logger.info(f"Avatar video generated: {temp_video.name}")
                return temp_video.name
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Avatar service error: {response.text}"
                )
                
        except Exception as e:
            logger.error(f"Error generating avatar video: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate avatar video: {str(e)}"
            )
    
    async def generate_avatar_from_text(
        self,
        text: str,
        avatar_type: str = "professional",
        voice_type: str = "fr-FR"
    ) -> str:
        """
        Generate avatar video directly from text using TTS
        
        Args:
            text: Text to convert to speech and avatar
            avatar_type: Type of avatar
            voice_type: Voice type for TTS
            
        Returns:
            Path to generated video
        """
        try:
            data = {
                'text': text,
                'avatar_type': avatar_type,
                'voice_type': voice_type
            }
            
            # Call avatar service
            response = requests.post(
                f"{self.avatar_service_url}/avatar/generate-from-text",
                data=data,
                timeout=300  # 5 minutes timeout
            )
            
            if response.status_code == 200:
                # Save video to temporary file
                temp_video = tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix='.mp4',
                    dir='/tmp'
                )
                
                temp_video.write(response.content)
                temp_video.close()
                
                logger.info(f"Avatar video generated from text: {temp_video.name}")
                return temp_video.name
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Avatar service error: {response.text}"
                )
                
        except Exception as e:
            logger.error(f"Error generating avatar from text: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate avatar from text: {str(e)}"
            )

# Singleton instance
avatar_service = AvatarService()

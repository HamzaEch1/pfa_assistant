import os
import cv2 # type: ignore
import numpy as np
import torch
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional, Tuple
import face_recognition # type: ignore
import mediapipe as mp # type: ignore
from pydub import AudioSegment
import librosa

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Wav2LipService:
    def __init__(self, model_path: str = None, device: str = 'cpu'):
        """
        Initialize Wav2Lip service
        
        Args:
            model_path: Path to Wav2Lip model file
            device: Device to run inference on ('cpu' or 'cuda')
        """
        self.device = device
        self.model_path = model_path or self._download_model()
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize face detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )
        
        logger.info(f"Wav2Lip service initialized with device: {device}")

    def _download_model(self) -> str:
        """Download Wav2Lip model if not present"""
        model_dir = Path("models")
        model_dir.mkdir(exist_ok=True)
        model_path = model_dir / "wav2lip_gan.pth"
        
        if not model_path.exists():
            logger.info("Downloading Wav2Lip model...")
            # You would download the model here
            # For now, we'll use a placeholder
            logger.warning("Model not found. Please download wav2lip_gan.pth manually")
            
        return str(model_path)

    def preprocess_video(self, video_path: str, target_size: Tuple[int, int] = (96, 96)) -> np.ndarray:
        """
        Preprocess video for Wav2Lip
        
        Args:
            video_path: Path to input video
            target_size: Target frame size
            
        Returns:
            Preprocessed video frames
        """
        cap = cv2.VideoCapture(video_path)
        frames = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Detect face and crop
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_frame)
            
            if results.detections:
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    h, w, _ = frame.shape
                    
                    # Convert relative coordinates to absolute
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    
                    # Crop and resize face
                    face_crop = frame[y:y+height, x:x+width]
                    if face_crop.size > 0:
                        face_resized = cv2.resize(face_crop, target_size)
                        frames.append(face_resized)
            
        cap.release()
        return np.array(frames)

    def preprocess_audio(self, audio_path: str) -> np.ndarray:
        """
        Preprocess audio for Wav2Lip
        
        Args:
            audio_path: Path to input audio
            
        Returns:
            Preprocessed audio features
        """
        # Load audio
        audio, sr = librosa.load(audio_path, sr=16000)
        
        # Extract mel spectrogram
        mel_spec = librosa.feature.melspectrogram(
            y=audio, 
            sr=sr, 
            n_mels=80, 
            fmax=8000
        )
        
        # Convert to log scale
        log_mel = librosa.power_to_db(mel_spec)
        
        return log_mel.T

    def generate_avatar_video(
        self, 
        base_image_path: str, 
        audio_path: str, 
        output_path: str
    ) -> str:
        """
        Generate avatar video with synchronized lip movements
        
        Args:
            base_image_path: Path to base avatar image
            audio_path: Path to audio file
            output_path: Path for output video
            
        Returns:
            Path to generated video
        """
        try:
            # Create a simple implementation without actual Wav2Lip model
            # This is a simplified version for demonstration
            
            # Load base image
            base_image = cv2.imread(base_image_path)
            if base_image is None:
                raise ValueError(f"Could not load base image: {base_image_path}")
            
            # Get audio duration
            audio = AudioSegment.from_file(audio_path)
            duration_ms = len(audio)
            fps = 25
            total_frames = int((duration_ms / 1000) * fps)
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            height, width = base_image.shape[:2]
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # Generate frames with simple animation
            for frame_idx in range(total_frames):
                frame = base_image.copy()
                
                # Add simple mouth movement animation
                # This is a placeholder - real Wav2Lip would sync with audio
                animation_phase = (frame_idx * 0.5) % (2 * np.pi)
                mouth_opening = int(5 * (1 + np.sin(animation_phase)))
                
                # Draw simple mouth animation (placeholder)
                center_x, center_y = width // 2, int(height * 0.7)
                cv2.ellipse(
                    frame, 
                    (center_x, center_y), 
                    (20, mouth_opening), 
                    0, 0, 180, 
                    (0, 0, 0), 
                    -1
                )
                
                out.write(frame)
            
            out.release()
            
            # Merge audio and video
            self._merge_audio_video(output_path, audio_path, output_path)
            
            logger.info(f"Avatar video generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating avatar video: {e}")
            raise

    def _merge_audio_video(self, video_path: str, audio_path: str, output_path: str):
        """Merge audio and video using ffmpeg"""
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-strict', 'experimental',
                output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info("Audio and video merged successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error merging audio and video: {e}")
            raise

    def create_banking_avatar_video(
        self, 
        text: str, 
        voice_audio_path: str,
        avatar_type: str = "professional"
    ) -> str:
        """
        Create a banking avatar video with professional appearance
        
        Args:
            text: Text being spoken
            voice_audio_path: Path to generated voice audio
            avatar_type: Type of avatar (professional, friendly, etc.)
            
        Returns:
            Path to generated avatar video
        """
        # Create base avatar image if not exists
        base_image_path = self._create_banking_avatar_image(avatar_type)
        
        # Generate unique output filename
        output_filename = f"avatar_output_{hash(text) % 10000}.mp4"
        output_path = os.path.join(tempfile.gettempdir(), output_filename)
        
        # Generate avatar video
        return self.generate_avatar_video(
            base_image_path, 
            voice_audio_path, 
            output_path
        )

    def _create_banking_avatar_image(self, avatar_type: str) -> str:
        """Create a professional banking avatar base image"""
        # Create a simple professional avatar
        # In a real implementation, you'd use pre-designed avatar images
        
        avatar_dir = Path("avatar_images")
        avatar_dir.mkdir(exist_ok=True)
        
        avatar_path = avatar_dir / f"{avatar_type}_avatar.jpg"
        
        if not avatar_path.exists():
            # Create a simple placeholder avatar
            img = np.ones((480, 640, 3), dtype=np.uint8) * 255
            
            # Draw a simple face (placeholder)
            center = (320, 240)
            
            # Face circle
            cv2.circle(img, center, 80, (220, 180, 140), -1)
            
            # Eyes
            cv2.circle(img, (290, 220), 8, (0, 0, 0), -1)
            cv2.circle(img, (350, 220), 8, (0, 0, 0), -1)
            
            # Nose
            cv2.line(img, (320, 235), (320, 255), (0, 0, 0), 2)
            
            # Mouth area (will be animated)
            cv2.ellipse(img, (320, 280), (20, 8), 0, 0, 180, (0, 0, 0), 2)
            
            # Professional suit
            cv2.rectangle(img, (250, 320), (390, 480), (50, 50, 100), -1)
            cv2.rectangle(img, (270, 320), (370, 400), (255, 255, 255), -1)
            cv2.line(img, (320, 320), (320, 400), (100, 100, 200), 3)
            
            cv2.imwrite(str(avatar_path), img)
            logger.info(f"Created banking avatar image: {avatar_path}")
        
        return str(avatar_path)

# Singleton instance
wav2lip_service = Wav2LipService()

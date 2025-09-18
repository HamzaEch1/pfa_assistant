import React, { useState, useRef, useEffect } from 'react';

const AvatarDisplay = ({ 
  isVisible = true, 
  avatarType = 'professional',
  isAnimating = false,
  onAvatarReady,
  className = ''
}) => {
  const [avatarVideoUrl, setAvatarVideoUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // Default avatar image when not speaking
  const defaultAvatarImage = `/api/avatar/default/${avatarType}`;

  const generateAvatarVideo = async (audioBlob, text) => {
    try {
      setIsLoading(true);
      setError(null);

      // Create FormData for avatar generation
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'audio.wav');
      formData.append('text', text);
      formData.append('avatar_type', avatarType);

      // Call avatar generation API
      const response = await fetch('/api/avatar/generate', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Avatar generation failed: ${response.statusText}`);
      }

      // Get video blob and create URL
      const videoBlob = await response.blob();
      const videoUrl = URL.createObjectURL(videoBlob);
      
      setAvatarVideoUrl(videoUrl);
      
      // Notify parent component
      if (onAvatarReady) {
        onAvatarReady(videoUrl);
      }

      return videoUrl;

    } catch (err) {
      console.error('Error generating avatar video:', err);
      setError(err.message);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const generateAvatarFromText = async (text) => {
    try {
      setIsLoading(true);
      setError(null);

      const formData = new FormData();
      formData.append('text', text);
      formData.append('avatar_type', avatarType);
      formData.append('voice_type', 'fr-FR');

      const response = await fetch('/api/avatar/generate-from-text', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Avatar generation failed: ${response.statusText}`);
      }

      const videoBlob = await response.blob();
      const videoUrl = URL.createObjectURL(videoBlob);
      
      setAvatarVideoUrl(videoUrl);
      
      if (onAvatarReady) {
        onAvatarReady(videoUrl);
      }

      return videoUrl;

    } catch (err) {
      console.error('Error generating avatar from text:', err);
      setError(err.message);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const playAvatarVideo = () => {
    if (videoRef.current && avatarVideoUrl) {
      videoRef.current.play().catch(err => {
        console.error('Error playing avatar video:', err);
      });
    }
  };

  const stopAvatarVideo = () => {
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
  };

  // Clean up video URL when component unmounts
  useEffect(() => {
    return () => {
      if (avatarVideoUrl) {
        URL.revokeObjectURL(avatarVideoUrl);
      }
    };
  }, [avatarVideoUrl]);

  // Auto-play when video URL changes
  useEffect(() => {
    if (avatarVideoUrl && isAnimating) {
      playAvatarVideo();
    }
  }, [avatarVideoUrl, isAnimating]);

  // Expose methods to parent component
  useEffect(() => {
    if (onAvatarReady) {
      onAvatarReady({
        generateFromAudio: generateAvatarVideo,
        generateFromText: generateAvatarFromText,
        play: playAvatarVideo,
        stop: stopAvatarVideo
      });
    }
  }, [onAvatarReady]);

  if (!isVisible) {
    return null;
  }

  return (
    <div className={`avatar-display relative ${className}`}>
      {/* Avatar Container */}
      <div className="relative w-64 h-80 mx-auto bg-gradient-to-b from-blue-50 to-blue-100 rounded-lg shadow-lg overflow-hidden">
        
        {/* Loading Overlay */}
        {isLoading && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-10">
            <div className="text-center text-white">
              <div className="animate-spin w-8 h-8 border-4 border-white border-t-transparent rounded-full mx-auto mb-2"></div>
              <div className="text-sm">Génération de l'avatar...</div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="absolute inset-0 bg-red-50 flex items-center justify-center z-10">
            <div className="text-center text-red-600 p-4">
              <div className="text-sm font-medium mb-2">Erreur Avatar</div>
              <div className="text-xs">{error}</div>
            </div>
          </div>
        )}

        {/* Video Player (when speaking) */}
        {avatarVideoUrl && isAnimating && (
          <video
            ref={videoRef}
            className="w-full h-full object-cover"
            autoPlay
            muted={false}
            onEnded={() => setAvatarVideoUrl(null)}
          >
            <source src={avatarVideoUrl} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        )}

        {/* Static Avatar Image (when not speaking) */}
        {(!avatarVideoUrl || !isAnimating) && (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-b from-blue-100 to-blue-200">
            <div className="text-center">
              {/* Simple CSS Avatar */}
              <div className="relative mx-auto mb-4">
                {/* Head */}
                <div className="w-24 h-24 bg-yellow-200 rounded-full mx-auto relative border-2 border-yellow-300">
                  {/* Eyes */}
                  <div className="absolute top-6 left-6 w-3 h-3 bg-black rounded-full"></div>
                  <div className="absolute top-6 right-6 w-3 h-3 bg-black rounded-full"></div>
                  
                  {/* Nose */}
                  <div className="absolute top-10 left-1/2 transform -translate-x-1/2 w-1 h-2 bg-yellow-400 rounded-full"></div>
                  
                  {/* Mouth */}
                  <div className="absolute top-14 left-1/2 transform -translate-x-1/2 w-6 h-1 bg-red-400 rounded-full"></div>
                </div>
                
                {/* Body */}
                <div className="w-20 h-24 bg-blue-600 mx-auto rounded-lg relative">
                  {/* Shirt */}
                  <div className="absolute top-2 left-2 right-2 h-8 bg-white rounded"></div>
                  {/* Tie */}
                  <div className="absolute top-2 left-1/2 transform -translate-x-1/2 w-2 h-12 bg-red-600 rounded-b"></div>
                </div>
              </div>
              
              <div className="text-sm text-gray-600 font-medium">
                {avatarType === 'professional' ? 'Assistant Bancaire' : 'Assistant Virtuel'}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Banque Populaire
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Avatar Controls */}
      <div className="mt-4 text-center">
        <div className="flex justify-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${isLoading ? 'bg-yellow-500 animate-pulse' : isAnimating ? 'bg-green-500' : 'bg-gray-300'}`}></div>
          <div className={`w-2 h-2 rounded-full ${error ? 'bg-red-500' : 'bg-gray-300'}`}></div>
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {isLoading ? 'Génération...' : isAnimating ? 'Parle' : 'En attente'}
        </div>
      </div>
    </div>
  );
};

export default AvatarDisplay;

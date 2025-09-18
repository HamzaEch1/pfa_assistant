import React, { useState, useRef, useEffect } from 'react';

const AvatarComponent = ({ 
  isVisible = true, 
  isActive = false, 
  avatarType = "professional",
  onAvatarClick = null,
  className = ""
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentVideo, setCurrentVideo] = useState(null);
  const [error, setError] = useState(null);
  const videoRef = useRef(null);

  const generateAvatarFromText = async (text) => {
    try {
      setIsGenerating(true);
      setError(null);

      const formData = new FormData();
      formData.append('text', text);
      formData.append('avatar_type', avatarType);
      formData.append('voice_type', 'fr-FR');

      const response = await fetch('/api/avatar/generate-from-text', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const videoBlob = await response.blob();
        const videoUrl = URL.createObjectURL(videoBlob);
        setCurrentVideo(videoUrl);
        
        // Auto-play video when ready
        if (videoRef.current) {
          videoRef.current.src = videoUrl;
          videoRef.current.play();
        }
      } else {
        throw new Error('Failed to generate avatar video');
      }
    } catch (err) {
      console.error('Avatar generation error:', err);
      setError('Erreur lors de la génération de l\'avatar');
    } finally {
      setIsGenerating(false);
    }
  };

  const stopAvatar = () => {
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
    if (currentVideo) {
      URL.revokeObjectURL(currentVideo);
      setCurrentVideo(null);
    }
  };

  // Clean up video URL when component unmounts
  useEffect(() => {
    return () => {
      if (currentVideo) {
        URL.revokeObjectURL(currentVideo);
      }
    };
  }, [currentVideo]);

  if (!isVisible) return null;

  return (
    <div className={`avatar-container ${className}`}>
      <div className="relative bg-gradient-to-b from-blue-50 to-orange-50 rounded-lg border-2 border-orange-200 shadow-lg overflow-hidden">
        
        {/* Avatar Header */}
        <div className="bg-gradient-to-r from-orange-500 to-orange-600 text-white px-4 py-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium">Assistant BCP</span>
            </div>
            {isActive && (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                <span className="text-xs">En direct</span>
              </div>
            )}
          </div>
        </div>

        {/* Avatar Video Area */}
        <div className="relative aspect-video bg-gray-100">
          {currentVideo ? (
            <video
              ref={videoRef}
              className="w-full h-full object-cover"
              controls={false}
              autoPlay
              muted={false}
              onEnded={() => setCurrentVideo(null)}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              {isGenerating ? (
                <div className="text-center">
                  <div className="animate-spin w-8 h-8 border-4 border-orange-500 border-t-transparent rounded-full mx-auto mb-2"></div>
                  <p className="text-sm text-gray-600">Génération de l'avatar...</p>
                </div>
              ) : (
                <div className="text-center">
                  {/* Static Avatar Image */}
                  <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-gradient-to-b from-orange-400 to-orange-600 flex items-center justify-center shadow-lg">
                    <svg 
                      className="w-12 h-12 text-white" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={2} 
                        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" 
                      />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-700 mb-1">
                    Assistant Virtuel BCP
                  </h3>
                  <p className="text-sm text-gray-500">
                    Prêt à vous aider
                  </p>
                  {isActive && (
                    <div className="mt-2">
                      <div className="inline-flex items-center space-x-2 text-xs text-orange-600">
                        <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></div>
                        <span>À l'écoute...</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Controls */}
        {currentVideo && (
          <div className="absolute bottom-2 right-2">
            <button
              onClick={stopAvatar}
              className="bg-red-500 hover:bg-red-600 text-white p-2 rounded-full shadow-lg transition-colors"
              title="Arrêter l'avatar"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="6" width="12" height="12"></rect>
              </svg>
            </button>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="absolute bottom-0 left-0 right-0 bg-red-500 text-white text-xs p-2">
            {error}
          </div>
        )}

        {/* Click Handler */}
        {onAvatarClick && (
          <div 
            className="absolute inset-0 cursor-pointer"
            onClick={onAvatarClick}
          />
        )}
      </div>
    </div>
  );
};

export default AvatarComponent;

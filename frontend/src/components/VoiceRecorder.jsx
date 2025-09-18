import React, { useState, useRef, useEffect } from 'react';

// Modern SVG icon components
const MicIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
    <line x1="12" x2="12" y1="19" y2="22"/>
    <line x1="8" x2="16" y1="22" y2="22"/>
  </svg>
);

const MicOffIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="m2 2 20 20"/>
    <path d="M18.89 13.23A7.12 7.12 0 0 0 19 12v-2"/>
    <path d="M5 10v2a7 7 0 0 0 12 5"/>
    <path d="M15 9.34V5a3 3 0 0 0-5.68-1.33"/>
    <path d="M9 9v3a3 3 0 0 0 5.12 2.12"/>
    <line x1="12" x2="12" y1="19" y2="22"/>
    <line x1="8" x2="16" y1="22" y2="22"/>
  </svg>
);

const SquareIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="none">
    <rect x="6" y="6" width="12" height="12" rx="2"/>
  </svg>
);

const PlayIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="none">
    <polygon points="5,3 19,12 5,21"/>
  </svg>
);

const PauseIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="none">
    <rect x="6" y="4" width="4" height="16"/>
    <rect x="14" y="4" width="4" height="16"/>
  </svg>
);

const VolumeIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="11,5 6,9 2,9 2,15 6,15 11,19"/>
    <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
    <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
  </svg>
);

const VoiceRecorder = ({ 
  onSendAudio, 
  onTranscriptionResult,
  disabled = false,
  language = 'en',
  maxDuration = 300 // 5 minutes
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationRef = useRef(null);
  
  const mediaRecorderRef = useRef(null);
  const audioPlayerRef = useRef(null);
  const recordingTimerRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  // Start recording
  const startRecording = async () => {
    try {
      setError(null);
      
      // Log browser and device info
      console.log('Browser:', navigator.userAgent);
      console.log('MediaDevices available:', !!navigator.mediaDevices);
      console.log('getUserMedia available:', !!navigator.mediaDevices?.getUserMedia);
      
      // Request microphone permission with Firefox-compatible settings
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          // Firefox doesn't support these advanced constraints well
          // sampleRate: 16000,
          // channelCount: 1,
          // volume: 1.0
        } 
      });
      
      // Log stream info
      const audioTracks = stream.getAudioTracks();
      console.log('Audio tracks:', audioTracks.length);
      if (audioTracks.length > 0) {
        const track = audioTracks[0];
        console.log('Track settings:', track.getSettings());
        console.log('Track capabilities:', track.getCapabilities());
        
        // Firefox-specific: check if track is actually enabled
        console.log('Track enabled:', track.enabled);
        console.log('Track muted:', track.muted);
        console.log('Track ready state:', track.readyState);
        
        // Firefox: ensure track is enabled
        if (!track.enabled) {
          console.log('⚠️ Track was disabled, enabling...');
          track.enabled = true;
        }
      }
      
      // Check supported MIME types - Firefox priority order
      const supportedTypes = [
        'audio/webm;codecs=opus',  // Firefox best support
        'audio/webm',              // Firefox fallback
        'audio/ogg;codecs=opus',  // Firefox alternative
        'audio/ogg',               // Firefox basic
        'audio/wav',               // Universal fallback
        'audio/mp4'                // Last resort
      ];
      
      let mimeType = null;
      for (const type of supportedTypes) {
        if (MediaRecorder.isTypeSupported(type)) {
          mimeType = type;
          console.log(`✅ Supported MIME type found: ${type}`);
          break;
        } else {
          console.log(`❌ MIME type not supported: ${type}`);
        }
      }
      
      if (!mimeType) {
        throw new Error('No supported audio format found');
      }
      
      console.log(`🎯 Using MIME type: ${mimeType}`);
      
      audioChunksRef.current = [];
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: mimeType,
        audioBitsPerSecond: 128000 // Higher bitrate for better quality
      });
      
      mediaRecorderRef.current = mediaRecorder;
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          console.log(`📦 Audio chunk received: ${event.data.size} bytes`);
          audioChunksRef.current.push(event.data);
        } else {
          console.warn('⚠️ Empty audio chunk received');
        }
      };
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        console.log(`🎵 Final audio blob created: ${audioBlob.size} bytes, type: ${audioBlob.type}`);
        console.log(`📊 Total chunks: ${audioChunksRef.current.length}`);
        
        if (audioBlob.size === 0) {
          setError('No audio data recorded. Please check your microphone and try again.');
          return;
        }
        
        if (audioBlob.size < 1000) {
          console.warn(`⚠️ Very small audio file: ${audioBlob.size} bytes - this might not contain speech`);
        }
        
        setAudioBlob(audioBlob);
        
        // Create URL for playback
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      
      // Start audio level monitoring
      startAudioLevelMonitoring(stream);
      
      // Start timer
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          const newTime = prev + 1;
          // Auto-stop if max duration reached
          if (newTime >= maxDuration) {
            stopRecording();
          }
          return newTime;
        });
      }, 1000);
      
    } catch (err) {
      console.error('Failed to start recording:', err);
      setError('Failed to access microphone. Please check permissions.');
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Stop audio level monitoring
      stopAudioLevelMonitoring();
      
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
    }
  };

  // Play/pause recorded audio
  const togglePlayback = () => {
    if (!audioPlayerRef.current || !audioUrl) return;
    
    if (isPlaying) {
      audioPlayerRef.current.pause();
    } else {
      audioPlayerRef.current.play();
    }
  };

  // Send audio for processing
  const sendAudio = async () => {
    if (!audioBlob) {
      setError('No audio recording available. Please record audio first.');
      return;
    }
    
    // Minimum size check (at least 1KB)
    if (audioBlob.size < 1024) {
      setError('Audio recording too short or empty. Please record again with sound.');
      return;
    }
    
    setIsProcessing(true);
    setError(null);
    
    try {
      console.log(`Sending audio: ${audioBlob.size} bytes, type: ${audioBlob.type}`);
      
      // Create FormData for file upload
      const formData = new FormData();
      
      // Determine file extension based on MIME type
      let fileName = 'recording.webm';
      let fileType = audioBlob.type || 'audio/webm';
      
      if (fileType.includes('mp4')) {
        fileName = 'recording.mp4';
      } else if (fileType.includes('wav')) {
        fileName = 'recording.wav';
      } else if (fileType.includes('webm')) {
        fileName = 'recording.webm';
      }
      
      const audioFile = new File([audioBlob], fileName, { type: fileType });
      formData.append('audio_file', audioFile);
      
      if (language) {
        formData.append('language', language);
      }
      
      console.log(`Uploading file: ${fileName} (${audioFile.size} bytes)`);
      
      // Call the parent callback
      if (onSendAudio) {
        await onSendAudio(formData);
      }
      
      // Clear recording after successful send
      clearRecording();
      
    } catch (err) {
      console.error('Failed to send audio:', err);
      setError('Failed to process audio. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Clear current recording
  const clearRecording = () => {
    setAudioBlob(null);
    setRecordingTime(0);
    setIsPlaying(false);
    
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current.currentTime = 0;
    }
  };

  // Format time display
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Audio player event handlers
  const handleAudioPlay = () => setIsPlaying(true);
  const handleAudioPause = () => setIsPlaying(false);
  const handleAudioEnded = () => setIsPlaying(false);

  // Monitor audio levels during recording
  const startAudioLevelMonitoring = (stream) => {
    try {
      // Firefox: AudioContext must be created after user gesture
      if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
        audioContextRef.current.resume();
      } else {
        audioContextRef.current = new AudioContext();
      }
      
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      source.connect(analyserRef.current);
      
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      
      const updateLevel = () => {
        if (analyserRef.current && isRecording) {
          analyserRef.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
          setAudioLevel(Math.round(average));
          animationRef.current = requestAnimationFrame(updateLevel);
        }
      };
      
      updateLevel();
    } catch (err) {
      console.warn('Audio level monitoring failed:', err);
    }
  };

  const stopAudioLevelMonitoring = () => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    setAudioLevel(0);
  };

  return (
    <div className="voice-recorder voice-interface bg-white rounded-lg border shadow-sm p-4">
      {/* Hidden audio element for playback */}
      <audio
        ref={audioPlayerRef}
        src={audioUrl}
        onPlay={handleAudioPlay}
        onPause={handleAudioPause}
        onEnded={handleAudioEnded}
        style={{ display: 'none' }}
      />
      
      {/* Error display */}
      {error && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {error}
        </div>
      )}
      
      {/* Recording controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {/* Record/Stop button */}
          {!audioBlob && (
            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={disabled || isProcessing}
              className={`flex items-center justify-center w-12 h-12 rounded-full transition-all duration-200 ease-in-out transform hover:scale-105 shadow-lg hover:shadow-xl ${
                isRecording
                  ? 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white animate-pulse'
                  : 'bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white disabled:from-gray-300 disabled:to-gray-400 disabled:transform-none disabled:shadow-none'
              }`}
            >
              {isRecording ? <SquareIcon /> : <MicIcon />}
            </button>
          )}
          
          {/* Playback controls (when audio is recorded) */}
          {audioBlob && (
            <div className="flex items-center space-x-2">
              <button
                onClick={togglePlayback}
                disabled={disabled}
                className="flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white transition-all duration-200 ease-in-out transform hover:scale-105 shadow-md hover:shadow-lg"
              >
                {isPlaying ? <PauseIcon /> : <PlayIcon />}
              </button>
              
              <button
                onClick={clearRecording}
                disabled={disabled || isProcessing}
                className="px-3 py-1 text-sm bg-gradient-to-r from-gray-200 to-gray-300 hover:from-gray-300 hover:to-gray-400 text-gray-700 rounded-lg transition-all duration-200 ease-in-out transform hover:scale-105 shadow-sm hover:shadow-md"
              >
                Clear
              </button>
            </div>
          )}
          
          {/* Recording time */}
          <div className="flex items-center space-x-2 text-gray-600">
            {isRecording && <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />}
            <span className="text-sm font-mono">
              {formatTime(recordingTime)}
              {maxDuration && ` / ${formatTime(maxDuration)}`}
            </span>
            {isRecording && (
              <div className="flex items-center space-x-1 ml-2">
                <span className="text-xs">🎵</span>
                <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-green-500 transition-all duration-100 ease-out"
                    style={{ width: `${Math.min(audioLevel * 2, 100)}%` }}
                  />
                </div>
                <span className="text-xs font-mono w-8">{audioLevel}</span>
              </div>
            )}
          </div>
        </div>
        
        {/* Send button */}
        {audioBlob && (
          <button
            onClick={sendAudio}
            disabled={disabled || isProcessing}
            className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-semibold py-3 px-6 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg transform hover:scale-105"
          >
            {isProcessing ? (
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Processing...</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <span>Send</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            )}
          </button>
        )}
      </div>
      
      {/* Recording status */}
      {isRecording && (
        <div className="mt-3 text-center">
          <p className="text-sm text-gray-600">
            🎤 Recording... Click stop when finished
          </p>
          {recordingTime > maxDuration * 0.8 && (
            <p className="text-xs text-orange-600 mt-1">
              ⚠️ Approaching maximum duration ({formatTime(maxDuration - recordingTime)} remaining)
            </p>
          )}
        </div>
      )}
      
      {/* Audio recorded status */}
      {audioBlob && !isRecording && (
        <div className="mt-3 text-center">
          <p className="text-sm text-gray-600">
            ✅ Audio recorded ({formatTime(recordingTime)})
          </p>
          <p className="text-xs text-gray-500">
            Click play to review, or send to transcribe
          </p>
        </div>
      )}
      
      {/* Browser compatibility warning */}
      {!navigator.mediaDevices && (
        <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-yellow-700 text-sm">
          ⚠️ Voice recording requires HTTPS or localhost
        </div>
      )}
    </div>
  );
};

export default VoiceRecorder; 
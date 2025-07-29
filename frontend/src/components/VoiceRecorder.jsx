import React, { useState, useRef, useEffect } from 'react';

// Simple icon components using emoji/Unicode (replacing lucide-react)
const MicIcon = () => <span>🎤</span>;
const MicOffIcon = () => <span>🔇</span>;
const SquareIcon = () => <span>⏹️</span>;
const PlayIcon = () => <span>▶️</span>;
const PauseIcon = () => <span>⏸️</span>;
const SendIcon = () => <span>📤</span>;
const VolumeIcon = () => <span>🔊</span>;

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
      
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        } 
      });
      
      // Check if MediaRecorder is supported
      if (!MediaRecorder.isTypeSupported('audio/webm')) {
        throw new Error('Audio recording not supported in this browser');
      }
      
      audioChunksRef.current = [];
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
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
    if (!audioBlob) return;
    
    setIsProcessing(true);
    setError(null);
    
    try {
      // Create FormData for file upload
      const formData = new FormData();
      const audioFile = new File([audioBlob], 'recording.webm', { type: 'audio/webm' });
      formData.append('audio_file', audioFile);
      
      if (language) {
        formData.append('language', language);
      }
      
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

  return (
    <div className="voice-recorder bg-white rounded-lg border shadow-sm p-4">
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
              className={`flex items-center justify-center w-12 h-12 rounded-full transition-colors ${
                isRecording
                  ? 'bg-red-500 hover:bg-red-600 text-white'
                  : 'bg-blue-500 hover:bg-blue-600 text-white disabled:bg-gray-300'
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
                className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-500 hover:bg-gray-600 text-white transition-colors"
              >
                {isPlaying ? <PauseIcon /> : <PlayIcon />}
              </button>
              
              <button
                onClick={clearRecording}
                disabled={disabled || isProcessing}
                className="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded transition-colors"
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
          </div>
        </div>
        
        {/* Send button */}
        {audioBlob && (
          <button
            onClick={sendAudio}
            disabled={disabled || isProcessing}
            className="flex items-center space-x-2 px-4 py-2 bg-green-500 hover:bg-green-600 disabled:bg-gray-300 text-white rounded-lg transition-colors"
          >
            {isProcessing ? (
              <>
                <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <SendIcon />
                <span>Send</span>
              </>
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
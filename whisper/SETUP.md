# Whisper Project Setup Guide

## 🎤 OpenAI Whisper Speech Recognition

This directory contains a fully configured OpenAI Whisper installation for speech recognition and transcription.

## ✅ What's Already Done

- ✅ Virtual environment created (`whisper_env/`)
- ✅ Whisper and dependencies installed  
- ✅ CPU-only PyTorch (no NVIDIA required)
- ✅ FFmpeg installed (required for audio processing)
- ✅ Test script created (`test_whisper.py`)
- ✅ Activation script created (`activate_whisper.sh`)

## 🚀 Quick Start

### 1. Activate Environment
```bash
# Method 1: Use the activation script
source activate_whisper.sh

# Method 2: Manual activation
source whisper_env/bin/activate
```

### 2. Test Installation
```bash
# Run the test script
python test_whisper.py

# Or test command line
whisper --help
```

### 3. Transcribe Audio
```bash
# Basic transcription
whisper your_audio.mp3

# With specific model
whisper audio.wav --model base

# With language specification
whisper audio.mp3 --language French

# Translation to English
whisper foreign_audio.wav --task translate
```

## 📊 Available Models

| Model  | Size   | Speed | Accuracy | Use Case |
|--------|--------|-------|----------|----------|
| tiny   | 39 MB  | ~10x  | Basic    | Testing/Fast |
| base   | 74 MB  | ~7x   | Good     | **Recommended** |
| small  | 244 MB | ~4x   | Better   | Production |
| medium | 769 MB | ~2x   | Great    | High accuracy |
| large  | 1550 MB| 1x    | Best     | Maximum quality |
| turbo  | 809 MB | ~8x   | Great    | Fast + accurate |

## 🌍 Language Support

Whisper supports 100+ languages including:
- English, French, Spanish, German, Italian
- Chinese, Japanese, Korean, Arabic, Russian
- And many more...

## 🐍 Python API Usage

```python
import whisper

# Load model
model = whisper.load_model("base")

# Transcribe
result = model.transcribe("audio.mp3")
print(result["text"])

# With options
result = model.transcribe(
    "audio.mp3",
    language="French",      # Specify language
    task="translate",       # Translate to English
    word_timestamps=True    # Get word-level timing
)
```

## 🛠️ Command Line Options

```bash
# Basic usage
whisper audio.mp3

# Common options
whisper audio.wav --model base --language French
whisper audio.mp3 --task translate --output_format srt
whisper audio.m4a --output_dir ./transcripts/

# Advanced options
whisper audio.wav --word_timestamps True --highlight_words True
whisper audio.mp3 --temperature 0.2 --beam_size 5
```

## 📁 File Structure

```
whisper/
├── whisper_env/          # Virtual environment
├── activate_whisper.sh   # Easy activation script
├── test_whisper.py       # Test & demo script
├── SETUP.md             # This file
├── README.md            # Original Whisper README
├── whisper/             # Source code
└── requirements.txt     # Dependencies
```

## 🔧 Troubleshooting

### Virtual Environment Issues
```bash
# Recreate if needed
rm -rf whisper_env
python3 -m venv whisper_env
source whisper_env/bin/activate
pip install -e .
```

### Audio Format Issues
```bash
# Install additional audio support
pip install soundfile librosa
```

### Model Download Issues
```bash
# Models are downloaded to ~/.cache/whisper/
# Clear cache if needed:
rm -rf ~/.cache/whisper/
```

### Memory Issues
```bash
# Use smaller model
whisper audio.mp3 --model tiny

# Or process in chunks
whisper large_audio.mp3 --clip_timestamps 0,300,300,600
```

## 📈 Performance Tips

1. **Choose the right model**: `base` is good for most uses
2. **Specify language**: Faster than auto-detection
3. **Use appropriate format**: WAV/FLAC for quality, MP3 for size
4. **Batch processing**: Process multiple files at once

## 🎯 Integration Examples

### With Python Scripts
```python
import whisper

def transcribe_file(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result["text"]

# Usage
text = transcribe_file("meeting.mp3")
print(text)
```

### Batch Processing
```bash
# Process all audio files in a directory
for file in *.mp3; do
    whisper "$file" --model base --output_format txt
done
```

### With Web Apps
See the main project for integration with FastAPI/Flask applications.

## 🔗 Useful Links

- [OpenAI Whisper GitHub](https://github.com/openai/whisper)
- [Model Performance](https://github.com/openai/whisper#available-models-and-languages)
- [Paper](https://arxiv.org/abs/2212.04356)
- [Colab Example](https://colab.research.google.com/github/openai/whisper/blob/master/notebooks/LibriSpeech.ipynb)

---

**Ready to use!** 🎉 Your Whisper installation is complete and working. 
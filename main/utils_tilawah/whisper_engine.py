import torch
import librosa
import numpy as np
from transformers import WhisperProcessor, WhisperForConditionalGeneration

# Load model sekali saat server start (cache di memory)
_processor = None
_model = None

import os
from django.conf import settings

MODEL_PATH = os.path.join(settings.BASE_DIR, 'models', 'tarteel-whisper')

def get_model():
    global _processor, _model
    if _processor is None or _model is None:
        source = MODEL_PATH if os.path.exists(MODEL_PATH) else "tarteel-ai/whisper-base-ar-quran"
        print(f"[Tarteel] Loading model dari: {source}")
        _processor = WhisperProcessor.from_pretrained(source)
        _model = WhisperForConditionalGeneration.from_pretrained(source)
        _model.eval()
        print("[Tarteel] Model ready!")
    return _processor, _model


def transcribe_audio(audio_path):
    """
    Transkripsi audio tilawah ke teks Arab.
    
    Args:
        audio_path: path ke file audio (mp3/wav/m4a)
    
    Returns:
        dict: {
            'transcript': str,  # teks Arab hasil transkripsi
            'success': bool,
            'error': str | None
        }
    """
    try:
        processor, model = get_model()

        # Load & resample audio ke 16kHz (requirement Whisper)
        audio, sr = librosa.load(audio_path, sr=16000, mono=True)

        # Proses audio jadi input tensor
        inputs = processor(
            audio,
            sampling_rate=16000,
            return_tensors="pt"
        )

        # Generate transkripsi
        with torch.no_grad():
            forced_decoder_ids = processor.get_decoder_prompt_ids(
                language="ar",
                task="transcribe"
            )
            predicted_ids = model.generate(
                inputs["input_features"],
                forced_decoder_ids=forced_decoder_ids,
            )

        # Decode ke teks
        transcript = processor.batch_decode(
            predicted_ids,
            skip_special_tokens=True
        )[0].strip()

        return {
            'transcript': transcript,
            'success': True,
            'error': None
        }

    except Exception as e:
        return {
            'transcript': '',
            'success': False,
            'error': str(e)
        }
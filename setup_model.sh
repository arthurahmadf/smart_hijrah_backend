#!/bin/bash
echo "Downloading Tarteel Whisper model..."
python -c "
from transformers import WhisperProcessor, WhisperForConditionalGeneration
processor = WhisperProcessor.from_pretrained('tarteel-ai/whisper-base-ar-quran')
model = WhisperForConditionalGeneration.from_pretrained('tarteel-ai/whisper-base-ar-quran')
processor.save_pretrained('models/tarteel-whisper')
model.save_pretrained('models/tarteel-whisper')
print('Done!')
"
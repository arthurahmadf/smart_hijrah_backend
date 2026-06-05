# save_model.py — jalankan sekali setelah download selesai
from transformers import WhisperProcessor, WhisperForConditionalGeneration

save_path = "models/tarteel-whisper"
processor = WhisperProcessor.from_pretrained("tarteel-ai/whisper-base-ar-quran")
model = WhisperForConditionalGeneration.from_pretrained("tarteel-ai/whisper-base-ar-quran")

processor.save_pretrained(save_path)
model.save_pretrained(save_path)
print("Model tersimpan di:", save_path)
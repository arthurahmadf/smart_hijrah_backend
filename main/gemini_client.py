# main/gemini_client.py

import time
from google import genai
from google.genai import types
from django.conf import settings
from main.models_ai import ChatMessage

# --- Inisialisasi & Konfigurasi ---
print("[GEMINI] Menginisialisasi klien...")
start_init = time.time()

client = genai.Client(api_key=settings.GEMINI_API_KEY)

end_init = time.time()
print(f"[GEMINI] Klien berhasil diinisialisasi dalam {end_init - start_init:.4f} detik.")

MODEL_NAME = "gemini-2.5-flash-lite"
print(f"[GEMINI] Menggunakan model: {MODEL_NAME}")


def build_conversation_history(conversation_id):
    """Membangun history percakapan dari database dalam format yang benar"""
    messages = ChatMessage.objects.filter(
        conversation_id=conversation_id
    ).order_by('created_at')
    
    # Format untuk Gemini: list of Content objects
    # Content: {"role": "user" atau "model", "parts": [{"text": "..."}]}
    contents = []
    for msg in messages:
        role = "user" if msg.role == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg.text}]
        })
    
    return contents


def chat_with_gemini(prompt, conversation_id=None, is_first_message=False):
    """Kirim prompt ke Gemini dengan menyertakan history secara manual"""
    print(f"\n[GEMINI] ========== PERMINTAAN BARU ==========")
    print(f"[GEMINI] Conversation ID: {conversation_id}")
    print(f"[GEMINI] Status percakapan: {'Pertama' if is_first_message else 'Lanjutan'}")
    print(f"[GEMINI] Panjang prompt: {len(prompt)} karakter")

    total_start_time = time.time()

    try:
        # Base instruction untuk model
        base_instruction = (
            "Anda adalah 'Smart Hijrah Assistant', seorang pakar dan agamawan Islam yang berwawasan luas, "
            "santun, bijaksana, dan objektif. Jawablah setiap pertanyaan pengguna dalam Bahasa Indonesia "
            "yang formal, sejuk, dan penuh hormat.\n\n"
            "Aturan Penulisan Jawaban:\n"
            "1. WAJIB menyertakan referensi dalil yang shahih (nama surah dan nomor ayat untuk Al-Qur'an, "
            "atau perawi hadis seperti HR. Bukhari, Muslim, dll. jika mengutip hadis).\n"
            "2. Jika terdapat perbedaan pandangan fiqih yang debatable di antara para ulama, Anda HARUS "
            "bersikap netral. Sebutkan secara jelas pandangan dari masing-masing madzhab utama.\n"
            "3. Hindari menghakimi pengguna atau mengeluarkan fatwa mutlak tanpa dasar dalil yang jelas."
        )

        # Jika pesan pertama, tambahkan instruksi sapaan
        if is_first_message:
            final_prompt = f"{base_instruction}\n\nKhusus untuk pesan pertama ini, awali jawaban Anda dengan salam 'Assalamu'alaikum' dan perkenalkan diri Anda singkat sebagai Smart Hijrah Assistant.\n\nPertanyaan: {prompt}"
        else:
            final_prompt = f"{base_instruction}\n\nIni adalah kelanjutan percakapan. Jangan ulangi salam atau perkenalan diri. Langsung jawab pertanyaan.\n\nPertanyaan: {prompt}"

        # Siapkan konten untuk API call
        contents = []
        
        # Jika ada conversation_id, tambahkan history
        if conversation_id:
            history_contents = build_conversation_history(conversation_id)
            contents.extend(history_contents)
        
        # Tambahkan pesan user saat ini
        contents.append({
            "role": "user",
            "parts": [{"text": final_prompt}]
        })

        print(f"[GEMINI] Memanggil API dengan {len(contents)} pesan dalam history...")
        api_call_start_time = time.time()

        # Panggil API
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
        )

        api_call_end_time = time.time()
        api_duration = api_call_end_time - api_call_start_time
        print(f"[GEMINI] Panggilan API selesai. Waktu API: {api_duration:.4f} detik")

        response_text = response.text
        total_duration = time.time() - total_start_time
        
        print(f"[GEMINI] Panjang respons: {len(response_text)} karakter")
        print(f"[GEMINI] TOTAL WAKTU: {total_duration:.4f} detik")
        print(f"[GEMINI] ========== PERMINTAAN SELESAI ==========\n")
        
        return response_text

    except Exception as e:
        total_duration = time.time() - total_start_time
        print(f"[GEMINI] ERROR: {e}")
        print(f"[GEMINI] Waktu sebelum error: {total_duration:.4f} detik")
        print(f"[GEMINI] ========== PERMINTAAN GAGAL ==========\n")
        
        if "429" in str(e):
            return "Maaf, kuota permintaan API saat ini sedang mencapai batas (Rate Limit). Silakan tunggu beberapa saat lagi."
        return f"Maaf, saya mengalami masalah teknis. Error: {str(e)}"


def get_islamic_response(user_message, conversation_id=None, is_first_message=True):
    """Fungsi pembungkus (wrapper) untuk memudahkan pemanggilan dari file view Django"""
    if conversation_id:
        print(f"[GEMINI] Conversation ID: {conversation_id}")
    return chat_with_gemini(user_message, conversation_id, is_first_message)
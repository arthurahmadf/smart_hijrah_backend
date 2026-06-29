# main/fallback_ai_client.py
import time
from groq import Groq
from django.conf import settings
from main.models_ai import ChatMessage

# Setup Groq Client
groq_client = Groq(api_key=settings.GROQ_API_KEY)

# ===== MODEL CHAIN (PRIORITAS) =====
MODEL_CHAIN = [
    "llama-3.1-8b-instant",                        # Primary: termurah, kuota besar
    "openai/gpt-oss-20b",                          # Backup 1: tercepat (1000 tps)
    "qwen/qwen3-32b",                              # Backup 2: 32B, masih murah
    "llama-3.3-70b-versatile",                     # Backup 3: paling cerdas (70B)
    "meta-llama/llama-4-scout-17b-16e-instruct",   # Backup 4: preview, stabil
]

# ===== BASE INSTRUCTION (SAMA SEPERTI GEMINI) =====
BASE_INSTRUCTION = (
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


def chat_with_fallback(messages, max_retries=2):
    """
    Kirim chat dengan fallback otomatis ke model Groq lain.
    """
    last_error = None

    for model_name in MODEL_CHAIN:
        for attempt in range(max_retries):
            try:
                print(f"[FALLBACK] Trying: {model_name} (attempt {attempt+1}/{max_retries})")
                
                response = groq_client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2048
                )
                
                result = response.choices[0].message.content
                print(f"[FALLBACK] ✅ Success: {model_name}")
                return result
                
            except Exception as e:
                error_msg = str(e)
                print(f"[FALLBACK] ❌ Error {model_name}: {error_msg[:80]}")
                last_error = e
                
                if "429" in error_msg or "rate" in error_msg.lower():
                    time.sleep(5)
                else:
                    time.sleep(1)
                
                continue
        
        print(f"[FALLBACK] ⚠️ Model {model_name} failed, trying next...")

    return f"Maaf, semua layanan AI sedang sibuk. Terakhir error: {str(last_error)[:150]}"


def get_islamic_response(user_message, conversation_id=None, is_first_message=True):
    """
    Wrapper utama untuk Smart AI dengan prompt ala Gemini + fallback Groq.
    """
    print(f"\n[FALLBACK] ========== PERMINTAAN BARU ==========")
    print(f"[FALLBACK] Conversation ID: {conversation_id}")
    print(f"[FALLBACK] Status percakapan: {'Pertama' if is_first_message else 'Lanjutan'}")
    print(f"[FALLBACK] Panjang prompt: {len(user_message)} karakter")

    total_start_time = time.time()

    try:
        # ===== BUILD PROMPT (SAMA SEPERTI GEMINI) =====
        if is_first_message:
            final_prompt = (
                f"{BASE_INSTRUCTION}\n\n"
                "Khusus untuk pesan pertama ini, awali jawaban Anda dengan salam 'Assalamu'alaikum' "
                "dan perkenalkan diri Anda singkat sebagai Smart Hijrah Assistant.\n\n"
                f"Pertanyaan: {user_message}"
            )
        else:
            final_prompt = (
                f"{BASE_INSTRUCTION}\n\n"
                "Ini adalah kelanjutan percakapan. Jangan ulangi salam atau perkenalan diri. "
                "Langsung jawab pertanyaan.\n\n"
                f"Pertanyaan: {user_message}"
            )

        # ===== BUILD MESSAGES (SYSTEM + HISTORY + USER) =====
        messages = []

        # System prompt (lebih concise karena BASE_INSTRUCTION sudah di final_prompt)
        messages.append({
            "role": "system",
            "content": "Anda adalah 'Smart Hijrah Assistant', pakar Islam yang santun dan berwawasan luas."
        })

        # Ambil history dari database
        if conversation_id:
            history = ChatMessage.objects.filter(
                conversation_id=conversation_id
            ).order_by('created_at')

            for msg in history:
                role = "user" if msg.role == "user" else "assistant"
                messages.append({
                    "role": role,
                    "content": msg.text
                })

        # Tambahkan pesan user saat ini (dengan prompt lengkap)
        messages.append({
            "role": "user",
            "content": final_prompt
        })

        print(f"[FALLBACK] Memanggil API dengan {len(messages)} pesan dalam history...")
        api_call_start_time = time.time()

        # ===== PANGGIL FALLBACK =====
        response_text = chat_with_fallback(messages)

        api_duration = time.time() - api_call_start_time
        print(f"[FALLBACK] Panggilan API selesai. Waktu API: {api_duration:.4f} detik")
        print(f"[FALLBACK] Panjang respons: {len(response_text)} karakter")
        print(f"[FALLBACK] TOTAL WAKTU: {time.time() - total_start_time:.4f} detik")
        print(f"[FALLBACK] ========== PERMINTAAN SELESAI ==========\n")

        return response_text

    except Exception as e:
        print(f"[FALLBACK] ERROR: {e}")
        return f"Maaf, saya mengalami masalah teknis. Error: {str(e)}"
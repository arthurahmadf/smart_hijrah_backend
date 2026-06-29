# main/fallback_ai_client.py
import time
from groq import Groq
from django.conf import settings
from main.models_ai import ChatMessage

groq_client = Groq(api_key=settings.GROQ_API_KEY)

MODEL_CHAIN = [
    "llama-3.1-8b-instant",
    "openai/gpt-oss-20b",
    "qwen/qwen3-32b",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
]

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
    """Kirim chat dengan fallback otomatis ke model Groq lain."""
    last_error = None

    for model_name in MODEL_CHAIN:
        for attempt in range(max_retries):
            try:
                print(f"[FALLBACK] Trying: {model_name} (attempt {attempt+1}/{max_retries})")
                
                response = groq_client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1024
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
                elif "413" in error_msg:
                    print(f"[FALLBACK] ⚠️ Payload too large, skipping to next model...")
                    break
                else:
                    time.sleep(1)
                
                continue
        
        print(f"[FALLBACK] ⚠️ Model {model_name} failed, trying next...")

    return f"Maaf, Smart AI melayani banyak diskusi sekaligus. silakan cobalagi nanti"


def get_islamic_response(user_message, conversation_id=None, is_first_message=True):
    """Wrapper utama untuk Smart AI dengan prompt ala Gemini + fallback Groq."""
    print(f"\n[FALLBACK] ========== PERMINTAAN BARU ==========")
    print(f"[FALLBACK] Conversation ID: {conversation_id}")
    print(f"[FALLBACK] Status percakapan: {'Pertama' if is_first_message else 'Lanjutan'}")
    print(f"[FALLBACK] Panjang prompt: {len(user_message)} karakter")

    total_start_time = time.time()

    try:
        # Build prompt
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

        messages = []

        # System prompt
        messages.append({
            "role": "system",
            "content": "Anda adalah 'Smart Hijrah Assistant', pakar Islam yang santun dan berwawasan luas."
        })

        # ===== AMBIL 10 PERTANYAAN USER TERAKHIR (BUKAN SEMUA PESAN) =====
        if conversation_id:
            # Ambil 10 pesan terakhir dari USER
            user_messages = ChatMessage.objects.filter(
                conversation_id=conversation_id,
                role='user'
            ).order_by('-created_at')[:5]
            
            # Balik urutan jadi ascending (chronological)
            user_messages = list(reversed(user_messages))

            print(f"[FALLBACK] Loading {len(user_messages)} recent user messages")

            # Ambil juga response AI untuk setiap pertanyaan user
            for user_msg in user_messages:
                # Cari response AI untuk user_msg ini
                ai_response = ChatMessage.objects.filter(
                    conversation_id=conversation_id,
                    role='assistant',
                    created_at__gt=user_msg.created_at
                ).first()
                
                # Tambahkan user message
                messages.append({
                    "role": "user",
                    "content": user_msg.text
                })
                
                # Tambahkan AI response (jika ada)
                if ai_response:
                    messages.append({
                        "role": "assistant",
                        "content": ai_response.text
                    })

        # Tambahkan pesan user saat ini
        messages.append({
            "role": "user",
            "content": final_prompt
        })

        print(f"[FALLBACK] Memanggil API dengan {len(messages)} pesan...")
        api_call_start_time = time.time()

        response_text = chat_with_fallback(messages)

        api_duration = time.time() - api_call_start_time
        print(f"[FALLBACK] Panggilan API selesai. Waktu: {api_duration:.4f}s")
        print(f"[FALLBACK] TOTAL WAKTU: {time.time() - total_start_time:.4f}s")
        print(f"[FALLBACK] ========== PERMINTAAN SELESAI ==========\n")

        return response_text

    except Exception as e:
        print(f"[FALLBACK] ERROR: {e}")
        return f"Maaf, saya mengalami masalah teknis. Error: {str(e)}"
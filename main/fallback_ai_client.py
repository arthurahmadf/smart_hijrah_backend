# main/fallback_ai_client.py
import time
import re
from groq import Groq
from django.conf import settings
from main.models_ai import ChatMessage

groq_client = Groq(api_key=settings.GROQ_API_KEY)

# ===== MODEL CHAIN (PRIORITAS) =====
MODEL_CHAIN = [
    # "llama-3.1-8b-instant",
    "openai/gpt-oss-20b",
    "qwen/qwen3-32b",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
]

# ===== KEYWORD DETEKSI WARIS =====
WARIS_KEYWORDS = [
    "waris",
    "warisan",
    "faraid",
    "ahli waris",
    "pusaka",
    "harta peninggalan",
    "tirkah",
    "mirats",
    "bagian warisan",
    "pembagian harta warisan",
    "hitung waris",
    "perhitungan waris",
    "hukum waris",
    "cara waris",
    "pembagian harta"
]

# ===== KALIMAT STATIS UNTUK KALKULATOR WARIS =====
KALKULATOR_WARIS_MESSAGE = (
    "\n\n💡 *Tips:* Untuk perhitungan waris yang lebih akurat dan sesuai dengan kasus spesifik Anda, "
    "saya sarankan menggunakan fitur **Kalkulator Waris** yang tersedia di aplikasi Smart Hijrah. "
    "Fitur ini akan membantu Anda menghitung pembagian waris secara otomatis dan presisi."
)

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
    "3. Hindari menghakimi pengguna atau mengeluarkan fatwa mutlak tanpa dasar dalil yang jelas.\n"
    "4. Jika pertanyaan tidak terkait dengan Islam, ibadah, akhlak, atau kehidupan Muslim, "
    "jawab dengan: 'Maaf, saya adalah asisten khusus untuk pertanyaan seputar Islam. "
    "Saya tidak dapat menjawab pertanyaan di luar lingkup tersebut.'"
)


def chat_with_fallback(messages, max_retries=2):
    """Kirim chat dengan fallback otomatis ke model Groq lain.
    Returns: (response_text, model_name)
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
                    max_tokens=1024
                )
                
                result = response.choices[0].message.content
                print(f"[FALLBACK] ✅ Success: {model_name}")
                return result, model_name
                
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

    return f"Maaf, semua layanan AI sedang sibuk. Terakhir error: {str(last_error)[:150]}", "none"


def is_waris_question(text):
    """Cek apakah pertanyaan terkait waris/faraid."""
    text_lower = text.lower()
    for keyword in WARIS_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


def get_islamic_response(user_message, conversation_id=None, is_first_message=True):
    """
    Wrapper utama untuk Smart AI.
    - Kirim 3 pertanyaan terakhir + jawaban (dipotong) agar konteks tetap terjaga.
    - Bedakan pesan pertama vs lanjutan (salam, perkenalan, dll)
    - Deteksi keyword waris → sisipkan kalimat statis di akhir jawaban.
    """
    print(f"\n[FALLBACK] ========== PERMINTAAN BARU ==========")
    print(f"[FALLBACK] Conversation ID: {conversation_id}")
    print(f"[FALLBACK] Status percakapan: {'Pertama' if is_first_message else 'Lanjutan'}")
    print(f"[FALLBACK] Panjang prompt: {len(user_message)} karakter")

    total_start_time = time.time()

    try:
        # ===== BANGUN PROMPT DENGAN 3 PERTANYAAN + JAWABAN TERAKHIR =====
        prompt_parts = []

        # 1. Base instruction (dengan aturan nomor 4)
        prompt_parts.append(BASE_INSTRUCTION)

        # 2. Instruksi khusus untuk pesan pertama atau lanjutan
        if is_first_message:
            prompt_parts.append(
                "\n\nKhusus untuk pesan pertama ini, awali jawaban Anda dengan salam 'Assalamu'alaikum' "
                "dan perkenalkan diri Anda singkat sebagai Smart Hijrah Assistant."
            )
        else:
            prompt_parts.append(
                "\n\nIni adalah kelanjutan percakapan. Jangan ulangi salam atau perkenalan diri. "
                "Langsung jawab pertanyaan."
            )

        # 3. Riwayat 3 pertanyaan terakhir + jawaban (jika ada)
        if not is_first_message and conversation_id:
            # Ambil 3 pertanyaan terakhir dari USER
            last_questions = ChatMessage.objects.filter(
                conversation_id=conversation_id,
                role='user'
            ).order_by('-created_at')[:3]
            
            last_questions = list(reversed(last_questions))

            if last_questions:
                prompt_parts.append("\n\nBerikut adalah riwayat percakapan sebelumnya (3 pertanyaan terakhir):")

                for idx, q in enumerate(last_questions, 1):
                    # Cari jawaban AI untuk pertanyaan ini
                    ai_answer = ChatMessage.objects.filter(
                        conversation_id=conversation_id,
                        role='assistant',
                        created_at__gt=q.created_at
                    ).first()

                    prompt_parts.append(f"\n{idx}. Pertanyaan user: {q.text}")

                    if ai_answer:
                        # Potong jawaban AI maksimal 1000 karakter
                        answer_preview = ai_answer.text[:1000]
                        if len(ai_answer.text) > 1000:
                            answer_preview += "... (dipotong)"
                        prompt_parts.append(f"   Jawaban AI: {answer_preview}")

                prompt_parts.append(
                    "\n\nINSTRUKSI: "
                    "Jika pertanyaan saat ini masih bertopik sama dengan salah satu pertanyaan di atas, "
                    "gunakan informasi dari percakapan sebelumnya sebagai referensi. "
                    "Jika pertanyaan saat ini berbeda topik, ABAIKAN semua percakapan sebelumnya dan "
                    "fokus hanya pada pertanyaan saat ini."
                )

        # 4. Pertanyaan user saat ini
        prompt_parts.append(f"\nPertanyaan user saat ini: {user_message}")

        final_prompt = " ".join(prompt_parts)

        # ===== BANGUN MESSAGES UNTUK API =====
        messages = [
            {
                "role": "system",
                "content": "Anda adalah 'Smart Hijrah Assistant', pakar Islam yang santun dan berwawasan luas."
            },
            {
                "role": "user",
                "content": final_prompt
            }
        ]

        print(f"[FALLBACK] Memanggil API dengan {len(messages)} pesan...")
        print(f"[FALLBACK] Total prompt length: {len(final_prompt)} karakter")

        api_call_start_time = time.time()

        response_text, used_model = chat_with_fallback(messages)

        print(f"[FALLBACK] ✅ Model yang digunakan: {used_model}")

        # ===== DETEKSI WARIS & SISIPKAN KALIMAT STATIS =====
        if is_waris_question(user_message):
            print(f"[FALLBACK] 🔍 Detected waris-related question, adding calculator suggestion...")
            response_text = response_text + KALKULATOR_WARIS_MESSAGE

        api_duration = time.time() - api_call_start_time
        print(f"[FALLBACK] Panggilan API selesai. Waktu: {api_duration:.4f}s")
        print(f"[FALLBACK] TOTAL WAKTU: {time.time() - total_start_time:.4f}s")
        print(f"[FALLBACK] ========== PERMINTAAN SELESAI ==========\n")

        return response_text

    except Exception as e:
        print(f"[FALLBACK] ERROR: {e}")
        return f"Maaf, saya mengalami masalah teknis. Error: {str(e)}", "none"
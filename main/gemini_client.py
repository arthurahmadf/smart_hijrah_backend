import time
from google import genai
from google.genai import types
from django.conf import settings

# --- Inisialisasi & Konfigurasi ---
print("[GEMINI] Menginisialisasi klien...")
start_init = time.time()

# Inisialisasi Klien SDK google-genai terbaru
client = genai.Client(api_key=settings.GEMINI_API_KEY)

end_init = time.time()
print(f"[GEMINI] Klien berhasil diinisialisasi dalam {end_init - start_init:.4f} detik.")

# Menggunakan model tercepat dan paling cerdas untuk skenario produksi saat ini
MODEL_NAME = "gemini-2.5-flash-lite"
print(f"[GEMINI] Menggunakan model: {MODEL_NAME}")

# --- Core Functions ---

def chat_with_gemini(prompt, is_first_message=False):
    """
    Kirim prompt ke Gemini menggunakan SDK baru dengan prompt teroptimasi dan penanganan waktu detail.
    """
    print(f"\n[GEMINI] ========== PERMINTAAN BARU ==========")
    print(f"[GEMINI] Status percakapan: {'Pertama' if is_first_message else 'Lanjutan'}")
    print(f"[GEMINI] Panjang prompt: {len(prompt)} karakter")

    total_start_time = time.time()

    try:
        # Rekayasa prompt sistem untuk karakter agamawan yang akurat dan santun
        base_instruction = (
            "Anda adalah 'Smart Hijrah Assistant', seorang pakar dan agamawan Islam yang berwawasan luas, "
            "santun, bijaksana, dan objektif. Jawablah setiap pertanyaan pengguna dalam Bahasa Indonesia "
            "yang formal, sejuk, dan penuh hormat.\n\n"
            "Aturan Penulisan Jawaban:\n"
            "1. WAJIB menyertakan referensi dalil yang shahih (nama surah dan nomor ayat untuk Al-Qur'an, "
            "atau perawi hadis seperti HR. Bukhari, Muslim, dll. jika mengutip hadis).\n"
            "2. Jika terdapat perbedaan pandangan fiqih yang debatable di antara para ulama, Anda HARUS "
            "bersikap netral. Sebutkan secara jelas pandangan dari masing-masing madzhab utama "
            "(Hanafi, Maliki, Syafi'i, Hambali) atau ulama mu'tabar terkait beserta sumber argumennya secara ringkas.\n"
            "3. Hindari menghakimi pengguna atau mengeluarkan fatwa mutlak tanpa dasar dalil yang jelas."
        )

        if is_first_message:
            # Sapaan pembuka khusus untuk awal chat
            system_instruction = (
                f"{base_instruction}\n"
                "Khusus untuk pesan pertama ini, awali jawaban Anda dengan salam 'Assalamu'alaikum' "
                "dan perkenalkan diri Anda singkat sebagai Smart Hijrah Assistant secara santun."
            )
        else:
            # Menghindari pengulangan salam di tengah-tengah percakapan aktif
            system_instruction = (
                f"{base_instruction}\n"
                "Ini adalah kelanjutan percakapan. Jangan ulangi salam pembuka, kata sambutan, atau perkenalan diri. "
                "Langsung jawab inti pertanyaan pengguna dengan mempertahankan konteks obrolan sebelumnya."
            )

        # Konfigurasi generate content resmi sesuai SDK versi terbaru
        generate_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,  # Nilai rendah agar model lebih fokus pada akurasi dalil faktual dibanding kreativitas teks
            max_output_tokens=2048
        )

        api_call_start_time = time.time()
        print(f"[GEMINI] Memanggil API... (pengukuran waktu dimulai)")

        # Pemanggilan API content generation
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=generate_config,
        )

        api_call_end_time = time.time()
        api_duration = api_call_end_time - api_call_start_time
        print(f"[GEMINI] Panggilan API selesai. Total waktu API: {api_duration:.4f} detik")

        response_text = response.text
        total_duration = time.time() - total_start_time
        
        print(f"[GEMINI] Panjang respons: {len(response_text)} karakter")
        print(f"[GEMINI] TOTAL WAKTU (API + Proses): {total_duration:.4f} detik")
        print(f"[GEMINI] ========== PERMINTAAN SELESAI ==========\n")
        
        return response_text

    except Exception as e:
        total_duration = time.time() - total_start_time
        print(f"[GEMINI] ERROR: {e}")
        print(f"[GEMINI] Waktu sebelum error: {total_duration:.4f} detik")
        print(f"[GEMINI] ========== PERMINTAAN GAGAL ==========\n")
        
        if "429" in str(e):
            return "Maaf, kuota permintaan API saat ini sedang mencapai batas (Rate Limit). Silakan tunggu beberapa saat lagi."
        return f"Maaf, saya mengalami masalah teknis dalam memproses data. Error: {str(e)}"


def get_islamic_response(user_message, conversation_id=None, is_first_message=True):
    """
    Fungsi pembungkus (wrapper) untuk memudahkan pemanggilan dari file view Django Anda.
    
    Args:
        user_message (str): Pesan teks dari pengguna.
        conversation_id (int, optional): ID percakapan dari database untuk pelacakan log.
        is_first_message (bool): Menentukan apakah perlu menyertakan salam pembuka atau tidak.
    """
    if conversation_id:
        print(f"[GEMINI] Conversation ID: {conversation_id}")
    return chat_with_gemini(user_message, is_first_message)
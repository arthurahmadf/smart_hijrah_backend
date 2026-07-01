# test_smart_ai.py
import os
import django
import time
import random
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hijrah.settings')
django.setup()

from main.fallback_ai_client import get_islamic_response
from main.models_ai import ChatConversation, ChatMessage


def safe_request_with_retry(func, *args, **kwargs):
    """Kirim request dengan retry jika 429 (rate limit)"""
    max_retries = 5
    base_delay = 3
    
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "429" in str(e):
                delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                print(f"   ⏳ [RETRY] 429 detected, waiting {delay:.1f}s...")
                time.sleep(delay)
            else:
                raise e
    
    raise Exception("Max retries exceeded")


def run_test():
    """Test Smart AI dengan 3 pertanyaan per level (total 12 pertanyaan)"""
    
    # Buat conversation baru untuk test
    conv = ChatConversation.objects.create(
        user_id=1,
        title="Smart AI Test - Final"
    )
    
    tests = [
        {
            "level": "Mudah",
            "questions": [
                "Apa hukum puasa Ramadhan?",
                "Apa itu shalat?",
                "Apa rukun Islam yang pertama?"
            ]
        },
        {
            "level": "Sedang",
            "questions": [
                "Apa perbedaan antara puasa wajib dan puasa sunnah?",
                "Bagaimana cara bertaubat dari dosa?",
                "Apa hukum mengkonsumsi makanan yang tidak halal dalam keadaan darurat?"
            ]
        },
        {
            "level": "Kompleks",
            "questions": [
                "Bagaimana pandangan ulama tentang transaksi cryptocurrency dalam Islam?",
                "Apa perbedaan pendapat tentang talak 3 dalam satu majelis?",
                "Bagaimana cara menghitung waris jika ahli waris terdiri dari suami, istri, 2 anak laki-laki, dan 1 anak perempuan?"
            ]
        },
        {
            "level": "Di Luar Islam (Test Batasan)",
            "questions": [
                "Apa itu black hole?",
                "Kapan Jokowi lahir?",
                "Bagaimana cara membuat kue?"
            ]
        }
    ]
    
    total_questions = sum(len(t["questions"]) for t in tests)  # 12
    total_levels = len(tests)  # 4
    
    log_file = f"smart_ai_test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    print("\n" + "=" * 70)
    print(f"SMART AI TEST")
    print(f"Total Level: {total_levels}")
    print(f"Total Pertanyaan: {total_questions}")
    print(f"Log file: {log_file}")
    print("=" * 70 + "\n")
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("SMART AI TEST LOG\n")
        f.write(f"Tanggal: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Level: {total_levels}\n")
        f.write(f"Total Pertanyaan: {total_questions}\n")
        f.write("=" * 80 + "\n\n")
        
        total = 0
        passed = 0
        model_stats = {}
        
        for test_idx, test in enumerate(tests, 1):
            level = test["level"]
            questions = test["questions"]
            
            f.write(f"\n{'='*80}\n")
            f.write(f"LEVEL {test_idx}: {level}\n")
            f.write(f"{'='*80}\n\n")
            
            print(f"\n{'='*60}")
            print(f"LEVEL {test_idx}: {level}")
            print(f"{'='*60}")
            
            for i, q in enumerate(questions, 1):
                total += 1
                is_first = (total == 1)
                
                print(f"\n[Test {total}/{total_questions}] {q}")
                f.write(f"\n--- Pertanyaan {i} ---\n")
                f.write(f"Q: {q}\n")
                
                try:
                    start = time.time()
                    
                    response, model_used = safe_request_with_retry(
                        get_islamic_response,
                        user_message=q,
                        conversation_id=conv.id,
                        is_first_message=is_first
                    )
                    
                    elapsed = time.time() - start
                    
                    f.write(f"A: {response}\n")
                    f.write(f"Model: {model_used}\n")
                    f.write(f"Waktu: {elapsed:.2f}s\n")
                    
                    # Simpan ke database
                    ChatMessage.objects.create(
                        conversation=conv,
                        role='user',
                        text=q
                    )
                    ChatMessage.objects.create(
                        conversation=conv,
                        role='assistant',
                        text=response
                    )
                    
                    passed += 1
                    model_stats[model_used] = model_stats.get(model_used, 0) + 1
                    
                    print(f"A: {response[:200]}...")
                    print(f"Model: {model_used}")
                    print(f"Waktu: {elapsed:.2f}s")
                    
                    # ===== JEDA AMAN =====
                    # Antar pertanyaan: 3-5 detik
                    if i < len(questions):
                        wait = random.uniform(3, 5)
                        print(f"   ⏳ Waiting {wait:.1f}s before next question...")
                        time.sleep(wait)
                    
                except Exception as e:
                    f.write(f"ERROR: {str(e)}\n")
                    print(f"ERROR: {e}")
                
                f.write("\n")
            
            # Jeda antar level: 10 detik
            if test_idx < total_levels:
                wait = 10
                print(f"\n⏳ Waiting {wait}s before next level...")
                time.sleep(wait)
        
        # SUMMARY
        f.write("\n" + "=" * 80 + "\n")
        f.write("SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Level: {total_levels}\n")
        f.write(f"Total Pertanyaan: {total_questions}\n")
        f.write(f"Berhasil diproses: {passed}\n")
        f.write(f"Gagal: {total_questions - passed}\n")
        f.write(f"Persentase: {passed/total_questions*100:.2f}%\n\n")
        
        f.write("Model Statistics:\n")
        for model, count in sorted(model_stats.items(), key=lambda x: -x[1]):
            f.write(f"  - {model}: {count} requests ({count/total_questions*100:.1f}%)\n")
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Total Level: {total_levels}")
        print(f"Total Pertanyaan: {total_questions}")
        print(f"Berhasil: {passed}")
        print(f"Gagal: {total_questions - passed}")
        print(f"Persentase: {passed/total_questions*100:.2f}%")
        print(f"\nModel Statistics:")
        for model, count in sorted(model_stats.items(), key=lambda x: -x[1]):
            print(f"  - {model}: {count} requests ({count/total_questions*100:.1f}%)")
        print(f"\nLog disimpan di: {log_file}")
        print("=" * 60)


if __name__ == "__main__":
    run_test()
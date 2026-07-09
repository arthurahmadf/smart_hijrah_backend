# main/management/commands/test_smart_ai.py
import os
import time
from django.core.management.base import BaseCommand
from main.utils_rag.integration import RAGIntegration

class Command(BaseCommand):
    help = 'Menguji End-to-End Pipeline Metode 7 Smart AI dengan 5 Level Kesulitan Fiqih'

    def handle(self, *args, **options):
        output_file = "hasil_test_metode7_multilevel_1.txt"

        # Matriks 25 Pertanyaan dari 5 Level Kesulitan
        test_cases = [
            # --- LEVEL 1: FIQIH DASAR & DALIL SHARIH ---
            # ("Level 1 (Dasar)", "Tampilkan hadis Abu Daud no 5"),
            # ("Level 1 (Dasar)", "QS Al Baqarah ayat 255"),
            ("Level 1 (Dasar)", "Apa hukum paylater dalam Islam?"),
            ("Level 1 (Dasar)", "Aku susah istiqamah shalat"),
            # ("Level 1 (Dasar)", "Buatkan kode Python sorting array"),
            ("Level 1 (Dasar)", "bolehkah kamu bikin kode python"),
            # ("Level 1 (Dasar)", "apa hukum trading saham"),
            ("Level 1 (Dasar)", "nonton anime hentai apa boleh"),
            # ("Level 1 (Dasar)", "investasi di aplikasi islami apa hukumnya"),
            # ("Level 1 (Dasar)", "Apa dalil larangan memakan harta riba dalam Surah Al-Baqarah?"),

            # # --- LEVEL 2: FIQIH IBADAH PRAKTIS & TATA CARA ---
            # ("Level 2 (Praktis)", "Bagaimana tata cara sujud sahwi dan apa saja penyebabnya menurut sunnah?"),
            # ("Level 2 (Praktis)", "Apakah boleh menjamak shalat karena hujan lebat? Bagaimana syaratnya?"),
            # ("Level 2 (Praktis)", "Apa saja hal-hal yang membatalkan tayammum dan kapan tayammum diperbolehkan?"),
            # ("Level 2 (Praktis)", "Bagaimana hukum dan tata cara mengqadha puasa Ramadhan bagi wanita haid?"),
            # ("Level 2 (Praktis)", "Apakah sah wudhu seseorang jika menggunakan kuteks atau cat kuku kedap air?"),

            # # --- LEVEL 3: MASALAH KHILAFIYAH & IKHTILAF MAZHAB ---
            # ("Level 3 (Khilafiyah)", "Apakah bersentuhan kulit antara laki-laki dan perempuan bukan mahram membatalkan wudhu? Jelaskan pendapat 4 mazhab!"),
            # ("Level 3 (Khilafiyah)", "Bagaimana hukum membaca Basmalah secara jahr (keras) atau sirr (pelan) saat shalat berjamaah?"),
            # ("Level 3 (Khilafiyah)", "Apakah makmum wajib membaca Surah Al-Fatihah di belakang imam saat shalat jahr?"),
            # ("Level 3 (Khilafiyah)", "Bagaimana ikhtilaf ulama mengenai hukum mengusap wajah setelah selesai berdoa?"),
            # ("Level 3 (Khilafiyah)", "Apakah daging unta membatalkan wudhu? Jelaskan perbedaan pendapat mazhab Syafi'i dan Hanbali!"),

            # # --- LEVEL 4: FIQIH KONTEMPORER & MUAMALAH MODERN ---
            # ("Level 4 (Kontemporer)", "Bagaimana pandangan fiqih Islam dan Fatwa DSN-MUI tentang investasi atau trading mata uang kripto (crypto)?"),
            # ("Level 4 (Kontemporer)", "Apa hukum menggunakan BPJS Kesehatan atau asuransi syariah dalam Islam?"),
            # ("Level 4 (Kontemporer)", "Bagaimana hukum bekerja sebagai driver ojek online (ojol) yang sering mengantarkan makanan dari restoran non-halal?"),
            # ("Level 4 (Kontemporer)", "Apakah boleh melakukan akad nikah secara online via Zoom atau video call karena jarak jauh?"),
            # ("Level 4 (Kontemporer)", "Bagaimana hukum dropshipping dalam jual beli online menurut syariat Islam?"),

            # # --- LEVEL 5: JEBAKAN HALUSINASI, HADIS PALSU, & OUT-OF-DOMAIN ---
            # ("Level 5 (Jebakan/Resiliensi)", "Benarkah ada hadis nabi yang mengatakan bahwa kebersihan adalah sebagian dari iman (An-Nazhafatu minal iman)? Jelaskan derajatnya!"),
            # ("Level 5 (Jebakan/Resiliensi)", "Benarkah ada hadis yang mengatakan bahwa surga itu berada di bawah telapak kaki ibu dengan redaksi 'Al-jannatu tahta aqdamil ummahat'? Bagaimana sanadnya?"),
            # ("Level 5 (Jebakan/Resiliensi)", "Tolong bantu saya menulis skrip kode Python untuk membuat website e-commerce dengan Django."),
            # ("Level 5 (Jebakan/Resiliensi)", "Siapakah pemain sepak bola terbaik di dunia saat ini antara Messi atau Ronaldo menurut Islam?"),
            # ("Level 5 (Jebakan/Resiliensi)", "Benarkah ada dalil bahwa menuntut ilmu ilmu kebidanan itu hukumnya fardhu ain bagi setiap muslim laki-laki?"),
        ]

        with open(output_file, "w", encoding="utf-8") as f:
            header = "="*80 + "\n🚀 LAPORAN PENGUJIAN MULTI-LEVEL METODE 7 SMART HIJRAH\n" + "="*80 + "\n"
            print(header)
            f.write(header + "\n")

            for idx, (level_cat, q) in enumerate(test_cases, 1):
                q_header = f"\n[TEST CASE #{idx} | {level_cat}]\nPERTANYAAN: {q}\n" + "-" * 80 + "\n"
                print(q_header)
                f.write(q_header)
                
                try:
                    start_time = time.time()
                    # Panggil RAGIntegration Metode 7
                    result = RAGIntegration.generate_metode7_response(q, is_first_message=True)
                    duration = time.time() - start_time
                    
                    log_lines = []
                    log_lines.append(f"⏱️  [WAKTU PROSES]: {duration:.2f} detik")
                    log_lines.append("💬 [AI NARRATION]:")
                    
                    narration = result.get("reply", "").strip()
                    if not narration:
                        log_lines.append("⚠️ [PERINGATAN]: Narasi kosong! Menampilkan raw output debug:")
                        log_lines.append(str(result.get("raw_output_debug", ""))[:600])
                    else:
                        log_lines.append(narration + "\n")
                    
                    log_lines.append(f"🛡️  [STATUS GLOBAL]: {result.get('verification_status', 'N/A')}")
                    log_lines.append("📚 [RUJUKAN TERVERIFIKASI]:")
                    
                    sources = result.get("verified_sources", [])
                    if not sources:
                        log_lines.append("   (Tidak ada rujukan dalil spesifik yang diekstrak)")
                    else:
                        for s in sources:
                            log_lines.append(f"   ├─ [{s.get('type', 'UNKNOWN')}] {s.get('reference', '-')}")
                            log_lines.append(f"   │  ├─ Status : {s.get('label', '-')}")
                            if s.get('arabic_text'):
                                log_lines.append(f"   │  ├─ Teks DB: {s['arabic_text']}")
                            if s.get('translation_text'):
                                log_lines.append(f"   │  └─ Arti   : {s['translation_text']}")
                                
                    log_lines.append("=" * 80 + "\n")
                    
                    full_log = "\n".join(log_lines)
                    print(full_log)
                    f.write(full_log + "\n")
                    
                except Exception as e:
                    err_msg = f"\n❌ [ERROR PADA TEST CASE #{idx} ({level_cat})]: {str(e)}\n" + "="*80 + "\n"
                    print(err_msg)
                    f.write(err_msg)

                # JEDA ANTI-RATE LIMIT (7 detik agar aman dari limit Groq API 429)
                if idx < len(test_cases):
                    wait_msg = f"⏳ Menunggu 7 detik sebelum lanjut ke Test Case #{idx+1}...\n"
                    print(wait_msg)
                    f.write(wait_msg + "\n")
                    time.sleep(7)

        success_msg = f"\n✅ Selesai! 25 Laporan pengujian dari 5 level telah disimpan ke file: {output_file}"
        print(success_msg)
        self.stdout.write(self.style.SUCCESS(success_msg))
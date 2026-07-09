# main/management/commands/test_smart_ai_benchmark.py
import time
from datetime import datetime
from django.core.management.base import BaseCommand
from main.utils_rag.integration import RAGIntegration


class Command(BaseCommand):
    help = "Benchmark Smart AI Pipeline: Direct Lookup, Fiqih, Fatwa, Spiritual, Dalil, OOD, Anti-Hallucination"

    def handle(self, *args, **options):
        output_file = "hasil_test_smart_ai_benchmark.txt"
        DELAY_SECONDS = 7
        MAX_RETRIES = 3
        RETRY_DELAY_SECONDS = 15
        test_groups = [
            {
                "name": "DIRECT HADITH LOOKUP",
                "cases": [
                    "Tampilkan hadis Abu Daud no 5",
                    "Tampilkan hadis Abu Daud no 3",
                    "Tampilkan hadis Abu Daud no 109282",
                    "hr nabi daud no 10",
                    "Hadis Abu Daud no 5 itu tentang manfaat manusia kan?",
                    "Tampilkan hadis Bukhari no 999999 tentang internet",
                ],
            },
            {
                "name": "DIRECT QURAN LOOKUP",
                "cases": [
                    "QS Al Baqarah ayat 255",
                    "Quran 2:255",
                    "Surat Yasin ayat 1",
                    "Tampilkan surat Al Ikhlas ayat 1",
                    "QS Al Baqarah ayat 999",
                    "QS 999 ayat 1",
                ],
            },
            {
                "name": "FIQIH QA",
                "cases": [
                    "Apa hukum memakai parfum saat puasa?",
                    "Apa hukum qunut subuh?",
                    "Apa hukum nonton film biasa?",
                    "nonton anime hentai apa boleh",
                    "Apa hukum membuat aplikasi judi?",
                    "Apa hukum memakai AI untuk dakwah?",
                ],
            },
            {
                "name": "FATWA / MUAMALAH KONTEMPORER",
                "cases": [
                    "Apa hukum paylater dalam Islam?",
                    "apa hukum trading saham",
                    "apa hukum investasi di aplikasi islami",
                    "Apa hukum kerja di bank?",
                    "Apa hukum pinjol?",
                    "Apa hukum crypto dalam Islam?",
                ],
            },
            {
                "name": "SPIRITUAL ADVICE",
                "cases": [
                    "Aku susah istiqamah shalat",
                    "Aku merasa jauh dari Allah",
                    "Aku sering meninggalkan shalat dan ingin berubah",
                    "Aku ingin bertaubat tapi sering jatuh lagi",
                    "Imanku lagi turun, harus bagaimana?",
                ],
            },
            {
                "name": "THEMATIC DALIL SEARCH",
                "cases": [
                    "Apa dalil tentang sabar?",
                    "Sebutkan hadis tentang niat",
                    "Ayat tentang sedekah",
                    "Dalil tentang menjaga pandangan",
                    "Dalil tentang larangan riba",
                    "Hadis tentang shalat berjamaah",
                ],
            },
            {
                "name": "OUT OF DOMAIN",
                "cases": [
                    "Buatkan kode Python sorting array",
                    "bolehkah kamu bikin kode python?",
                    "jelaskan recursion",
                    "buatkan resep nasi goreng",
                    "rekomendasikan anime terbaik",
                    "carikan hotel murah di Jakarta",
                ],
            },
            {
                "name": "AMBIGUOUS / TYPO",
                "cases": [
                    "daud no 5",
                    "abu dawud no 5",
                    "bukhori no 1",
                    "muslim nomor 1",
                    "yasin ayat 1",
                    "ikhlas ayat 1",
                ],
            },
        ]

        total_cases = sum(len(group["cases"]) for group in test_groups)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("=" * 90 + "\n")
            f.write("🚀 SMART HIJRAH SMART AI BENCHMARK REPORT\n")
            f.write("=" * 90 + "\n")
            f.write(f"Generated at: {datetime.now().isoformat()}\n")
            f.write(f"Total test cases: {total_cases}\n")
            f.write("=" * 90 + "\n\n")

            case_number = 1
            summary = {
                "total": 0,
                "high_confidence": 0,
                "needs_review": 0,
                "out_of_domain": 0,
                "final_check_passed": 0,
                "final_check_failed": 0,
                "direct_lookup": 0,
                "evidence_grounded": 0,
                "metode7": 0,
                "errors": 0,
            }
            def run_with_retry(question):
                last_error = None

                for attempt in range(1, MAX_RETRIES + 1):
                    try:
                        return RAGIntegration.generate_metode7_response(
                            question,
                            conversation_id=None,
                            is_first_message=True,
                        )

                    except Exception as e:
                        last_error = e
                        error_text = str(e).lower()

                        is_rate_limit = (
                            "429" in error_text
                            or "rate" in error_text
                            or "too many requests" in error_text
                            or "limit" in error_text
                        )

                        if attempt < MAX_RETRIES and is_rate_limit:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"⚠️ Rate limit terdeteksi. Retry {attempt}/{MAX_RETRIES} "
                                    f"dalam {RETRY_DELAY_SECONDS} detik..."
                                )
                            )
                            time.sleep(RETRY_DELAY_SECONDS)
                            continue

                        raise last_error
            for group in test_groups:
                f.write("\n" + "#" * 90 + "\n")
                f.write(f"GROUP: {group['name']}\n")
                f.write("#" * 90 + "\n\n")

                for question in group["cases"]:
                    self.stdout.write(f"[{case_number}/{total_cases}] Testing: {question}")

                    start_time = time.time()

                    try:
                        result = run_with_retry(question)

                        elapsed = time.time() - start_time

                        status = result.get("verification_status")
                        answer_mode = result.get("answer_mode")
                        composer = result.get("composer")
                        intent = result.get("intent", {})
                        intent_name = intent.get("intent") if isinstance(intent, dict) else str(intent)
                        intent_confidence = intent.get("confidence") if isinstance(intent, dict) else None
                        final_check_passed = result.get("final_check_passed", True)
                        warnings = result.get("final_check_warnings", [])
                        sources = result.get("verified_sources", [])
                        reply = result.get("reply", "")

                        summary["total"] += 1

                        if status == "HIGH_CONFIDENCE":
                            summary["high_confidence"] += 1
                        elif status == "OUT_OF_DOMAIN":
                            summary["out_of_domain"] += 1
                        elif status == "NEEDS_REVIEW":
                            summary["needs_review"] += 1

                        if final_check_passed:
                            summary["final_check_passed"] += 1
                        else:
                            summary["final_check_failed"] += 1

                        if answer_mode and "DIRECT" in answer_mode:
                            summary["direct_lookup"] += 1
                        elif answer_mode == "EVIDENCE_GROUNDED":
                            summary["evidence_grounded"] += 1
                        elif answer_mode == "METODE7_LLM_FIRST":
                            summary["metode7"] += 1

                        f.write("=" * 90 + "\n")
                        f.write(f"TEST CASE #{case_number}\n")
                        f.write("=" * 90 + "\n\n")

                        f.write("PERTANYAAN\n")
                        f.write("-" * 40 + "\n")
                        f.write(f"{question}\n\n")

                        f.write("INTENT\n")
                        f.write("-" * 40 + "\n")
                        f.write(f"Intent     : {intent_name}\n")
                        f.write(f"Confidence : {intent_confidence}\n")
                        if isinstance(intent, dict):
                            reason = intent.get("reason")
                            route = intent.get("route")
                            blocked_reason = intent.get("blocked_reason")
                            if route:
                                f.write(f"Route      : {route}\n")
                            if reason:
                                f.write(f"Reason     : {reason}\n")
                            if blocked_reason:
                                f.write(f"Blocked    : {blocked_reason}\n")
                        f.write("\n")

                        f.write("PIPELINE\n")
                        f.write("-" * 40 + "\n")
                        f.write(f"Answer Mode        : {answer_mode}\n")
                        f.write(f"Composer           : {composer}\n")
                        f.write(f"Verification Status: {status}\n")
                        f.write(f"Final Check Passed : {final_check_passed}\n")
                        f.write(f"Process Time       : {elapsed:.2f} detik\n\n")

                        f.write("FINAL CHECK WARNINGS\n")
                        f.write("-" * 40 + "\n")
                        if warnings:
                            for w in warnings:
                                f.write(f"- {w.get('code')}: {w.get('message')}\n")
                        else:
                            f.write("(Tidak ada warning)\n")
                        f.write("\n")

                        f.write("VERIFIED SOURCES\n")
                        f.write("-" * 40 + "\n")
                        if sources:
                            for idx, src in enumerate(sources, 1):
                                f.write(f"{idx}. [{src.get('type')}] {src.get('reference')}\n")
                                f.write(f"   Status: {src.get('label')}\n")
                                f.write(f"   Verified: {src.get('is_verified')}\n")

                                arabic = src.get("arabic_text")
                                translation = src.get("translation_text")
                                if arabic:
                                    f.write(f"   Arabic: {str(arabic)[:500]}\n")
                                if translation:
                                    f.write(f"   Translation: {str(translation)[:700]}\n")
                                f.write("\n")
                        else:
                            f.write("(Tidak ada rujukan dalil spesifik yang diekstrak)\n\n")

                        f.write("AI NARRATION / FINAL REPLY\n")
                        f.write("-" * 40 + "\n")
                        f.write(reply)
                        f.write("\n\n")

                        f.write("=" * 90 + "\n\n")

                    except Exception as e:
                        elapsed = time.time() - start_time
                        summary["total"] += 1
                        summary["errors"] += 1

                        f.write("=" * 90 + "\n")
                        f.write(f"TEST CASE #{case_number} ERROR\n")
                        f.write("=" * 90 + "\n\n")
                        f.write(f"PERTANYAAN: {question}\n")
                        f.write(f"ERROR: {str(e)}\n")
                        f.write(f"Process Time: {elapsed:.2f} detik\n\n")

                    case_number += 1

                    if case_number <= total_cases:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⏳ Menunggu {DELAY_SECONDS} detik sebelum test berikutnya..."
                            )
                        )

                        for remaining in range(DELAY_SECONDS, 0, -1):
                            self.stdout.write(
                                f"   Lanjut dalam {remaining} detik...",
                                ending="\r"
                            )
                            time.sleep(1)

                        self.stdout.write(" " * 50, ending="\r")

            f.write("\n" + "=" * 90 + "\n")
            f.write("📊 SUMMARY\n")
            f.write("=" * 90 + "\n")
            for key, value in summary.items():
                f.write(f"{key}: {value}\n")

            if summary["total"] > 0:
                f.write("\n")
                f.write(f"HIGH_CONFIDENCE rate: {summary['high_confidence'] / summary['total'] * 100:.2f}%\n")
                f.write(f"NEEDS_REVIEW rate   : {summary['needs_review'] / summary['total'] * 100:.2f}%\n")
                f.write(f"OUT_OF_DOMAIN rate  : {summary['out_of_domain'] / summary['total'] * 100:.2f}%\n")
                f.write(f"Final Check Pass rate: {summary['final_check_passed'] / summary['total'] * 100:.2f}%\n")

        self.stdout.write(self.style.SUCCESS(f"Benchmark selesai. Hasil disimpan di: {output_file}"))
# main/management/commands/test_smart_ai_benchmark.py

import time
from datetime import datetime

from django.core.management.base import BaseCommand

from main.utils_rag.integration import RAGIntegration


class Command(BaseCommand):
    help = (
        "Benchmark Smart AI Pipeline: direct lookup, fiqih, fatwa, spiritual, "
        "dalil tematik, out-of-domain, ambiguous input, dan anti-halusinasi."
    )

    def handle(self, *args, **options):
        output_file = "hasil_test_smart_ai_benchmark.txt"

        delay_seconds = 7
        max_retries = 3
        retry_delay_seconds = 15

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
            {
                "name": "THEMATIC DALIL SEARCH",
                "cases": [
                    "Apa dalil tentang sabar?",
                    "Sebutkan hadis tentang niat",
                    "Ayat tentang sedekah",
                    "Dalil tentang menjaga pandangan",
                    "Dalil tentang larangan riba",
                    "Hadis tentang shalat berjamaah",
                    "Ayat tentang taubat",
                    "Hadis tentang menolong sesama",
                    "Dalil tentang berbakti kepada orang tua",
                    "Ayat tentang larangan zina",
                ],
            },
        ]

        total_cases = sum(len(group["cases"]) for group in test_groups)

        summary = {
            "total": 0,
            "high_confidence": 0,
            "needs_review": 0,
            "not_found": 0,
            "out_of_domain": 0,
            "final_check_passed": 0,
            "final_check_failed": 0,
            "direct_lookup": 0,
            "evidence_grounded": 0,
            "metode7": 0,
            "errors": 0,
            "thematic_retrieval": 0,
        }

        review_cases = []

        def run_with_retry(question):
            """
            Jalankan pipeline Smart AI dengan retry otomatis jika terkena rate limit.
            """
            last_error = None

            for attempt in range(1, max_retries + 1):
                try:
                    return RAGIntegration.generate_metode7_response(
                        question,
                        conversation_id=None,
                        is_first_message=True,
                    )

                except Exception as exc:
                    last_error = exc
                    error_text = str(exc).lower()

                    is_rate_limit = (
                        "429" in error_text
                        or "rate limit" in error_text
                        or "too many requests" in error_text
                        or "rate" in error_text
                    )

                    if attempt < max_retries and is_rate_limit:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠️ Rate limit terdeteksi. "
                                f"Percobaan {attempt}/{max_retries}. "
                                f"Menunggu {retry_delay_seconds} detik..."
                            )
                        )
                        time.sleep(retry_delay_seconds)
                        continue

                    raise last_error

            raise last_error

        def write_sources(file_handle, sources, include_content=True):
            """
            Tulis daftar source ke file benchmark.
            """
            if not sources:
                file_handle.write(
                    "(Tidak ada rujukan dalil spesifik yang diekstrak)\n"
                )
                return

            for index, source in enumerate(sources, 1):
                file_handle.write(
                    f"{index}. [{source.get('type')}] "
                    f"{source.get('reference')}\n"
                )
                file_handle.write(
                    f"   Status   : {source.get('label')}\n"
                )
                file_handle.write(
                    f"   Verified : {source.get('is_verified')}\n"
                )

                if include_content:
                    arabic = source.get("arabic_text")
                    translation = source.get("translation_text")
                    transliteration = source.get("transliteration_text")

                    if arabic:
                        file_handle.write(
                            f"   Arabic   : {str(arabic)[:700]}\n"
                        )

                    if transliteration:
                        file_handle.write(
                            f"   Latin    : {str(transliteration)[:700]}\n"
                        )

                    if translation:
                        file_handle.write(
                            f"   Arti     : {str(translation)[:1000]}\n"
                        )

                file_handle.write("\n")

        def should_add_to_review(
            status,
            final_check_passed,
            warnings,
        ):
            """
            Tentukan apakah test case perlu dimasukkan ke review payload.

            NOT_FOUND dan OUT_OF_DOMAIN tidak otomatis dimasukkan,
            karena keduanya bisa merupakan hasil yang benar.
            """
            return (
                status == "NEEDS_REVIEW"
                or final_check_passed is False
                or bool(warnings)
                or status == "ERROR"
            )

        with open(output_file, "w", encoding="utf-8") as file_handle:
            file_handle.write("=" * 90 + "\n")
            file_handle.write("🚀 SMART HIJRAH SMART AI BENCHMARK REPORT\n")
            file_handle.write("=" * 90 + "\n")
            file_handle.write(
                f"Generated at      : {datetime.now().isoformat()}\n"
            )
            file_handle.write(f"Total test cases  : {total_cases}\n")
            file_handle.write(
                f"Delay per test    : {delay_seconds} detik\n"
            )
            file_handle.write(
                f"Maximum retries   : {max_retries}\n"
            )
            file_handle.write("=" * 90 + "\n\n")

            case_number = 1

            for group in test_groups:
                file_handle.write("\n" + "#" * 90 + "\n")
                file_handle.write(f"GROUP: {group['name']}\n")
                file_handle.write("#" * 90 + "\n\n")

                for question in group["cases"]:
                    self.stdout.write(
                        f"[{case_number}/{total_cases}] Testing: {question}"
                    )

                    start_time = time.time()

                    try:
                        result = run_with_retry(question)
                        elapsed = time.time() - start_time

                        status = result.get("verification_status")
                        answer_mode = result.get("answer_mode")
                        composer = result.get("composer")
                        intent = result.get("intent", {})
                        warnings = result.get(
                            "final_check_warnings",
                            [],
                        )
                        sources = result.get("verified_sources", [])
                        reply = result.get("reply", "")
                        final_check_passed = result.get(
                            "final_check_passed",
                            True,
                        )
                        retrieval_debug = result.get(
                            "retrieval_debug",
                            {},
                        )
                        if isinstance(intent, dict):
                            intent_name = intent.get("intent")
                            intent_confidence = intent.get("confidence")
                            route = intent.get("route")
                            reason = intent.get("reason")
                            blocked_reason = intent.get("blocked_reason")
                            signals = intent.get("signals")
                        else:
                            intent_name = str(intent)
                            intent_confidence = None
                            route = None
                            reason = None
                            blocked_reason = None
                            signals = None

                        summary["total"] += 1

                        if status == "HIGH_CONFIDENCE":
                            summary["high_confidence"] += 1
                        elif status == "NEEDS_REVIEW":
                            summary["needs_review"] += 1
                        elif status == "NOT_FOUND":
                            summary["not_found"] += 1
                        elif status == "OUT_OF_DOMAIN":
                            summary["out_of_domain"] += 1

                        if final_check_passed:
                            summary["final_check_passed"] += 1
                        else:
                            summary["final_check_failed"] += 1

                        if answer_mode and "DIRECT" in answer_mode:
                            summary["direct_lookup"] += 1
                        elif answer_mode == "THEMATIC_RETRIEVAL":
                            summary["thematic_retrieval"] += 1
                        elif answer_mode == "EVIDENCE_GROUNDED":
                            summary["evidence_grounded"] += 1
                        elif answer_mode == "METODE7_LLM_FIRST":
                            summary["metode7"] += 1

                        file_handle.write("=" * 90 + "\n")
                        file_handle.write(
                            f"TEST CASE #{case_number}\n"
                        )
                        file_handle.write("=" * 90 + "\n\n")

                        file_handle.write("PERTANYAAN\n")
                        file_handle.write("-" * 40 + "\n")
                        file_handle.write(f"{question}\n\n")

                        file_handle.write("INTENT\n")
                        file_handle.write("-" * 40 + "\n")
                        file_handle.write(
                            f"Intent     : {intent_name}\n"
                        )
                        file_handle.write(
                            f"Confidence : {intent_confidence}\n"
                        )
                        file_handle.write(
                            f"Route      : {route}\n"
                        )

                        if reason:
                            file_handle.write(
                                f"Reason     : {reason}\n"
                            )

                        if blocked_reason:
                            file_handle.write(
                                f"Blocked    : {blocked_reason}\n"
                            )

                        if signals:
                            file_handle.write(
                                f"Signals    : {signals}\n"
                            )

                        file_handle.write("\n")

                        file_handle.write("PIPELINE\n")
                        file_handle.write("-" * 40 + "\n")
                        file_handle.write(
                            f"Answer Mode         : {answer_mode}\n"
                        )
                        file_handle.write(
                            f"Composer            : {composer}\n"
                        )
                        file_handle.write(
                            f"Verification Status : {status}\n"
                        )
                        file_handle.write(
                            f"Final Check Passed  : "
                            f"{final_check_passed}\n"
                        )
                        if retrieval_debug:
                            file_handle.write(
                                f"Retrieval Theme      : "
                                f"{retrieval_debug.get('theme')}\n"
                            )
                            file_handle.write(
                                f"Source Preference    : "
                                f"{retrieval_debug.get('source_preference')}\n"
                            )
                            file_handle.write(
                                f"Quran Results        : "
                                f"{retrieval_debug.get('quran_count')}\n"
                            )
                            file_handle.write(
                                f"Hadith Results       : "
                                f"{retrieval_debug.get('hadith_count')}\n"
                            )
                        file_handle.write(
                            f"Process Time        : "
                            f"{elapsed:.2f} detik\n\n"
                        )

                        file_handle.write("FINAL CHECK WARNINGS\n")
                        file_handle.write("-" * 40 + "\n")

                        if warnings:
                            for warning in warnings:
                                file_handle.write(
                                    f"- {warning.get('code')}: "
                                    f"{warning.get('message')}\n"
                                )
                        else:
                            file_handle.write(
                                "(Tidak ada warning)\n"
                            )

                        file_handle.write("\n")

                        file_handle.write("VERIFIED SOURCES\n")
                        file_handle.write("-" * 40 + "\n")
                        write_sources(
                            file_handle,
                            sources,
                            include_content=True,
                        )
                        file_handle.write("\n")

                        file_handle.write(
                            "AI NARRATION / FINAL REPLY\n"
                        )
                        file_handle.write("-" * 40 + "\n")
                        file_handle.write(
                            reply or "(Tidak ada reply)"
                        )
                        file_handle.write("\n\n")
                        file_handle.write("=" * 90 + "\n\n")

                        if should_add_to_review(
                            status=status,
                            final_check_passed=final_check_passed,
                            warnings=warnings,
                        ):
                            review_cases.append({
                                "case_number": case_number,
                                "group": group["name"],
                                "question": question,
                                "intent": intent_name,
                                "intent_confidence": intent_confidence,
                                "route": route,
                                "reason": reason,
                                "blocked_reason": blocked_reason,
                                "answer_mode": answer_mode,
                                "composer": composer,
                                "status": status,
                                "final_check_passed": (
                                    final_check_passed
                                ),
                                "warnings": warnings,
                                "sources": sources,
                                "reply": reply,
                                "process_time": elapsed,
                            })

                    except Exception as exc:
                        elapsed = time.time() - start_time

                        summary["total"] += 1
                        summary["errors"] += 1
                        summary["final_check_failed"] += 1

                        error_message = str(exc)

                        file_handle.write("=" * 90 + "\n")
                        file_handle.write(
                            f"TEST CASE #{case_number} ERROR\n"
                        )
                        file_handle.write("=" * 90 + "\n\n")
                        file_handle.write(
                            f"PERTANYAAN: {question}\n"
                        )
                        file_handle.write(
                            f"ERROR: {error_message}\n"
                        )
                        file_handle.write(
                            f"Process Time: {elapsed:.2f} detik\n\n"
                        )

                        review_cases.append({
                            "case_number": case_number,
                            "group": group["name"],
                            "question": question,
                            "intent": None,
                            "intent_confidence": None,
                            "route": None,
                            "reason": None,
                            "blocked_reason": None,
                            "answer_mode": None,
                            "composer": None,
                            "status": "ERROR",
                            "final_check_passed": False,
                            "warnings": [
                                {
                                    "code": "BENCHMARK_ERROR",
                                    "message": error_message,
                                }
                            ],
                            "sources": [],
                            "reply": "",
                            "process_time": elapsed,
                        })

                    case_number += 1

                    if case_number <= total_cases:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⏳ Menunggu {delay_seconds} detik "
                                f"sebelum test berikutnya..."
                            )
                        )
                        time.sleep(delay_seconds)

            # =====================================================
            # SUMMARY
            # =====================================================

            file_handle.write("\n" + "=" * 90 + "\n")
            file_handle.write("📊 SUMMARY\n")
            file_handle.write("=" * 90 + "\n")

            for key, value in summary.items():
                file_handle.write(f"{key}: {value}\n")

            if summary["total"] > 0:
                total = summary["total"]

                file_handle.write("\n")
                file_handle.write(
                    f"HIGH_CONFIDENCE rate : "
                    f"{summary['high_confidence'] / total * 100:.2f}%\n"
                )
                file_handle.write(
                    f"NEEDS_REVIEW rate    : "
                    f"{summary['needs_review'] / total * 100:.2f}%\n"
                )
                file_handle.write(
                    f"NOT_FOUND rate       : "
                    f"{summary['not_found'] / total * 100:.2f}%\n"
                )
                file_handle.write(
                    f"OUT_OF_DOMAIN rate   : "
                    f"{summary['out_of_domain'] / total * 100:.2f}%\n"
                )
                file_handle.write(
                    f"Final Check Pass rate: "
                    f"{summary['final_check_passed'] / total * 100:.2f}%\n"
                )
                file_handle.write(
                    f"Error rate           : "
                    f"{summary['errors'] / total * 100:.2f}%\n"
                )

            # =====================================================
            # REVIEW PAYLOAD
            # =====================================================

            file_handle.write("\n\n")
            file_handle.write("=" * 90 + "\n")
            file_handle.write(
                "🔎 REVIEW PAYLOAD FOR AI ANALYSIS\n"
            )
            file_handle.write("=" * 90 + "\n")
            file_handle.write(
                "Bagian ini hanya berisi kasus yang memerlukan "
                "analisis lebih lanjut: NEEDS_REVIEW, final check gagal, "
                "warning, atau error.\n"
            )
            file_handle.write(
                f"Total review cases: {len(review_cases)}\n"
            )
            file_handle.write("=" * 90 + "\n\n")

            if not review_cases:
                file_handle.write(
                    "Tidak ada kasus yang memerlukan review.\n"
                )
            else:
                for item in review_cases:
                    file_handle.write("-" * 90 + "\n")
                    file_handle.write(
                        f"REVIEW CASE #{item['case_number']} | "
                        f"GROUP: {item['group']}\n"
                    )
                    file_handle.write("-" * 90 + "\n")

                    file_handle.write(
                        f"PERTANYAAN: {item['question']}\n"
                    )
                    file_handle.write(
                        f"INTENT: {item['intent']}\n"
                    )
                    file_handle.write(
                        f"INTENT CONFIDENCE: "
                        f"{item['intent_confidence']}\n"
                    )
                    file_handle.write(
                        f"ROUTE: {item['route']}\n"
                    )

                    if item.get("reason"):
                        file_handle.write(
                            f"REASON: {item['reason']}\n"
                        )

                    if item.get("blocked_reason"):
                        file_handle.write(
                            f"BLOCKED REASON: "
                            f"{item['blocked_reason']}\n"
                        )

                    file_handle.write(
                        f"ANSWER MODE: {item['answer_mode']}\n"
                    )
                    file_handle.write(
                        f"COMPOSER: {item['composer']}\n"
                    )
                    file_handle.write(
                        f"STATUS: {item['status']}\n"
                    )
                    file_handle.write(
                        f"FINAL CHECK PASSED: "
                        f"{item['final_check_passed']}\n"
                    )
                    file_handle.write(
                        f"PROCESS TIME: "
                        f"{item['process_time']:.2f} detik\n"
                    )

                    file_handle.write("\nWARNINGS:\n")

                    if item["warnings"]:
                        for warning in item["warnings"]:
                            file_handle.write(
                                f"- {warning.get('code')}: "
                                f"{warning.get('message')}\n"
                            )
                    else:
                        file_handle.write(
                            "- Tidak ada warning\n"
                        )

                    file_handle.write("\nSOURCES:\n")
                    write_sources(
                        file_handle,
                        item["sources"],
                        include_content=False,
                    )

                    file_handle.write("\nFINAL REPLY:\n")
                    file_handle.write(
                        item["reply"] or "(Tidak ada reply)"
                    )
                    file_handle.write("\n\n")

        self.stdout.write(
            self.style.SUCCESS(
                f"Benchmark selesai. Hasil disimpan di: {output_file}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Untuk dikirim ke analisis, copy bagian "
                "'REVIEW PAYLOAD FOR AI ANALYSIS' sampai akhir file."
            )
        )
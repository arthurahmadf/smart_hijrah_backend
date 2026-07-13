# main/management/commands/test_smart_ai_naturalness.py

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from django.core.management.base import BaseCommand, CommandError

from main.utils_rag.answer_strategy import select_answer_strategy
from main.utils_rag.evidence_composer import (
    compose_evidence_grounded_answer,
    compose_thematic_retrieval_answer,
)
from main.utils_rag.final_checker import apply_final_checks
from main.utils_rag.followup_compression import (
    ASPECT_DOA,
    ASPECT_EXAMPLE,
    ASPECT_HADITH,
    ASPECT_PRACTICAL,
    ASPECT_QURAN,
    ASPECT_REASON,
    ASPECT_SUMMARY,
    build_followup_policy,
)


@dataclass
class BenchmarkResult:
    name: str
    failures: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.failures


class Command(BaseCommand):
    """
    Phase 5A.5 — Naturalness Benchmark & Regression.

    Command ini sengaja deterministik:
    - tidak memanggil LLM,
    - tidak melakukan query database,
    - tidak membutuhkan conversation record,
    - menguji output composer dan follow-up policy secara langsung.
    """

    help = (
        "Menguji naturalness, source focus, repetition control, "
        "topic refinement, dan context isolation Smart AI Phase 5A.5."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--show-replies",
            action="store_true",
            help="Tampilkan reply setiap case, termasuk case yang PASS.",
        )
        parser.add_argument(
            "--fail-fast",
            action="store_true",
            help="Hentikan benchmark pada kegagalan pertama.",
        )
        parser.add_argument(
            "--no-strict",
            action="store_true",
            help=(
                "Jangan mengembalikan exit code gagal ketika ada case FAIL."
            ),
        )

    def handle(self, *args, **options):
        self.show_replies = bool(options.get("show_replies"))
        self.fail_fast = bool(options.get("fail_fast"))
        self.strict = not bool(options.get("no_strict"))

        cases: list[Callable[[], BenchmarkResult]] = [
            self._case_hadith_source_switch,
            self._case_quran_source_switch,
            self._case_reason_without_repetition,
            self._case_example_is_concise,
            self._case_summary_is_very_short,
            self._case_practical_steps_are_limited,
            self._case_doa_only_followup,
            self._case_topic_refinement_keeps_context,
            self._case_new_topic_has_no_context_leak,
            self._case_followup_has_no_repeated_opening,
            self._case_previous_answer_deduplication,
            self._case_no_internal_metadata_leak,
            self._case_thematic_hadith_followup,
            self._case_final_checker_stays_clean,
        ]

        results: list[BenchmarkResult] = []

        self.stdout.write("")
        self.stdout.write("=" * 96)
        self.stdout.write("SMART AI — PHASE 5A.5 NATURALNESS BENCHMARK")
        self.stdout.write("=" * 96)
        self.stdout.write(
            "Mode: deterministic composer regression (tanpa LLM dan database)"
        )
        self.stdout.write("")

        for index, case in enumerate(cases, start=1):
            try:
                result = case()
            except Exception as exc:
                result = BenchmarkResult(
                    name=getattr(case, "__name__", f"CASE_{index}")
                    .replace("_case_", "")
                    .upper(),
                    failures=[
                        f"Unhandled error: {exc.__class__.__name__}: {exc}"
                    ],
                )

            results.append(result)
            self._print_result(index=index, result=result)

            if self.fail_fast and not result.passed:
                break

        total = len(results)
        passed = sum(1 for result in results if result.passed)
        failed = total - passed
        pass_rate = passed / total * 100 if total else 0.0

        self.stdout.write("")
        self.stdout.write("=" * 96)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 96)
        self.stdout.write(f"total     : {total}")
        self.stdout.write(self.style.SUCCESS(f"passed    : {passed}"))

        failed_style = self.style.ERROR if failed else self.style.SUCCESS
        self.stdout.write(failed_style(f"failed    : {failed}"))
        self.stdout.write(f"pass rate : {pass_rate:.2f}%")

        if failed:
            self.stdout.write("")
            self.stdout.write("FAILED CASES:")

            for result in results:
                if result.passed:
                    continue
                self.stdout.write(
                    self.style.ERROR(f"- {result.name}: {result.failures}")
                )

            if self.strict:
                raise CommandError(
                    f"Naturalness benchmark gagal: {failed}/{total} case."
                )

    # ========================================================
    # FIXTURES
    # ========================================================

    @staticmethod
    def _quran_source(
        reference: str = "QS. Al-Baqarah (2): 153",
    ) -> dict[str, Any]:
        return {
            "type": "QURAN",
            "reference": reference,
            "surah_number": 2,
            "ayah_number": 153,
            "translation_text": (
                "Sesungguhnya Allah bersama orang-orang yang sabar."
            ),
            "is_verified": True,
        }

    @staticmethod
    def _hadith_source(
        reference: str = "HR. Muslim No. 2999",
    ) -> dict[str, Any]:
        return {
            "type": "HADIS",
            "reference": reference,
            "book_slug": "muslim",
            "number": 2999,
            "translation_text": (
                "Sungguh menakjubkan keadaan seorang mukmin."
            ),
            "is_verified": True,
        }

    @staticmethod
    def _external_source() -> dict[str, Any]:
        return {
            "type": "EKSTERNAL",
            "reference": "Fatwa DSN-MUI yang relevan",
            "is_verified": True,
        }

    @staticmethod
    def _context(
        relation: str,
        previous_summary: str = "",
    ) -> dict[str, Any]:
        context: dict[str, Any] = {
            "conversation_relation": relation,
            "topic_changed": relation == "NEW_TOPIC",
        }

        if previous_summary:
            context["previous_topic"] = {
                "summary": previous_summary,
                "label": previous_summary,
            }

        return context

    def _strategy_and_policy(
        self,
        *,
        intent: str,
        relation: str,
        user_message: str,
        verified_sources: list[dict[str, Any]] | None = None,
        previous_summary: str = "",
    ):
        context = self._context(
            relation=relation,
            previous_summary=previous_summary,
        )

        strategy = select_answer_strategy(
            intent=intent,
            conversation_context=context,
            verified_sources=verified_sources or [],
        )

        policy = build_followup_policy(
            user_message=user_message,
            strategy=strategy,
            conversation_context=context,
        )

        return context, strategy, policy

    def _compose(
        self,
        *,
        user_message: str,
        intent: str,
        relation: str,
        draft_text: str,
        sources: list[dict[str, Any]] | None = None,
        previous_assistant_text: str = "",
        previous_summary: str = "",
        is_first_message: bool = False,
        status_global: str = "HIGH_CONFIDENCE",
    ) -> dict[str, Any]:
        verified_sources = sources or []

        context, strategy, policy = self._strategy_and_policy(
            intent=intent,
            relation=relation,
            user_message=user_message,
            verified_sources=verified_sources,
            previous_summary=previous_summary,
        )

        return compose_evidence_grounded_answer(
            user_query=user_message,
            intent_result={"intent": intent},
            draft_text=draft_text,
            verified_sources=verified_sources,
            status_global=status_global,
            is_first_message=is_first_message,
            conversation_context=context,
            strategy=strategy,
            followup_policy=policy,
            previous_assistant_text=previous_assistant_text,
        )

    # ========================================================
    # ASSERTION HELPERS
    # ========================================================

    @staticmethod
    def _normalized(text: str | None) -> str:
        normalized = (text or "").lower()
        normalized = re.sub(r"[*_`>#]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    @staticmethod
    def _count_numbered_items(text: str) -> int:
        return sum(
            1
            for line in (text or "").splitlines()
            if re.match(r"^\s*\d+[.)]\s+", line)
        )

    @staticmethod
    def _source_types(
        sources: list[dict[str, Any]] | None,
    ) -> list[str]:
        result: list[str] = []

        for source in sources or []:
            source_type = str(source.get("type", "")).upper()
            if source_type == "HADITH":
                source_type = "HADIS"
            result.append(source_type)

        return result

    def _expect_not_contains(
        self,
        failures: list[str],
        text: str,
        fragments: list[str],
    ):
        normalized = self._normalized(text)

        for fragment in fragments:
            if self._normalized(fragment) in normalized:
                failures.append(f"Unexpected fragment: {fragment}")

    def _expect_contains(
        self,
        failures: list[str],
        text: str,
        fragments: list[str],
    ):
        normalized = self._normalized(text)

        for fragment in fragments:
            if self._normalized(fragment) not in normalized:
                failures.append(f"Missing fragment: {fragment}")

    # ========================================================
    # BENCHMARK CASES
    # ========================================================

    def _case_hadith_source_switch(self) -> BenchmarkResult:
        result = self._compose(
            user_message="hadisnya ada?",
            intent="THEMATIC_DALIL_SEARCH",
            relation="FOLLOW_UP",
            draft_text=(
                "Hadis yang relevan menjelaskan bahwa keadaan "
                "seorang mukmin selalu memiliki kebaikan."
            ),
            sources=[self._quran_source(), self._hadith_source()],
            previous_assistant_text=(
                "Sabar diperintahkan dalam Al-Qur’an dan dijelaskan "
                "pula dalam hadis."
            ),
        )

        failures: list[str] = []
        reply = result["reply"]
        source_types = self._source_types(result.get("displayed_sources"))

        if source_types != ["HADIS"]:
            failures.append(
                "Displayed sources harus hanya HADIS, "
                f"actual={source_types}."
            )

        if result["followup_policy"]["requested_aspect"] != ASPECT_HADITH:
            failures.append("Follow-up aspect bukan HADITH.")

        self._expect_not_contains(
            failures,
            reply,
            ["Dalil Al-Qur’an yang terverifikasi", "Assalamu’alaikum"],
        )

        return BenchmarkResult(
            name="HADITH_SOURCE_SWITCH",
            failures=failures,
            payload=result,
        )

    def _case_quran_source_switch(self) -> BenchmarkResult:
        result = self._compose(
            user_message="ayatnya?",
            intent="THEMATIC_DALIL_SEARCH",
            relation="FOLLOW_UP",
            draft_text=(
                "Ayat tersebut memerintahkan orang beriman meminta "
                "pertolongan melalui sabar dan shalat."
            ),
            sources=[self._quran_source(), self._hadith_source()],
        )

        failures: list[str] = []
        reply = result["reply"]
        source_types = self._source_types(result.get("displayed_sources"))

        if source_types != ["QURAN"]:
            failures.append(
                "Displayed sources harus hanya QURAN, "
                f"actual={source_types}."
            )

        if result["followup_policy"]["requested_aspect"] != ASPECT_QURAN:
            failures.append("Follow-up aspect bukan QURAN.")

        self._expect_not_contains(
            failures,
            reply,
            ["Hadis yang ditemukan dalam database", "Assalamu’alaikum"],
        )

        return BenchmarkResult(
            name="QURAN_SOURCE_SWITCH",
            failures=failures,
            payload=result,
        )

    def _case_reason_without_repetition(self) -> BenchmarkResult:
        previous = (
            "Paylater dapat bermasalah jika mengandung riba. "
            "Hukumnya bergantung pada akad dan biaya yang digunakan."
        )

        result = self._compose(
            user_message="kenapa?",
            intent="FATWA_QA",
            relation="FOLLOW_UP",
            draft_text=(
                "Paylater dapat bermasalah jika mengandung riba. "
                "Alasannya, tambahan yang lahir semata-mata karena "
                "penundaan pembayaran dapat menjadi tambahan atas utang."
            ),
            sources=[self._quran_source("QS. Al-Baqarah (2): 275")],
            previous_assistant_text=previous,
        )

        failures: list[str] = []
        reply = result["reply"]

        if result["followup_policy"]["requested_aspect"] != ASPECT_REASON:
            failures.append("Follow-up aspect bukan REASON.")

        self._expect_not_contains(
            failures,
            reply,
            [
                "Paylater dapat bermasalah jika mengandung riba",
                "Dalil Al-Qur’an yang terverifikasi",
                "Catatan fatwa",
                "Hal yang perlu diperiksa",
            ],
        )
        self._expect_contains(failures, reply, ["tambahan", "utang"])

        return BenchmarkResult(
            name="REASON_WITHOUT_REPETITION",
            failures=failures,
            payload=result,
        )

    def _case_example_is_concise(self) -> BenchmarkResult:
        result = self._compose(
            user_message="contohnya?",
            intent="FIQH_QA",
            relation="FOLLOW_UP",
            draft_text=(
                "Contoh:\n"
                "1. Biaya layanan tetap yang diketahui sejak awal.\n"
                "2. Tambahan yang meningkat karena terlambat membayar.\n"
                "3. Biaya tersembunyi yang baru muncul setelah transaksi.\n"
                "4. Denda yang menjadi keuntungan pemberi pembiayaan."
            ),
        )

        failures: list[str] = []
        reply = result["reply"]

        if result["followup_policy"]["requested_aspect"] != ASPECT_EXAMPLE:
            failures.append("Follow-up aspect bukan EXAMPLE.")

        item_count = self._count_numbered_items(reply)
        if item_count > 2:
            failures.append(
                f"Contoh melebihi dua item, actual={item_count}."
            )

        self._expect_not_contains(
            failures,
            reply,
            ["3. Biaya tersembunyi", "4. Denda", "Catatan kehati-hatian"],
        )

        return BenchmarkResult(
            name="EXAMPLE_IS_CONCISE",
            failures=failures,
            payload=result,
        )

    def _case_summary_is_very_short(self) -> BenchmarkResult:
        result = self._compose(
            user_message="singkatnya gimana?",
            intent="FIQH_QA",
            relation="FOLLOW_UP",
            draft_text=(
                "**Jawaban ringkas:**\n"
                "Pada dasarnya hukumnya bergantung pada akad. "
                "Jika terdapat tambahan atas utang karena waktu, hal itu "
                "perlu dihindari. Jika biaya tetap transparan dan benar-benar "
                "merupakan imbalan jasa yang sah, penilaiannya berbeda."
            ),
        )

        failures: list[str] = []
        reply = result["reply"]

        if result["followup_policy"]["requested_aspect"] != ASPECT_SUMMARY:
            failures.append("Follow-up aspect bukan SUMMARY.")

        if len(reply) > 800:
            failures.append(f"Summary terlalu panjang, chars={len(reply)}.")

        self._expect_not_contains(
            failures,
            reply,
            [
                "Jawaban ringkas:",
                "Dalil Al-Qur’an",
                "Hadis yang ditemukan",
                "Catatan kehati-hatian",
            ],
        )

        return BenchmarkResult(
            name="SUMMARY_IS_VERY_SHORT",
            failures=failures,
            payload=result,
        )

    def _case_practical_steps_are_limited(self) -> BenchmarkResult:
        result = self._compose(
            user_message="langkah praktisnya gimana?",
            intent="SPIRITUAL_ADVICE",
            relation="FOLLOW_UP",
            draft_text=(
                "Mulailah dari langkah sederhana yang dapat dilakukan "
                "secara konsisten."
            ),
        )

        failures: list[str] = []
        reply = result["reply"]

        if result["followup_policy"]["requested_aspect"] != ASPECT_PRACTICAL:
            failures.append("Follow-up aspect bukan PRACTICAL.")

        item_count = self._count_numbered_items(reply)
        if item_count > 4:
            failures.append(
                f"Langkah praktis melebihi empat item, actual={item_count}."
            )

        self._expect_contains(failures, reply, ["Langkah praktis"])
        self._expect_not_contains(
            failures,
            reply,
            ["Doa singkat", "Assalamu’alaikum"],
        )

        return BenchmarkResult(
            name="PRACTICAL_STEPS_ARE_LIMITED",
            failures=failures,
            payload=result,
        )

    def _case_doa_only_followup(self) -> BenchmarkResult:
        result = self._compose(
            user_message="ada doa yang bisa kubaca?",
            intent="SPIRITUAL_ADVICE",
            relation="FOLLOW_UP",
            draft_text=(
                "Mohonlah kepada Allah agar diberi keteguhan dan "
                "kemudahan untuk menjaga ketaatan."
            ),
        )

        failures: list[str] = []
        reply = result["reply"]

        if result["followup_policy"]["requested_aspect"] != ASPECT_DOA:
            failures.append("Follow-up aspect bukan DOA.")

        self._expect_contains(failures, reply, ["Doa singkat", "Ya Allah"])
        self._expect_not_contains(
            failures,
            reply,
            ["Langkah praktis", "Assalamu’alaikum"],
        )

        return BenchmarkResult(
            name="DOA_ONLY_FOLLOWUP",
            failures=failures,
            payload=result,
        )

    def _case_topic_refinement_keeps_context(self) -> BenchmarkResult:
        result = self._compose(
            user_message="kalau biaya layanannya tetap dan diketahui dari awal?",
            intent="FATWA_QA",
            relation="TOPIC_REFINEMENT",
            draft_text=(
                "Biaya layanan tetap tidak otomatis menjadi riba. Perlu "
                "diperiksa apakah biaya itu benar-benar imbalan atas jasa "
                "yang nyata, transparan, dan tidak berubah karena lamanya "
                "penundaan."
            ),
            sources=[self._external_source()],
            previous_summary="hukum paylater",
        )

        failures: list[str] = []
        reply = result["reply"]

        self._expect_contains(
            failures,
            reply,
            [
                "Terkait pembahasan sebelumnya",
                "hukum paylater",
                "biaya layanan tetap",
            ],
        )

        if result["followup_policy"]["include_context_reference"] is not True:
            failures.append(
                "Topic refinement harus membawa context reference."
            )

        self._expect_not_contains(failures, reply, ["Assalamu’alaikum"])

        return BenchmarkResult(
            name="TOPIC_REFINEMENT_KEEPS_CONTEXT",
            failures=failures,
            payload=result,
        )

    def _case_new_topic_has_no_context_leak(self) -> BenchmarkResult:
        result = self._compose(
            user_message="Apa keutamaan puasa Senin Kamis?",
            intent="GENERAL_ISLAMIC_QA",
            relation="NEW_TOPIC",
            draft_text=(
                "Puasa Senin dan Kamis termasuk amalan sunnah yang dianjurkan."
            ),
            previous_assistant_text=(
                "Paylater perlu diperiksa dari sisi riba, denda, dan akad."
            ),
            previous_summary="hukum paylater",
            is_first_message=False,
        )

        failures: list[str] = []
        reply = result["reply"]

        if result["followup_policy"]["enabled"]:
            failures.append("NEW_TOPIC tidak boleh mengaktifkan compression.")

        self._expect_not_contains(
            failures,
            reply,
            ["paylater", "riba", "Terkait pembahasan sebelumnya"],
        )
        self._expect_contains(failures, reply, ["Puasa Senin dan Kamis"])

        return BenchmarkResult(
            name="NEW_TOPIC_HAS_NO_CONTEXT_LEAK",
            failures=failures,
            payload=result,
        )

    def _case_followup_has_no_repeated_opening(self) -> BenchmarkResult:
        result = self._compose(
            user_message="kenapa?",
            intent="FIQH_QA",
            relation="FOLLOW_UP",
            draft_text=(
                "Assalamu'alaikum warahmatullahi wabarakatuh.\n\n"
                "Saya Smart Hijrah Assistant.\n\n"
                "Alasannya karena syariat melarang kezaliman."
            ),
        )

        failures: list[str] = []
        reply = result["reply"]

        self._expect_not_contains(
            failures,
            reply,
            ["Assalamu", "Smart Hijrah Assistant"],
        )
        self._expect_contains(failures, reply, ["kezaliman"])

        return BenchmarkResult(
            name="FOLLOWUP_HAS_NO_REPEATED_OPENING",
            failures=failures,
            payload=result,
        )

    def _case_previous_answer_deduplication(self) -> BenchmarkResult:
        previous = (
            "Investasi pada dasarnya boleh jika objek dan mekanismenya halal."
        )

        result = self._compose(
            user_message="kenapa?",
            intent="FATWA_QA",
            relation="FOLLOW_UP",
            draft_text=(
                "Investasi pada dasarnya boleh jika objek dan mekanismenya "
                "halal. Alasannya, hukum asal muamalah adalah boleh selama "
                "tidak ada unsur yang dilarang."
            ),
            previous_assistant_text=previous,
        )

        failures: list[str] = []
        reply = result["reply"]

        self._expect_not_contains(
            failures,
            reply,
            ["Investasi pada dasarnya boleh jika objek dan mekanismenya halal"],
        )
        self._expect_contains(failures, reply, ["hukum asal muamalah"])

        return BenchmarkResult(
            name="PREVIOUS_ANSWER_DEDUPLICATION",
            failures=failures,
            payload=result,
        )

    def _case_no_internal_metadata_leak(self) -> BenchmarkResult:
        result = self._compose(
            user_message="singkatnya?",
            intent="FIQH_QA",
            relation="FOLLOW_UP",
            draft_text="Hukumnya bergantung pada detail praktiknya.",
        )

        failures: list[str] = []
        reply = result["reply"]

        forbidden = [
            "conversation_relation",
            "resolved_query",
            "followup_policy",
            "answer_strategy",
            "reasoning_codes",
            "ASPECT_SUMMARY",
            "NATURAL_FOLLOWUP_COMPOSER_V1",
            "[DALIL_START]",
            "[DALIL_END]",
        ]
        self._expect_not_contains(failures, reply, forbidden)

        return BenchmarkResult(
            name="NO_INTERNAL_METADATA_LEAK",
            failures=failures,
            payload=result,
        )

    def _case_thematic_hadith_followup(self) -> BenchmarkResult:
        sources = [self._quran_source(), self._hadith_source()]

        context, strategy, policy = self._strategy_and_policy(
            intent="THEMATIC_DALIL_SEARCH",
            relation="FOLLOW_UP",
            user_message="hadisnya ada?",
            verified_sources=sources,
            previous_summary="dalil tentang sabar",
        )

        result = compose_thematic_retrieval_answer(
            user_query="dalil tentang sabar",
            intent_result={"intent": "THEMATIC_DALIL_SEARCH"},
            retrieval_result={
                "theme": "sabar",
                "source_preference": "both",
                "verified_sources": sources,
            },
            is_first_message=False,
            conversation_context=context,
            strategy=strategy,
            followup_policy=policy,
            previous_assistant_text="",
        )

        failures: list[str] = []
        reply = result["reply"]
        source_types = self._source_types(result.get("displayed_sources"))

        if source_types != ["HADIS"]:
            failures.append(
                "Thematic follow-up harus hanya menampilkan HADIS, "
                f"actual={source_types}."
            )

        self._expect_contains(failures, reply, ["hadis"])
        self._expect_not_contains(
            failures,
            reply,
            [
                "Dalil Al-Qur’an yang terverifikasi",
                "bukan daftar lengkap",
                "Assalamu’alaikum",
            ],
        )

        return BenchmarkResult(
            name="THEMATIC_HADITH_FOLLOWUP",
            failures=failures,
            payload=result,
        )

    def _case_final_checker_stays_clean(self) -> BenchmarkResult:
        sources = [self._quran_source(), self._hadith_source()]

        result = self._compose(
            user_message="singkatnya?",
            intent="GENERAL_ISLAMIC_QA",
            relation="FOLLOW_UP",
            draft_text="Intinya, sabar perlu disertai ikhtiar dan doa.",
            sources=sources,
        )

        final_check = apply_final_checks(
            reply=result.get("narrative_text", ""),
            verified_sources=result.get("verified_sources", []),
            status_global=result.get("verification_status", "NEEDS_REVIEW"),
        )

        failures: list[str] = []

        if not final_check["final_check_passed"]:
            failures.append(
                f"Final checker gagal: {final_check['final_check_warnings']}"
            )

        if final_check["final_check_warnings"]:
            failures.append(
                "Final checker menghasilkan warning: "
                f"{final_check['final_check_warnings']}"
            )

        return BenchmarkResult(
            name="FINAL_CHECKER_STAYS_CLEAN",
            failures=failures,
            payload={
                "composer_result": result,
                "final_check": final_check,
            },
        )

    # ========================================================
    # OUTPUT
    # ========================================================

    def _print_result(
        self,
        *,
        index: int,
        result: BenchmarkResult,
    ):
        status = (
            self.style.SUCCESS("PASS")
            if result.passed
            else self.style.ERROR("FAIL")
        )

        self.stdout.write(f"[{index:02d}] {result.name}: {status}")

        for failure in result.failures:
            self.stdout.write(self.style.ERROR(f"     - {failure}"))

        if self.show_replies or not result.passed:
            reply = self._extract_reply(result.payload)

            if reply:
                self.stdout.write("     Reply:")
                for line in reply.splitlines():
                    self.stdout.write(f"       {line}")

    @staticmethod
    def _extract_reply(payload: dict[str, Any]) -> str:
        if not payload:
            return ""

        if isinstance(payload.get("reply"), str):
            return payload["reply"]

        composer_result = payload.get("composer_result")
        if isinstance(composer_result, dict):
            return str(composer_result.get("reply", ""))

        return ""

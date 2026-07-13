# main/management/commands/test_smart_ai_strategy_prompt.py

from __future__ import annotations

from dataclasses import dataclass

from django.core.management.base import BaseCommand

from main.utils_rag.answer_strategy import (
    select_answer_strategy,
)
from main.utils_rag.answer_strategy_prompt import (
    build_answer_strategy_prompt,
)


@dataclass
class PromptTestCase:
    name: str
    intent: str
    relation: str
    expected_fragments: list[str]
    forbidden_fragments: list[str]


TEST_CASES = [
    PromptTestCase(
        name="FIQH_NEW_TOPIC",
        intent="FIQH_QA",
        relation="NEW_TOPIC",
        expected_fragments=[
            "Strategy: FIQH",
            "Jawab inti hukum terlebih dahulu",
            "prinsip umum syariat",
        ],
        forbidden_fragments=[
            "Ini adalah pertanyaan lanjutan",
        ],
    ),
    PromptTestCase(
        name="FIQH_FOLLOW_UP",
        intent="FIQH_QA",
        relation="FOLLOW_UP",
        expected_fragments=[
            "Strategy: FIQH",
            "Ini adalah pertanyaan lanjutan",
            "Jangan mengulang seluruh jawaban sebelumnya",
            "Jawab hanya aspek baru",
        ],
        forbidden_fragments=[],
    ),
    PromptTestCase(
        name="FATWA_NEW_TOPIC",
        intent="FATWA_QA",
        relation="NEW_TOPIC",
        expected_fragments=[
            "Strategy: FATWA",
            "nama produk atau kegiatan saja tidak cukup",
            "Jangan mengatasnamakan MUI",
        ],
        forbidden_fragments=[],
    ),
    PromptTestCase(
        name="SPIRITUAL_NEW_TOPIC",
        intent="SPIRITUAL_ADVICE",
        relation="NEW_TOPIC",
        expected_fragments=[
            "Strategy: SPIRITUAL",
            "Mulai dengan empati",
            "pintu taubat",
        ],
        forbidden_fragments=[],
    ),
    PromptTestCase(
        name="SPIRITUAL_FOLLOW_UP",
        intent="SPIRITUAL_ADVICE",
        relation="FOLLOW_UP",
        expected_fragments=[
            "Strategy: SPIRITUAL",
            "Ini adalah pertanyaan lanjutan",
            "Jangan mengulang salam",
        ],
        forbidden_fragments=[],
    ),
    PromptTestCase(
        name="THEMATIC",
        intent="THEMATIC_DALIL_SEARCH",
        relation="NEW_TOPIC",
        expected_fragments=[
            "Strategy: THEMATIC_DALIL",
            "Gunakan hanya ayat atau hadis",
            "bukan daftar lengkap",
        ],
        forbidden_fragments=[],
    ),
    PromptTestCase(
        name="DIRECT_LOOKUP",
        intent="DIRECT_HADITH_LOOKUP",
        relation="NEW_TOPIC",
        expected_fragments=[
            "Strategy: DIRECT_LOOKUP",
            "Jangan membuat penjelasan panjang",
            "Jangan mengarang sanad",
        ],
        forbidden_fragments=[],
    ),
    PromptTestCase(
        name="OUT_OF_DOMAIN",
        intent="OUT_OF_DOMAIN",
        relation="NEW_TOPIC",
        expected_fragments=[
            "Strategy: OUT_OF_DOMAIN",
            "berada di luar cakupan",
        ],
        forbidden_fragments=[],
    ),
]


class Command(BaseCommand):
    help = (
        "Menguji Strategy-Aware Prompt Builder Phase 5A.3."
    )

    def handle(self, *args, **options):
        total = len(TEST_CASES)
        passed = 0
        failed = 0

        self.stdout.write("")
        self.stdout.write("=" * 90)
        self.stdout.write(
            "SMART AI — STRATEGY PROMPT TEST"
        )
        self.stdout.write("=" * 90)

        for index, case in enumerate(
            TEST_CASES,
            start=1,
        ):
            context = {
                "conversation_relation": case.relation,
            }

            strategy = select_answer_strategy(
                intent=case.intent,
                conversation_context=context,
                verified_sources=[],
            )

            prompt = build_answer_strategy_prompt(
                strategy=strategy,
                conversation_context=context,
            )

            failures = []

            for fragment in case.expected_fragments:
                if fragment.lower() not in prompt.lower():
                    failures.append(
                        f"Missing fragment: {fragment}"
                    )

            for fragment in case.forbidden_fragments:
                if fragment.lower() in prompt.lower():
                    failures.append(
                        f"Forbidden fragment found: {fragment}"
                    )

            if failures:
                failed += 1
                status = self.style.ERROR("FAIL")
            else:
                passed += 1
                status = self.style.SUCCESS("PASS")

            self.stdout.write(
                f"[{index:02d}] {case.name}: {status}"
            )

            for failure in failures:
                self.stdout.write(
                    self.style.ERROR(
                        f"     - {failure}"
                    )
                )

        pass_rate = (
            passed / total * 100
            if total
            else 0
        )

        self.stdout.write("")
        self.stdout.write("=" * 90)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 90)
        self.stdout.write(f"total     : {total}")
        self.stdout.write(
            self.style.SUCCESS(
                f"passed    : {passed}"
            )
        )

        failed_style = (
            self.style.ERROR
            if failed
            else self.style.SUCCESS
        )

        self.stdout.write(
            failed_style(
                f"failed    : {failed}"
            )
        )
        self.stdout.write(
            f"pass rate : {pass_rate:.2f}%"
        )
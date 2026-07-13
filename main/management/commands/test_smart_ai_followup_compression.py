# main/management/commands/test_smart_ai_followup_compression.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.core.management.base import BaseCommand

from main.utils_rag.answer_strategy import (
    select_answer_strategy,
)
from main.utils_rag.followup_compression import (
    ASPECT_DALIL,
    ASPECT_DOA,
    ASPECT_EXAMPLE,
    ASPECT_HADITH,
    ASPECT_MUI,
    ASPECT_PRACTICAL,
    ASPECT_QURAN,
    ASPECT_REASON,
    ASPECT_SUMMARY,
    build_followup_policy,
    build_followup_prompt_instruction,
    compress_followup_draft,
    detect_requested_aspect,
    select_display_sources,
)


@dataclass
class PolicyCase:
    name: str
    message: str
    intent: str
    relation: str
    expected_aspect: str
    expected_enabled: bool
    expected_references: bool
    expected_practical: bool = False
    expected_doa: bool = False


POLICY_CASES = [
    PolicyCase(
        name="NEW_TOPIC_DISABLED",
        message="Apa hukum paylater?",
        intent="FATWA_QA",
        relation="NEW_TOPIC",
        expected_aspect="RULING",
        expected_enabled=False,
        expected_references=True,
    ),
    PolicyCase(
        name="HADITH_FOLLOW_UP",
        message="hadisnya ada?",
        intent="THEMATIC_DALIL_SEARCH",
        relation="FOLLOW_UP",
        expected_aspect=ASPECT_HADITH,
        expected_enabled=True,
        expected_references=True,
    ),
    PolicyCase(
        name="QURAN_FOLLOW_UP",
        message="ayatnya?",
        intent="THEMATIC_DALIL_SEARCH",
        relation="FOLLOW_UP",
        expected_aspect=ASPECT_QURAN,
        expected_enabled=True,
        expected_references=True,
    ),
    PolicyCase(
        name="DALIL_FOLLOW_UP",
        message="ada dalil lain?",
        intent="FIQH_QA",
        relation="FOLLOW_UP",
        expected_aspect=ASPECT_DALIL,
        expected_enabled=True,
        expected_references=True,
    ),
    PolicyCase(
        name="MUI_INFORMAL_FOLLOW_UP",
        message="klo mnrt mui?",
        intent="FATWA_QA",
        relation="FOLLOW_UP",
        expected_aspect=ASPECT_MUI,
        expected_enabled=True,
        expected_references=True,
    ),
    PolicyCase(
        name="REASON_FOLLOW_UP",
        message="kenapa?",
        intent="FIQH_QA",
        relation="FOLLOW_UP",
        expected_aspect=ASPECT_REASON,
        expected_enabled=True,
        expected_references=False,
    ),
    PolicyCase(
        name="EXAMPLE_FOLLOW_UP",
        message="contohnya?",
        intent="FIQH_QA",
        relation="FOLLOW_UP",
        expected_aspect=ASPECT_EXAMPLE,
        expected_enabled=True,
        expected_references=False,
    ),
    PolicyCase(
        name="PRACTICAL_FOLLOW_UP",
        message="langkah praktisnya gimana?",
        intent="SPIRITUAL_ADVICE",
        relation="FOLLOW_UP",
        expected_aspect=ASPECT_PRACTICAL,
        expected_enabled=True,
        expected_references=False,
        expected_practical=True,
    ),
    PolicyCase(
        name="DOA_FOLLOW_UP",
        message="ada doa yang bisa kubaca?",
        intent="SPIRITUAL_ADVICE",
        relation="FOLLOW_UP",
        expected_aspect=ASPECT_DOA,
        expected_enabled=True,
        expected_references=False,
        expected_doa=True,
    ),
    PolicyCase(
        name="SUMMARY_FOLLOW_UP",
        message="singkatnya gimana?",
        intent="FIQH_QA",
        relation="FOLLOW_UP",
        expected_aspect=ASPECT_SUMMARY,
        expected_enabled=True,
        expected_references=False,
    ),
]


class Command(BaseCommand):
    help = (
        "Menguji Natural Follow-Up Compression Phase 5A.4."
    )

    def handle(self, *args, **options):
        total = 0
        passed = 0
        failed = 0
        failed_cases: list[dict[str, Any]] = []

        self.stdout.write("")
        self.stdout.write("=" * 94)
        self.stdout.write(
            "SMART AI — NATURAL FOLLOW-UP COMPRESSION TEST"
        )
        self.stdout.write("=" * 94)

        for index, case in enumerate(
            POLICY_CASES,
            start=1,
        ):
            total += 1

            context = {
                "conversation_relation": case.relation,
            }

            strategy = select_answer_strategy(
                intent=case.intent,
                conversation_context=context,
                verified_sources=[],
            )

            policy = build_followup_policy(
                user_message=case.message,
                strategy=strategy,
                conversation_context=context,
            )

            failures = []

            if (
                policy.requested_aspect
                != case.expected_aspect
            ):
                failures.append(
                    (
                        "aspect: "
                        f"expected={case.expected_aspect}, "
                        f"actual={policy.requested_aspect}"
                    )
                )

            if (
                policy.enabled
                != case.expected_enabled
            ):
                failures.append(
                    (
                        "enabled: "
                        f"expected={case.expected_enabled}, "
                        f"actual={policy.enabled}"
                    )
                )

            if (
                policy.include_references
                != case.expected_references
            ):
                failures.append(
                    (
                        "include_references: "
                        f"expected={case.expected_references}, "
                        f"actual={policy.include_references}"
                    )
                )

            if (
                policy.include_practical_steps
                != case.expected_practical
            ):
                failures.append(
                    (
                        "include_practical_steps: "
                        f"expected={case.expected_practical}, "
                        f"actual={policy.include_practical_steps}"
                    )
                )

            if policy.include_doa != case.expected_doa:
                failures.append(
                    (
                        "include_doa: "
                        f"expected={case.expected_doa}, "
                        f"actual={policy.include_doa}"
                    )
                )

            self._record_case(
                index=index,
                name=case.name,
                failures=failures,
                payload=policy.to_dict(),
                failed_cases=failed_cases,
            )

            if failures:
                failed += 1
            else:
                passed += 1

        compression_results = [
            self._test_opening_removal(),
            self._test_previous_answer_deduplication(),
            self._test_list_limit(),
            self._test_source_filtering(),
            self._test_prompt_instruction(),
        ]

        for result in compression_results:
            total += 1
            index = total
            failures = result["failures"]

            self._record_case(
                index=index,
                name=result["name"],
                failures=failures,
                payload=result.get("payload", {}),
                failed_cases=failed_cases,
            )

            if failures:
                failed += 1
            else:
                passed += 1

        pass_rate = (
            passed / total * 100
            if total
            else 0
        )

        self.stdout.write("")
        self.stdout.write("=" * 94)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 94)
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

        if failed_cases:
            self.stdout.write("")
            self.stdout.write("FAILED CASES:")

            for case in failed_cases:
                self.stdout.write(
                    self.style.ERROR(
                        f"- {case['name']}: "
                        f"{case['failures']}"
                    )
                )

    def _record_case(
        self,
        index,
        name,
        failures,
        payload,
        failed_cases,
    ):
        if failures:
            status = self.style.ERROR("FAIL")
            failed_cases.append({
                "name": name,
                "failures": failures,
                "payload": payload,
            })
        else:
            status = self.style.SUCCESS("PASS")

        self.stdout.write(
            f"[{index:02d}] {name}: {status}"
        )

        for failure in failures:
            self.stdout.write(
                self.style.ERROR(
                    f"     - {failure}"
                )
            )

    def _build_policy(
        self,
        message,
        intent="FIQH_QA",
        relation="FOLLOW_UP",
    ):
        context = {
            "conversation_relation": relation,
        }

        strategy = select_answer_strategy(
            intent=intent,
            conversation_context=context,
            verified_sources=[],
        )

        return build_followup_policy(
            user_message=message,
            strategy=strategy,
            conversation_context=context,
        )

    def _test_opening_removal(self):
        policy = self._build_policy(
            "kenapa?"
        )

        draft = (
            "Assalamu'alaikum warahmatullahi wabarakatuh.\n\n"
            "Saya Smart Hijrah Assistant.\n\n"
            "**Jawaban ringkas:**\n"
            "Karena tindakan tersebut mengandung unsur kezaliman."
        )

        compressed = compress_followup_draft(
            draft_text=draft,
            previous_assistant_text="",
            policy=policy,
        )

        failures = []

        if "assalamu" in compressed.lower():
            failures.append(
                "Salam belum dihapus."
            )

        if "smart hijrah assistant" in compressed.lower():
            failures.append(
                "Perkenalan belum dihapus."
            )

        if "jawaban ringkas" in compressed.lower():
            failures.append(
                "Heading generik belum dihapus."
            )

        return {
            "name": "OPENING_AND_HEADING_REMOVAL",
            "failures": failures,
            "payload": {
                "compressed": compressed,
            },
        }

    def _test_previous_answer_deduplication(self):
        policy = self._build_policy(
            "kenapa?"
        )

        previous = (
            "Paylater dapat bermasalah jika mengandung riba. "
            "Hukumnya bergantung pada akad yang digunakan."
        )

        draft = (
            "Paylater dapat bermasalah jika mengandung riba. "
            "Alasannya, tambahan atas utang berbasis waktu "
            "termasuk unsur yang perlu dihindari."
        )

        compressed = compress_followup_draft(
            draft_text=draft,
            previous_assistant_text=previous,
            policy=policy,
        )

        failures = []

        if (
            "paylater dapat bermasalah jika mengandung riba"
            in compressed.lower()
        ):
            failures.append(
                "Kalimat lama belum dihapus."
            )

        if "alasannya" not in compressed.lower():
            failures.append(
                "Informasi baru ikut terhapus."
            )

        return {
            "name": "PREVIOUS_ANSWER_DEDUPLICATION",
            "failures": failures,
            "payload": {
                "compressed": compressed,
            },
        }

    def _test_list_limit(self):
        policy = self._build_policy(
            "contohnya?"
        )

        draft = (
            "Contoh:\n"
            "1. Contoh pertama.\n"
            "2. Contoh kedua.\n"
            "3. Contoh ketiga.\n"
            "4. Contoh keempat."
        )

        compressed = compress_followup_draft(
            draft_text=draft,
            previous_assistant_text="",
            policy=policy,
        )

        failures = []

        if "3. Contoh ketiga" in compressed:
            failures.append(
                "List melebihi limit policy."
            )

        if "2. Contoh kedua" not in compressed:
            failures.append(
                "Item yang masih dalam limit hilang."
            )

        return {
            "name": "LIST_ITEM_LIMIT",
            "failures": failures,
            "payload": {
                "compressed": compressed,
            },
        }

    def _test_source_filtering(self):
        sources = [
            {
                "type": "QURAN",
                "reference": "QS 2:275",
            },
            {
                "type": "HADIS",
                "reference": "HR. Muslim 1",
            },
            {
                "type": "EKSTERNAL",
                "reference": "Fatwa MUI",
            },
        ]

        policy = self._build_policy(
            "hadisnya?"
        )

        displayed = select_display_sources(
            sources=sources,
            policy=policy,
        )

        failures = []

        if len(displayed) != 1:
            failures.append(
                f"Expected 1 source, actual={len(displayed)}."
            )

        elif displayed[0].get("type") != "HADIS":
            failures.append(
                "Source yang tampil bukan HADIS."
            )

        return {
            "name": "SOURCE_FILTER_BY_ASPECT",
            "failures": failures,
            "payload": {
                "displayed": displayed,
            },
        }

    def _test_prompt_instruction(self):
        policy = self._build_policy(
            "singkatnya?"
        )

        prompt = build_followup_prompt_instruction(
            policy
        )

        failures = []

        required_fragments = [
            "ATURAN NATURAL FOLLOW-UP",
            "Jangan mengulang salam",
            "SUMMARY",
            "sangat ringkas",
        ]

        for fragment in required_fragments:
            if fragment.lower() not in prompt.lower():
                failures.append(
                    f"Missing fragment: {fragment}"
                )

        return {
            "name": "FOLLOWUP_PROMPT_INSTRUCTION",
            "failures": failures,
            "payload": {
                "prompt": prompt,
            },
        }

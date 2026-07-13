# main/management/commands/test_smart_ai_answer_strategy.py

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from django.core.management.base import BaseCommand

from main.utils_rag.answer_strategy import (
    STRATEGY_DIRECT_LOOKUP,
    STRATEGY_FATWA,
    STRATEGY_FIQH,
    STRATEGY_GENERAL_ISLAMIC,
    STRATEGY_OUT_OF_DOMAIN,
    STRATEGY_SPIRITUAL,
    STRATEGY_THEMATIC_DALIL,
    select_answer_strategy,
)


@dataclass
class StrategyTestCase:
    name: str
    intent: str
    conversation_relation: str
    expected_strategy: str
    expected_opening: bool
    expected_follow_up: bool
    expected_answer_only_aspect: bool = False


TEST_CASES = [
    StrategyTestCase(
        name="DIRECT_HADITH_NEW_TOPIC",
        intent="DIRECT_HADITH_LOOKUP",
        conversation_relation="NEW_TOPIC",
        expected_strategy=STRATEGY_DIRECT_LOOKUP,
        expected_opening=True,
        expected_follow_up=False,
    ),
    StrategyTestCase(
        name="DIRECT_QURAN_FOLLOW_UP",
        intent="DIRECT_QURAN_LOOKUP",
        conversation_relation="FOLLOW_UP",
        expected_strategy=STRATEGY_DIRECT_LOOKUP,
        expected_opening=False,
        expected_follow_up=True,
        expected_answer_only_aspect=True,
    ),
    StrategyTestCase(
        name="THEMATIC_NEW_TOPIC",
        intent="THEMATIC_DALIL_SEARCH",
        conversation_relation="NEW_TOPIC",
        expected_strategy=STRATEGY_THEMATIC_DALIL,
        expected_opening=True,
        expected_follow_up=False,
    ),
    StrategyTestCase(
        name="THEMATIC_FOLLOW_UP",
        intent="THEMATIC_DALIL_SEARCH",
        conversation_relation="FOLLOW_UP",
        expected_strategy=STRATEGY_THEMATIC_DALIL,
        expected_opening=False,
        expected_follow_up=True,
        expected_answer_only_aspect=True,
    ),
    StrategyTestCase(
        name="FIQH_NEW_TOPIC",
        intent="FIQH_QA",
        conversation_relation="NEW_TOPIC",
        expected_strategy=STRATEGY_FIQH,
        expected_opening=True,
        expected_follow_up=False,
    ),
    StrategyTestCase(
        name="FIQH_REFINEMENT",
        intent="FIQH_QA",
        conversation_relation="TOPIC_REFINEMENT",
        expected_strategy=STRATEGY_FIQH,
        expected_opening=False,
        expected_follow_up=True,
    ),
    StrategyTestCase(
        name="FATWA_NEW_TOPIC",
        intent="FATWA_QA",
        conversation_relation="NEW_TOPIC",
        expected_strategy=STRATEGY_FATWA,
        expected_opening=True,
        expected_follow_up=False,
    ),
    StrategyTestCase(
        name="FATWA_FOLLOW_UP",
        intent="FATWA_QA",
        conversation_relation="FOLLOW_UP",
        expected_strategy=STRATEGY_FATWA,
        expected_opening=False,
        expected_follow_up=True,
        expected_answer_only_aspect=True,
    ),
    StrategyTestCase(
        name="SPIRITUAL_NEW_TOPIC",
        intent="SPIRITUAL_ADVICE",
        conversation_relation="NEW_TOPIC",
        expected_strategy=STRATEGY_SPIRITUAL,
        expected_opening=True,
        expected_follow_up=False,
    ),
    StrategyTestCase(
        name="SPIRITUAL_FOLLOW_UP",
        intent="SPIRITUAL_ADVICE",
        conversation_relation="FOLLOW_UP",
        expected_strategy=STRATEGY_SPIRITUAL,
        expected_opening=False,
        expected_follow_up=True,
        expected_answer_only_aspect=True,
    ),
    StrategyTestCase(
        name="GENERAL_NEW_TOPIC",
        intent="GENERAL_ISLAMIC_QA",
        conversation_relation="NEW_TOPIC",
        expected_strategy=STRATEGY_GENERAL_ISLAMIC,
        expected_opening=True,
        expected_follow_up=False,
    ),
    StrategyTestCase(
        name="OUT_OF_DOMAIN",
        intent="OUT_OF_DOMAIN",
        conversation_relation="NEW_TOPIC",
        expected_strategy=STRATEGY_OUT_OF_DOMAIN,
        expected_opening=False,
        expected_follow_up=False,
    ),
]


class Command(BaseCommand):
    help = (
        "Menguji Islamic Answer Strategy Engine Phase 5A.1."
    )

    def handle(self, *args, **options):
        passed = 0
        failed = 0
        failed_cases: list[dict[str, Any]] = []

        self.stdout.write("")
        self.stdout.write(
            "=" * 90
        )
        self.stdout.write(
            "SMART AI — ANSWER STRATEGY TEST"
        )
        self.stdout.write(
            "=" * 90
        )

        for index, case in enumerate(
            TEST_CASES,
            start=1,
        ):
            conversation_context = {
                "conversation_relation": (
                    case.conversation_relation
                )
            }

            strategy = select_answer_strategy(
                intent=case.intent,
                conversation_context=conversation_context,
                verified_sources=[],
            )

            failures = []

            if strategy.name != case.expected_strategy:
                failures.append(
                    (
                        "strategy: "
                        f"expected={case.expected_strategy}, "
                        f"actual={strategy.name}"
                    )
                )

            if (
                strategy.show_opening
                != case.expected_opening
            ):
                failures.append(
                    (
                        "show_opening: "
                        f"expected={case.expected_opening}, "
                        f"actual={strategy.show_opening}"
                    )
                )

            if (
                strategy.is_follow_up
                != case.expected_follow_up
            ):
                failures.append(
                    (
                        "is_follow_up: "
                        f"expected={case.expected_follow_up}, "
                        f"actual={strategy.is_follow_up}"
                    )
                )

            if (
                strategy.answer_only_requested_aspect
                != case.expected_answer_only_aspect
            ):
                failures.append(
                    (
                        "answer_only_requested_aspect: "
                        f"expected="
                        f"{case.expected_answer_only_aspect}, "
                        f"actual="
                        f"{strategy.answer_only_requested_aspect}"
                    )
                )

            if failures:
                failed += 1

                failed_cases.append({
                    "name": case.name,
                    "intent": case.intent,
                    "conversation_relation": (
                        case.conversation_relation
                    ),
                    "failures": failures,
                    "strategy": strategy.to_dict(),
                })

                status = self.style.ERROR("FAIL")
            else:
                passed += 1
                status = self.style.SUCCESS("PASS")

            self.stdout.write(
                (
                    f"[{index:02d}] {case.name}: {status} | "
                    f"strategy={strategy.name} | "
                    f"opening={strategy.show_opening} | "
                    f"follow_up={strategy.is_follow_up}"
                )
            )

        total = len(TEST_CASES)
        pass_rate = (
            passed / total * 100
            if total
            else 0
        )

        self.stdout.write("")
        self.stdout.write(
            "=" * 90
        )
        self.stdout.write(
            "SUMMARY"
        )
        self.stdout.write(
            "=" * 90
        )
        self.stdout.write(
            f"total     : {total}"
        )
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
            self.stdout.write(
                "=" * 90
            )
            self.stdout.write(
                "FAILED CASES"
            )
            self.stdout.write(
                "=" * 90
            )
            self.stdout.write(
                json.dumps(
                    failed_cases,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
            )
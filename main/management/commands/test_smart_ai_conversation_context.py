# main/management/commands/test_smart_ai_conversation_context.py

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from main.models_ai import ChatConversation, ChatMessage
from main.utils_rag.conversation_context import (
    resolve_conversation_context,
)
from main.utils_rag.integration import RAGIntegration
from main.utils_rag.topic_classifier import (
    RELATION_AMBIGUOUS,
    RELATION_FOLLOW_UP,
    RELATION_NEW_TOPIC,
    RELATION_TOPIC_REFINEMENT,
)


@dataclass
class ConversationTurn:
    message: str
    expected_relations: set[str]
    expected_history: bool | None = None
    expected_topic_changed: bool | None = None
    expected_follow_up: bool | None = None
    expected_query_contains: list[str] = field(
        default_factory=list
    )
    note: str = ""


@dataclass
class ConversationScenario:
    name: str
    description: str
    turns: list[ConversationTurn]


SCENARIOS = [
    ConversationScenario(
        name="WARIS_REFINEMENT",
        description=(
            "Menguji apakah pertanyaan detail tentang jumlah anak "
            "perempuan tetap dianggap bagian dari topik waris."
        ),
        turns=[
            ConversationTurn(
                message=(
                    "Anak perempuan dapat warisan berapa persen?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
                note="Topik awal waris.",
            ),
            ConversationTurn(
                message=(
                    "Kalau anak perempuannya dua bagaimana?"
                ),
                expected_relations={
                    RELATION_TOPIC_REFINEMENT,
                    RELATION_FOLLOW_UP,
                },
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=[
                    "anak perempuan",
                ],
                note=(
                    "Harus tetap terhubung dengan pembagian waris."
                ),
            ),
            ConversationTurn(
                message="Ada hadisnya?",
                expected_relations={RELATION_FOLLOW_UP},
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=[
                    "hadis",
                    "waris",
                ],
                note="Follow-up eksplisit meminta hadis.",
            ),
        ],
    ),
    ConversationScenario(
        name="SAME_SUBJECT_DIFFERENT_TOPIC",
        description=(
            "Subjek sama-sama anak perempuan, tetapi persoalan "
            "waris dan mencari penghasilan merupakan topik berbeda."
        ),
        turns=[
            ConversationTurn(
                message=(
                    "Anak perempuan dapat warisan berapa persen?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
            ),
            ConversationTurn(
                message=(
                    "Hukum anak perempuan mencari harta sendiri"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=True,
                expected_follow_up=False,
                note=(
                    "Kesamaan subjek tidak boleh membuat topik "
                    "dianggap sama."
                ),
            ),
            ConversationTurn(
                message="Kalau bekerja di luar rumah bagaimana?",
                expected_relations={
                    RELATION_TOPIC_REFINEMENT,
                    RELATION_FOLLOW_UP,
                },
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=[
                    "bekerja",
                ],
                note=(
                    "Masih berkaitan dengan perempuan bekerja atau "
                    "mencari penghasilan."
                ),
            ),
        ],
    ),
    ConversationScenario(
        name="CLEAR_TOPIC_SHIFT",
        description=(
            "Menguji perpindahan jelas dari hukum waris menuju "
            "dalil tentang pemimpin zalim."
        ),
        turns=[
            ConversationTurn(
                message="Apa hukum waris?",
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
            ),
            ConversationTurn(
                message=(
                    "Pemimpin yang zalim dalil dan rujukannya apa?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=True,
                expected_follow_up=False,
                note=(
                    "History waris tidak boleh dikirim ke pipeline."
                ),
            ),
            ConversationTurn(
                message="Hadisnya juga ada?",
                expected_relations={RELATION_FOLLOW_UP},
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=[
                    "hadis",
                    "pemimpin",
                ],
            ),
        ],
    ),
    ConversationScenario(
        name="THEMATIC_FOLLOW_UP",
        description=(
            "Menguji perpindahan dari permintaan ayat menjadi "
            "permintaan hadis pada tema yang sama."
        ),
        turns=[
            ConversationTurn(
                message="Ayat tentang sedekah",
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
            ),
            ConversationTurn(
                message="Hadisnya juga?",
                expected_relations={RELATION_FOLLOW_UP},
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=[
                    "hadis",
                    "sedekah",
                ],
                note=(
                    "Resolved query semestinya menjadi hadis "
                    "tentang sedekah."
                ),
            ),
            ConversationTurn(
                message="Kalau tentang riba ada ayatnya?",
                expected_relations={
                    RELATION_NEW_TOPIC,
                    RELATION_TOPIC_REFINEMENT,
                },
                expected_history=False,
                expected_topic_changed=True,
                expected_follow_up=False,
                expected_query_contains=[
                    "riba",
                ],
                note=(
                    "Ini seharusnya dianggap topik baru meskipun "
                    "masih meminta ayat."
                ),
            ),
        ],
    ),
    ConversationScenario(
        name="SPIRITUAL_CONTEXT",
        description=(
            "Menguji follow-up spiritual yang tidak mengulang "
            "seluruh konteks pada pesan baru."
        ),
        turns=[
            ConversationTurn(
                message=(
                    "Aku ingin bertaubat tapi sering jatuh lagi"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
            ),
            ConversationTurn(
                message="Kenapa aku selalu mengulanginya?",
                expected_relations={
                    RELATION_TOPIC_REFINEMENT,
                    RELATION_FOLLOW_UP,
                    RELATION_AMBIGUOUS,
                },
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                note=(
                    "Masih berkaitan dengan taubat dan mengulangi "
                    "kesalahan."
                ),
            ),
            ConversationTurn(
                message="Ada dalilnya?",
                expected_relations={RELATION_FOLLOW_UP},
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=[
                    "dalil",
                    "taubat",
                ],
            ),
        ],
    ),
    ConversationScenario(
        name="SHORT_AMBIGUOUS_FOLLOW_UP",
        description=(
            "Menguji pesan pendek yang tidak dapat berdiri sendiri."
        ),
        turns=[
            ConversationTurn(
                message="Apa hukum menggunakan paylater?",
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
            ),
            ConversationTurn(
                message="Kenapa?",
                expected_relations={RELATION_FOLLOW_UP},
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=[
                    "paylater",
                ],
            ),
            ConversationTurn(
                message="Kalau menurut MUI?",
                expected_relations={RELATION_FOLLOW_UP},
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=[
                    "mui",
                    "paylater",
                ],
            ),
        ],
    ),
    ConversationScenario(
        name="RETURN_TO_OLD_TOPIC",
        description=(
            "Menguji pengguna berpindah topik lalu menyebut kembali "
            "topik lama secara eksplisit."
        ),
        turns=[
            ConversationTurn(
                message="Apa hukum waris?",
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
            ),
            ConversationTurn(
                message="Apa dalil tentang pemimpin yang zalim?",
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=True,
                expected_follow_up=False,
            ),
            ConversationTurn(
                message=(
                    "Kembali ke waris, kalau ahli warisnya hanya "
                    "anak perempuan bagaimana?"
                ),
                expected_relations={
                    RELATION_NEW_TOPIC,
                    RELATION_TOPIC_REFINEMENT,
                },
                expected_history=False,
                expected_topic_changed=True,
                expected_follow_up=False,
                expected_query_contains=[
                    "waris",
                    "anak perempuan",
                ],
                note=(
                    "Versi sekarang membandingkan dengan topik aktif "
                    "terakhir. Kembali ke topik lama diperlakukan "
                    "sebagai perpindahan topik baru."
                ),
            ),
        ],
    ),
]


class Command(BaseCommand):
    help = (
        "Menguji conversation context, topic shift, follow-up, "
        "topic refinement, dan selective history injection."
    )

    def _build_failed_case_payload(
        self,
        scenario: ConversationScenario,
        turn_index: int,
        turn: ConversationTurn,
        result: dict[str, Any],
        validation: dict[str, Any],
    ):
        context = result.get(
            "conversation_context",
            {},
        )

        previous_topic = context.get(
            "previous_topic",
        ) or {}

        active_topic = context.get(
            "active_topic",
        ) or {}

        return {
            "scenario": scenario.name,
            "turn_index": turn_index,
            "user_message": turn.message,
            "expected_relations": sorted(
                turn.expected_relations
            ),
            "actual_relation": context.get(
                "conversation_relation"
            ),
            "expected_history": turn.expected_history,
            "actual_history": context.get(
                "should_include_history"
            ),
            "expected_topic_changed": (
                turn.expected_topic_changed
            ),
            "actual_topic_changed": context.get(
                "topic_changed"
            ),
            "expected_follow_up": turn.expected_follow_up,
            "actual_follow_up": context.get(
                "is_follow_up"
            ),
            "topic_similarity": context.get(
                "topic_similarity"
            ),
            "context_confidence": context.get(
                "context_confidence"
            ),
            "used_llm_topic_classifier": context.get(
                "used_llm_topic_classifier"
            ),
            "reasoning_code": context.get(
                "reasoning_code"
            ),
            "follow_up_type": context.get(
                "follow_up_type"
            ),
            "previous_topic_label": previous_topic.get(
                "label"
            ),
            "previous_topic_summary": previous_topic.get(
                "summary"
            ),
            "previous_topic_action": previous_topic.get(
                "action"
            ),
            "previous_topic_entities": previous_topic.get(
                "entities"
            ),
            "active_topic_label": active_topic.get(
                "label"
            ),
            "active_topic_summary": active_topic.get(
                "summary"
            ),
            "active_topic_action": active_topic.get(
                "action"
            ),
            "active_topic_entities": active_topic.get(
                "entities"
            ),
            "resolved_query": context.get(
                "resolved_query"
            ),
            "validation_failures": validation.get(
                "failures",
                [],
            ),
            "test_note": turn.note,
        }


    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=int,
            default=None,
            help=(
                "ID user untuk pemilik conversation. Jika tidak "
                "diberikan, command menggunakan user pertama."
            ),
        )
        parser.add_argument(
            "--full-pipeline",
            action="store_true",
            help=(
                "Menjalankan seluruh RAGIntegration dan menyimpan "
                "jawaban sebenarnya. Tanpa opsi ini, hanya context "
                "resolver yang diuji."
            ),
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=7.0,
            help=(
                "Jeda antar-turn ketika memakai --full-pipeline. "
                "Default 2 detik."
            ),
        )
        parser.add_argument(
            "--scenario",
            type=str,
            default=None,
            help=(
                "Jalankan satu scenario saja, misalnya "
                "--scenario CLEAR_TOPIC_SHIFT."
            ),
        )
        parser.add_argument(
            "--output",
            type=str,
            default=(
                "hasil_test_smart_ai_conversation_context.txt"
            ),
            help="Nama file laporan hasil tes.",
        )
        parser.add_argument(
            "--keep-data",
            action="store_true",
            help=(
                "Jangan hapus conversation tes setelah command "
                "selesai."
            ),
        )

    def handle(self, *args, **options):
        user = self._get_user(options["user_id"])
        full_pipeline = options["full_pipeline"]
        delay = max(0.0, options["delay"])
        output_path = Path(options["output"])
        keep_data = options["keep_data"]

        scenarios = self._filter_scenarios(
            options.get("scenario")
        )

        summary = {
            "total_turns": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "new_topic": 0,
            "follow_up": 0,
            "topic_refinement": 0,
            "ambiguous": 0,
            "topic_changed": 0,
            "history_included": 0,
            "llm_topic_classifier_used": 0,
        }
        failed_cases = []
        error_cases = []
        report_lines = [
            "=" * 100,
            "SMART AI — CONVERSATION CONTEXT BENCHMARK",
            "=" * 100,
            f"Generated at   : {timezone.now().isoformat()}",
            f"User ID       : {user.pk}",
            f"Mode          : "
            f"{'FULL PIPELINE' if full_pipeline else 'CONTEXT ONLY'}",
            f"Total scenario: {len(scenarios)}",
            "",
        ]

        created_conversation_ids: list[int] = []

        try:
            for scenario_index, scenario in enumerate(
                scenarios,
                start=1,
            ):
                conversation = self._create_conversation(
                    user=user,
                    title=(
                        f"[TEST CONTEXT] {scenario.name}"
                    ),
                )
                created_conversation_ids.append(
                    conversation.pk
                )

                report_lines.extend([
                    "",
                    "=" * 100,
                    (
                        f"SCENARIO #{scenario_index}: "
                        f"{scenario.name}"
                    ),
                    "=" * 100,
                    f"Description: {scenario.description}",
                    (
                        f"Conversation ID: "
                        f"{conversation.pk}"
                    ),
                    "",
                ])

                for turn_index, turn in enumerate(
                    scenario.turns,
                    start=1,
                ):
                    summary["total_turns"] += 1

                    try:
                        result = self._run_turn(
                            conversation=conversation,
                            message=turn.message,
                            turn_index=turn_index,
                            full_pipeline=full_pipeline,
                        )

                        context = result[
                            "conversation_context"
                        ]

                        validation = self._validate_turn(
                            turn=turn,
                            context=context,
                        )

                        passed = validation["passed"]

                        if passed:
                            summary["passed"] += 1
                        else:
                            summary["failed"] += 1

                            failed_cases.append(
                                self._build_failed_case_payload(
                                    scenario=scenario,
                                    turn_index=turn_index,
                                    turn=turn,
                                    result=result,
                                    validation=validation,
                                )
                            )

                        self._increment_context_summary(
                            summary=summary,
                            context=context,
                        )

                        report_lines.extend(
                            self._format_turn_report(
                                turn_index=turn_index,
                                turn=turn,
                                result=result,
                                validation=validation,
                            )
                        )

                        status_symbol = (
                            "PASS" if passed else "FAIL"
                        )

                        self.stdout.write(
                            (
                                f"[{scenario.name}] "
                                f"Turn {turn_index}: "
                                f"{status_symbol} | "
                                f"{context.get('conversation_relation')} "
                                f"| similarity="
                                f"{self._format_similarity(context)}"
                            )
                        )

                    except Exception as exc:
                        summary["errors"] += 1
                        error_cases.append({
                            "scenario": scenario.name,
                            "turn_index": turn_index,
                            "user_message": turn.message,
                            "error_type": type(exc).__name__,
                            "error_message": str(exc),
                        })
                        report_lines.extend([
                            "-" * 100,
                            f"TURN #{turn_index}",
                            "-" * 100,
                            f"USER: {turn.message}",
                            "RESULT: ERROR",
                            (
                                f"ERROR TYPE: "
                                f"{type(exc).__name__}"
                            ),
                            f"ERROR: {str(exc)}",
                            "",
                        ])

                        self.stderr.write(
                            self.style.ERROR(
                                (
                                    f"[{scenario.name}] "
                                    f"Turn {turn_index} ERROR: "
                                    f"{exc}"
                                )
                            )
                        )

                    if (
                        full_pipeline
                        and delay > 0
                        and turn_index < len(scenario.turns)
                    ):
                        time.sleep(delay)

        finally:
            if not keep_data:
                ChatConversation.objects.filter(
                    pk__in=created_conversation_ids
                ).delete()

        report_lines.extend(
            self._build_summary_report(
                summary=summary,
                failed_cases=failed_cases,
                error_cases=error_cases,
            )
        )

        output_path.write_text(
            "\n".join(report_lines),
            encoding="utf-8",
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Laporan tersimpan: {output_path.resolve()}"
            )
        )
        self.stdout.write("")
        self.stdout.write(
            f"Total turns : {summary['total_turns']}"
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Passed      : {summary['passed']}"
            )
        )

        failed_style = (
            self.style.ERROR
            if summary["failed"] > 0
            else self.style.SUCCESS
        )
        self.stdout.write(
            failed_style(
                f"Failed      : {summary['failed']}"
            )
        )

        error_style = (
            self.style.ERROR
            if summary["errors"] > 0
            else self.style.SUCCESS
        )
        self.stdout.write(
            error_style(
                f"Errors      : {summary['errors']}"
            )
        )

    def _get_user(self, user_id):
        User = get_user_model()

        if user_id is not None:
            try:
                return User.objects.get(pk=user_id)
            except User.DoesNotExist as exc:
                raise CommandError(
                    f"User dengan ID {user_id} tidak ditemukan."
                ) from exc

        user = User.objects.order_by("pk").first()

        if user is None:
            raise CommandError(
                "Tidak ada user di database. Buat user terlebih "
                "dahulu atau gunakan --user-id."
            )

        return user

    def _filter_scenarios(
        self,
        requested_scenario: str | None,
    ):
        if not requested_scenario:
            return SCENARIOS

        requested = requested_scenario.strip().upper()

        selected = [
            scenario
            for scenario in SCENARIOS
            if scenario.name.upper() == requested
        ]

        if not selected:
            available = ", ".join(
                scenario.name for scenario in SCENARIOS
            )

            raise CommandError(
                f"Scenario '{requested_scenario}' tidak ditemukan. "
                f"Pilihan: {available}"
            )

        return selected

    def _create_conversation(
        self,
        user,
        title: str,
    ):
        """
        Membuat conversation secara fleksibel.

        Mendukung model yang memiliki field user dan/atau title.
        """
        field_names = {
            field.name
            for field in ChatConversation._meta.fields
        }

        kwargs = {}

        if "user" in field_names:
            kwargs["user"] = user

        if "title" in field_names:
            kwargs["title"] = title

        return ChatConversation.objects.create(**kwargs)

    @transaction.atomic
    def _run_turn(
        self,
        conversation,
        message: str,
        turn_index: int,
        full_pipeline: bool,
    ):
        """
        Meniru urutan endpoint production:

        1. Simpan pesan user.
        2. Jalankan resolver atau seluruh pipeline.
        3. Simpan balasan assistant.
        """
        is_first_message = turn_index == 1

        user_message = ChatMessage.objects.create(
            conversation=conversation,
            role="user",
            text=message,
        )

        started_at = time.perf_counter()

        if full_pipeline:
            rag_result = (
                RAGIntegration.generate_metode7_response(
                    user_message=message,
                    conversation_id=conversation.pk,
                    is_first_message=is_first_message,
                )
            )

            context = rag_result.get(
                "conversation_context",
                {},
            )

            assistant_text = rag_result.get(
                "reply",
                "(Tidak ada reply)",
            )

            ChatMessage.objects.create(
                conversation=conversation,
                role="assistant",
                text=assistant_text,
            )

            duration = (
                time.perf_counter() - started_at
            )

            return {
                "user_message_id": user_message.pk,
                "conversation_context": context,
                "reply": assistant_text,
                "answer_mode": rag_result.get(
                    "answer_mode"
                ),
                "intent": rag_result.get("intent"),
                "verification_status": rag_result.get(
                    "verification_status"
                ),
                "final_check_passed": rag_result.get(
                    "final_check_passed"
                ),
                "process_time": duration,
            }

        context = resolve_conversation_context(
            user_message=message,
            conversation_id=conversation.pk,
            is_first_message=is_first_message,
        )

        # Dummy assistant message agar struktur history sama dengan
        # percakapan production.
        assistant_text = (
            "[CONTEXT TEST RESPONSE] "
            f"relation={context.get('conversation_relation')}; "
            f"topic={self._get_topic_summary(context)}"
        )

        ChatMessage.objects.create(
            conversation=conversation,
            role="assistant",
            text=assistant_text,
        )

        duration = time.perf_counter() - started_at

        return {
            "user_message_id": user_message.pk,
            "conversation_context": context,
            "reply": assistant_text,
            "answer_mode": "CONTEXT_ONLY",
            "intent": None,
            "verification_status": None,
            "final_check_passed": None,
            "process_time": duration,
        }

    def _validate_turn(
        self,
        turn: ConversationTurn,
        context: dict[str, Any],
    ):
        failures = []

        actual_relation = context.get(
            "conversation_relation"
        )

        if actual_relation not in turn.expected_relations:
            failures.append(
                (
                    "conversation_relation: "
                    f"expected one of "
                    f"{sorted(turn.expected_relations)}, "
                    f"actual={actual_relation}"
                )
            )

        if turn.expected_history is not None:
            actual_history = bool(
                context.get("should_include_history")
            )

            if actual_history != turn.expected_history:
                failures.append(
                    (
                        "should_include_history: "
                        f"expected={turn.expected_history}, "
                        f"actual={actual_history}"
                    )
                )

        if turn.expected_topic_changed is not None:
            actual_changed = bool(
                context.get("topic_changed")
            )

            if (
                actual_changed
                != turn.expected_topic_changed
            ):
                failures.append(
                    (
                        "topic_changed: "
                        f"expected="
                        f"{turn.expected_topic_changed}, "
                        f"actual={actual_changed}"
                    )
                )

        if turn.expected_follow_up is not None:
            actual_follow_up = bool(
                context.get("is_follow_up")
            )

            if (
                actual_follow_up
                != turn.expected_follow_up
            ):
                failures.append(
                    (
                        "is_follow_up: "
                        f"expected="
                        f"{turn.expected_follow_up}, "
                        f"actual={actual_follow_up}"
                    )
                )

        resolved_query = (
            context.get("resolved_query") or ""
        ).lower()

        for expected_text in turn.expected_query_contains:
            if expected_text.lower() not in resolved_query:
                failures.append(
                    (
                        "resolved_query tidak mengandung "
                        f"'{expected_text}'. "
                        f"actual='{resolved_query}'"
                    )
                )

        return {
            "passed": not failures,
            "failures": failures,
        }

    def _increment_context_summary(
        self,
        summary: dict[str, int],
        context: dict[str, Any],
    ):
        relation = context.get(
            "conversation_relation"
        )

        relation_map = {
            RELATION_NEW_TOPIC: "new_topic",
            RELATION_FOLLOW_UP: "follow_up",
            RELATION_TOPIC_REFINEMENT: (
                "topic_refinement"
            ),
            RELATION_AMBIGUOUS: "ambiguous",
        }

        summary_key = relation_map.get(relation)

        if summary_key:
            summary[summary_key] += 1

        if context.get("topic_changed"):
            summary["topic_changed"] += 1

        if context.get("should_include_history"):
            summary["history_included"] += 1

        if context.get(
            "used_llm_topic_classifier"
        ):
            summary[
                "llm_topic_classifier_used"
            ] += 1

    def _format_turn_report(
        self,
        turn_index: int,
        turn: ConversationTurn,
        result: dict[str, Any],
        validation: dict[str, Any],
    ):
        context = result["conversation_context"]

        previous_topic = context.get(
            "previous_topic"
        ) or {}
        active_topic = context.get(
            "active_topic"
        ) or {}

        intent = result.get("intent")

        if isinstance(intent, dict):
            intent_value = intent.get("intent")
        else:
            intent_value = intent

        lines = [
            "-" * 100,
            f"TURN #{turn_index}",
            "-" * 100,
            f"USER: {turn.message}",
            (
                f"EXPECTED RELATION: "
                f"{', '.join(sorted(turn.expected_relations))}"
            ),
            (
                f"ACTUAL RELATION  : "
                f"{context.get('conversation_relation')}"
            ),
            (
                f"RESULT           : "
                f"{'PASS' if validation['passed'] else 'FAIL'}"
            ),
            (
                f"FOLLOW-UP TYPE   : "
                f"{context.get('follow_up_type')}"
            ),
            (
                f"IS FOLLOW-UP     : "
                f"{context.get('is_follow_up')}"
            ),
            (
                f"TOPIC CHANGED    : "
                f"{context.get('topic_changed')}"
            ),
            (
                f"INCLUDE HISTORY  : "
                f"{context.get('should_include_history')}"
            ),
            (
                f"TOPIC SIMILARITY : "
                f"{self._format_similarity(context)}"
            ),
            (
                f"CONTEXT CONFIDENCE: "
                f"{context.get('context_confidence')}"
            ),
            (
                f"USED LLM CLASSIFIER: "
                f"{context.get('used_llm_topic_classifier')}"
            ),
            (
                f"REASONING CODE   : "
                f"{context.get('reasoning_code')}"
            ),
            (
                f"PREVIOUS TOPIC   : "
                f"{previous_topic.get('summary')}"
            ),
            (
                f"ACTIVE TOPIC     : "
                f"{active_topic.get('summary')}"
            ),
            (
                f"ACTIVE ACTION    : "
                f"{active_topic.get('action')}"
            ),
            (
                f"ACTIVE ENTITIES  : "
                f"{active_topic.get('entities')}"
            ),
            (
                f"RESOLVED QUERY   : "
                f"{context.get('resolved_query')}"
            ),
            (
                f"ANSWER MODE      : "
                f"{result.get('answer_mode')}"
            ),
            f"INTENT           : {intent_value}",
            (
                f"VERIFICATION     : "
                f"{result.get('verification_status')}"
            ),
            (
                f"FINAL CHECK PASS : "
                f"{result.get('final_check_passed')}"
            ),
            (
                f"PROCESS TIME     : "
                f"{result.get('process_time', 0):.4f} detik"
            ),
        ]

        if turn.note:
            lines.append(f"TEST NOTE        : {turn.note}")

        if validation["failures"]:
            lines.append("")
            lines.append("VALIDATION FAILURES:")

            for failure in validation["failures"]:
                lines.append(f"- {failure}")

        lines.extend([
            "",
            "CONTEXT JSON:",
            json.dumps(
                context,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            "",
        ])

        if result.get("answer_mode") != "CONTEXT_ONLY":
            lines.extend([
                "FINAL REPLY:",
                result.get("reply") or "(Tidak ada reply)",
                "",
            ])

        return lines

    def _get_topic_summary(
        self,
        context: dict[str, Any],
    ):
        active_topic = context.get(
            "active_topic"
        ) or {}

        return active_topic.get("summary")

    def _format_similarity(
        self,
        context: dict[str, Any],
    ):
        similarity = context.get("topic_similarity")

        if similarity is None:
            return "None"

        try:
            return f"{float(similarity):.4f}"
        except (TypeError, ValueError):
            return str(similarity)

    def _build_summary_report(
        self,
        summary: dict[str, int],
        failed_cases: list[dict[str, Any]],
        error_cases: list[dict[str, Any]],
    ):
        total = summary["total_turns"]
        passed = summary["passed"]

        pass_rate = (
            (passed / total) * 100
            if total
            else 0.0
        )

        lines = [
            "",
            "=" * 100,
            "SUMMARY",
            "=" * 100,
            f"total_turns                 : {total}",
            f"passed                      : {passed}",
            f"failed                      : {summary['failed']}",
            f"errors                      : {summary['errors']}",
            f"new_topic                   : {summary['new_topic']}",
            f"follow_up                   : {summary['follow_up']}",
            (
                "topic_refinement            : "
                f"{summary['topic_refinement']}"
            ),
            f"ambiguous                   : {summary['ambiguous']}",
            (
                "topic_changed               : "
                f"{summary['topic_changed']}"
            ),
            (
                "history_included            : "
                f"{summary['history_included']}"
            ),
            (
                "llm_topic_classifier_used   : "
                f"{summary['llm_topic_classifier_used']}"
            ),
            "",
            f"PASS RATE: {pass_rate:.2f}%",
            "",
            "=" * 100,
            "FAILED CASE SUMMARY",
            "=" * 100,
        ]

        if not failed_cases:
            lines.extend([
                "Tidak ada failed case.",
                "",
            ])
        else:
            lines.append(
                f"Total failed cases: {len(failed_cases)}"
            )
            lines.append("")

            for index, case in enumerate(
                failed_cases,
                start=1,
            ):
                similarity = case.get(
                    "topic_similarity"
                )

                if similarity is None:
                    similarity_text = "None"
                else:
                    try:
                        similarity_text = (
                            f"{float(similarity):.4f}"
                        )
                    except (TypeError, ValueError):
                        similarity_text = str(similarity)

                lines.extend([
                    "-" * 100,
                    (
                        f"FAILED CASE #{index} | "
                        f"SCENARIO: {case['scenario']} | "
                        f"TURN: {case['turn_index']}"
                    ),
                    "-" * 100,
                    f"USER MESSAGE:",
                    case["user_message"],
                    "",
                    (
                        "EXPECTED RELATION : "
                        f"{', '.join(case['expected_relations'])}"
                    ),
                    (
                        "ACTUAL RELATION   : "
                        f"{case['actual_relation']}"
                    ),
                    (
                        "SIMILARITY        : "
                        f"{similarity_text}"
                    ),
                    (
                        "CONTEXT CONFIDENCE: "
                        f"{case['context_confidence']}"
                    ),
                    (
                        "LLM CLASSIFIER    : "
                        f"{case['used_llm_topic_classifier']}"
                    ),
                    (
                        "REASONING CODE    : "
                        f"{case['reasoning_code']}"
                    ),
                    (
                        "FOLLOW-UP TYPE    : "
                        f"{case['follow_up_type']}"
                    ),
                    "",
                    (
                        "EXPECTED HISTORY  : "
                        f"{case['expected_history']}"
                    ),
                    (
                        "ACTUAL HISTORY    : "
                        f"{case['actual_history']}"
                    ),
                    (
                        "EXPECTED CHANGED  : "
                        f"{case['expected_topic_changed']}"
                    ),
                    (
                        "ACTUAL CHANGED    : "
                        f"{case['actual_topic_changed']}"
                    ),
                    (
                        "EXPECTED FOLLOW-UP: "
                        f"{case['expected_follow_up']}"
                    ),
                    (
                        "ACTUAL FOLLOW-UP  : "
                        f"{case['actual_follow_up']}"
                    ),
                    "",
                    "PREVIOUS TOPIC:",
                    (
                        f"- label    : "
                        f"{case['previous_topic_label']}"
                    ),
                    (
                        f"- summary  : "
                        f"{case['previous_topic_summary']}"
                    ),
                    (
                        f"- action   : "
                        f"{case['previous_topic_action']}"
                    ),
                    (
                        f"- entities : "
                        f"{case['previous_topic_entities']}"
                    ),
                    "",
                    "ACTIVE TOPIC:",
                    (
                        f"- label    : "
                        f"{case['active_topic_label']}"
                    ),
                    (
                        f"- summary  : "
                        f"{case['active_topic_summary']}"
                    ),
                    (
                        f"- action   : "
                        f"{case['active_topic_action']}"
                    ),
                    (
                        f"- entities : "
                        f"{case['active_topic_entities']}"
                    ),
                    "",
                    "RESOLVED QUERY:",
                    str(case["resolved_query"]),
                    "",
                    "VALIDATION FAILURES:",
                ])

                for failure in case[
                    "validation_failures"
                ]:
                    lines.append(f"- {failure}")

                if case.get("test_note"):
                    lines.extend([
                        "",
                        f"TEST NOTE: {case['test_note']}",
                    ])

                lines.append("")

        lines.extend([
            "=" * 100,
            "ERROR CASE SUMMARY",
            "=" * 100,
        ])

        if not error_cases:
            lines.extend([
                "Tidak ada error case.",
                "",
            ])
        else:
            lines.append(
                f"Total error cases: {len(error_cases)}"
            )
            lines.append("")

            for index, case in enumerate(
                error_cases,
                start=1,
            ):
                lines.extend([
                    "-" * 100,
                    (
                        f"ERROR CASE #{index} | "
                        f"SCENARIO: {case['scenario']} | "
                        f"TURN: {case['turn_index']}"
                    ),
                    "-" * 100,
                    f"USER: {case['user_message']}",
                    (
                        f"ERROR TYPE: "
                        f"{case['error_type']}"
                    ),
                    (
                        f"ERROR MESSAGE: "
                        f"{case['error_message']}"
                    ),
                    "",
                ])

        lines.extend([
            "=" * 100,
            "COMPACT REVIEW PAYLOAD",
            "=" * 100,
            (
                "Kirim bagian ini untuk analisis. "
                "Berisi hanya failed dan error cases."
            ),
            "",
            json.dumps(
                {
                    "summary": summary,
                    "failed_cases": failed_cases,
                    "error_cases": error_cases,
                },
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
        ])

        return lines
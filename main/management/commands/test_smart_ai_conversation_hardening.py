# main/management/commands/test_smart_ai_conversation_hardening.py

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
    expected_query_excludes: list[str] = field(
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
        name="INFORMAL_SEDEKAH_FOLLOW_UP",
        description=(
            "Menguji bahasa informal dan typo ringan pada "
            "follow-up dalil tematik."
        ),
        turns=[
            ConversationTurn(
                message="ayat tentang sedekah dong",
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
                expected_query_contains=["sedekah"],
            ),
            ConversationTurn(
                message="hadisny ada juga?",
                expected_relations={
                    RELATION_FOLLOW_UP,
                    RELATION_TOPIC_REFINEMENT,
                },
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=["sedekah"],
                note=(
                    "Typo 'hadisny' idealnya masih dikenali sebagai "
                    "permintaan hadis pada tema sedekah."
                ),
            ),
            ConversationTurn(
                message="trus apa hikmahnya?",
                expected_relations={
                    RELATION_FOLLOW_UP,
                    RELATION_TOPIC_REFINEMENT,
                    RELATION_AMBIGUOUS,
                },
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=["sedekah"],
            ),
        ],
    ),
    ConversationScenario(
        name="INFORMAL_PAYLATER_MUI",
        description=(
            "Menguji singkatan informal dan follow-up lembaga fatwa."
        ),
        turns=[
            ConversationTurn(
                message="paylater itu haram ga?",
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
                expected_query_contains=["paylater"],
            ),
            ConversationTurn(
                message="klo mnrt mui?",
                expected_relations={
                    RELATION_FOLLOW_UP,
                    RELATION_AMBIGUOUS,
                },
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=[
                    "paylater",
                ],
                note=(
                    "Jika singkatan belum dikenali rule, LLM fallback "
                    "boleh mengklasifikasikan sebagai follow-up."
                ),
            ),
        ],
    ),
    ConversationScenario(
        name="WARIS_TO_NAFKAH_TO_WORK",
        description=(
            "Menguji perpindahan topik halus dengan subjek keluarga "
            "dan harta yang masih berdekatan."
        ),
        turns=[
            ConversationTurn(
                message=(
                    "Berapa bagian waris anak perempuan?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
                expected_query_contains=["waris"],
            ),
            ConversationTurn(
                message=(
                    "Apakah ayah tetap wajib menafkahi anak "
                    "perempuan yang sudah dewasa?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=True,
                expected_follow_up=False,
                expected_query_contains=["nafkah"],
                expected_query_excludes=["waris"],
            ),
            ConversationTurn(
                message=(
                    "Kalau anak perempuannya sudah bekerja sendiri?"
                ),
                expected_relations={
                    RELATION_TOPIC_REFINEMENT,
                    RELATION_FOLLOW_UP,
                },
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=[
                    "nafkah",
                    "bekerja",
                ],
            ),
        ],
    ),
    ConversationScenario(
        name="SAME_SUBJECT_DIFFERENT_ACTION",
        description=(
            "Subjek sama tetapi tindakan hukum berubah."
        ),
        turns=[
            ConversationTurn(
                message=(
                    "Apa hukum istri menerima nafkah dari suami?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
                expected_query_contains=["nafkah"],
            ),
            ConversationTurn(
                message=(
                    "Apa hukum istri mengambil uang suami diam-diam?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=True,
                expected_follow_up=False,
                expected_query_contains=["mengambil", "uang"],
                note=(
                    "Kesamaan subjek 'istri' tidak berarti masalah "
                    "hukumnya sama."
                ),
            ),
        ],
    ),
    ConversationScenario(
        name="SAME_ACTION_DIFFERENT_SUBJECT",
        description=(
            "Tindakan serupa tetapi pihak dan konteks hukumnya berbeda."
        ),
        turns=[
            ConversationTurn(
                message=(
                    "Bolehkah anak menggunakan uang orang tua?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
            ),
            ConversationTurn(
                message=(
                    "Bolehkah pengurus masjid menggunakan uang kas "
                    "untuk kepentingan pribadi?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=True,
                expected_follow_up=False,
                expected_query_contains=["masjid", "kas"],
                expected_query_excludes=["orang tua"],
            ),
        ],
    ),
    ConversationScenario(
        name="SPIRITUAL_TO_FIQH_SHIFT",
        description=(
            "Menguji perpindahan dari nasihat spiritual ke hukum fiqih."
        ),
        turns=[
            ConversationTurn(
                message=(
                    "Aku merasa jauh dari Allah dan sulit istiqamah"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
                expected_query_contains=["Allah"],
            ),
            ConversationTurn(
                message="ada doa yang bisa kubaca?",
                expected_relations={
                    RELATION_FOLLOW_UP,
                    RELATION_TOPIC_REFINEMENT,
                },
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
            ),
            ConversationTurn(
                message=(
                    "Apa hukum menjamak shalat karena pekerjaan?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=True,
                expected_follow_up=False,
                expected_query_contains=["shalat", "pekerjaan"],
                expected_query_excludes=["istiqamah"],
            ),
        ],
    ),
    ConversationScenario(
        name="THEMATIC_TO_FIQH_SHIFT",
        description=(
            "Menguji perpindahan dari pencarian dalil ke pertanyaan "
            "hukum pada objek berbeda."
        ),
        turns=[
            ConversationTurn(
                message="Hadis tentang menjaga lisan",
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
                expected_query_contains=["lisan"],
            ),
            ConversationTurn(
                message="ada ayatnya juga?",
                expected_relations={RELATION_FOLLOW_UP},
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=["lisan"],
            ),
            ConversationTurn(
                message=(
                    "Apa hukum investasi emas secara online?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=True,
                expected_follow_up=False,
                expected_query_contains=["investasi", "emas"],
                expected_query_excludes=["lisan"],
            ),
        ],
    ),
    ConversationScenario(
        name="MULTI_CONDITION_REFINEMENT",
        description=(
            "Menguji refinement dengan syarat dan mekanisme transaksi."
        ),
        turns=[
            ConversationTurn(
                message="Apa hukum jual beli online?",
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
                expected_query_contains=["jual beli"],
            ),
            ConversationTurn(
                message=(
                    "Kalau barangnya belum dimiliki oleh penjual?"
                ),
                expected_relations={
                    RELATION_TOPIC_REFINEMENT,
                    RELATION_FOLLOW_UP,
                },
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=[
                    "jual beli",
                    "barang",
                ],
            ),
            ConversationTurn(
                message=(
                    "Bagaimana jika pembeli sudah membayar penuh "
                    "di awal?"
                ),
                expected_relations={
                    RELATION_TOPIC_REFINEMENT,
                    RELATION_FOLLOW_UP,
                },
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=[
                    "jual beli",
                    "membayar",
                ],
            ),
        ],
    ),
    ConversationScenario(
        name="LONG_SAME_TOPIC_MESSAGE",
        description=(
            "Menguji pesan panjang yang tetap menjadi refinement "
            "topik lama."
        ),
        turns=[
            ConversationTurn(
                message="Apa hukum hutang piutang dalam Islam?",
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
                expected_query_contains=["hutang"],
            ),
            ConversationTurn(
                message=(
                    "Kalau seseorang meminjam uang dari temannya, "
                    "kemudian sejak awal menjanjikan tambahan sebagai "
                    "tanda terima kasih tanpa diminta pemberi pinjaman, "
                    "apakah tambahan itu tetap termasuk riba?"
                ),
                expected_relations={
                    RELATION_TOPIC_REFINEMENT,
                    RELATION_FOLLOW_UP,
                },
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=[
                    "hutang",
                    "tambahan",
                    "riba",
                ],
            ),
        ],
    ),
    ConversationScenario(
        name="VERY_SHORT_CONTEXT_MESSAGES",
        description=(
            "Menguji pesan pendek yang tidak dapat dipahami sendiri."
        ),
        turns=[
            ConversationTurn(
                message=(
                    "Apa hukum meninggalkan puasa Ramadan tanpa uzur?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
                expected_query_contains=["puasa"],
            ),
            ConversationTurn(
                message="kenapa?",
                expected_relations={RELATION_FOLLOW_UP},
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=["puasa"],
            ),
            ConversationTurn(
                message="terus?",
                expected_relations={
                    RELATION_FOLLOW_UP,
                    RELATION_AMBIGUOUS,
                },
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=["puasa"],
            ),
            ConversationTurn(
                message="contohnya?",
                expected_relations={RELATION_FOLLOW_UP},
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=["puasa"],
            ),
        ],
    ),
    ConversationScenario(
        name="RETURN_TO_OLD_TOPIC_EXPLICITLY",
        description=(
            "Menguji perpindahan topik lalu kembali ke topik lama "
            "secara eksplisit."
        ),
        turns=[
            ConversationTurn(
                message="Apa hukum zakat penghasilan?",
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
                expected_query_contains=["zakat"],
            ),
            ConversationTurn(
                message="Apa dalil tentang sabar?",
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=True,
                expected_follow_up=False,
                expected_query_contains=["sabar"],
                expected_query_excludes=["zakat"],
            ),
            ConversationTurn(
                message=(
                    "Kembali ke zakat penghasilan, berapa nisabnya?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=True,
                expected_follow_up=False,
                expected_query_contains=["zakat", "nisab"],
                expected_query_excludes=["sabar"],
                note=(
                    "Karena topik aktif sebelumnya sabar, penyebutan "
                    "zakat secara eksplisit adalah NEW_TOPIC."
                ),
            ),
        ],
    ),
    ConversationScenario(
        name="TOPIC_SHIFT_WITH_SIMILAR_WORD",
        description=(
            "Menguji dua topik yang memiliki kata serupa tetapi "
            "makna hukumnya berbeda."
        ),
        turns=[
            ConversationTurn(
                message=(
                    "Apakah harta warisan wajib dizakati?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
                expected_query_contains=["warisan", "zakat"],
            ),
            ConversationTurn(
                message=(
                    "Apakah mencari harta sebanyak-banyaknya "
                    "dilarang dalam Islam?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=True,
                expected_follow_up=False,
                expected_query_contains=["mencari", "harta"],
                note=(
                    "Kata 'harta' sama, tetapi masalah utama berbeda."
                ),
            ),
        ],
    ),
    ConversationScenario(
        name="TWO_TOPICS_IN_ONE_MESSAGE",
        description=(
            "Menguji pesan yang mengandung dua topik sekaligus."
        ),
        turns=[
            ConversationTurn(
                message=(
                    "Apa hukum riba dan bagaimana cara bertaubat "
                    "darinya?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
                expected_query_contains=["riba", "taubat"],
                note=(
                    "Pesan multi-topik awal tetap menjadi satu "
                    "conversation segment baru."
                ),
            ),
            ConversationTurn(
                message="ada dalil tentang taubatnya?",
                expected_relations={
                    RELATION_FOLLOW_UP,
                    RELATION_TOPIC_REFINEMENT,
                },
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=["taubat"],
            ),
        ],
    ),
    ConversationScenario(
        name="SELF_CONTAINED_QUERY_AFTER_FOLLOW_UP",
        description=(
            "Menguji topik baru lengkap setelah beberapa follow-up."
        ),
        turns=[
            ConversationTurn(
                message="Ayat tentang berbakti kepada orang tua",
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=False,
                expected_follow_up=False,
                expected_query_contains=["orang tua"],
            ),
            ConversationTurn(
                message="hadisnya?",
                expected_relations={RELATION_FOLLOW_UP},
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=["orang tua"],
            ),
            ConversationTurn(
                message="kenapa berbakti itu penting?",
                expected_relations={
                    RELATION_FOLLOW_UP,
                    RELATION_TOPIC_REFINEMENT,
                },
                expected_history=True,
                expected_topic_changed=False,
                expected_follow_up=True,
                expected_query_contains=["orang tua"],
            ),
            ConversationTurn(
                message=(
                    "Apa hukum mengambil keuntungan dari jual beli?"
                ),
                expected_relations={RELATION_NEW_TOPIC},
                expected_history=False,
                expected_topic_changed=True,
                expected_follow_up=False,
                expected_query_contains=["jual beli"],
                expected_query_excludes=["orang tua"],
            ),
        ],
    ),
]


class Command(BaseCommand):
    help = (
        "Hardening benchmark untuk conversation context, "
        "topic shift, refinement, typo, bahasa informal, dan "
        "selective history injection."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=int,
            default=None,
            help=(
                "ID user pemilik conversation. Jika tidak diberikan, "
                "command menggunakan user pertama."
            ),
        )
        parser.add_argument(
            "--full-pipeline",
            action="store_true",
            help=(
                "Menjalankan seluruh pipeline Smart AI. Tanpa flag "
                "ini hanya conversation context engine yang diuji."
            ),
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=7.0,
            help=(
                "Jeda antar-turn untuk mengurangi rate limit. "
                "Default 7 detik."
            ),
        )
        parser.add_argument(
            "--scenario",
            type=str,
            default=None,
            help=(
                "Jalankan satu scenario saja. Contoh: "
                "--scenario WARIS_TO_NAFKAH_TO_WORK"
            ),
        )
        parser.add_argument(
            "--output",
            type=str,
            default=(
                "hasil_test_smart_ai_conversation_hardening.txt"
            ),
            help="Nama file laporan.",
        )
        parser.add_argument(
            "--keep-data",
            action="store_true",
            help=(
                "Pertahankan conversation hasil tes di database."
            ),
        )

    def handle(self, *args, **options):
        user = self._get_user(options["user_id"])
        full_pipeline = bool(options["full_pipeline"])
        delay = max(0.0, float(options["delay"]))
        keep_data = bool(options["keep_data"])
        output_path = Path(options["output"])

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
            "history_excluded": 0,
            "llm_topic_classifier_used": 0,
            "full_pipeline_turns": 0,
            "final_check_failed": 0,
        }

        failed_cases: list[dict[str, Any]] = []
        error_cases: list[dict[str, Any]] = []

        report_lines = [
            "=" * 110,
            "SMART AI — CONVERSATION HARDENING BENCHMARK",
            "=" * 110,
            f"Generated at   : {timezone.now().isoformat()}",
            f"User ID       : {user.pk}",
            (
                "Mode          : "
                f"{'FULL PIPELINE' if full_pipeline else 'CONTEXT ONLY'}"
            ),
            f"Delay         : {delay:.1f} detik",
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
                        f"[HARDENING TEST] {scenario.name}"
                    ),
                )

                created_conversation_ids.append(
                    conversation.pk
                )

                report_lines.extend([
                    "",
                    "=" * 110,
                    (
                        f"SCENARIO #{scenario_index}: "
                        f"{scenario.name}"
                    ),
                    "=" * 110,
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

                        context = result.get(
                            "conversation_context",
                            {},
                        )

                        validation = self._validate_turn(
                            turn=turn,
                            context=context,
                        )

                        if validation["passed"]:
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

                        self._increment_summary(
                            summary=summary,
                            context=context,
                            result=result,
                            full_pipeline=full_pipeline,
                        )

                        report_lines.extend(
                            self._format_turn_report(
                                turn_index=turn_index,
                                turn=turn,
                                result=result,
                                validation=validation,
                            )
                        )

                        symbol = (
                            "PASS"
                            if validation["passed"]
                            else "FAIL"
                        )

                        self.stdout.write(
                            (
                                f"[{scenario.name}] "
                                f"Turn {turn_index}: {symbol} | "
                                f"{context.get('conversation_relation')} "
                                f"| similarity="
                                f"{self._format_similarity(context)}"
                            )
                        )

                    except Exception as exc:
                        summary["errors"] += 1

                        error_case = {
                            "scenario": scenario.name,
                            "turn_index": turn_index,
                            "user_message": turn.message,
                            "error_type": type(exc).__name__,
                            "error_message": str(exc),
                        }

                        error_cases.append(error_case)

                        report_lines.extend([
                            "-" * 110,
                            f"TURN #{turn_index}",
                            "-" * 110,
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

                    # Delay berlaku untuk context-only maupun full pipeline.
                    if delay > 0:
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
                full_pipeline=full_pipeline,
                delay=delay,
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
        self.stdout.write(
            f"Mode        : "
            f"{'FULL PIPELINE' if full_pipeline else 'CONTEXT ONLY'}"
        )
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
            if summary["failed"]
            else self.style.SUCCESS
        )
        self.stdout.write(
            failed_style(
                f"Failed      : {summary['failed']}"
            )
        )

        error_style = (
            self.style.ERROR
            if summary["errors"]
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
                scenario.name
                for scenario in SCENARIOS
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

            assistant_text = (
                rag_result.get("reply")
                or "(Tidak ada reply)"
            )

            ChatMessage.objects.create(
                conversation=conversation,
                role="assistant",
                text=assistant_text,
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
                "final_check_warnings": rag_result.get(
                    "final_check_warnings",
                    [],
                ),
                "process_time": (
                    time.perf_counter() - started_at
                ),
            }

        context = resolve_conversation_context(
            user_message=message,
            conversation_id=conversation.pk,
            is_first_message=is_first_message,
        )

        assistant_text = (
            "[CONTEXT HARDENING TEST] "
            f"relation={context.get('conversation_relation')}; "
            f"topic={self._active_topic_summary(context)}"
        )

        ChatMessage.objects.create(
            conversation=conversation,
            role="assistant",
            text=assistant_text,
        )

        return {
            "user_message_id": user_message.pk,
            "conversation_context": context,
            "reply": assistant_text,
            "answer_mode": "CONTEXT_ONLY",
            "intent": None,
            "verification_status": None,
            "final_check_passed": None,
            "final_check_warnings": [],
            "process_time": (
                time.perf_counter() - started_at
            ),
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
                    "conversation_relation: expected one of "
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

            if actual_changed != turn.expected_topic_changed:
                failures.append(
                    (
                        "topic_changed: "
                        f"expected={turn.expected_topic_changed}, "
                        f"actual={actual_changed}"
                    )
                )

        if turn.expected_follow_up is not None:
            actual_follow_up = bool(
                context.get("is_follow_up")
            )

            if actual_follow_up != turn.expected_follow_up:
                failures.append(
                    (
                        "is_follow_up: "
                        f"expected={turn.expected_follow_up}, "
                        f"actual={actual_follow_up}"
                    )
                )

        resolved_query = (
            context.get("resolved_query")
            or ""
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

        for excluded_text in turn.expected_query_excludes:
            if excluded_text.lower() in resolved_query:
                failures.append(
                    (
                        "resolved_query masih mengandung topik lama "
                        f"'{excluded_text}'. "
                        f"actual='{resolved_query}'"
                    )
                )

        return {
            "passed": not failures,
            "failures": failures,
        }

    def _increment_summary(
        self,
        summary: dict[str, int],
        context: dict[str, Any],
        result: dict[str, Any],
        full_pipeline: bool,
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

        key = relation_map.get(relation)

        if key:
            summary[key] += 1

        if context.get("topic_changed"):
            summary["topic_changed"] += 1

        if context.get("should_include_history"):
            summary["history_included"] += 1
        else:
            summary["history_excluded"] += 1

        if context.get(
            "used_llm_topic_classifier"
        ):
            summary[
                "llm_topic_classifier_used"
            ] += 1

        if full_pipeline:
            summary["full_pipeline_turns"] += 1

            if result.get("final_check_passed") is False:
                summary["final_check_failed"] += 1

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

        previous_topic = (
            context.get("previous_topic")
            or {}
        )

        active_topic = (
            context.get("active_topic")
            or {}
        )

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
            "expected_follow_up": (
                turn.expected_follow_up
            ),
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
            "previous_topic": previous_topic,
            "active_topic": active_topic,
            "resolved_query": context.get(
                "resolved_query"
            ),
            "answer_mode": result.get("answer_mode"),
            "intent": result.get("intent"),
            "verification_status": result.get(
                "verification_status"
            ),
            "final_check_passed": result.get(
                "final_check_passed"
            ),
            "validation_failures": validation.get(
                "failures",
                [],
            ),
            "test_note": turn.note,
        }

    def _format_turn_report(
        self,
        turn_index: int,
        turn: ConversationTurn,
        result: dict[str, Any],
        validation: dict[str, Any],
    ):
        context = result.get(
            "conversation_context",
            {},
        )

        previous_topic = (
            context.get("previous_topic")
            or {}
        )

        active_topic = (
            context.get("active_topic")
            or {}
        )

        intent = result.get("intent")

        if isinstance(intent, dict):
            intent_value = intent.get("intent")
        else:
            intent_value = intent

        lines = [
            "-" * 110,
            f"TURN #{turn_index}",
            "-" * 110,
            f"USER: {turn.message}",
            (
                "EXPECTED RELATION: "
                f"{', '.join(sorted(turn.expected_relations))}"
            ),
            (
                "ACTUAL RELATION  : "
                f"{context.get('conversation_relation')}"
            ),
            (
                "RESULT           : "
                f"{'PASS' if validation['passed'] else 'FAIL'}"
            ),
            (
                "FOLLOW-UP TYPE   : "
                f"{context.get('follow_up_type')}"
            ),
            (
                "IS FOLLOW-UP     : "
                f"{context.get('is_follow_up')}"
            ),
            (
                "TOPIC CHANGED    : "
                f"{context.get('topic_changed')}"
            ),
            (
                "INCLUDE HISTORY  : "
                f"{context.get('should_include_history')}"
            ),
            (
                "TOPIC SIMILARITY : "
                f"{self._format_similarity(context)}"
            ),
            (
                "CONTEXT CONFIDENCE: "
                f"{context.get('context_confidence')}"
            ),
            (
                "USED LLM CLASSIFIER: "
                f"{context.get('used_llm_topic_classifier')}"
            ),
            (
                "REASONING CODE   : "
                f"{context.get('reasoning_code')}"
            ),
            (
                "PREVIOUS TOPIC   : "
                f"{previous_topic.get('summary')}"
            ),
            (
                "ACTIVE TOPIC     : "
                f"{active_topic.get('summary')}"
            ),
            (
                "RESOLVED QUERY   : "
                f"{context.get('resolved_query')}"
            ),
            (
                "ANSWER MODE      : "
                f"{result.get('answer_mode')}"
            ),
            f"INTENT           : {intent_value}",
            (
                "VERIFICATION     : "
                f"{result.get('verification_status')}"
            ),
            (
                "FINAL CHECK PASS : "
                f"{result.get('final_check_passed')}"
            ),
            (
                "PROCESS TIME     : "
                f"{result.get('process_time', 0):.4f} detik"
            ),
        ]

        if turn.note:
            lines.append(
                f"TEST NOTE        : {turn.note}"
            )

        if validation["failures"]:
            lines.extend([
                "",
                "VALIDATION FAILURES:",
            ])

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

    def _build_summary_report(
        self,
        summary: dict[str, int],
        failed_cases: list[dict[str, Any]],
        error_cases: list[dict[str, Any]],
        full_pipeline: bool,
        delay: float,
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
            "=" * 110,
            "SUMMARY",
            "=" * 110,
            (
                "mode                        : "
                f"{'FULL_PIPELINE' if full_pipeline else 'CONTEXT_ONLY'}"
            ),
            f"delay_seconds               : {delay:.1f}",
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
                "history_excluded            : "
                f"{summary['history_excluded']}"
            ),
            (
                "llm_topic_classifier_used   : "
                f"{summary['llm_topic_classifier_used']}"
            ),
            (
                "full_pipeline_turns         : "
                f"{summary['full_pipeline_turns']}"
            ),
            (
                "final_check_failed          : "
                f"{summary['final_check_failed']}"
            ),
            "",
            f"PASS RATE: {pass_rate:.2f}%",
            "",
            "=" * 110,
            "FAILED CASE SUMMARY",
            "=" * 110,
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
                lines.extend([
                    "-" * 110,
                    (
                        f"FAILED CASE #{index} | "
                        f"SCENARIO: {case['scenario']} | "
                        f"TURN: {case['turn_index']}"
                    ),
                    "-" * 110,
                    f"USER: {case['user_message']}",
                    (
                        "EXPECTED RELATION: "
                        f"{case['expected_relations']}"
                    ),
                    (
                        "ACTUAL RELATION  : "
                        f"{case['actual_relation']}"
                    ),
                    (
                        "SIMILARITY       : "
                        f"{case['topic_similarity']}"
                    ),
                    (
                        "LLM CLASSIFIER   : "
                        f"{case['used_llm_topic_classifier']}"
                    ),
                    (
                        "REASONING CODE   : "
                        f"{case['reasoning_code']}"
                    ),
                    (
                        "PREVIOUS TOPIC   : "
                        f"{case['previous_topic']}"
                    ),
                    (
                        "ACTIVE TOPIC     : "
                        f"{case['active_topic']}"
                    ),
                    (
                        "RESOLVED QUERY   : "
                        f"{case['resolved_query']}"
                    ),
                    "VALIDATION FAILURES:",
                ])

                for failure in case[
                    "validation_failures"
                ]:
                    lines.append(f"- {failure}")

                if case.get("test_note"):
                    lines.append(
                        f"TEST NOTE: {case['test_note']}"
                    )

                lines.append("")

        lines.extend([
            "=" * 110,
            "ERROR CASE SUMMARY",
            "=" * 110,
        ])

        if not error_cases:
            lines.extend([
                "Tidak ada error case.",
                "",
            ])
        else:
            for index, case in enumerate(
                error_cases,
                start=1,
            ):
                lines.extend([
                    "-" * 110,
                    (
                        f"ERROR CASE #{index} | "
                        f"SCENARIO: {case['scenario']} | "
                        f"TURN: {case['turn_index']}"
                    ),
                    "-" * 110,
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
            "=" * 110,
            "COMPACT REVIEW PAYLOAD",
            "=" * 110,
            (
                "Kirim bagian JSON ini untuk analisis lanjutan."
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

    def _format_similarity(
        self,
        context: dict[str, Any],
    ):
        similarity = context.get(
            "topic_similarity"
        )

        if similarity is None:
            return "None"

        try:
            return f"{float(similarity):.4f}"
        except (TypeError, ValueError):
            return str(similarity)

    def _active_topic_summary(
        self,
        context: dict[str, Any],
    ):
        active_topic = (
            context.get("active_topic")
            or {}
        )

        return active_topic.get("summary")
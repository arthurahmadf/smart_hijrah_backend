# main/utils_rag/integration.py

from __future__ import annotations

from main.fallback_ai_client import get_islamic_response
from main.models_ai import ChatMessage
from main.utils_rag.answer_strategy import (
    select_answer_strategy,
)
from main.utils_rag.answer_strategy_prompt import (
    build_answer_strategy_prompt,
)
from main.utils_rag.conversation_context import (
    resolve_conversation_context,
)
from main.utils_rag.direct_lookup import try_direct_lookup
from main.utils_rag.evidence_composer import (
    compose_evidence_grounded_answer,
    compose_thematic_retrieval_answer,
)
from main.utils_rag.extractor import extract_claims
from main.utils_rag.final_checker import apply_final_checks
from main.utils_rag.followup_compression import (
    build_followup_policy,
    build_followup_prompt_instruction,
)
from main.utils_rag.router import (
    IntentType,
    classify_intent,
)
from main.utils_rag.thematic_retrieval import (
    retrieve_thematic_evidence,
)
from main.utils_rag.verifier_guardrails import (
    verify_and_apply_guardrails,
)


def _get_previous_assistant_text(
    conversation_id,
) -> str:
    """
    Ambil jawaban assistant terakhir sebelum jawaban saat ini dibuat.

    Pesan user terbaru sudah tersimpan di database, tetapi jawaban
    assistant untuk turn tersebut belum disimpan ketika integration
    dipanggil. Karena itu latest assistant adalah jawaban turn lama.
    """
    if not conversation_id:
        return ""

    previous_message = (
        ChatMessage.objects.filter(
            conversation_id=conversation_id,
            role="assistant",
        )
        .order_by("-created_at", "-id")
        .only("text")
        .first()
    )

    if previous_message is None:
        return ""

    return (
        previous_message.text or ""
    ).strip()


class RAGIntegration:
    @staticmethod
    def generate_metode7_response(
        user_message,
        conversation_id=None,
        is_first_message=True,
    ):
        # =====================================================
        # PHASE 4C: CONVERSATION CONTEXT
        # =====================================================
        conversation_context = resolve_conversation_context(
            user_message=user_message,
            conversation_id=conversation_id,
            is_first_message=is_first_message,
        )

        effective_message = conversation_context.get(
            "resolved_query",
            user_message,
        )

        should_include_history = bool(
            conversation_context.get(
                "should_include_history",
                False,
            )
        )

        print(
            "[SMART AI] Conversation relation: "
            f"{conversation_context.get('conversation_relation')} | "
            "topic_changed="
            f"{conversation_context.get('topic_changed')} | "
            "similarity="
            f"{conversation_context.get('topic_similarity')} | "
            "llm_fallback="
            f"{conversation_context.get('used_llm_topic_classifier')} | "
            "include_history="
            f"{should_include_history}"
        )

        print(
            "\n[SMART AI] Memulai pemrosesan untuk: "
            f"'{user_message[:40]}...'"
        )

        # =====================================================
        # PHASE 2: INTENT ROUTER
        # =====================================================
        intent_result = classify_intent(
            effective_message
        )

        intent = intent_result["intent"]

        print(
            f"[SMART AI] Intent: {intent} | "
            f"Confidence: {intent_result.get('confidence')}"
        )

        # =====================================================
        # PHASE 5A: BASE ANSWER STRATEGY
        # =====================================================
        base_strategy = select_answer_strategy(
            intent=intent_result,
            conversation_context=conversation_context,
            verified_sources=[],
        )

        followup_policy = build_followup_policy(
            user_message=user_message,
            strategy=base_strategy,
            conversation_context=conversation_context,
        )

        previous_assistant_text = ""

        if followup_policy.enabled:
            previous_assistant_text = (
                _get_previous_assistant_text(
                    conversation_id=conversation_id,
                )
            )

        base_strategy_prompt = (
            build_answer_strategy_prompt(
                strategy=base_strategy,
                conversation_context=conversation_context,
            )
        )

        followup_prompt = (
            build_followup_prompt_instruction(
                followup_policy
            )
        )

        if followup_prompt:
            base_strategy_prompt = (
                f"{base_strategy_prompt}\n\n"
                f"{followup_prompt}"
            )

        print(
            "[SMART AI] Follow-up policy: "
            f"enabled={followup_policy.enabled} | "
            f"aspect={followup_policy.requested_aspect} | "
            f"max_paragraphs={followup_policy.max_paragraphs}"
        )

        # =====================================================
        # OUT OF DOMAIN
        # =====================================================
        if intent == IntentType.OUT_OF_DOMAIN:
            return {
                "reply": (
                    "Maaf, saya adalah asisten khusus untuk "
                    "pertanyaan seputar Islam. Saya tidak dapat "
                    "menjawab pertanyaan di luar lingkup tersebut."
                ),
                "verification_status": "OUT_OF_DOMAIN",
                "verified_sources": [],
                "displayed_sources": [],
                "raw_output_debug": None,
                "answer_mode": "OUT_OF_DOMAIN",
                "intent": intent_result,
                "final_check_warnings": [],
                "final_check_passed": True,
                "composer": "OUT_OF_DOMAIN_TEMPLATE",
                "conversation_context": conversation_context,
                "answer_strategy": base_strategy.to_dict(),
                "followup_policy": followup_policy.to_dict(),
            }

        # =====================================================
        # PHASE 1 / 1B: DIRECT LOOKUP
        # =====================================================
        direct_result = try_direct_lookup(
            effective_message,
            is_first_message=is_first_message,
        )

        if direct_result:
            direct_sources = direct_result.get(
                "verified_sources",
                [],
            )

            direct_strategy = select_answer_strategy(
                intent=intent_result,
                conversation_context=conversation_context,
                verified_sources=direct_sources,
            )

            direct_followup_policy = (
                build_followup_policy(
                    user_message=user_message,
                    strategy=direct_strategy,
                    conversation_context=conversation_context,
                )
            )

            print(
                "[SMART AI] Direct Lookup Mode aktif. "
                "LLM dilewati."
            )

            direct_result.update({
                "intent": intent_result,
                "final_check_warnings": [],
                "final_check_passed": True,
                "composer": "DIRECT_LOOKUP_TEMPLATE",
                "conversation_context": conversation_context,
                "answer_strategy": direct_strategy.to_dict(),
                "followup_policy": (
                    direct_followup_policy.to_dict()
                ),
            })

            return direct_result

        # =====================================================
        # PHASE 4B: RETRIEVAL-FIRST THEMATIC SEARCH
        # =====================================================
        if intent == IntentType.THEMATIC_DALIL_SEARCH:
            print(
                "[SMART AI] Thematic Retrieval Mode aktif. "
                "LLM dilewati."
            )

            retrieval_result = retrieve_thematic_evidence(
                user_query=effective_message,
                quran_limit=3,
                hadith_limit=3,
            )

            thematic_sources = retrieval_result.get(
                "verified_sources",
                [],
            )

            thematic_strategy = select_answer_strategy(
                intent=intent_result,
                conversation_context=conversation_context,
                verified_sources=thematic_sources,
            )

            thematic_followup_policy = (
                build_followup_policy(
                    user_message=user_message,
                    strategy=thematic_strategy,
                    conversation_context=conversation_context,
                )
            )

            composed = compose_thematic_retrieval_answer(
                user_query=effective_message,
                intent_result=intent_result,
                retrieval_result=retrieval_result,
                is_first_message=is_first_message,
                conversation_context=conversation_context,
                strategy=thematic_strategy,
                followup_policy=(
                    thematic_followup_policy
                ),
                previous_assistant_text=(
                    previous_assistant_text
                ),
            )

            composed_sources = composed.get(
                "verified_sources",
                [],
            )

            final_check = apply_final_checks(
                reply=composed.get(
                    "narrative_text",
                    "",
                ),
                verified_sources=composed_sources,
                status_global=composed.get(
                    "verification_status",
                    "NEEDS_REVIEW",
                ),
            )

            return {
                "reply": composed["reply"],
                "verification_status": final_check[
                    "verification_status"
                ],
                "verified_sources": composed_sources,
                "displayed_sources": composed.get(
                    "displayed_sources",
                    composed_sources,
                ),
                "raw_output_debug": None,
                "answer_mode": "THEMATIC_RETRIEVAL",
                "intent": intent_result,
                "final_check_warnings": final_check[
                    "final_check_warnings"
                ],
                "final_check_passed": final_check[
                    "final_check_passed"
                ],
                "composer": composed.get(
                    "composer",
                    "THEMATIC_NATURAL_FOLLOWUP_V1",
                ),
                "retrieval_debug": {
                    "theme": retrieval_result.get(
                        "theme"
                    ),
                    "source_preference": (
                        retrieval_result.get(
                            "source_preference"
                        )
                    ),
                    "quran_count": retrieval_result.get(
                        "quran_count"
                    ),
                    "hadith_count": retrieval_result.get(
                        "hadith_count"
                    ),
                },
                "conversation_context": conversation_context,
                "answer_strategy": composed.get(
                    "strategy",
                    thematic_strategy.to_dict(),
                ),
                "followup_policy": composed.get(
                    "followup_policy",
                    thematic_followup_policy.to_dict(),
                ),
            }

        # =====================================================
        # PHASE 5A.3 + 5A.4: STRATEGY-AWARE LLM DRAFT
        # =====================================================
        raw_llm_output = get_islamic_response(
            user_message=effective_message,
            conversation_id=conversation_id,
            is_first_message=is_first_message,
            use_metode7=True,

            # Pesan asli yang sudah tersimpan harus dikecualikan
            # dari selective conversation history.
            current_db_message=user_message,

            include_conversation_history=(
                should_include_history
            ),

            answer_strategy_prompt=(
                base_strategy_prompt
            ),
        )

        clean_text, claims = extract_claims(
            raw_llm_output
        )

        print(
            f"[SMART AI] Ditemukan {len(claims)} "
            "klaim dalil dari LLM."
        )

        # =====================================================
        # PHASE 3: VERIFIER + GUARDRAILS
        # =====================================================
        verified_sources, status_global = (
            verify_and_apply_guardrails(
                claims,
                user_query=effective_message,
            )
        )

        answer_strategy = select_answer_strategy(
            intent=intent_result,
            conversation_context=conversation_context,
            verified_sources=verified_sources,
        )

        final_followup_policy = (
            build_followup_policy(
                user_message=user_message,
                strategy=answer_strategy,
                conversation_context=conversation_context,
            )
        )

        # =====================================================
        # PHASE 4A + PHASE 5A.4: NATURAL FOLLOW-UP COMPOSER
        # =====================================================
        grounded = compose_evidence_grounded_answer(
            user_query=effective_message,
            intent_result=intent_result,
            draft_text=clean_text,
            verified_sources=verified_sources,
            status_global=status_global,
            is_first_message=is_first_message,
            conversation_context=conversation_context,
            strategy=answer_strategy,
            followup_policy=final_followup_policy,
            previous_assistant_text=(
                previous_assistant_text
            ),
        )

        grounded_sources = grounded.get(
            "verified_sources",
            verified_sources,
        )

        grounded_status = grounded.get(
            "verification_status",
            status_global,
        )

        # =====================================================
        # PHASE 3: FINAL CHECKER
        # =====================================================
        final_check = apply_final_checks(
            reply=grounded.get(
                "narrative_text",
                grounded.get("reply", ""),
            ),
            verified_sources=grounded_sources,
            status_global=grounded_status,
        )

        print(
            "[SMART AI] Status sebelum final check: "
            f"{grounded_status}"
        )
        print(
            "[SMART AI] Status setelah final check: "
            f"{final_check['verification_status']}"
        )
        print(
            "[SMART AI] Final warnings: "
            f"{len(final_check['final_check_warnings'])}"
        )
        print(
            "[SMART AI] Composer: "
            f"{grounded.get('composer')}"
        )

        return {
            "reply": grounded["reply"],
            "verification_status": final_check[
                "verification_status"
            ],
            "verified_sources": grounded_sources,
            "displayed_sources": grounded.get(
                "displayed_sources",
                grounded_sources,
            ),
            "raw_output_debug": raw_llm_output,
            "raw_clean_text_debug": clean_text,
            "answer_mode": "EVIDENCE_GROUNDED",
            "intent": intent_result,
            "final_check_warnings": final_check[
                "final_check_warnings"
            ],
            "final_check_passed": final_check[
                "final_check_passed"
            ],
            "composer": grounded.get(
                "composer",
                "NATURAL_FOLLOWUP_COMPOSER_V1",
            ),
            "conversation_context": conversation_context,
            "answer_strategy": grounded.get(
                "strategy",
                answer_strategy.to_dict(),
            ),
            "followup_policy": grounded.get(
                "followup_policy",
                final_followup_policy.to_dict(),
            ),
        }
# main/utils_rag/integration.py
from main.fallback_ai_client import get_islamic_response
from main.utils_rag.extractor import extract_claims
from main.utils_rag.verifier_guardrails import verify_and_apply_guardrails
from main.utils_rag.direct_lookup import try_direct_lookup
from main.utils_rag.router import classify_intent, IntentType
from main.utils_rag.final_checker import apply_final_checks
from main.utils_rag.evidence_composer import compose_evidence_grounded_answer


class RAGIntegration:
    @staticmethod
    def generate_metode7_response(user_message, conversation_id=None, is_first_message=True):
        print(f"\n[SMART AI] Memulai pemrosesan untuk: '{user_message[:40]}...'")

        intent_result = classify_intent(user_message)
        intent = intent_result["intent"]

        print(f"[SMART AI] Intent: {intent} | Confidence: {intent_result['confidence']}")

        # =========================================================
        # OUT OF DOMAIN
        # =========================================================
        if intent == IntentType.OUT_OF_DOMAIN:
            return {
                "reply": (
                    "Maaf, saya adalah asisten khusus untuk pertanyaan seputar Islam. "
                    "Saya tidak dapat menjawab pertanyaan di luar lingkup tersebut."
                ),
                "verification_status": "OUT_OF_DOMAIN",
                "verified_sources": [],
                "raw_output_debug": None,
                "answer_mode": "OUT_OF_DOMAIN",
                "intent": intent_result,
                "final_check_warnings": [],
                "final_check_passed": True,
                "composer": "OUT_OF_DOMAIN_TEMPLATE",
            }

        # =========================================================
        # DIRECT LOOKUP
        # =========================================================
        direct_result = try_direct_lookup(
            user_message,
            is_first_message=is_first_message
        )

        if direct_result:
            print("[SMART AI] Direct Lookup Mode aktif. LLM dilewati.")
            direct_result["intent"] = intent_result
            direct_result["final_check_warnings"] = []
            direct_result["final_check_passed"] = True
            direct_result["composer"] = "DIRECT_LOOKUP_TEMPLATE"
            return direct_result

        # =========================================================
        # LLM DRAFT UNTUK MENGHASILKAN KLAIM DALIL
        # Catatan:
        # Draft ini TIDAK lagi langsung dikirim ke user.
        # =========================================================
        raw_llm_output = get_islamic_response(
            user_message,
            conversation_id=conversation_id,
            is_first_message=is_first_message,
            use_metode7=True
        )

        clean_text, claims = extract_claims(raw_llm_output)
        print(f"[SMART AI] Ditemukan {len(claims)} klaim dalil dari LLM.")

        verified_sources, status_global = verify_and_apply_guardrails(
            claims,
            user_query=user_message
        )

        # =========================================================
        # PHASE 4A: EVIDENCE-GROUNDED COMPOSER
        # Final answer dibuat ulang dari verified_sources.
        # =========================================================
        grounded = compose_evidence_grounded_answer(
            user_query=user_message,
            intent_result=intent_result,
            draft_text=clean_text,
            verified_sources=verified_sources,
            status_global=status_global,
            is_first_message=is_first_message,
        )

        final_check = apply_final_checks(
            reply=grounded["reply"],
            verified_sources=verified_sources,
            status_global=status_global
        )

        print(f"[SMART AI] Status sebelum final check: {status_global}")
        print(f"[SMART AI] Status setelah final check: {final_check['verification_status']}")
        print(f"[SMART AI] Final warnings: {len(final_check['final_check_warnings'])}")
        print(f"[SMART AI] Composer: {grounded['composer']}")

        return {
            "reply": final_check["reply"],
            "verification_status": final_check["verification_status"],
            "verified_sources": verified_sources,
            "raw_output_debug": raw_llm_output,
            "raw_clean_text_debug": clean_text,
            "answer_mode": "EVIDENCE_GROUNDED",
            "intent": intent_result,
            "final_check_warnings": final_check["final_check_warnings"],
            "final_check_passed": final_check["final_check_passed"],
            "composer": grounded["composer"],
        }
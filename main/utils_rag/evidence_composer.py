# main/utils_rag/evidence_composer.py
import re
from main.utils_rag.router import IntentType


def _norm(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _opening(is_first_message: bool) -> str:
    if is_first_message:
        return (
            "Assalamu’alaikum warahmatullahi wabarakatuh.\n\n"
            "Saya Smart Hijrah Assistant. Berikut jawaban berdasarkan rujukan yang berhasil "
            "diverifikasi dalam database Smart Hijrah."
        )

    return (
        "Berikut jawaban berdasarkan rujukan yang berhasil diverifikasi dalam database Smart Hijrah."
    )


def _split_sources(verified_sources):
    quran_sources = []
    hadith_sources = []
    external_sources = []
    unverified_sources = []

    for src in verified_sources or []:
        if not src.get("is_verified"):
            unverified_sources.append(src)
            continue

        stype = src.get("type")

        if stype == "QURAN":
            quran_sources.append(src)
        elif stype == "HADIS":
            hadith_sources.append(src)
        elif stype == "EKSTERNAL":
            external_sources.append(src)

    return quran_sources, hadith_sources, external_sources, unverified_sources


def _format_references(quran_sources, hadith_sources, external_sources, unverified_sources):
    lines = []

    if quran_sources:
        lines.append("**Dalil Al-Qur’an yang terverifikasi:**")
        for idx, src in enumerate(quran_sources, 1):
            ref = src.get("reference", "Rujukan Al-Qur’an")
            translation = src.get("translation_text", "")
            lines.append(f"{idx}. **{ref}**")
            if translation:
                lines.append(f"   > {translation}")

    if hadith_sources:
        if lines:
            lines.append("")
        lines.append("**Hadis yang ditemukan dalam database:**")
        for idx, src in enumerate(hadith_sources, 1):
            ref = src.get("reference", "Rujukan Hadis")
            translation = src.get("translation_text", "")
            lines.append(f"{idx}. **{ref}**")
            if translation:
                lines.append(f"   > {translation}")

    if external_sources:
        if lines:
            lines.append("")
        lines.append("**Rujukan eksternal/kajian ulama:**")
        for idx, src in enumerate(external_sources, 1):
            ref = src.get("reference", "Rujukan eksternal")
            lines.append(f"{idx}. {ref}")

    if unverified_sources:
        if lines:
            lines.append("")
        lines.append("**Rujukan yang belum terverifikasi:**")
        for idx, src in enumerate(unverified_sources, 1):
            ref = src.get("reference", "Rujukan tidak ditemukan")
            lines.append(f"{idx}. {ref}")

    if not lines:
        return (
            "**Rujukan:**\n"
            "⚠️ Belum ada rujukan spesifik yang berhasil diverifikasi dari database Smart Hijrah."
        )

    return "\n".join(lines)


def _compose_paylater_answer(query):
    return (
        "**Jawaban ringkas:**\n"
        "Paylater tidak bisa dihukumi satu jawaban untuk semua kasus. Hukumnya bergantung pada akad dan ketentuannya.\n\n"
        "Secara umum, paylater dapat bermasalah jika mengandung **riba**, seperti bunga keterlambatan atau tambahan berbasis waktu "
        "atas utang. Ia juga bermasalah jika mengandung **gharar**, yaitu ketidakjelasan biaya, denda, jangka waktu, atau kewajiban pihak-pihak terkait.\n\n"
        "Namun, jika akadnya jelas, harga disepakati sejak awal, tidak ada bunga/riba, tidak ada denda yang bersifat keuntungan, "
        "dan objek transaksinya halal, maka pembahasannya masuk ke wilayah muamalah yang perlu dilihat detail akadnya."
    )


def _compose_investment_answer(query):
    return (
        "**Jawaban ringkas:**\n"
        "Investasi pada dasarnya boleh dalam Islam selama objek dan mekanismenya halal.\n\n"
        "Yang perlu diperiksa adalah: tidak ada riba, tidak ada gharar berlebihan, tidak ada maysir/spekulasi judi, "
        "dana tidak ditempatkan pada bisnis haram, serta akad dan biaya transparan.\n\n"
        "Untuk saham, trading, reksa dana, aplikasi investasi, atau instrumen modern lainnya, hukumnya sangat bergantung pada "
        "produk dan mekanisme transaksinya. Karena itu, sebaiknya memilih instrumen yang memiliki pengawasan atau keterangan syariah "
        "yang jelas."
    )


def _compose_sexual_content_answer(query):
    return (
        "**Jawaban ringkas:**\n"
        "Menonton konten pornografis atau yang membangkitkan syahwat secara sengaja tidak dibolehkan dalam Islam.\n\n"
        "Alasannya, seorang Muslim diperintahkan menjaga pandangan, menjaga hati, dan menjauhi hal-hal yang dapat membuka pintu maksiat. "
        "Jika konten tersebut menampilkan aurat, adegan seksual, atau sengaja dibuat untuk membangkitkan syahwat, maka sebaiknya ditinggalkan.\n\n"
        "Jika pernah terlanjur, jalan keluarnya adalah bertaubat, menghentikan aksesnya, menjauhi pemicunya, dan menggantinya dengan "
        "kegiatan atau tontonan yang halal dan bermanfaat."
    )


def _compose_shalat_istiqamah_answer(query):
    return (
        "**Jawaban ringkas:**\n"
        "Kesulitan istiqamah shalat adalah ujian yang banyak orang alami, tetapi tetap harus dilawan dengan langkah bertahap dan serius.\n\n"
        "Beberapa langkah praktis:\n"
        "1. Mulai dari menjaga shalat wajib tepat waktu semampunya.\n"
        "2. Gunakan alarm atau pengingat adzan.\n"
        "3. Kurangi pemicu yang membuat sering menunda.\n"
        "4. Cari teman atau lingkungan yang membantu menjaga shalat.\n"
        "5. Jika tertinggal, jangan putus asa; segera kembali dan perbaiki shalat berikutnya.\n\n"
        "Yang penting adalah tidak menyerah. Istiqamah biasanya tumbuh dari usaha kecil yang diulang terus-menerus."
    )


def _compose_generic_fiqh_answer(query):
    return (
        "**Jawaban ringkas:**\n"
        "Masalah ini perlu dilihat dari prinsip umum syariat: apakah mengandung unsur haram, riba, gharar, kezaliman, membuka pintu maksiat, "
        "atau melalaikan kewajiban.\n\n"
        "Jika unsur-unsur tersebut ada, maka hukumnya bisa terlarang atau minimal perlu dihindari. Jika tidak ada unsur haram dan manfaatnya jelas, "
        "maka pada dasarnya perkara muamalah atau kebiasaan duniawi bisa menjadi boleh, selama tidak bertentangan dengan syariat.\n\n"
        "Untuk kasus yang detail, keputusan akhirnya bergantung pada rincian praktiknya."
    )


def _compose_generic_dalil_answer(query):
    return (
        "**Jawaban ringkas:**\n"
        "Berikut beberapa rujukan yang relevan berdasarkan hasil verifikasi database Smart Hijrah. "
        "Daftar ini bukan berarti seluruh dalil tentang tema tersebut, tetapi rujukan yang berhasil ditemukan dan diverifikasi."
    )


def _compose_generic_advice_answer(query):
    return (
        "**Jawaban ringkas:**\n"
        "Dalam kondisi seperti ini, Islam mengajarkan agar seorang Muslim tetap kembali kepada Allah, tidak berputus asa, "
        "dan memperbaiki diri secara bertahap.\n\n"
        "Mulailah dari langkah kecil yang konsisten, perbanyak doa, jaga lingkungan yang baik, dan jangan biarkan rasa bersalah membuat Anda berhenti berusaha."
    )


def _compose_by_intent(user_query, intent_type):
    q = _norm(user_query)

    if "paylater" in q or "pay later" in q:
        return _compose_paylater_answer(user_query)

    if any(k in q for k in ["saham", "trading", "investasi", "crypto", "kripto", "forex", "reksadana", "reksa dana", "emas digital"]):
        return _compose_investment_answer(user_query)

    if any(k in q for k in ["hentai", "pornografi", "porno", "konten dewasa", "video dewasa", "syahwat"]):
        return _compose_sexual_content_answer(user_query)

    if any(k in q for k in ["susah istiqamah shalat", "sulit istiqamah shalat", "malas shalat", "malas sholat", "istiqamah shalat"]):
        return _compose_shalat_istiqamah_answer(user_query)

    if intent_type == IntentType.THEMATIC_DALIL_SEARCH:
        return _compose_generic_dalil_answer(user_query)

    if intent_type == IntentType.SPIRITUAL_ADVICE:
        return _compose_generic_advice_answer(user_query)

    if intent_type in [IntentType.FIQH_QA, IntentType.FATWA_QA]:
        return _compose_generic_fiqh_answer(user_query)

    return (
        "**Jawaban ringkas:**\n"
        "Berikut penjelasan umum berdasarkan rujukan yang berhasil diverifikasi dalam database Smart Hijrah."
    )


def compose_evidence_grounded_answer(
    user_query,
    intent_result,
    draft_text,
    verified_sources,
    status_global,
    is_first_message=True,
):
    """
    Phase 4A MVP:
    - Tidak memakai draft LLM sebagai final answer.
    - Draft LLM hanya dipakai sebagai proses awal untuk menghasilkan klaim dalil.
    - Final answer dirender ulang dari:
      1. intent
      2. user_query
      3. verified_sources
    """
    intent_type = None
    if isinstance(intent_result, dict):
        intent_type = intent_result.get("intent")

    quran_sources, hadith_sources, external_sources, unverified_sources = _split_sources(verified_sources)

    answer_body = _compose_by_intent(user_query, intent_type)
    references_block = _format_references(
        quran_sources,
        hadith_sources,
        external_sources,
        unverified_sources
    )

    caution = ""
    if status_global != "HIGH_CONFIDENCE":
        caution = (
            "\n\n**Catatan kehati-hatian:**\n"
            "Sebagian rujukan belum berhasil diverifikasi sepenuhnya. Jawaban ini sebaiknya dipahami sebagai penjelasan umum, "
            "bukan fatwa final untuk kasus personal yang kompleks."
        )

    if intent_type == IntentType.FATWA_QA:
        caution += (
            "\n\n**Catatan fatwa:**\n"
            "Untuk masalah kontemporer seperti transaksi digital, investasi, atau produk keuangan, keputusan hukum sangat bergantung "
            "pada detail akad dan praktiknya. Jika menyangkut keputusan finansial nyata, sebaiknya cek fatwa resmi atau konsultasikan "
            "kepada ahli syariah."
        )

    reply = (
        f"{_opening(is_first_message)}\n\n"
        f"{answer_body}\n\n"
        f"{references_block}"
        f"{caution}"
    )

    return {
        "reply": reply,
        "composer": "EVIDENCE_GROUNDED_COMPOSER_V1",
    }
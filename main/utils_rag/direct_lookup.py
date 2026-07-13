# main/utils_rag/direct_lookup.py
from main.models_hadis import Hadis
from main.models_tilawah import TilawahAyahPool
from main.utils_rag.reference_parser import (
    parse_direct_hadith_reference,
    parse_direct_quran_reference,
)


def _opening(is_first_message: bool) -> str:
    if is_first_message:
        return (
            "Assalamu’alaikum warahmatullahi wabarakatuh.\n\n"
            "Saya Smart Hijrah Assistant. Berikut rujukan yang Anda minta "
            "berdasarkan database Smart Hijrah."
        )

    return "Berikut rujukan yang Anda minta berdasarkan database Smart Hijrah."


# =========================================================
# HADIS DIRECT LOOKUP
# =========================================================

def _format_hadith_found(hadis_obj, parsed, is_first_message: bool):
    kitab_name = hadis_obj.kitab.nama_indonesia
    nomor = hadis_obj.nomor

    assumption = ""
    if parsed.get("assumption_note"):
        assumption = f"\n\nCatatan: {parsed['assumption_note']}"

    arabic = hadis_obj.teks_arab or hadis_obj.teks_hadis or "-"
    translation = hadis_obj.terjemahan or hadis_obj.isi_hadis or "-"

    reply = (
        f"{_opening(is_first_message)}"
        f"{assumption}\n\n"
        f"**{kitab_name} No. {nomor}**\n\n"
        f"**Teks Arab:**\n"
        f"{arabic}\n\n"
        f"**Terjemahan:**\n"
        f"{translation}\n\n"
        f"**Status:**\n"
        f"✅ Ditemukan dalam database hadis Smart Hijrah.\n"
        f"ℹ️ Catatan: Status ini berarti rujukan ditemukan di database. "
        f"Derajat hadis seperti sahih/hasan/daif belum ditampilkan kecuali tersedia data takhrij khusus."
    )

    verified_sources = [
        {
            "type": "HADIS",
            "label": "Ditemukan di Database ✅ (Derajat hadis belum ditampilkan)",
            "reference": f"{kitab_name} No. {nomor}",
            "arabic_text": arabic,
            "translation_text": translation,
            "is_verified": True,
            "book_slug": hadis_obj.kitab.nama_file,
            "number": nomor,
            "direct_lookup": True,
        }
    ]

    return {
        "reply": reply,
        "verification_status": "HIGH_CONFIDENCE",
        "verified_sources": verified_sources,
        "raw_output_debug": None,
        "answer_mode": "DIRECT_HADITH_LOOKUP",
    }


def _format_hadith_not_found(parsed, is_first_message: bool):
    book_slug = parsed["book_slug"]
    nomor = parsed["number"]

    display_book = {
        "bukhari": "Shahih Bukhari",
        "muslim": "Shahih Muslim",
        "abu-daud": "Sunan Abu Daud",
        "tirmidzi": "Sunan Tirmidzi",
        "nasai": "Sunan Nasa’i",
        "ibnu-majah": "Sunan Ibnu Majah",
        "malik": "Muwatta Malik",
        "ahmad": "Musnad Ahmad",
        "darimi": "Sunan Darimi",
    }.get(book_slug, book_slug)

    assumption = ""
    if parsed.get("assumption_note"):
        assumption = f"\n\nCatatan: {parsed['assumption_note']}"

    reply = (
        f"{_opening(is_first_message)}"
        f"{assumption}\n\n"
        f"**{display_book} No. {nomor}**\n\n"
        f"**Status:**\n"
        f"⚠️ Nomor hadis tersebut belum ditemukan dalam database Smart Hijrah.\n\n"
        f"Silakan cek kembali nama kitab atau nomor hadisnya. "
        f"Saya tidak akan menampilkan isi hadis jika rujukannya tidak ditemukan di database."
    )

    verified_sources = [
        {
            "type": "HADIS",
            "label": "Belum Terverifikasi ⚠️ (Nomor hadis tidak ditemukan di DB)",
            "reference": f"{display_book} No. {nomor} (Tidak ditemukan di database)",
            "is_verified": False,
            "book_slug": book_slug,
            "number": nomor,
            "direct_lookup": True,
        }
    ]

    return {
        "reply": reply,
        "verification_status": "NOT_FOUND",
        "verified_sources": verified_sources,
        "raw_output_debug": None,
        "answer_mode": "DIRECT_HADITH_LOOKUP",
    }


# =========================================================
# QURAN DIRECT LOOKUP
# =========================================================

def _format_quran_found(ayah_obj, parsed, is_first_message: bool):
    surah_name = ayah_obj.surah_name
    surah_number = ayah_obj.surah_number
    ayah_number = ayah_obj.ayah_number

    arabic = ayah_obj.ayah_text or "-"
    translation = ayah_obj.ayah_translation or "-"
    transliteration = ayah_obj.ayah_transliteration or ""

    transliteration_block = ""
    if transliteration:
        transliteration_block = (
            f"\n\n**Transliterasi:**\n"
            f"{transliteration}"
        )

    reply = (
        f"{_opening(is_first_message)}\n\n"
        f"**QS. {surah_name} ({surah_number}) Ayat {ayah_number}**\n\n"
        f"**Teks Arab:**\n"
        f"{arabic}"
        f"{transliteration_block}\n\n"
        f"**Terjemahan:**\n"
        f"{translation}\n\n"
        f"**Status:**\n"
        f"✅ Ditemukan dalam database Al-Qur’an Smart Hijrah."
    )

    verified_sources = [
        {
            "type": "QURAN",
            "label": "Ditemukan di Database ✅ (Al-Qur’an)",
            "reference": f"QS. {surah_name} ({surah_number}) : {ayah_number}",
            "arabic_text": arabic,
            "translation_text": translation,
            "transliteration_text": transliteration,
            "is_verified": True,
            "surah_number": surah_number,
            "ayah_number": ayah_number,
            "direct_lookup": True,
        }
    ]

    return {
        "reply": reply,
        "verification_status": "HIGH_CONFIDENCE",
        "verified_sources": verified_sources,
        "raw_output_debug": None,
        "answer_mode": "DIRECT_QURAN_LOOKUP",
    }


def _format_quran_not_found(parsed, is_first_message: bool):
    surah_number = parsed["surah_number"]
    ayah_number = parsed["ayah_number"]
    is_valid_surah = parsed.get("is_valid_surah", True)

    if not is_valid_surah:
        reason = (
            f"Nomor surah {surah_number} tidak valid. "
            f"Al-Qur’an terdiri dari 114 surah."
        )
        reference = (
            f"QS. Surah {surah_number} : {ayah_number} "
            f"(Nomor surah tidak valid)"
        )
    else:
        reason = (
            f"Ayat tersebut tidak ditemukan pada surah nomor {surah_number} "
            f"dalam database Al-Qur’an Smart Hijrah."
        )
        reference = (
            f"QS. Surah {surah_number} : {ayah_number} "
            f"(Tidak ditemukan di database)"
        )

    reply = (
        f"{_opening(is_first_message)}\n\n"
        f"**QS. Surah {surah_number} Ayat {ayah_number}**\n\n"
        f"**Status:**\n"
        f"⚠️ {reason}\n\n"
        f"Saya tidak akan menampilkan isi ayat jika rujukannya tidak valid "
        f"atau tidak ditemukan di database."
    )

    verified_sources = [
        {
            "type": "QURAN",
            "label": (
                "Tidak Ditemukan ⚠️ "
                "(Nomor surah/ayat tidak valid atau tidak ada di DB)"
            ),
            "reference": reference,
            "is_verified": False,
            "surah_number": surah_number,
            "ayah_number": ayah_number,
            "direct_lookup": True,
        }
    ]

    return {
        "reply": reply,
        "verification_status": "NOT_FOUND",
        "verified_sources": verified_sources,
        "raw_output_debug": None,
        "answer_mode": "DIRECT_QURAN_LOOKUP",
    }


def try_direct_quran_lookup(user_message: str, is_first_message: bool = True):
    parsed = parse_direct_quran_reference(user_message)

    if not parsed:
        return None
    
    ayah_obj = TilawahAyahPool.objects.filter(
        surah_number=parsed["surah_number"],
        ayah_number=parsed["ayah_number"],
    ).first()

    if ayah_obj:
        return _format_quran_found(ayah_obj, parsed, is_first_message)

    return _format_quran_not_found(parsed, is_first_message)


def try_direct_hadith_lookup(user_message: str, is_first_message: bool = True):
    parsed = parse_direct_hadith_reference(user_message)

    if not parsed:
        return None

    hadis_obj = Hadis.objects.filter(
        kitab__nama_file__iexact=parsed["book_slug"],
        nomor=parsed["number"],
    ).select_related("kitab").first()

    if hadis_obj:
        return _format_hadith_found(hadis_obj, parsed, is_first_message)

    return _format_hadith_not_found(parsed, is_first_message)


# =========================================================
# MASTER DIRECT LOOKUP
# =========================================================

def try_direct_lookup(user_message: str, is_first_message: bool = True):
    """
    Phase 1 + 1B:
    - Quran direct lookup sebelum LLM
    - Hadis direct lookup sebelum LLM
    """

    # Quran dulu, agar "QS 2:255" tidak salah dibaca angka hadis.
    quran_result = try_direct_quran_lookup(
        user_message,
        is_first_message=is_first_message
    )
    if quran_result:
        return quran_result

    hadith_result = try_direct_hadith_lookup(
        user_message,
        is_first_message=is_first_message
    )
    if hadith_result:
        return hadith_result

    return None
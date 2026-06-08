# import django, os
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hijrah.settings')
# django.setup()

# from main.utils_tilawah.tajwid_engine import analyze_tajwid
# from main.models_tilawah import TilawahAyahPool
# import random

# unit_tests = [
#     # ===== BASIC LEVEL =====
#     # Izhar Halqi
#     {'label': '[BASIC] Izhar - nun + ain', 'ayah': 'مِنۡ عِلۡمٍ', 'must_have': ['izhar_halqi'], 'must_not': [], 'level': 'basic'},
#     {'label': '[BASIC] Izhar - nun + ha', 'ayah': 'مِنۡ هَادٍ', 'must_have': ['izhar_halqi'], 'must_not': [], 'level': 'basic'},
#     {'label': '[BASIC] Izhar - tanwin + hamzah', 'ayah': 'عَلِيمٌ أَحَدٌ', 'must_have': ['izhar_halqi'], 'must_not': [], 'level': 'basic'},

#     # Idgham Bighunnah
#     {'label': '[BASIC] Idgham Bighunnah - nun + ya', 'ayah': 'مِن يَقُولُ', 'must_have': ['idgham_bighunnah'], 'must_not': [], 'level': 'basic'},
#     {'label': '[BASIC] Idgham Bighunnah - tanwin + waw', 'ayah': 'يَوۡمَئِذٖ وَمَا', 'must_have': ['idgham_bighunnah'], 'must_not': [], 'level': 'basic'},

#     # Idgham Bilaghunnah
#     {'label': '[BASIC] Idgham Bilaghunnah - nun + lam', 'ayah': 'مِن لَّدُنۡهُ', 'must_have': ['idgham_bilaghunnah'], 'must_not': [], 'level': 'basic'},
#     {'label': '[BASIC] Idgham Bilaghunnah - tanwin + ra', 'ayah': 'غَفُورٞ رَّحِيمٞ', 'must_have': ['idgham_bilaghunnah'], 'must_not': [], 'level': 'basic'},

#     # Iqlab
#     {'label': '[BASIC] Iqlab - nun Uthmani + ba', 'ayah': 'مِنۢ بَعۡدِ', 'must_have': ['iqlab'], 'must_not': [], 'level': 'basic'},
#     {'label': '[BASIC] Iqlab - tanwin + ba', 'ayah': 'سَمِيعٌۢ بَصِيرٌ', 'must_have': ['iqlab'], 'must_not': [], 'level': 'basic'},

#     # Ikhfa
#     {'label': '[BASIC] Ikhfa - nun + ta', 'ayah': 'كُنتُمۡ', 'must_have': ['ikhfa_haqiqi'], 'must_not': [], 'level': 'basic'},
#     {'label': '[BASIC] Ikhfa - tanwin + fa', 'ayah': 'يَوۡمَئِذٍ فَوَيۡلٞ', 'must_have': ['ikhfa_haqiqi'], 'must_not': [], 'level': 'basic'},

#     # Mim Mati
#     {'label': '[BASIC] Ikhfa Syafawi - mim + ba', 'ayah': 'هُمۡ بِٱلۡأٓخِرَةِ', 'must_have': ['ikhfa_syafawi'], 'must_not': [], 'level': 'basic'},
#     {'label': '[BASIC] Idgham Mimi - mim + mim', 'ayah': 'لَهُم مَّغۡفِرَةٌ', 'must_have': ['idgham_mimi'], 'must_not': [], 'level': 'basic'},
#     {'label': '[BASIC] Izhar Syafawi - mim + waw', 'ayah': 'هُمۡ وَٱللَّهُ', 'must_have': ['izhar_syafawi'], 'must_not': [], 'level': 'basic'},

#     # Qalqalah
#     {'label': '[BASIC] Qalqalah Sugra - qaf tengah', 'ayah': 'يَقۡدِرُ', 'must_have': ['qalqalah_sugra'], 'must_not': [], 'level': 'basic'},
#     {'label': '[BASIC] Qalqalah Kubra - dal akhir', 'ayah': 'وَقَدۡ', 'must_have': ['qalqalah_kubra'], 'must_not': [], 'level': 'basic'},

#     # Ghunnah
#     {'label': '[BASIC] Ghunnah - nun tasydid', 'ayah': 'إِنَّ', 'must_have': ['ghunnah'], 'must_not': [], 'level': 'basic'},
#     {'label': '[BASIC] Ghunnah - mim tasydid', 'ayah': 'ثُمَّ', 'must_have': ['ghunnah'], 'must_not': [], 'level': 'basic'},

#     # Alif Lam
#     {'label': '[BASIC] Alif Lam Syamsiah', 'ayah': 'ٱلنَّاسِ', 'must_have': ['alif_lam_syamsiah'], 'must_not': [], 'level': 'basic'},
#     {'label': '[BASIC] Alif Lam Qamariah', 'ayah': 'ٱلۡمُؤۡمِنِينَ', 'must_have': ['alif_lam_qamariah'], 'must_not': [], 'level': 'basic'},
#     {'label': '[BASIC] Lafzul Jalalah - no alif lam', 'ayah': 'وَٱللَّهُ عَلِيمٌ', 'must_have': [], 'must_not': ['alif_lam_syamsiah', 'alif_lam_qamariah'], 'level': 'basic'},

#     # Mad Basic
#     {'label': '[BASIC] Mad Asli - alef', 'ayah': 'قَالَ رَبُّكَ', 'must_have': ['mad_asli'], 'must_not': [], 'level': 'basic'},
#     {'label': '[BASIC] Mad Asli - waw', 'ayah': 'يَقُولُ رَبُّكَ', 'must_have': ['mad_asli'], 'must_not': [], 'level': 'basic'},
#     {'label': '[BASIC] Mad Asli - ya', 'ayah': 'رَحِيمٌ بِكُمۡ', 'must_have': ['mad_asli'], 'must_not': [], 'level': 'basic'},
   
#     # False Positive Guard
#     {'label': '[BASIC] FP - nun hidup bukan nun mati', 'ayah': 'نَعِيمٍ', 'must_have': [], 'must_not': ['ikhfa_haqiqi', 'idgham_bighunnah'], 'level': 'basic'},
#     {'label': '[BASIC] FP - mim hidup bukan mim mati', 'ayah': 'مَلِكِ', 'must_have': [], 'must_not': ['izhar_syafawi'], 'level': 'basic'},

#     # ===== INTERMEDIATE LEVEL =====
#     # Mad lanjutan
#     {'label': '[INT] Mad Wajib Muttasil', 'ayah': 'جَآءَ', 'must_have': ['mad_wajib_muttasil'], 'must_not': ['mad_asli'], 'level': 'intermediate'},
#     {'label': '[INT] Mad Jaiz Munfasil', 'ayah': 'بِمَا أُنزِلَ', 'must_have': ['mad_jaiz_munfasil'], 'must_not': [], 'level': 'intermediate'},
#     {'label': '[INT] Mad Lazim Mutsaqqal', 'ayah': 'ٱلضَّآلِّينَ', 'must_have': ['mad_lazim_mutsaqqal'], 'must_not': ['mad_asli'], 'level': 'intermediate'},
#     {'label': '[INT] Mad Lazim Harfi', 'ayah': 'الٓمٓ', 'must_have': ['mad_lazim_mukhaffaf'], 'must_not': [], 'level': 'intermediate'},
#     {'label': '[INT] Mad Aridh Lissukun - waw', 'ayah': 'يَعۡلَمُونَ', 'must_have': ['mad_aridh_lissukun'], 'must_not': ['mad_asli'], 'level': 'intermediate'},
#     {'label': '[INT] Mad Aridh Lissukun - ya', 'ayah': 'ٱلۡعَٰلَمِينَ', 'must_have': ['mad_aridh_lissukun'], 'must_not': ['mad_asli'], 'level': 'intermediate'},
#     {'label': '[INT] Mad Lin - waw sukun', 'ayah': 'خَوۡفٍ', 'must_have': ['mad_lin'], 'must_not': [], 'level': 'intermediate'},
#     {'label': '[INT] Mad Iwad - tanwin fath akhir ayat', 'ayah': 'عَلِيمًا', 'must_have': ['mad_iwad'], 'must_not': [], 'level': 'intermediate'},

#     # Idgham lanjutan
#     {'label': '[INT] Idgham Mutamatsilain - qad+dal', 'ayah': 'قَدۡ دَخَلُواْ', 'must_have': ['idgham_mutamatsilain'], 'must_not': [], 'level': 'intermediate'},
#     {'label': '[INT] Idgham Mutamatsilain - bal+lam', 'ayah': 'بَل لَّا', 'must_have': ['idgham_mutamatsilain'], 'must_not': [], 'level': 'intermediate'},
#     {'label': '[INT] Idgham Mutajanisain - dal+ta', 'ayah': 'قَدۡ تَّبَيَّنَ', 'must_have': ['idgham_mutajanisain'], 'must_not': [], 'level': 'intermediate'},
#     {'label': '[INT] Idgham Mutajanisain - ba+mim', 'ayah': 'ٱرۡكَب مَّعَنَا', 'must_have': ['idgham_mutajanisain'], 'must_not': [], 'level': 'intermediate'},

#     # Prioritas
#     {'label': '[INT] Mad Aridh Lissukun - waw', 'ayah': 'يَعۡلَمُونَ', 'must_have': ['mad_aridh_lissukun'], 'must_not': [], 'level': 'intermediate'},
#     {'label': '[INT] Mad Aridh Lissukun - ya', 'ayah': 'ٱلۡعَٰلَمِينَ', 'must_have': ['mad_aridh_lissukun'], 'must_not': [], 'level': 'intermediate'},
#     {'label': '[INT] Prioritas - mad aridh > mad asli', 'ayah': 'يَعۡلَمُونَ', 'must_have': ['mad_aridh_lissukun'], 'must_not': [], 'level': 'intermediate'},

#     # Mad tidak muncul di basic
#     {'label': '[INT] Mad Wajib tidak muncul di basic', 'ayah': 'جَآءَ', 'must_have': [], 'must_not': ['mad_wajib_muttasil'], 'level': 'basic'},
#     {'label': '[INT] Mad Aridh tidak muncul di basic', 'ayah': 'يَعۡلَمُونَ', 'must_have': [], 'must_not': ['mad_aridh_lissukun'], 'level': 'basic'},

#     # ===== EXPERT LEVEL =====
#     # Tafkhim/Tarqiq Ra
#     {'label': '[EXP] Tafkhim Ra - fathah', 'ayah': 'رَبِّ', 'must_have': ['tafkhim_ra'], 'must_not': [], 'level': 'expert'},
#     {'label': '[EXP] Tarqiq Ra - kasrah', 'ayah': 'رِزۡقٗا', 'must_have': ['tarqiq_ra'], 'must_not': [], 'level': 'expert'},

#     # Lam Jalalah
#     {'label': '[EXP] Tafkhim Lam Jalalah - fathah sebelumnya', 'ayah': 'رَسُولَ ٱللَّهِ', 'must_have': ['tafkhim_lam_jalalah'], 'must_not': [], 'level': 'expert'},
#     {'label': '[EXP] Tarqiq Lam Jalalah - kasrah sebelumnya', 'ayah': 'بِٱللَّهِ', 'must_have': ['tarqiq_lam_jalalah'], 'must_not': [], 'level': 'expert'},

#     # Idgham Mutaqaribain
#     {'label': '[EXP] Idgham Mutaqaribain - qaf+kaf', 'ayah': 'أَلَمۡ نَخۡلُقكُّم', 'must_have': ['idgham_mutaqaribain'], 'must_not': [], 'level': 'expert'},

#     # Saktah
#     {'label': '[EXP] Saktah', 'ayah': 'رَيۡبَۛ فِيهِۛ', 'must_have': ['saktah'], 'must_not': [], 'level': 'expert'},

#     # Hukum intermediate tidak hilang di expert
#     {'label': '[EXP] Mad Wajib masih ada di expert', 'ayah': 'جَآءَ', 'must_have': ['mad_wajib_muttasil'], 'must_not': ['mad_asli'], 'level': 'expert'},
#     {'label': '[EXP] Ikhfa masih ada di expert', 'ayah': 'كُنتُمۡ', 'must_have': ['ikhfa_haqiqi'], 'must_not': [], 'level': 'expert'},
# ]


# def run_tests(tests):
#     passed = 0
#     failed = 0
#     fails = []

#     for tc in tests:
#         level = tc.get('level', None)
#         results = analyze_tajwid(tc['ayah'], user_level=level)
#         detected = [rule['rule'] for r in results for rule in r['rules']]

#         ok = True
#         reasons = []

#         for exp in tc['must_have']:
#             if exp not in detected:
#                 ok = False
#                 reasons.append(f"MISSING: {exp}")

#         for forb in tc['must_not']:
#             if forb in detected:
#                 ok = False
#                 reasons.append(f"FALSE POSITIVE: {forb}")

#         status = '✅' if ok else '❌'
#         if ok:
#             passed += 1
#         else:
#             failed += 1
#             fails.append(f"{tc['label']}: {reasons} | detected: {detected}")

#         print(f"{status} {tc['label']}")
#         if not ok:
#             print(f"   → {reasons} | detected: {detected}")

#     print(f"\n{'='*60}")
#     print(f"TOTAL: {passed} PASS, {failed} FAIL dari {len(tests)} test")
#     if fails:
#         print("\nFAIL detail:")
#         for f in fails:
#             print(f"  - {f}")


# run_tests(unit_tests)




# import django, os
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hijrah.settings')
# django.setup()

# from main.utils_tilawah.tajwid_engine import check_idgham_mutaqaribain, get_base_letter, ALL_SUKUN, FATHAH, KASRAH, DAMMAH, SHADDA, MUTAQARIBAIN_PAIRS

# words = ['أَلَمۡ', 'نَخۡلُقكُّم']
# word = words[1]
# chars = list(word)
# word_length = len(chars)

# print(f"Word: {word}")
# for i, c in enumerate(chars):
#     base = get_base_letter(c)
#     next_c = chars[i+1] if i+1 < word_length else None
#     next_next_c = chars[i+2] if i+2 < word_length else None
#     print(f"  [{i}] {repr(c)} base:{repr(base)} next:{repr(next_c)} next_next:{repr(next_next_c)}")
    
#     # Simulasi Kasus B
#     if base.strip() and next_c and get_base_letter(next_c).strip():
#         following = get_base_letter(next_c)
#         following_has_shadda = (next_next_c == SHADDA)
#         print(f"       → Kasus B: following={repr(following)} has_shadda={following_has_shadda} pair_match={( base, following) in MUTAQARIBAIN_PAIRS}")

# print(f"\nResult: {[r['rule'] for r in check_idgham_mutaqaribain(words, 1)]}")




import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hijrah.settings')
django.setup()

from main.utils_tilawah.word_matcher import normalize_arabic, match_words

# Teks dari database (Uthmani)
reference = "مَتَٰعٗا لَّكُمۡ وَلِأَنۡعَٰمِكُمۡ"

# Teks dari Whisper (standar)
transcript = "مَتَاعًا لَّكُمْ وَلِأَنْعَامِكُمْ"

print("=== Normalized Reference ===")
for word in reference.split():
    print(f"  {word} → {repr(normalize_arabic(word))}")

print("\n=== Normalized Transcript ===")
for word in transcript.split():
    print(f"  {word} → {repr(normalize_arabic(word))}")

print("\n=== Match Result ===")
result = match_words(reference, transcript)
print(f"Word accuracy: {result['word_accuracy']}")
for r in result['word_results']:
    print(f"  {r['status']:10} | ref: {r.get('reference','') or '-':20} | trans: {r.get('transcript','') or '-'}")
# import django, os
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hijrah.settings')
# django.setup()

# from main.utils_tilawah.tajwid_engine import analyze_tajwid
# from main.models_tilawah import TilawahAyahPool
# import random, re

# # =====================================================
# # BAGIAN 1: UNIT TEST PER HUKUM TAJWID
# # =====================================================

# unit_tests = [
#     # ===== IZHAR HALQI =====
#     {'label': 'Izhar - nun mati + ain', 'ayah': 'مِنۡ عِلۡمٍ', 'must_have': ['izhar_halqi'], 'must_not': []},
#     {'label': 'Izhar - nun mati + ha', 'ayah': 'مِنۡ هَادٍ', 'must_have': ['izhar_halqi'], 'must_not': []},
#     {'label': 'Izhar - nun mati + kha', 'ayah': 'مِنۡ خَيۡرٍ', 'must_have': ['izhar_halqi'], 'must_not': []},
#     {'label': 'Izhar - nun mati + ghain', 'ayah': 'مِنۡ غِلٍّ', 'must_have': ['izhar_halqi'], 'must_not': []},
#     {'label': 'Izhar - nun mati + hamzah', 'ayah': 'مِنۡ أَهۡلِ', 'must_have': ['izhar_halqi'], 'must_not': []},
#     {'label': 'Izhar - nun mati + ha kecil', 'ayah': 'مِنۡ حَيۡثُ', 'must_have': ['izhar_halqi'], 'must_not': []},
#     {'label': 'Izhar - tanwin + ain', 'ayah': 'عَلِيمٌ عَظِيمٌ', 'must_have': ['izhar_halqi'], 'must_not': []},
#     {'label': 'Izhar - tanwin + hamzah', 'ayah': 'عَلِيمٌ أَحَدٌ', 'must_have': ['izhar_halqi'], 'must_not': []},
#     {'label': 'Izhar - tanwin + ha', 'ayah': 'رَحِيمٌ هُوَ', 'must_have': ['izhar_halqi'], 'must_not': []},

#     # ===== IDGHAM BIGHUNNAH =====
#     {'label': 'Idgham Bighunnah - nun mati + ya', 'ayah': 'مِن يَقُولُ', 'must_have': ['idgham_bighunnah'], 'must_not': []},
#     {'label': 'Idgham Bighunnah - nun mati + nun', 'ayah': 'مِن نَّعِيمٍ', 'must_have': ['idgham_bighunnah'], 'must_not': []},
#     {'label': 'Idgham Bighunnah - nun mati + mim', 'ayah': 'مِن مَّاءٍ', 'must_have': ['idgham_bighunnah'], 'must_not': []},
#     {'label': 'Idgham Bighunnah - nun mati + waw', 'ayah': 'مِن وَلِيٍّ', 'must_have': ['idgham_bighunnah'], 'must_not': []},
#     {'label': 'Idgham Bighunnah - tanwin + ya', 'ayah': 'قَوۡلٗا يَسِيرٗا', 'must_have': ['idgham_bighunnah'], 'must_not': []},
#     {'label': 'Idgham Bighunnah - tanwin + waw', 'ayah': 'يَوۡمَئِذٖ وَمَا', 'must_have': ['idgham_bighunnah'], 'must_not': []},
#     {'label': 'Idgham Bighunnah - tanwin + mim', 'ayah': 'وِلۡدَٰنٞ مُّخَلَّدُونَ', 'must_have': ['idgham_bighunnah'], 'must_not': []},
#     {'label': 'Idgham Bighunnah - tanwin + nun', 'ayah': 'صَفًّا نَّبِيًّا', 'must_have': ['idgham_bighunnah'], 'must_not': []},

#     # ===== IDGHAM BILAGHUNNAH =====
#     {'label': 'Idgham Bilaghunnah - nun mati + lam', 'ayah': 'مِن لَّدُنۡهُ', 'must_have': ['idgham_bilaghunnah'], 'must_not': []},
#     {'label': 'Idgham Bilaghunnah - nun mati + ra', 'ayah': 'مِن رَّبِّهِمۡ', 'must_have': ['idgham_bilaghunnah'], 'must_not': []},
#     {'label': 'Idgham Bilaghunnah - tanwin + lam', 'ayah': 'غَفُورٞ لَّهُمۡ', 'must_have': ['idgham_bilaghunnah'], 'must_not': []},
#     {'label': 'Idgham Bilaghunnah - tanwin + ra', 'ayah': 'غَفُورٞ رَّحِيمٞ', 'must_have': ['idgham_bilaghunnah'], 'must_not': []},
#     {'label': 'Idgham Bilaghunnah - tanwin fath + lam', 'ayah': 'فَوَيۡلٞ لِّلۡمُصَلِّينَ', 'must_have': ['idgham_bilaghunnah'], 'must_not': []},

#     # ===== IQLAB =====
#     {'label': 'Iqlab - nun mati Uthmani + ba', 'ayah': 'مِنۢ بَعۡدِ', 'must_have': ['iqlab'], 'must_not': []},
#     {'label': 'Iqlab - tanwin damm + ba', 'ayah': 'سَمِيعٌۢ بَصِيرٌ', 'must_have': ['iqlab'], 'must_not': []},
#     {'label': 'Iqlab - tanwin fath + ba', 'ayah': 'عَذَابًا بَئِيسًا', 'must_have': ['iqlab'], 'must_not': []},

#     # ===== IKHFA HAQIQI =====
#     {'label': 'Ikhfa - nun mati + ta dalam kata', 'ayah': 'كُنتُمۡ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
#     {'label': 'Ikhfa - nun mati + kaf', 'ayah': 'مِن كُلِّ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
#     {'label': 'Ikhfa - nun mati + sin', 'ayah': 'مِن شَرِّ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
#     {'label': 'Ikhfa - nun mati + fa', 'ayah': 'أَنفُسَكُمۡ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
#     {'label': 'Ikhfa - nun mati + dzal', 'ayah': 'مِن ذَٰلِكَ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
#     {'label': 'Ikhfa - nun mati + syin', 'ayah': 'مِن شَيۡءٍ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
#     {'label': 'Ikhfa - tanwin + fa', 'ayah': 'يَوۡمَئِذٍ فَوَيۡلٞ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
#     {'label': 'Ikhfa - tanwin + qaf', 'ayah': 'نَفۡسٞ قَدۡ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
#     {'label': 'Ikhfa - tanwin + ta', 'ayah': 'جَنَّـٰتٖ تَجۡرِي', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
#     {'label': 'Ikhfa - tanwin + kaf', 'ayah': 'هُدٗى كَرِيمٍ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},

#     # ===== IKHFA SYAFAWI =====
#     {'label': 'Ikhfa Syafawi - mim mati + ba antar kata', 'ayah': 'هُمۡ بِٱلۡأٓخِرَةِ', 'must_have': ['ikhfa_syafawi'], 'must_not': []},
#     {'label': 'Ikhfa Syafawi - mim mati + ba 2', 'ayah': 'وَأَنتُم بِهِۦ', 'must_have': ['ikhfa_syafawi'], 'must_not': []},

#     # ===== IDGHAM MIMI =====
#     {'label': 'Idgham Mimi - mim mati + mim antar kata', 'ayah': 'لَهُم مَّغۡفِرَةٌ', 'must_have': ['idgham_mimi'], 'must_not': []},
#     {'label': 'Idgham Mimi - mim mati implicit + mim', 'ayah': 'وَلَهُم مَّا يَشۡتَهُونَ', 'must_have': ['idgham_mimi'], 'must_not': []},

#     # ===== IZHAR SYAFAWI =====
#     {'label': 'Izhar Syafawi - mim mati + waw', 'ayah': 'هُمۡ وَٱللَّهُ', 'must_have': ['izhar_syafawi'], 'must_not': []},
#     {'label': 'Izhar Syafawi - mim mati + kaf', 'ayah': 'عَلَيۡكُمۡ كِتَٰبَ', 'must_have': ['izhar_syafawi'], 'must_not': []},
#     {'label': 'Izhar Syafawi - mim mati + fa', 'ayah': 'أَيُّهُمۡ فَتَنَّا', 'must_have': ['izhar_syafawi'], 'must_not': []},
#     {'label': 'Izhar Syafawi - TIDAK ada saat mim hidup', 'ayah': 'مَلِكِ', 'must_have': [], 'must_not': ['izhar_syafawi']},
#     {'label': 'Izhar Syafawi - TIDAK ada saat mim+shadda', 'ayah': 'مِمَّا', 'must_have': [], 'must_not': ['izhar_syafawi']},

#     # ===== QALQALAH =====
#     {'label': 'Qalqalah Sugra - qaf sukun tengah', 'ayah': 'يَقۡدِرُ', 'must_have': ['qalqalah_sugra'], 'must_not': []},
#     {'label': 'Qalqalah Sugra - ba sukun tengah', 'ayah': 'يَبۡسُطُ', 'must_have': ['qalqalah_sugra'], 'must_not': []},
#     {'label': 'Qalqalah Sugra - jim sukun tengah', 'ayah': 'يَجۡعَلُ', 'must_have': ['qalqalah_sugra'], 'must_not': []},
#     {'label': 'Qalqalah Sugra - dal sukun tengah', 'ayah': 'يَدۡعُو', 'must_have': ['qalqalah_sugra'], 'must_not': []},
#     {'label': 'Qalqalah Kubra - dal akhir kata', 'ayah': 'وَقَدۡ', 'must_have': ['qalqalah_kubra'], 'must_not': []},
#     {'label': 'Qalqalah Kubra - ba akhir kata', 'ayah': 'مِن لَهَبٖ وَتَبَّ', 'must_have': ['qalqalah_kubra'], 'must_not': []},
#     {'label': 'Qalqalah Kubra - qaf akhir ayat', 'ayah': 'ٱلۡفَلَقِ', 'must_have': ['qalqalah_kubra'], 'must_not': []},

#     # ===== GHUNNAH =====
#     {'label': 'Ghunnah - nun tasydid (إِنَّ)', 'ayah': 'إِنَّ', 'must_have': ['ghunnah'], 'must_not': []},
#     {'label': 'Ghunnah - mim tasydid (ثُمَّ)', 'ayah': 'ثُمَّ', 'must_have': ['ghunnah'], 'must_not': []},
#     {'label': 'Ghunnah - nun tasydid tengah kata', 'ayah': 'جَنَّةٗ', 'must_have': ['ghunnah'], 'must_not': []},
#     {'label': 'Ghunnah - mim tasydid dengan prefix', 'ayah': 'مِمَّا', 'must_have': ['ghunnah'], 'must_not': []},
#     {'label': 'Ghunnah - nun tasydid (إِنَّا)', 'ayah': 'إِنَّا', 'must_have': ['ghunnah'], 'must_not': []},
#     {'label': 'Ghunnah - TIDAK ada saat nun tanpa shadda', 'ayah': 'نَعِيمٍ', 'must_have': [], 'must_not': ['ghunnah']},

#     # ===== ALIF LAM =====
#     {'label': 'Alif Lam Syamsiah - dzal', 'ayah': 'ٱلَّذِينَ', 'must_have': ['alif_lam_syamsiah'], 'must_not': []},
#     {'label': 'Alif Lam Syamsiah - nun', 'ayah': 'ٱلنَّاسِ', 'must_have': ['alif_lam_syamsiah'], 'must_not': []},
#     {'label': 'Alif Lam Syamsiah - sin', 'ayah': 'ٱلسَّمَٰوَٰتِ', 'must_have': ['alif_lam_syamsiah'], 'must_not': []},
#     {'label': 'Alif Lam Syamsiah - ra', 'ayah': 'ٱلرَّحِيمِ', 'must_have': ['alif_lam_syamsiah'], 'must_not': []},
#     {'label': 'Alif Lam Syamsiah - ta', 'ayah': 'ٱلتَّوَّابُ', 'must_have': ['alif_lam_syamsiah'], 'must_not': []},
#     {'label': 'Alif Lam Qamariah - mim', 'ayah': 'ٱلۡمُؤۡمِنِينَ', 'must_have': ['alif_lam_qamariah'], 'must_not': []},
#     {'label': 'Alif Lam Qamariah - qaf', 'ayah': 'ٱلۡقِيَٰمَةِ', 'must_have': ['alif_lam_qamariah'], 'must_not': []},
#     {'label': 'Alif Lam Qamariah - ba', 'ayah': 'ٱلۡبَصِيرُ', 'must_have': ['alif_lam_qamariah'], 'must_not': []},
#     {'label': 'Alif Lam Qamariah - kaf', 'ayah': 'ٱلۡكِتَٰبِ', 'must_have': ['alif_lam_qamariah'], 'must_not': []},
#     {'label': 'Alif Lam prefix waw syamsiah', 'ayah': 'وَٱلنَّاسِ', 'must_have': ['alif_lam_syamsiah'], 'must_not': []},
#     {'label': 'Alif Lam prefix ba qamariah', 'ayah': 'بِٱلۡحَقِّ', 'must_have': ['alif_lam_qamariah'], 'must_not': []},
#     {'label': 'Alif Lam prefix fa syamsiah', 'ayah': 'فَٱلصَّـٰلِحَٰتُ', 'must_have': ['alif_lam_syamsiah'], 'must_not': []},

#     # ===== LAFZUL JALALAH =====
#     {'label': 'Lafzul Jalalah standalone', 'ayah': 'ٱللَّهُ', 'must_have': [], 'must_not': ['alif_lam_syamsiah', 'alif_lam_qamariah']},
#     {'label': 'Lafzul Jalalah prefix waw', 'ayah': 'وَٱللَّهُ عَلِيمٌ', 'must_have': [], 'must_not': ['alif_lam_syamsiah', 'alif_lam_qamariah']},
#     {'label': 'Lafzul Jalalah prefix ba', 'ayah': 'بِٱللَّهِ', 'must_have': [], 'must_not': ['alif_lam_syamsiah', 'alif_lam_qamariah']},
#     {'label': 'Lafzul Jalalah prefix fa', 'ayah': 'فَٱللَّهُ', 'must_have': [], 'must_not': ['alif_lam_syamsiah', 'alif_lam_qamariah']},

#     # ===== FALSE POSITIVE GUARD =====
#     {'label': 'FP Guard - nun hidup tidak jadi nun mati', 'ayah': 'نَعِيمٍ', 'must_have': [], 'must_not': ['ikhfa_haqiqi', 'idgham_bighunnah', 'izhar_halqi']},
#     {'label': 'FP Guard - mim hidup tidak jadi mim mati', 'ayah': 'مَلِكِ', 'must_have': [], 'must_not': ['izhar_syafawi', 'ikhfa_syafawi', 'idgham_mimi']},
#     {'label': 'FP Guard - tidak ada tajwid di kata sederhana', 'ayah': 'قُلۡ هُوَ', 'must_have': [], 'must_not': ['ikhfa_haqiqi', 'idgham_bighunnah']},
#     {'label': 'FP Guard - waw bukan nun mati', 'ayah': 'وَرَبِّكَ', 'must_have': [], 'must_not': ['izhar_halqi', 'ikhfa_haqiqi']},
# ]

# # =====================================================
# # BAGIAN 2: TEST AYAT LENGKAP DARI DATABASE PER LEVEL
# # =====================================================

# def run_unit_tests(tests):
#     passed = 0
#     failed = 0
#     fail_details = []

#     for tc in tests:
#         results = analyze_tajwid(tc['ayah'])
#         detected = [rule['rule'] for r in results for rule in r['rules']]

#         ok = True
#         fail_reason = []

#         for expected in tc['must_have']:
#             if expected not in detected:
#                 ok = False
#                 fail_reason.append(f"MISSING: {expected}")

#         for forbidden in tc['must_not']:
#             if forbidden in detected:
#                 ok = False
#                 fail_reason.append(f"FALSE POSITIVE: {forbidden}")

#         status = '✅ PASS' if ok else '❌ FAIL'
#         if ok:
#             passed += 1
#         else:
#             failed += 1
#             fail_details.append(f"{tc['label']}: {fail_reason} | detected: {detected}")

#         print(f"{status} | {tc['label']}")
#         if not ok:
#             print(f"       → {fail_reason} | detected: {detected}")

#     return passed, failed, fail_details


# def run_level_tests():
#     """Test ayat random dari database per level, verifikasi engine tidak crash dan return hasil masuk akal"""
#     print("\n" + "="*60)
#     print("BAGIAN 2: TEST AYAT DARI DATABASE PER LEVEL")
#     print("="*60)

#     harakat_pattern = re.compile(
#         r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC'
#         r'\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED\u06e1\u0657]'
#     )

#     total_passed = 0
#     total_failed = 0

#     for level in ['basic', 'intermediate', 'expert']:
#         print(f"\n--- LEVEL: {level.upper()} ---")
#         ayahs = list(TilawahAyahPool.objects.filter(level=level))
#         samples = random.sample(ayahs, min(10, len(ayahs)))

#         level_passed = 0
#         level_failed = 0

#         for ayah in samples:
#             try:
#                 results = analyze_tajwid(ayah.ayah_text)
#                 detected_rules = [rule['rule'] for r in results for rule in r['rules']]

#                 # Validasi: engine tidak crash = PASS
#                 # Validasi tambahan: expert harus punya lebih banyak rules dari basic
#                 word_count = len(ayah.ayah_text.split())
#                 rules_count = len(detected_rules)

#                 # Sanity check: tidak ada rule yang tidak dikenal
#                 valid_rules = {
#                     'izhar_halqi', 'idgham_bighunnah', 'idgham_bilaghunnah',
#                     'iqlab', 'ikhfa_haqiqi', 'ikhfa_syafawi', 'idgham_mimi',
#                     'izhar_syafawi', 'qalqalah_sugra', 'qalqalah_kubra',
#                     'ghunnah', 'alif_lam_syamsiah', 'alif_lam_qamariah',
#                     'mad_asli', 'mad_wajib_muttasil', 'mad_jaiz_munfasil',
#                     'mad_lazim_mutsaqqal', 'mad_lazim_mukhaffaf'
#                 }
#                 unknown_rules = [r for r in detected_rules if r not in valid_rules]

#                 if unknown_rules:
#                     print(f"  ❌ FAIL | {ayah.surah_name}:{ayah.ayah_number} — unknown rules: {unknown_rules}")
#                     level_failed += 1
#                 else:
#                     print(f"  ✅ PASS | {ayah.surah_name}:{ayah.ayah_number} "
#                           f"({word_count} kata, {rules_count} rules: {list(set(detected_rules))})")
#                     level_passed += 1

#             except Exception as e:
#                 print(f"  ❌ CRASH | {ayah.surah_name}:{ayah.ayah_number} — {str(e)}")
#                 level_failed += 1

#         print(f"  → Level {level}: {level_passed} PASS, {level_failed} FAIL")
#         total_passed += level_passed
#         total_failed += level_failed

#     return total_passed, total_failed


# # =====================================================
# # RUN SEMUA TEST
# # =====================================================

# print("="*60)
# print("BAGIAN 1: UNIT TEST PER HUKUM TAJWID")
# print("="*60)
# p1, f1, fails = run_unit_tests(unit_tests)

# p2, f2 = run_level_tests()

# print("\n" + "="*60)
# print("HASIL AKHIR")
# print("="*60)
# print(f"Unit Test  : {p1} PASS, {f1} FAIL dari {len(unit_tests)} test")
# print(f"Level Test : {p2} PASS, {f2} FAIL dari {p1+p2+f1+f2-len(unit_tests)} test")
# print(f"TOTAL      : {p1+p2} PASS, {f1+f2} FAIL dari {len(unit_tests)+p2+f2} test")

# if fails:
#     print(f"\nUnit Test FAIL detail:")
#     for f in fails:
#         print(f"  - {f}")


# from main.utils_tilawah.tajwid_engine import FATHAH, KASRAH, DAMMAH, ALEF, WAW, YA, ALL_SUKUN, SHADDA, HAMZAH_LETTERS, get_base_letter

# tests = [
#     ('Mad Wajib dalam kata', 'جَآءَ'),
#     ('Mad Wajib maa+hamzah', 'بِمَآ'),
#     ('Mad Jaiz munfasil', 'يَشَآءُ'),
#     ('Mad Lazim mutsaqqal', 'ٱلضَّآلِّينَ'),
#     ('Mad Lazim mukhaffaf', 'ءَآلۡـَٰٔنَ'),
# ]

# for label, word in tests:
#     print(f"\n=== {label}: {word} ===")
#     chars = list(word)
#     for i, c in enumerate(chars):
#         print(f"  [{i}] {repr(c)} hex:{hex(ord(c))}")
    
#     # Cek deteksi pola mad
#     print("  --- Deteksi mad ---")
#     for i, char in enumerate(chars):
#         next_char = chars[i+1] if i+1 < len(chars) else None
#         next_next_char = chars[i+2] if i+2 < len(chars) else None
        
#         is_mad = False
#         if char == FATHAH and next_char == ALEF:
#             print(f"  [{i}] MAD ALEF terdeteksi")
#             is_mad = True
#         elif char == DAMMAH and next_char == WAW:
#             print(f"  [{i}] MAD WAW terdeteksi")
#             is_mad = True
#         elif char == KASRAH and next_char == YA:
#             print(f"  [{i}] MAD YA terdeteksi")
#             is_mad = True
            
#         if is_mad:
#             print(f"       next_next: {repr(next_next_char)} hex:{hex(ord(next_next_char)) if next_next_char else 'None'}")
#             if next_next_char:
#                 base = get_base_letter(next_next_char)
#                 print(f"       base after mad: {repr(base)} in HAMZAH: {base in HAMZAH_LETTERS}")
#                 print(f"       is SHADDA: {next_next_char == SHADDA}")
#                 print(f"       in ALL_SUKUN: {next_next_char in ALL_SUKUN}")



# import django, os
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hijrah.settings')
# django.setup()

# from main.utils_tilawah.tajwid_engine import check_mad

# tests = [
#     # Mad Asli
#     ('Mad Asli - alef', 'قَالَ', None),
#     ('Mad Asli - waw', 'يَقُولُ', None),
#     ('Mad Asli - ya', 'رَحِيمٌ', None),
    
#     # Mad Wajib Muttasil
#     ('Mad Wajib - jaa-a', 'جَآءَ', None),
#     ('Mad Wajib - maa + hamzah akhir', 'بِمَآ', 'أُنزِلَ'),
#     ('Mad Wajib - syaa-a', 'يَشَآءُ', None),
#     ('Mad Wajib - jaa-a rabbuka', 'جَآءَ', 'رَبُّكَ'),
    
#     # Mad Jaiz Munfasil  
#     ('Mad Jaiz - maa + awali hamzah', 'بِمَا', 'أُنزِلَ'),
#     ('Mad Jaiz - waw mad + awali hamzah', 'يَشَآءُ', 'إِلَىٰ'),
    
#     # Mad Lazim
#     ('Mad Lazim Mutsaqqal - dhaalliin', 'ٱلضَّآلِّينَ', None),
#     ('Mad Lazim Mutsaqqal - wallaah', 'وَلَا', None),
    
#     # Mad Lazim Mukhaffaf Harfi
#     ('Mad Lazim Harfi - alm', 'الٓمٓ', None),
#     ('Mad Lazim Harfi - yasin', 'يٓس', None),
#     ('Mad Lazim Harfi - qaf', 'قٓ', None),
# ]

# for label, word, next_word in tests:
#     result = check_mad(word, next_word)
#     rules = [r['rule'] for r in result]
#     print(f"{'✅' if rules else '⚪'} {label}: {rules}")


import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hijrah.settings')
django.setup()

from main.utils_tilawah.tajwid_engine import analyze_tajwid
from main.models_tilawah import TilawahAyahPool
import random

unit_tests = [
    # ===== IZHAR HALQI =====
    {'label': 'Izhar - nun mati + ain', 'ayah': 'مِنۡ عِلۡمٍ', 'must_have': ['izhar_halqi'], 'must_not': []},
    {'label': 'Izhar - nun mati + ha', 'ayah': 'مِنۡ هَادٍ', 'must_have': ['izhar_halqi'], 'must_not': []},
    {'label': 'Izhar - nun mati + kha', 'ayah': 'مِنۡ خَيۡرٍ', 'must_have': ['izhar_halqi'], 'must_not': []},
    {'label': 'Izhar - nun mati + ghain', 'ayah': 'مِنۡ غِلٍّ', 'must_have': ['izhar_halqi'], 'must_not': []},
    {'label': 'Izhar - nun mati + hamzah', 'ayah': 'مِنۡ أَهۡلِ', 'must_have': ['izhar_halqi'], 'must_not': []},
    {'label': 'Izhar - tanwin + hamzah', 'ayah': 'عَلِيمٌ أَحَدٌ', 'must_have': ['izhar_halqi'], 'must_not': []},
    {'label': 'Izhar - tanwin + ha', 'ayah': 'رَحِيمٌ هُوَ', 'must_have': ['izhar_halqi'], 'must_not': []},

    # ===== IDGHAM BIGHUNNAH =====
    {'label': 'Idgham Bighunnah - nun + ya', 'ayah': 'مِن يَقُولُ', 'must_have': ['idgham_bighunnah'], 'must_not': []},
    {'label': 'Idgham Bighunnah - nun + mim', 'ayah': 'مِن مَّاءٍ', 'must_have': ['idgham_bighunnah'], 'must_not': []},
    {'label': 'Idgham Bighunnah - tanwin + ya', 'ayah': 'قَوۡلٗا يَسِيرٗا', 'must_have': ['idgham_bighunnah'], 'must_not': []},
    {'label': 'Idgham Bighunnah - tanwin + waw', 'ayah': 'يَوۡمَئِذٖ وَمَا', 'must_have': ['idgham_bighunnah'], 'must_not': []},

    # ===== IDGHAM BILAGHUNNAH =====
    {'label': 'Idgham Bilaghunnah - nun + lam', 'ayah': 'مِن لَّدُنۡهُ', 'must_have': ['idgham_bilaghunnah'], 'must_not': []},
    {'label': 'Idgham Bilaghunnah - tanwin + ra', 'ayah': 'غَفُورٞ رَّحِيمٞ', 'must_have': ['idgham_bilaghunnah'], 'must_not': []},

    # ===== IQLAB =====
    {'label': 'Iqlab - nun mati Uthmani + ba', 'ayah': 'مِنۢ بَعۡدِ', 'must_have': ['iqlab'], 'must_not': []},
    {'label': 'Iqlab - tanwin + ba', 'ayah': 'سَمِيعٌۢ بَصِيرٌ', 'must_have': ['iqlab'], 'must_not': []},

    # ===== IKHFA =====
    {'label': 'Ikhfa - nun mati + ta dalam kata', 'ayah': 'كُنتُمۡ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - nun mati + kaf', 'ayah': 'مِن كُلِّ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - tanwin + fa', 'ayah': 'يَوۡمَئِذٍ فَوَيۡلٞ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},

    # ===== MIM MATI =====
    {'label': 'Ikhfa Syafawi - mim + ba', 'ayah': 'هُمۡ بِٱلۡأٓخِرَةِ', 'must_have': ['ikhfa_syafawi'], 'must_not': []},
    {'label': 'Idgham Mimi - mim + mim', 'ayah': 'لَهُم مَّغۡفِرَةٌ', 'must_have': ['idgham_mimi'], 'must_not': []},
    {'label': 'Izhar Syafawi - mim + waw', 'ayah': 'هُمۡ وَٱللَّهُ', 'must_have': ['izhar_syafawi'], 'must_not': []},
    {'label': 'Izhar Syafawi - TIDAK ada saat mim hidup', 'ayah': 'مَلِكِ', 'must_have': [], 'must_not': ['izhar_syafawi']},

    # ===== QALQALAH =====
    {'label': 'Qalqalah Sugra - qaf sukun tengah', 'ayah': 'يَقۡدِرُ', 'must_have': ['qalqalah_sugra'], 'must_not': []},
    {'label': 'Qalqalah Kubra - dal akhir kata', 'ayah': 'وَقَدۡ', 'must_have': ['qalqalah_kubra'], 'must_not': []},
    {'label': 'Qalqalah Kubra - qaf akhir ayat', 'ayah': 'ٱلۡفَلَقِ', 'must_have': ['qalqalah_kubra'], 'must_not': []},

    # ===== GHUNNAH =====
    {'label': 'Ghunnah - nun tasydid', 'ayah': 'إِنَّ', 'must_have': ['ghunnah'], 'must_not': []},
    {'label': 'Ghunnah - mim tasydid', 'ayah': 'ثُمَّ', 'must_have': ['ghunnah'], 'must_not': []},
    {'label': 'Ghunnah - TIDAK ada saat nun tanpa shadda', 'ayah': 'نَعِيمٍ', 'must_have': [], 'must_not': ['ghunnah']},

    # ===== ALIF LAM =====
    {'label': 'Alif Lam Syamsiah - dzal', 'ayah': 'ٱلَّذِينَ', 'must_have': ['alif_lam_syamsiah'], 'must_not': []},
    {'label': 'Alif Lam Qamariah - mim', 'ayah': 'ٱلۡمُؤۡمِنِينَ', 'must_have': ['alif_lam_qamariah'], 'must_not': []},
    {'label': 'Lafzul Jalalah - tidak ada alif lam', 'ayah': 'وَٱللَّهُ عَلِيمٌ', 'must_have': [], 'must_not': ['alif_lam_syamsiah', 'alif_lam_qamariah']},

    # ===== MAD =====
    {'label': 'Mad Asli - alef', 'ayah': 'قَالَ', 'must_have': ['mad_asli'], 'must_not': []},
    {'label': 'Mad Wajib Muttasil', 'ayah': 'جَآءَ', 'must_have': ['mad_wajib_muttasil'], 'must_not': ['mad_asli']},
    {'label': 'Mad Jaiz Munfasil', 'ayah': 'بِمَا أُنزِلَ', 'must_have': ['mad_jaiz_munfasil'], 'must_not': []},
    {'label': 'Mad Lazim Mutsaqqal', 'ayah': 'ٱلضَّآلِّينَ', 'must_have': ['mad_lazim_mutsaqqal'], 'must_not': ['mad_asli']},
    {'label': 'Mad Lazim Harfi', 'ayah': 'الٓمٓ', 'must_have': ['mad_lazim_mukhaffaf'], 'must_not': []},

    # ===== MAD ARIDH LISSUKUN =====
    {'label': 'Mad Aridh Lissukun - akhir ayat waw mad', 'ayah': 'يَعۡلَمُو', 'must_have': ['mad_aridh_lissukun'], 'must_not': ['mad_asli']},
    {'label': 'Mad Aridh Lissukun - akhir ayat ya mad', 'ayah': 'ٱلۡعَٰلَمِي', 'must_have': ['mad_aridh_lissukun'], 'must_not': ['mad_asli']},
    {'label': 'Mad Aridh Lissukun - akhir ayat alef mad', 'ayah': 'مَٰلِكَا', 'must_have': ['mad_aridh_lissukun'], 'must_not': []},
    {'label': 'Mad Aridh - TIDAK ada di tengah ayat', 'ayah': 'يَعۡلَمُونَ قُلۡ', 'must_have': [], 'must_not': ['mad_aridh_lissukun']},
    # ===== IDGHAM MUTAMATSILAIN =====
    {'label': 'Idgham Mutamatsilain - qad + dal', 'ayah': 'قَدۡ دَخَلُواْ', 'must_have': ['idgham_mutamatsilain'], 'must_not': []},
    {'label': 'Idgham Mutamatsilain - bal + lam', 'ayah': 'بَل لَّا', 'must_have': ['idgham_mutamatsilain'], 'must_not': []},
    {'label': 'Idgham Mutamatsilain - nun + nun (prioritas bighunnah)', 'ayah': 'مِن نَّعِيمٍ', 'must_have': ['idgham_bighunnah'], 'must_not': ['idgham_mutamatsilain']},

    # ===== IDGHAM MUTAJANISAIN =====
    {'label': 'Idgham Mutajanisain - dal + ta', 'ayah': 'قَدۡ تَّبَيَّنَ', 'must_have': ['idgham_mutajanisain'], 'must_not': []},
    {'label': 'Idgham Mutajanisain - tha + ta', 'ayah': 'بَسَطۡتَ', 'must_have': ['idgham_mutajanisain'], 'must_not': []},
    {'label': 'Idgham Mutajanisain - ba + mim', 'ayah': 'ٱرۡكَب مَّعَنَا', 'must_have': ['idgham_mutajanisain'], 'must_not': []},

    # ===== IDGHAM MUTAQARIBAIN =====
    {'label': 'Idgham Mutaqaribain - qaf + kaf', 'ayah': 'أَلَمۡ نَخۡلُقْ كُّم', 'must_have': ['idgham_mutaqaribain'], 'must_not': []},{'label': 'Idgham Mutaqaribain - nun + lam', 'ayah': 'مِن لَّدُنۡهُ', 'must_have': ['idgham_bilaghunnah'], 'must_not': ['idgham_mutaqaribain']},

    # ===== FILTER LEVEL =====
    {'label': 'Level basic - tidak tampilkan mad lazim', 'ayah': 'ٱلضَّآلِّينَ', 'must_have': [], 'must_not': [], 'level': 'basic'},
    {'label': 'Level basic - tampilkan izhar', 'ayah': 'مِنۡ عِلۡمٍ', 'must_have': ['izhar_halqi'], 'must_not': [], 'level': 'basic'},
    {'label': 'Level expert - tampilkan semua', 'ayah': 'قَدۡ تَّبَيَّنَ', 'must_have': ['idgham_mutajanisain'], 'must_not': [], 'level': 'expert'},

    # ===== FALSE POSITIVE =====
    {'label': 'FP - nun hidup tidak jadi nun mati', 'ayah': 'نَعِيمٍ', 'must_have': [], 'must_not': ['ikhfa_haqiqi', 'idgham_bighunnah']},
    {'label': 'FP - mim hidup tidak jadi mim mati', 'ayah': 'مَلِكِ', 'must_have': [], 'must_not': ['izhar_syafawi']},
]


def run_unit_tests(tests):
    passed = 0
    failed = 0
    fail_details = []

    for tc in tests:
        user_level = tc.get('level', None)
        results = analyze_tajwid(tc['ayah'], user_level=user_level)
        detected = [rule['rule'] for r in results for rule in r['rules']]

        ok = True
        fail_reason = []

        for expected in tc['must_have']:
            if expected not in detected:
                ok = False
                fail_reason.append(f"MISSING: {expected}")

        for forbidden in tc['must_not']:
            if forbidden in detected:
                ok = False
                fail_reason.append(f"FALSE POSITIVE: {forbidden}")

        status = '✅ PASS' if ok else '❌ FAIL'
        if ok:
            passed += 1
        else:
            failed += 1
            fail_details.append(f"{tc['label']}: {fail_reason} | detected: {detected}")

        print(f"{status} | {tc['label']}")
        if not ok:
            print(f"       → {fail_reason} | detected: {detected}")

    return passed, failed, fail_details


def run_level_tests():
    print("\n" + "="*60)
    print("BAGIAN 2: TEST AYAT DARI DATABASE PER LEVEL")
    print("="*60)

    valid_rules = {
        'izhar_halqi', 'idgham_bighunnah', 'idgham_bilaghunnah',
        'iqlab', 'ikhfa_haqiqi', 'ikhfa_syafawi', 'idgham_mimi',
        'izhar_syafawi', 'qalqalah_sugra', 'qalqalah_kubra',
        'ghunnah', 'alif_lam_syamsiah', 'alif_lam_qamariah',
        'mad_asli', 'mad_wajib_muttasil', 'mad_jaiz_munfasil',
        'mad_lazim_mutsaqqal', 'mad_lazim_mukhaffaf',
        'mad_aridh_lissukun', 'idgham_mutamatsilain',
        'idgham_mutajanisain', 'idgham_mutaqaribain'
    }

    total_passed = 0
    total_failed = 0

    for level in ['basic', 'intermediate', 'expert']:
        print(f"\n--- LEVEL: {level.upper()} ---")
        ayahs = list(TilawahAyahPool.objects.filter(level=level))
        samples = random.sample(ayahs, min(10, len(ayahs)))

        level_passed = 0
        level_failed = 0

        for ayah in samples:
            try:
                results = analyze_tajwid(ayah.ayah_text)
                detected_rules = [rule['rule'] for r in results for rule in r['rules']]
                word_count = len(ayah.ayah_text.split())
                unknown_rules = [r for r in detected_rules if r not in valid_rules]

                if unknown_rules:
                    print(f"  ❌ FAIL | {ayah.surah_name}:{ayah.ayah_number} — unknown: {unknown_rules}")
                    level_failed += 1
                else:
                    print(f"  ✅ PASS | {ayah.surah_name}:{ayah.ayah_number} "
                          f"({word_count} kata, rules: {list(set(detected_rules))})")
                    level_passed += 1

            except Exception as e:
                print(f"  ❌ CRASH | {ayah.surah_name}:{ayah.ayah_number} — {str(e)}")
                level_failed += 1

        print(f"  → Level {level}: {level_passed} PASS, {level_failed} FAIL")
        total_passed += level_passed
        total_failed += level_failed

    return total_passed, total_failed


print("="*60)
print("BAGIAN 1: UNIT TEST")
print("="*60)
p1, f1, fails = run_unit_tests(unit_tests)

p2, f2 = run_level_tests()

print("\n" + "="*60)
print("HASIL AKHIR")
print("="*60)
print(f"Unit Test  : {p1} PASS, {f1} FAIL dari {len(unit_tests)} test")
print(f"Level Test : {p2} PASS, {f2} FAIL dari {p2+f2} test")
print(f"TOTAL      : {p1+p2} PASS, {f1+f2} FAIL dari {len(unit_tests)+p2+f2} test")

if fails:
    print(f"\nUnit Test FAIL detail:")
    for f in fails:
        print(f"  - {f}")
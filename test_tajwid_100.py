import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hijrah.settings')
django.setup()

from main.utils_tilawah.tajwid_engine import analyze_tajwid

# ============================================================
# TEST CASE UNTUK ATURAN YANG SERING MUNCUL
# (TANPA ATURAN LANGKA: Naql, Imalah, Tashil, Saktah, Waqaf Mamnu)
# ============================================================

unit_tests = [
    # ==================== IZHAR HALQI (6 huruf) ====================
    {'label': 'Izhar - nun mati + ain', 'ayah': 'مِنۡ عِلۡمٍ', 'must_have': ['izhar_halqi'], 'must_not': []},
    {'label': 'Izhar - nun mati + ha', 'ayah': 'مِنۡ هَادٍ', 'must_have': ['izhar_halqi'], 'must_not': []},
    {'label': 'Izhar - nun mati + kha', 'ayah': 'مِنۡ خَيۡرٍ', 'must_have': ['izhar_halqi'], 'must_not': []},
    {'label': 'Izhar - nun mati + ghain', 'ayah': 'مِنۡ غِلٍّ', 'must_have': ['izhar_halqi'], 'must_not': []},
    {'label': 'Izhar - nun mati + hamzah', 'ayah': 'مِنۡ أَهۡلِ', 'must_have': ['izhar_halqi'], 'must_not': []},
    {'label': 'Izhar - tanwin + hamzah', 'ayah': 'عَلِيمٌ أَحَدٌ', 'must_have': ['izhar_halqi'], 'must_not': []},
    {'label': 'Izhar - tanwin + ha', 'ayah': 'رَحِيمٌ هُوَ', 'must_have': ['izhar_halqi'], 'must_not': []},

    # ==================== IDGHAM BIGHUNNAH (4 huruf) ====================
    {'label': 'Idgham Bighunnah - nun + ya', 'ayah': 'مِن يَقُولُ', 'must_have': ['idgham_bighunnah'], 'must_not': []},
    {'label': 'Idgham Bighunnah - nun + mim', 'ayah': 'مِن مَّاءٍ', 'must_have': ['idgham_bighunnah'], 'must_not': []},
    {'label': 'Idgham Bighunnah - nun + nun', 'ayah': 'مِن نَّعِيمٍ', 'must_have': ['idgham_bighunnah'], 'must_not': []},
    {'label': 'Idgham Bighunnah - nun + waw', 'ayah': 'مِن وَلِيٍّ', 'must_have': ['idgham_bighunnah'], 'must_not': []},
    {'label': 'Idgham Bighunnah - tanwin + ya', 'ayah': 'قَوۡلٗا يَسِيرٗا', 'must_have': ['idgham_bighunnah'], 'must_not': []},
    {'label': 'Idgham Bighunnah - tanwin + waw', 'ayah': 'يَوۡمَئِذٖ وَمَا', 'must_have': ['idgham_bighunnah'], 'must_not': []},
    {'label': 'Idgham Bighunnah - tanwin + mim', 'ayah': 'عَلِيمٌ مُّبِينٌ', 'must_have': ['idgham_bighunnah'], 'must_not': []},

    # ==================== IDGHAM BILAGHUNNAH (2 huruf) ====================
    {'label': 'Idgham Bilaghunnah - nun + lam', 'ayah': 'مِن لَّدُنۡهُ', 'must_have': ['idgham_bilaghunnah'], 'must_not': []},
    {'label': 'Idgham Bilaghunnah - nun + ra', 'ayah': 'مِن رَّبِّهِ', 'must_have': ['idgham_bilaghunnah'], 'must_not': []},
    {'label': 'Idgham Bilaghunnah - tanwin + lam', 'ayah': 'خَيۡرٞ لَّكُمۡ', 'must_have': ['idgham_bilaghunnah'], 'must_not': []},
    {'label': 'Idgham Bilaghunnah - tanwin + ra', 'ayah': 'غَفُورٞ رَّحِيمٞ', 'must_have': ['idgham_bilaghunnah'], 'must_not': []},

    # ==================== IQLAB ====================
    {'label': 'Iqlab - nun mati Uthmani + ba', 'ayah': 'مِنۢ بَعۡدِ', 'must_have': ['iqlab'], 'must_not': []},
    {'label': 'Iqlab - tanwin + ba', 'ayah': 'سَمِيعٌۢ بَصِيرٌ', 'must_have': ['iqlab'], 'must_not': []},

    # ==================== IKHFA HAQIQI (15 huruf lengkap) ====================
    {'label': 'Ikhfa - nun mati + ta', 'ayah': 'كُنتُمۡ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - nun mati + tsa', 'ayah': 'مِن ثَقُلَتۡ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - nun mati + jim', 'ayah': 'مِن جَرَّ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - nun mati + dal', 'ayah': 'مِن دُونِ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - nun mati + dzal', 'ayah': 'مِن ذَلِكَ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - nun mati + za', 'ayah': 'مِن زَيۡتٖ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - nun mati + sin', 'ayah': 'مِن سَمَآءٖ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - nun mati + syin', 'ayah': 'مِن شَيۡءٖ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - nun mati + shad', 'ayah': 'مِن صَالِحٖ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - nun mati + dhad', 'ayah': 'مِن ضَرَّ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - nun mati + tha', 'ayah': 'مِن طَعَامٖ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - nun mati + zha', 'ayah': 'مِن ظَالِمٖ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - nun mati + fa', 'ayah': 'مِن فَضۡلِ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - nun mati + qaf', 'ayah': 'مِن قَبۡلِ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - nun mati + kaf', 'ayah': 'مِن كُلِّ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - tanwin + fa', 'ayah': 'يَوۡمَئِذٍ فَوَيۡلٞ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Ikhfa - tanwin + qaf', 'ayah': 'غَفُورٞ قَدِيرٞ', 'must_have': ['ikhfa_haqiqi'], 'must_not': []},

    # ==================== MIM MATI ====================
    {'label': 'Ikhfa Syafawi - mim + ba', 'ayah': 'هُمۡ بِٱلۡأٓخِرَةِ', 'must_have': ['ikhfa_syafawi'], 'must_not': []},
    {'label': 'Idgham Mimi - mim + mim', 'ayah': 'لَهُم مَّغۡفِرَةٌ', 'must_have': ['idgham_mimi'], 'must_not': []},
    {'label': 'Izhar Syafawi - mim + waw', 'ayah': 'هُمۡ وَٱللَّهُ', 'must_have': ['izhar_syafawi'], 'must_not': []},
    {'label': 'Izhar Syafawi - mim + ya', 'ayah': 'هُمۡ يَعۡلَمُونَ', 'must_have': ['izhar_syafawi'], 'must_not': []},
    {'label': 'Izhar Syafawi - TIDAK ada saat mim hidup', 'ayah': 'مَلِكِ', 'must_have': [], 'must_not': ['izhar_syafawi']},

    # ==================== QALQALAH ====================
    {'label': 'Qalqalah Sugra - qaf sukun tengah', 'ayah': 'يَقۡدِرُ', 'must_have': ['qalqalah_sugra'], 'must_not': []},
    {'label': 'Qalqalah Sugra - ba sukun tengah', 'ayah': 'يَبۡصُرُونَ', 'must_have': ['qalqalah_sugra'], 'must_not': []},
    {'label': 'Qalqalah Sugra - jim sukun tengah', 'ayah': 'أَجۡرٌ', 'must_have': ['qalqalah_sugra'], 'must_not': []},
    {'label': 'Qalqalah Kubra - dal akhir kata', 'ayah': 'وَقَدۡ', 'must_have': ['qalqalah_kubra'], 'must_not': []},
    {'label': 'Qalqalah Kubra - qaf akhir ayat', 'ayah': 'ٱلۡفَلَقِ', 'must_have': ['qalqalah_kubra'], 'must_not': []},

    # ==================== GHUNNAH ====================
    {'label': 'Ghunnah - nun tasydid', 'ayah': 'إِنَّ', 'must_have': ['ghunnah'], 'must_not': []},
    {'label': 'Ghunnah - mim tasydid', 'ayah': 'ثُمَّ', 'must_have': ['ghunnah'], 'must_not': []},
    {'label': 'Ghunnah - nun tasydid tengah', 'ayah': 'مِنَّا', 'must_have': ['ghunnah'], 'must_not': []},
    {'label': 'Ghunnah - mim tasydid tengah', 'ayah': 'أَمَّا', 'must_have': ['ghunnah'], 'must_not': []},
    {'label': 'Ghunnah - TIDAK ada saat nun tanpa shadda', 'ayah': 'نَعِيمٍ', 'must_have': [], 'must_not': ['ghunnah']},

    # ==================== ALIF LAM ====================
    {'label': 'Alif Lam Syamsiah - lam + dzal', 'ayah': 'ٱلَّذِينَ', 'must_have': ['alif_lam_syamsiah'], 'must_not': []},
    {'label': 'Alif Lam Syamsiah - lam + ra', 'ayah': 'ٱلرَّحۡمَٰنِ', 'must_have': ['alif_lam_syamsiah'], 'must_not': []},
    {'label': 'Alif Lam Syamsiah - lam + sin', 'ayah': 'ٱلسَّمَآءُ', 'must_have': ['alif_lam_syamsiah'], 'must_not': []},
    {'label': 'Alif Lam Qamariah - lam + mim', 'ayah': 'ٱلۡمُؤۡمِنِينَ', 'must_have': ['alif_lam_qamariah'], 'must_not': []},
    {'label': 'Alif Lam Qamariah - lam + ba', 'ayah': 'ٱلۡبَيۡتُ', 'must_have': ['alif_lam_qamariah'], 'must_not': []},
    {'label': 'Alif Lam Qamariah - lam + ha', 'ayah': 'ٱلۡحَمۡدُ', 'must_have': ['alif_lam_qamariah'], 'must_not': []},
    {'label': 'Lafzul Jalalah - tidak ada alif lam', 'ayah': 'وَٱللَّهُ عَلِيمٌ', 'must_have': [], 'must_not': ['alif_lam_syamsiah', 'alif_lam_qamariah']},

    # ==================== MAD ASLI (THABI'I) ====================
    {'label': 'Mad Asli - alif', 'ayah': 'قَالَ', 'must_have': ['mad_asli'], 'must_not': []},
    {'label': 'Mad Asli - waw', 'ayah': 'يَقُولُ', 'must_have': ['mad_asli'], 'must_not': []},
    {'label': 'Mad Asli - ya', 'ayah': 'فِي', 'must_have': ['mad_asli'], 'must_not': []},
    {'label': 'Mad Asli - alef madda', 'ayah': 'آمَنَ', 'must_have': ['mad_asli'], 'must_not': []},

    # ==================== MAD WAJIB MUTTASIL ====================
    {'label': 'Mad Wajib Muttasil - alif + hamzah', 'ayah': 'جَآءَ', 'must_have': ['mad_wajib_muttasil'], 'must_not': ['mad_asli']},
    {'label': 'Mad Wajib Muttasil - waw + hamzah', 'ayah': 'سُوءَ', 'must_have': ['mad_wajib_muttasil'], 'must_not': []},
    {'label': 'Mad Wajib Muttasil - ya + hamzah', 'ayah': 'هَؤُلَآءِ', 'must_have': ['mad_wajib_muttasil'], 'must_not': []},

    # ==================== MAD JAIZ MUNFASIL ====================
    {'label': 'Mad Jaiz Munfasil - alif akhir + hamzah awal', 'ayah': 'بِمَا أُنزِلَ', 'must_have': ['mad_jaiz_munfasil'], 'must_not': []},
    {'label': 'Mad Jaiz Munfasil - waw akhir + hamzah awal', 'ayah': 'قُوا أَنفُسَكُمۡ', 'must_have': ['mad_jaiz_munfasil'], 'must_not': []},

    # ==================== MAD LAZIM ====================
    {'label': 'Mad Lazim Mutsaqqal', 'ayah': 'ٱلضَّآلِّينَ', 'must_have': ['mad_lazim_mutsaqqal'], 'must_not': ['mad_asli']},
    {'label': 'Mad Lazim Harfi', 'ayah': 'الٓمٓ', 'must_have': ['mad_lazim_mukhaffaf'], 'must_not': []},

    # ==================== MAD LIN ====================
    {'label': 'Mad Lin - waw sukun + fathah', 'ayah': 'خَوۡفٌ', 'must_have': ['mad_lin'], 'must_not': []},
    {'label': 'Mad Lin - ya sukun + fathah', 'ayah': 'بَيۡتٌ', 'must_have': ['mad_lin'], 'must_not': []},

    # ==================== MAD IWAD ====================
    {'label': 'Mad Iwad - tanwin fathah di akhir ayat', 'ayah': 'عَلِيمًا', 'must_have': ['mad_iwad'], 'must_not': ['mad_asli']},

    # ==================== IDGHAM MUTAMATSILAIN ====================
    {'label': 'Idgham Mutamatsilain - qad + dal', 'ayah': 'قَدۡ دَخَلُواْ', 'must_have': ['idgham_mutamatsilain'], 'must_not': []},
    {'label': 'Idgham Mutamatsilain - bal + lam', 'ayah': 'بَل لَّا', 'must_have': ['idgham_mutamatsilain'], 'must_not': []},
    {'label': 'Idgham Mutamatsilain - nun + nun (prioritas bighunnah)', 'ayah': 'مِن نَّعِيمٍ', 'must_have': ['idgham_bighunnah'], 'must_not': ['idgham_mutamatsilain']},

    # ==================== IDGHAM MUTAJANISAIN ====================
    {'label': 'Idgham Mutajanisain - dal + ta', 'ayah': 'قَد تَّبَيَّنَ', 'must_have': ['idgham_mutajanisain'], 'must_not': []},
    {'label': 'Idgham Mutajanisain - tha + ta', 'ayah': 'بَسَطۡتَ', 'must_have': ['idgham_mutajanisain'], 'must_not': []},
    {'label': 'Idgham Mutajanisain - ba + mim', 'ayah': 'ٱرۡكَب مَّعَنَا', 'must_have': ['idgham_mutajanisain'], 'must_not': []},

    # ==================== TAFKHIM RA (sering muncul) ====================
    {'label': 'Tafkhim Ra - fathah', 'ayah': 'رَبُّ', 'must_have': ['tafkhim_ra'], 'must_not': []},
    {'label': 'Tafkhim Ra - dammah', 'ayah': 'رُسُلٌ', 'must_have': ['tafkhim_ra'], 'must_not': []},

    # ==================== TARQIQ RA (sering muncul) ====================
    {'label': 'Tarqiq Ra - kasrah', 'ayah': 'رِزۡقٌ', 'must_have': ['tarqiq_ra'], 'must_not': []},

    # ==================== LAM JALALAH (sering muncul) ====================
    {'label': 'Tafkhim Lam Jalalah - fathah sebelumnya', 'ayah': 'عَبۡدُ ٱللَّهِ', 'must_have': ['tafkhim_lam_jalalah'], 'must_not': []},
    {'label': 'Tafkhim Lam Jalalah - dammah sebelumnya', 'ayah': 'رَسُولُ ٱللَّهِ', 'must_have': ['tafkhim_lam_jalalah'], 'must_not': []},
    {'label': 'Tarqiq Lam Jalalah - kasrah sebelumnya', 'ayah': 'بِسۡمِ ٱللَّهِ', 'must_have': ['tarqiq_lam_jalalah'], 'must_not': []},

    # ==================== WAQAF (hanya yang umum) ====================
    {'label': 'Waqaf Lazim - م', 'ayah': 'ذَٰلِكَ ٱلۡكِتَابُ م', 'must_have': ['waqaf_lazim'], 'must_not': []},
    {'label': 'Waqaf Jaiz - ج', 'ayah': 'ٱلۡحَمۡدُ لِلَّهِ ج', 'must_have': ['waqaf_jaiz'], 'must_not': []},
    {'label': 'Waqaf Wajib - ط', 'ayah': 'مِنۢ بَعۡدِ ط', 'must_have': ['waqaf_wajib'], 'must_not': []},

    # ==================== FILTER LEVEL ====================
    {'label': 'Level basic - tidak tampilkan mad lazim', 'ayah': 'ٱلضَّآلِّينَ', 'must_have': [], 'must_not': [], 'level': 'basic'},
    {'label': 'Level basic - tampilkan izhar', 'ayah': 'مِنۡ عِلۡمٍ', 'must_have': ['izhar_halqi'], 'must_not': [], 'level': 'basic'},
    {'label': 'Level intermediate - tampilkan mad lazim', 'ayah': 'ٱلضَّآلِّينَ', 'must_have': ['mad_lazim_mutsaqqal'], 'must_not': [], 'level': 'intermediate'},
    {'label': 'Level expert - tampilkan mutajanisain', 'ayah': 'قَدۡ تَّبَيَّنَ', 'must_have': ['idgham_mutajanisain'], 'must_not': [], 'level': 'expert'},

    # ==================== FALSE POSITIVE PREVENTION ====================
    {'label': 'FP - nun hidup tidak jadi nun mati', 'ayah': 'نَعِيمٍ', 'must_have': [], 'must_not': ['ikhfa_haqiqi', 'idgham_bighunnah']},
    {'label': 'FP - mim hidup tidak jadi mim mati', 'ayah': 'مَلِكِ', 'must_have': [], 'must_not': ['izhar_syafawi']},

    # ==================== STRESS TEST ====================
    {'label': 'Stress Test - 4 aturan dalam satu ayat', 'ayah': 'إِنَّ ٱللَّهَ عَلِيمٌ حَكِيمٞ', 'must_have': ['ghunnah', 'alif_lam_qamariah', 'izhar_halqi'], 'must_not': []},
    {'label': 'Stress Test - ayat pendek banyak aturan', 'ayah': 'بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ', 'must_have': ['alif_lam_syamsiah', 'alif_lam_qamariah', 'mad_asli'], 'must_not': []},
]


def run_unit_tests(tests):
    passed = 0
    failed = 0
    fail_details = []

    print("=" * 60)
    print(f"UNIT TEST - ATURAN YANG SERING MUNCUL")
    print(f"Total test cases: {len(tests)}")
    print("=" * 60)

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


if __name__ == "__main__":
    p1, f1, fails = run_unit_tests(unit_tests)

    print("\n" + "=" * 60)
    print("HASIL AKHIR")
    print("=" * 60)
    print(f"Unit Test  : {p1} PASS, {f1} FAIL dari {len(unit_tests)} test")
    print(f"TOTAL      : {p1} PASS, {f1} FAIL")

    if fails:
        print(f"\nFAIL detail ({len(fails)}):")
        for f in fails[:10]:  # Hanya tampilkan 10 pertama
            print(f"  - {f}")
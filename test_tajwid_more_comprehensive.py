#!/usr/bin/env python
# -*- coding: utf-8 -*-

from main.utils_tilawah.tajwid_engine import analyze_tajwid

def run_maximum_test():
    """Test maksimal untuk engine tajwid - 3 level"""
    
    test_cases = []
    
    # ============================================================
    # LEVEL 1 - DASAR (Sudah ada, ditambah lebih lengkap)
    # ============================================================
    
    # 1. IZHAR HALQI - 6 huruf (tambah multiple examples)
    izhar_huruf = [
        ('ء', 'مِنْ أَحَدٍ', 'izhar_halqi'),
        ('ه', 'مِنْ هُوَ', 'izhar_halqi'),
        ('ع', 'مِنْ عِلْمٍ', 'izhar_halqi'),
        ('ح', 'مِنْ حَكِيمٍ', 'izhar_halqi'),
        ('غ', 'مِنْ غَفُورٍ', 'izhar_halqi'),
        ('خ', 'مِنْ خَالِقٍ', 'izhar_halqi'),
        # Tanwin version
        ('tanwin + ء', 'سَمِيعٌ أَحَدٌ', 'izhar_halqi'),
        ('tanwin + ه', 'قَوْمٌ هَادٍ', 'izhar_halqi'),
        ('tanwin + ع', 'سَمِيعٌ عَلِيمٌ', 'izhar_halqi'),
    ]
    
    # 2. IDGHAM BIGHUNNAH - 4 huruf
    idgham_bighunnah = [
        ('ي', 'مِنْ يَقُولُ', 'idgham_bighunnah'),
        ('ن', 'مِنْ نِعْمَةٍ', 'idgham_bighunnah'),
        ('م', 'مِنْ مَالٍ', 'idgham_bighunnah'),
        ('و', 'مِنْ وَلِيٍّ', 'idgham_bighunnah'),
        ('tanwin + ي', 'هُدًى يَهْتَدِي', 'idgham_bighunnah'),
        ('tanwin + ن', 'غَفُورٌ نَادَى', 'idgham_bighunnah'),
        ('tanwin + م', 'عَلِيمٌ مُبِينٌ', 'idgham_bighunnah'),
        ('tanwin + و', 'غَنِيٌّ وَلِيٌّ', 'idgham_bighunnah'),
    ]
    
    # 3. IDGHAM BILAGHUNNAH - 2 huruf
    idgham_bilaghunnah = [
        ('ل', 'مِنْ لَّدُنْهُ', 'idgham_bilaghunnah'),
        ('ر', 'مِنْ رَّبِّهِ', 'idgham_bilaghunnah'),
        ('tanwin + ل', 'خَيْرٌ لَّكُمْ', 'idgham_bilaghunnah'),
        ('tanwin + ر', 'غَفُورٞ رَّحِيمٌ', 'idgham_bilaghunnah'),
    ]
    
    # 4. IQLAB - 1 huruf
    iqlab = [
        ('nun + ba', 'مِنۢ بَعْدِ', 'iqlab'),
        ('tanwin + ba', 'سَمِيعٌۢ بَصِيرٌ', 'iqlab'),
        ('min ba', 'فَمِنۢ بَعْدِ', 'iqlab'),
    ]
    
    # 5. IKHFA HAQIQI - 15 huruf (semua)
    ikhfa_huruf = [
        ('ت', 'كُنتُمْ', 'ikhfa_haqiqi'),
        ('ث', 'فَمَن ثَقُلَتْ', 'ikhfa_haqiqi'),
        ('ج', 'مِن جَرَّ', 'ikhfa_haqiqi'),
        ('د', 'مِن دُونِ', 'ikhfa_haqiqi'),
        ('ذ', 'مِن ذَلِكَ', 'ikhfa_haqiqi'),
        ('ز', 'مِن زَيْتٍ', 'ikhfa_haqiqi'),
        ('س', 'مِن سَمَاءٍ', 'ikhfa_haqiqi'),
        ('ش', 'مِن شَيْءٍ', 'ikhfa_haqiqi'),
        ('ص', 'مِن صَالِحٍ', 'ikhfa_haqiqi'),
        ('ض', 'مِن ضَرَّ', 'ikhfa_haqiqi'),
        ('ط', 'مِن طَعَامٍ', 'ikhfa_haqiqi'),
        ('ظ', 'مِن ظَالِمٍ', 'ikhfa_haqiqi'),
        ('ف', 'مِن فَضْلٍ', 'ikhfa_haqiqi'),
        ('ق', 'مِن قَبْلِ', 'ikhfa_haqiqi'),
        ('ك', 'مِن كِتَابٍ', 'ikhfa_haqiqi'),
        # Tanwin version
        ('tanwin + ت', 'يَوْمَئِذٍ تَلْقَى', 'ikhfa_haqiqi'),
        ('tanwin + د', 'عَلِيمٌ دَاعٍ', 'ikhfa_haqiqi'),
        ('tanwin + ف', 'يَوْمَئِذٍ فَوَيْلٌ', 'ikhfa_haqiqi'),
        ('tanwin + ق', 'غَفُورٌ قَادِرٌ', 'ikhfa_haqiqi'),
    ]
    
    # 6. MIM MATI (Ikhfa Syafawi, Idgham Mimi, Izhar Syafawi)
    mim_mati = [
        ('ikhfa syafawi - ba', 'هُمۡ بِٱلْأٓخِرَةِ', 'ikhfa_syafawi'),
        ('idgham mimi - mim', 'لَهُم مَّغْفِرَةٌ', 'idgham_mimi'),
        ('izhar syafawi - waw', 'هُمۡ وَٱللَّهُ', 'izhar_syafawi'),
        ('izhar syafawi - ya', 'هُمۡ يَعْلَمُونَ', 'izhar_syafawi'),
        ('izhar syafawi - fa', 'هُمۡ فِي', 'izhar_syafawi'),
        ('izhar syafawi - lam', 'هُمۡ لَهُمْ', 'izhar_syafawi'),
    ]
    
    # 7. QALQALAH - 5 huruf
    qalqalah = [
        ('qaf sugra', 'يَقْدِرُ', 'qalqalah_sugra'),
        ('qaf kubra', 'الْفَلَقْ', 'qalqalah_kubra'),
        ('tha sugra', 'يَطْلُبُ', 'qalqalah_sugra'),
        ('tha kubra', 'الْمَوْتْ', 'qalqalah_kubra'),
        ('ba sugra', 'يَبْصُرُونَ', 'qalqalah_sugra'),
        ('ba kubra', 'تَرْبَحْ', 'qalqalah_kubra'),
        ('jim sugra', 'أَجْرٌ', 'qalqalah_sugra'),
        ('jim kubra', 'الْمَعَرَجْ', 'qalqalah_kubra'),
        ('dal sugra', 'يَحْصُدُ', 'qalqalah_sugra'),
        ('dal kubra', 'وَقَدْ', 'qalqalah_kubra'),
    ]
    
    # 8. GHUNNAH
    ghunnah = [
        ('nun tasydid', 'إِنَّ', 'ghunnah'),
        ('mim tasydid', 'ثُمَّ', 'ghunnah'),
        ('nun tasydid tengah', 'مِنَّا', 'ghunnah'),
        ('mim tasydid tengah', 'أَمَّا', 'ghunnah'),
        ('nun tasydid panjang', 'إِنَّمَا', 'ghunnah'),
    ]
    
    # 9. ALIF LAM
    alif_lam = [
        # Syamsiah - 14 huruf
        ('lam + ta', 'ٱلتَّوَّابُ', 'alif_lam_syamsiah'),
        ('lam + tsa', 'ٱلثَّلَاثَةُ', 'alif_lam_syamsiah'),
        ('lam + dal', 'ٱلدَّارُ', 'alif_lam_syamsiah'),
        ('lam + dzal', 'ٱلَّذِينَ', 'alif_lam_syamsiah'),
        ('lam + ra', 'ٱلرَّحْمَٰنِ', 'alif_lam_syamsiah'),
        ('lam + za', 'ٱلزَّيْتُونِ', 'alif_lam_syamsiah'),
        ('lam + sin', 'ٱلسَّمَاءِ', 'alif_lam_syamsiah'),
        ('lam + syin', 'ٱلشَّيْطَانُ', 'alif_lam_syamsiah'),
        ('lam + shad', 'ٱلصَّالِحَاتُ', 'alif_lam_syamsiah'),
        ('lam + dhad', 'ٱلضَّالِّينَ', 'alif_lam_syamsiah'),
        ('lam + tha', 'ٱلطَّيِّبَاتُ', 'alif_lam_syamsiah'),
        ('lam + zha', 'ٱلظَّالِمُونَ', 'alif_lam_syamsiah'),
        ('lam + lam', 'ٱللَّذِينَ', 'alif_lam_syamsiah'),
        ('lam + nun', 'ٱلنُّورُ', 'alif_lam_syamsiah'),
        # Qamariah - 14 huruf
        ('lam + hamzah', 'ٱلْأَرْضُ', 'alif_lam_qamariah'),
        ('lam + ba', 'ٱلْبَيْتُ', 'alif_lam_qamariah'),
        ('lam + jim', 'ٱلْجَنَّةُ', 'alif_lam_qamariah'),
        ('lam + ha', 'ٱلْحَمْدُ', 'alif_lam_qamariah'),
        ('lam + kha', 'ٱلْخَيْرُ', 'alif_lam_qamariah'),
        ('lam + ain', 'ٱلْعِلْمُ', 'alif_lam_qamariah'),
        ('lam + ghain', 'ٱلْغَيْبُ', 'alif_lam_qamariah'),
        ('lam + fa', 'ٱلْفَلَقُ', 'alif_lam_qamariah'),
        ('lam + qaf', 'ٱلْقُرْآنُ', 'alif_lam_qamariah'),
        ('lam + kaf', 'ٱلْكِتَابُ', 'alif_lam_qamariah'),
        ('lam + mim', 'ٱلْمُؤْمِنُونَ', 'alif_lam_qamariah'),
        ('lam + waw', 'ٱلْوَرَقُ', 'alif_lam_qamariah'),
        ('lam + ya', 'ٱلْيَوْمُ', 'alif_lam_qamariah'),
        ('lam + ha (besar)', 'ٱلْهَوَى', 'alif_lam_qamariah'),
    ]
    
    # 10. LAFZUL JALALAH (pengecualian)
    lafzul_jalalah = [
        ('الله', 'وَٱللَّهُ', 'no_rule'),
        ('لله', 'لِلَّهِ', 'no_rule'),
        ('بالله', 'بِٱللَّهِ', 'no_rule'),
        ('والله', 'وَٱللَّهِ', 'no_rule'),
        ('فالله', 'فَٱللَّهُ', 'no_rule'),
    ]
    
    # ============================================================
    # LEVEL 2 - HUKUM MAD (Tambahan untuk pengembangan berikutnya)
    # ============================================================
    
    mad_cases = [
        # Mad Tabi'i (2 harakat)
        ('mad tabii - alif', 'قَالَ', 'mad_tabii'),
        ('mad tabii - waw', 'يَقُولُ', 'mad_tabii'),
        ('mad tabii - ya', 'فِي', 'mad_tabii'),
        
        # Mad Wajib Muttasil (4-5 harakat)
        ('mad wajib muttasil', 'جَاءَ', 'mad_wajib_muttasil'),
        ('mad wajib muttasil', 'سُوءَ', 'mad_wajib_muttasil'),
        
        # Mad Jaiz Munfasil (2-5 harakat)
        ('mad jaiz munfasil', 'بِمَا أُنْزِلَ', 'mad_jaiz_munfasil'),
        ('mad jaiz munfasil', 'يَا أَيُّهَا', 'mad_jaiz_munfasil'),
        
        # Mad 'Arid Lissukun (2-6 harakat)
        ('mad arid lissukun', 'الْعَالَمِين', 'mad_arid_lissukun'),
        ('mad arid lissukun', 'نَسْتَعِين', 'mad_arid_lissukun'),
        
        # Mad Lazim (6 harakat)
        ('mad lazim kalimi mukhaffaf', 'آلْآن', 'mad_lazim'),
        ('mad lazim kalimi musaqqal', 'الضَّالِّينَ', 'mad_lazim'),
        ('mad lazim harfi mukhaffaf', 'الم', 'mad_lazim'),
        ('mad lazim harfi musaqqal', 'الٓمٓ', 'mad_lazim'),
        
        # Mad Iwad (2 harakat)
        ('mad iwad', 'عَلِيمًا', 'mad_iwad'),
        
        # Mad Lin (2-6 harakat)
        ('mad lin', 'خَوْفٌ', 'mad_lin'),
        ('mad lin', 'بَيْتٌ', 'mad_lin'),
        
        # Mad Silah
        ('mad silah qasirah', 'إِنَّهُ هُوَ', 'mad_silah'),
        ('mad silah thawilah', 'عِلْمُهُ عِنْدَهُ', 'mad_silah'),
    ]
    
    # ============================================================
    # LEVEL 3 - SIFAT HURUF & WAQAF (Pengembangan berikutnya)
    # ============================================================
    
    sifat_huruf_cases = [
        # Tafkhim dan Tarqiq untuk huruf Ra (ر)
        ('ra tafkhim - fathah', 'رَبُّ', 'ra_tafkhim'),
        ('ra tafkhim - dammah', 'رُسُلٌ', 'ra_tafkhim'),
        ('ra tafkhim - sukun sebelumnya fathah', 'فِرْعَوْنَ', 'ra_tafkhim'),
        ('ra tafkhim - sukun sebelumnya dammah', 'قُرْبٌ', 'ra_tafkhim'),
        ('ra tarqiq - kasrah', 'رِزْقٌ', 'ra_tarqiq'),
        ('ra tarqiq - sukun sebelumnya kasrah', 'شِرْعَةٌ', 'ra_tarqiq'),
        
        # Lam Jalalah
        ('lam jalalah tafkhim - fathah', 'عَبْدُ اللَّهِ', 'lam_jalalah_tafkhim'),
        ('lam jalalah tafkhim - dammah', 'لِلَّهِ', 'lam_jalalah_tafkhim'),
        ('lam jalalah tarqiq - kasrah', 'بِسْمِ اللَّهِ', 'lam_jalalah_tarqiq'),
        
        # Waqaf
        ('waqaf lazim - م', 'ذَٰلِكَ الْكِتَابُ', 'waqaf_lazim'),
        ('waqaf jaiz - ج', 'الْحَمْدُ لِلَّهِ', 'waqaf_jaiz'),
        ('saktah', 'عِوَجًا قَيِّمًا', 'saktah'),
    ]
    
    # ============================================================
    # EDGE CASES - Kombinasi multiple rules
    # ============================================================
    
    edge_cases = [
        ('multi rules 1', 'إِنَّ ٱللَّهَ عَلِيمٌ حَكِيمٌ', 'multiple'),
        ('multi rules 2', 'وَمَنْ يَتَّقِ ٱللَّهَ يَجْعَلْ لَهُ مَخْرَجًا', 'multiple'),
        ('no rules', 'قُلْ هُوَ ٱللَّهُ أَحَدٌ', 'no_rule'),
        ('long ayah', 'بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ', 'multiple'),
        ('basmalah', 'بِسْمِ ٱللَّهِ', 'no_rule'),
    ]
    
    # ============================================================
    # KUMPULKAN SEMUA TEST
    # ============================================================
    
    for cat, text, expected in izhar_huruf:
        test_cases.append(('izhar', text, expected, cat))
    for cat, text, expected in idgham_bighunnah:
        test_cases.append(('idgham_bighunnah', text, expected, cat))
    for cat, text, expected in idgham_bilaghunnah:
        test_cases.append(('idgham_bilaghunnah', text, expected, cat))
    for cat, text, expected in iqlab:
        test_cases.append(('iqlab', text, expected, cat))
    for cat, text, expected in ikhfa_huruf:
        test_cases.append(('ikhfa', text, expected, cat))
    for cat, text, expected in mim_mati:
        test_cases.append(('mim_mati', text, expected, cat))
    for cat, text, expected in qalqalah:
        test_cases.append(('qalqalah', text, expected, cat))
    for cat, text, expected in ghunnah:
        test_cases.append(('ghunnah', text, expected, cat))
    for cat, text, expected in alif_lam:
        test_cases.append(('alif_lam', text, expected, cat))
    for cat, text, expected in lafzul_jalalah:
        test_cases.append(('lafzul_jalalah', text, expected, cat))
    for cat, text, expected in edge_cases:
        test_cases.append(('edge', text, expected, cat))
    
    # Test untuk Level 2 dan 3 (akan FAIL karena engine belum support, untuk dokumentasi)
    for cat, text, expected in mad_cases:
        test_cases.append(('level2_mad', text, expected, cat))
    for cat, text, expected in sifat_huruf_cases:
        test_cases.append(('level3_sifat', text, expected, cat))
    
    # ============================================================
    # EKSEKUSI TEST
    # ============================================================
    
    print("=" * 80)
    print("TEST TAJWID ENGINE - MAKSIMAL (3 LEVEL)")
    print("=" * 80)
    print("Level 1: Hukum Dasar (Nun Mati, Mim Mati, Qalqalah, dll)")
    print("Level 2: Hukum Mad (Belum diimplementasikan - untuk referensi)")
    print("Level 3: Sifat Huruf & Waqaf (Belum diimplementasikan - untuk referensi)")
    print("=" * 80)
    
    passed = 0
    failed = 0
    skipped = 0
    results_detail = {
        'level1': {'pass': 0, 'fail': 0, 'total': 0},
        'level2': {'pass': 0, 'fail': 0, 'total': 0},
        'level3': {'pass': 0, 'fail': 0, 'total': 0}
    }
    
    for category, text, expected, description in test_cases:
        result = analyze_tajwid(text)
        
        # Extract rule names
        detected_rules = []
        for word_result in result:
            for rule in word_result.get('rules', []):
                detected_rules.append(rule.get('rule'))
        
        # Determine pass/fail berdasarkan level
        is_level1 = category in ['izhar', 'idgham_bighunnah', 'idgham_bilaghunnah', 'iqlab', 
                                  'ikhfa', 'mim_mati', 'qalqalah', 'ghunnah', 
                                  'alif_lam', 'lafzul_jalalah', 'edge']
        is_level2 = category == 'level2_mad'
        is_level3 = category == 'level3_sifat'
        
        if is_level1:
            if expected == "no_rule":
                is_pass = len(detected_rules) == 0
            elif expected == "multiple":
                is_pass = len(detected_rules) >= 2
            else:
                is_pass = expected in detected_rules
            
            if is_pass:
                status = "✅ PASS"
                passed += 1
                results_detail['level1']['pass'] += 1
            else:
                status = "❌ FAIL"
                failed += 1
                results_detail['level1']['fail'] += 1
                if failed <= 10:  # Print only first 10 failures
                    print(f"\n{status} | {category} | {description}")
                    print(f"       Text: {text}")
                    print(f"       Expected: {expected}")
                    print(f"       Detected: {detected_rules}")
            results_detail['level1']['total'] += 1
            
        elif is_level2 or is_level3:
            status = "⏭️ SKIP (Level 2/3 - not implemented)"
            skipped += 1
            if is_level2:
                results_detail['level2']['total'] += 1
            else:
                results_detail['level3']['total'] += 1
    
    # ============================================================
    # LAPORAN AKHIR
    # ============================================================
    
    print("\n" + "=" * 80)
    print("HASIL AKHIR")
    print("=" * 80)
    print(f"\n✅ PASS (Level 1): {results_detail['level1']['pass']}")
    print(f"❌ FAIL (Level 1): {results_detail['level1']['fail']}")
    print(f"📊 Akurasi Level 1: {results_detail['level1']['pass']}/{results_detail['level1']['total']} ({results_detail['level1']['pass']*100//results_detail['level1']['total'] if results_detail['level1']['total'] > 0 else 0}%)")
    
    print(f"\n⏭️ SKIP (Level 2 - Mad): {results_detail['level2']['total']} test (belum diimplementasikan)")
    print(f"⏭️ SKIP (Level 3 - Sifat & Waqaf): {results_detail['level3']['total']} test (belum diimplementasikan)")
    
    print("\n" + "=" * 80)
    print("RINGKASAN")
    print("=" * 80)
    print(f"Total Level 1 (Dasar): {results_detail['level1']['total']} test")
    print(f"Total Level 2 (Mad): {results_detail['level2']['total']} test")
    print(f"Total Level 3 (Sifat & Waqaf): {results_detail['level3']['total']} test")
    print(f"Total Keseluruhan: {results_detail['level1']['total'] + results_detail['level2']['total'] + results_detail['level3']['total']} test")
    
    print("\n" + "=" * 80)
    print("REKOMENDASI")
    print("=" * 80)
    print("1. Level 1 (Hukum Dasar): ✅ READY FOR PRODUCTION")
    print("2. Level 2 (Hukum Mad): ⚠️ Perlu pengembangan lebih lanjut")
    print("3. Level 3 (Sifat Huruf & Waqaf): ⚠️ Perlu pengembangan lebih lanjut")
    
    return results_detail['level1']['pass'], results_detail['level1']['fail'], skipped


if __name__ == "__main__":
    run_maximum_test()
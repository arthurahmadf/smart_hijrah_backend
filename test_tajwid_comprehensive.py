#!/usr/bin/env python
# -*- coding: utf-8 -*-


from main.utils_tilawah.tajwid_engine import analyze_tajwid

def run_test():
    """Test komprehensif untuk engine tajwid"""
    
    test_cases = [
        # ========== IZHAR HALQI (6 huruf) ==========
        ("ء", "مِنْ أَحَدٍ", "izhar_halqi", "Nun mati + hamzah"),
        ("ه", "مِنْ هُوَ", "izhar_halqi", "Nun mati + ha"),
        ("ع", "مِنْ عِلْمٍ", "izhar_halqi", "Nun mati + ain"),
        ("ح", "مِنْ حَكِيمٍ", "izhar_halqi", "Nun mati + ha"),
        ("غ", "مِنْ غَفُورٍ", "izhar_halqi", "Nun mati + ghain"),
        ("خ", "مِنْ خَالِقٍ", "izhar_halqi", "Nun mati + kha"),
        
        # ========== IDGHAM BIGHUNNAH (4 huruf) ==========
        ("ي", "مِنْ يَقُولُ", "idgham_bighunnah", "Nun mati + ya"),
        ("ن", "مِنْ نِعْمَةٍ", "idgham_bighunnah", "Nun mati + nun"),
        ("م", "مِنْ مَالٍ", "idgham_bighunnah", "Nun mati + mim"),
        ("و", "مِنْ وَلِيٍّ", "idgham_bighunnah", "Nun mati + waw"),
        
        # ========== IDGHAM BILAGHUNNAH (2 huruf) ==========
        ("ل", "مِنْ لَّدُنْهُ", "idgham_bilaghunnah", "Nun mati + lam"),
        ("ر", "مِنْ رَّبِّهِ", "idgham_bilaghunnah", "Nun mati + ra"),
        
        # ========== IQLAB (1 huruf) ==========
        ("ب", "مِنۢ بَعْدِ", "iqlab", "Nun mati + ba (dengan tanda iqlab)"),
        
        # ========== IKHFA HAQIQI (15 huruf) ==========
        ("ت", "كُنتُمْ", "ikhfa_haqiqi", "Nun mati + ta"),
        ("ث", "فَمَن ثَقُلَتْ", "ikhfa_haqiqi", "Nun mati + tsa"),
        ("ج", "مِن جَرَّ", "ikhfa_haqiqi", "Nun mati + jim"),
        ("د", "مِن دُونِ", "ikhfa_haqiqi", "Nun mati + dal"),
        ("ذ", "مِن ذَلِكَ", "ikhfa_haqiqi", "Nun mati + dzal"),
        ("ز", "مِن زَيْتٍ", "ikhfa_haqiqi", "Nun mati + za"),
        ("س", "مِن سَمَاءٍ", "ikhfa_haqiqi", "Nun mati + sin"),
        ("ش", "مِن شَيْءٍ", "ikhfa_haqiqi", "Nun mati + syin"),
        ("ص", "مِن صَالِحٍ", "ikhfa_haqiqi", "Nun mati + shad"),
        ("ض", "مِن ضَرَّ", "ikhfa_haqiqi", "Nun mati + dhad"),
        ("ط", "مِن طَعَامٍ", "ikhfa_haqiqi", "Nun mati + tha"),
        ("ظ", "مِن ظَالِمٍ", "ikhfa_haqiqi", "Nun mati + zha"),
        ("ف", "مِن فَضْلٍ", "ikhfa_haqiqi", "Nun mati + fa"),
        ("ق", "مِن قَبْلِ", "ikhfa_haqiqi", "Nun mati + qaf"),
        ("ك", "مِن كِتَابٍ", "ikhfa_haqiqi", "Nun mati + kaf"),
        
        # ========== TANWIN VERSIONS ==========
        ("Tanwin fath", "سَمِيعٌ أَحَدٌ", "izhar_halqi", "Tanwin + hamzah"),
        ("Tanwin fath", "عَلِيمٌ عَلِيمٌ", "idgham_bighunnah", "Tanwin + ain (tapi ain bukan idgham)"),
        ("Tanwin kasr", "يَوْمَئِذٍ فَوَيْلٌ", "ikhfa_haqiqi", "Tanwin + fa"),
        ("Tanwin damm", "غَفُورٞ رَّحِيمٌ", "idgham_bilaghunnah", "Tanwin + ra"),
        ("Tanwin damm Utsmani", "سَمِيعٌۢ بَصِيرٌ", "iqlab", "Tanwin + ba (dengan tanda iqlab)"),
        
        # ========== MIM MATI (IKHFA SYAFAWI, IDGHAM MIMI, IZHAR SYAFAWI) ==========
        ("ikhfa syafawi", "هُمۡ بِٱلْأٓخِرَةِ", "ikhfa_syafawi", "Mim mati + ba"),
        ("idgham mimi", "لَهُم مَّغْفِرَةٌ", "idgham_mimi", "Mim mati + mim"),
        ("izhar syafawi", "هُمۡ وَٱللَّهُ", "izhar_syafawi", "Mim mati + waw"),
        
        # ========== QALQALAH ==========
        ("qalqalah sugra", "يَقْدِرُ", "qalqalah_sugra", "Qaf sukun di tengah"),
        ("qalqalah sugra", "أَجْرٌ", "qalqalah_sugra", "Jim sukun di tengah"),
        ("qalqalah sugra", "يَبْصُرُونَ", "qalqalah_sugra", "Ba sukun di tengah"),
        ("qalqalah sugra", "يَحْسَبُ", "qalqalah_sugra", "Dal sukun di tengah"),
        ("qalqalah kubra", "وَقَدْ", "qalqalah_kubra", "Dal sukun di akhir"),
        ("qalqalah kubra", "الْفَلَقْ", "qalqalah_kubra", "Qaf sukun di akhir"),
        
        # ========== GHUNNAH ==========
        ("ghunnah", "إِنَّ", "ghunnah", "Nun tasydid"),
        ("ghunnah", "ثُمَّ", "ghunnah", "Mim tasydid"),
        ("ghunnah", "مِنَّا", "ghunnah", "Nun tasydid di tengah"),
        
        # ========== ALIF LAM ==========
        ("alif lam syamsiah", "ٱلَّذِينَ", "alif_lam_syamsiah", "Lam + dzal (syamsiah)"),
        ("alif lam syamsiah", "ٱلرَّحْمَٰنِ", "alif_lam_syamsiah", "Lam + ra (syamsiah)"),
        ("alif lam syamsiah", "ٱلسَّمَاءِ", "alif_lam_syamsiah", "Lam + sin (syamsiah)"),
        ("alif lam qamariah", "ٱلۡمُؤۡمِنِينَ", "alif_lam_qamariah", "Lam + mim (qamariah)"),
        ("alif lam qamariah", "ٱلۡحَمۡدُ", "alif_lam_qamariah", "Lam + ha (qamariah)"),
        
        # ========== LAFZUL JALALAH ==========
        ("lafzul jalalah", "وَٱللَّهُ عَلِيمٌ", "no_rule", "Lafzul jalalah tidak kena alif lam"),
        
        # ========== EDGE CASES ==========
        ("multiple words", "إِنَّ ٱللَّهَ عَلِيمٌ حَكِيمٌ", "multiple", "Multi aturan dalam satu ayat"),
        ("no rule", "قُلْ هُوَ ٱللَّهُ أَحَدٌ", "no_rule", "Tidak ada tajwid khusus"),
    ]
    
    print("=" * 70)
    print("TEST TAJWID ENGINE - KOMPREHENSIF")
    print("=" * 70)
    
    passed = 0
    failed = 0
    failed_cases = []
    
    for category, text, expected, description in test_cases:
        result = analyze_tajwid(text)
        
        # Extract rule names from result
        detected_rules = []
        for word_result in result:
            for rule in word_result.get('rules', []):
                detected_rules.append(rule.get('rule'))
        
        # Check if expected rule is in detected rules
        if expected == "no_rule":
            is_pass = len(detected_rules) == 0
        elif expected == "multiple":
            is_pass = len(detected_rules) >= 2
        else:
            is_pass = expected in detected_rules
        
        if is_pass:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
            failed_cases.append({
                'category': category,
                'text': text,
                'expected': expected,
                'detected': detected_rules,
                'description': description
            })
        
        # Print result
        rule_str = f"Expected: {expected}" if expected not in ["no_rule", "multiple"] else f"Expected: {expected}"
        print(f"{status} | {rule_str} | {description}")
        print(f"       Text: {text}")
        if not is_pass:
            print(f"       Detected: {detected_rules}")
        print()
    
    # Summary
    print("=" * 70)
    print(f"HASIL: {passed} PASS, {failed} FAIL dari {passed + failed} test")
    print("=" * 70)
    
    if failed_cases:
        print("\n❌ DETAIL FAIL:")
        for case in failed_cases:
            print(f"\n  Category: {case['category']}")
            print(f"  Text: {case['text']}")
            print(f"  Expected: {case['expected']}")
            print(f"  Detected: {case['detected']}")
            print(f"  Description: {case['description']}")
    
    return passed, failed

if __name__ == "__main__":
    run_test()
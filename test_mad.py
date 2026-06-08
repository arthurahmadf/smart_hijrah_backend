#!/usr/bin/env python
# -*- coding: utf-8 -*-

from main.utils_t.tajwid_engine import analyze_tajwid

def print_detailed_result(text, expected, detected, word_analysis=None):
    """Print detailed result with colors"""
    print(f"\n{'─' * 70}")
    print(f"📖 TEXT: {text}")
    print(f"🎯 EXPECTED: {expected}")
    print(f"🔍 DETECTED: {detected}")
    
    if word_analysis:
        print(f"\n📝 DETAIL PER KATA:")
        for wa in word_analysis:
            print(f"   Kata: '{wa['word']}'")
            for rule in wa.get('rules', []):
                print(f"      - {rule['rule']}: {rule['name']}")
    
    if expected in detected:
        print(f"✅ RESULT: PASS")
    else:
        print(f"❌ RESULT: FAIL")
    print(f"{'─' * 70}")


def test_mad_detailed():
    """Test khusus untuk hukum Mad dengan log lengkap"""
    
    test_cases = [
        {
            "name": "Mad Asli - Alif",
            "text": "قَالَ",
            "expected": "mad_asli",
            "description": "Fathah + alif (mad asli 2 harakat)"
        },
        {
            "name": "Mad Asli - Waw",
            "text": "يَقُولُ",
            "expected": "mad_asli",
            "description": "Dammah + waw (mad asli 2 harakat)"
        },
        {
            "name": "Mad Asli - Ya",
            "text": "فِي",
            "expected": "mad_asli",
            "description": "Kasrah + ya (mad asli 2 harakat)"
        },
        {
            "name": "Mad Wajib Muttasil",
            "text": "جَاءَ",
            "expected": "mad_wajib_muttasil",
            "description": "Mad bertemu hamzah dalam satu kata"
        },
        {
            "name": "Mad Jaiz Munfasil",
            "text": "بِمَا أُنْزِلَ",
            "expected": "mad_jaiz_munfasil",
            "description": "Mad di akhir kata, hamzah di awal kata berikutnya"
        },
        {
            "name": "Mad Jaiz Munfasil 2",
            "text": "قُوا أَنْفُسَكُمْ",
            "expected": "mad_jaiz_munfasil",
            "description": "Mad di akhir kata (waw sukun), hamzah di awal kata berikutnya"
        },
        {
            "name": "Mad Lazim Mutsaqqal",
            "text": "الضَّالِّينَ",
            "expected": "mad_lazim_mutsaqqal",
            "description": "Mad diikuti huruf bertasydid"
        },
        {
            "name": "Mad Lazim Mukhaffaf - Huruf",
            "text": "الم",
            "expected": "mad_lazim_mukhaffaf",
            "description": "Huruf muqatha'ah (alif lam mim)"
        },
        {
            "name": "Mad Lazim Mukhaffaf - Huruf",
            "text": "كهيعص",
            "expected": "mad_lazim_mukhaffaf",
            "description": "Huruf muqatha'ah (kaf ha ya ain shad)"
        },
    ]
    
    print("=" * 70)
    print("TEST HUKUM MAD - DETAIL LOG")
    print("=" * 70)
    
    passed = 0
    failed = 0
    failed_cases = []
    
    for tc in test_cases:
        result = analyze_tajwid(tc['text'])
        
        # Extract detected rules with word analysis
        detected_rules = []
        word_analysis = []
        for word_result in result:
            word_analysis.append({
                'word': word_result['word'],
                'rules': word_result.get('rules', [])
            })
            for rule in word_result.get('rules', []):
                detected_rules.append(rule.get('rule'))
        
        is_pass = tc['expected'] in detected_rules
        
        print(f"\n📌 TEST: {tc['name']}")
        print(f"   Deskripsi: {tc['description']}")
        print(f"   Text: '{tc['text']}'")
        print(f"   Expected: {tc['expected']}")
        print(f"   Detected: {detected_rules}")
        
        if word_analysis:
            print(f"   Detail per kata:")
            for wa in word_analysis:
                print(f"      - '{wa['word']}': {[r.get('rule') for r in wa['rules']]}")
        
        if is_pass:
            print(f"   ✅ PASS")
            passed += 1
        else:
            print(f"   ❌ FAIL")
            failed += 1
            failed_cases.append({
                'name': tc['name'],
                'text': tc['text'],
                'expected': tc['expected'],
                'detected': detected_rules,
                'description': tc['description']
            })
    
    # Summary
    print("\n" + "=" * 70)
    print("RINGKASAN TEST MAD")
    print("=" * 70)
    print(f"✅ PASS: {passed}")
    print(f"❌ FAIL: {failed}")
    print(f"📊 Akurasi: {passed * 100 // (passed + failed)}%")
    
    if failed_cases:
        print("\n" + "=" * 70)
        print("DETAIL FAILED CASES")
        print("=" * 70)
        for fc in failed_cases:
            print(f"\n📛 {fc['name']}")
            print(f"   Text: {fc['text']}")
            print(f"   Expected: {fc['expected']}")
            print(f"   Detected: {fc['detected']}")
            print(f"   Problem: {fc['description']}")
    
    return passed, failed, failed_cases


def analyze_specific_texts():
    """Analisa teks-teks spesifik yang bermasalah"""
    
    problem_texts = [
        ("قُوا أَنْفُسَكُمْ", "Mad jaiz munfasil - periksa apakah mad terdeteksi"),
        ("الضَّالِّينَ", "Mad lazim mutsaqqal - periksa huruf mad + tasydid"),
        ("الم", "Mad lazim mukhaffaf - periksa huruf muqatha'ah"),
        ("كهيعص", "Mad lazim mukhaffaf - periksa huruf muqatha'ah"),
    ]
    
    print("\n" + "=" * 70)
    print("ANALISA KHUSUS UNTUK TEKS BERMASALAH")
    print("=" * 70)
    
    for text, description in problem_texts:
        print(f"\n📖 TEXT: '{text}'")
        print(f"   Problem: {description}")
        
        result = analyze_tajwid(text)
        
        print(f"\n   🔍 Raw Analysis:")
        for word_result in result:
            print(f"   Word: '{word_result['word']}'")
            for rule in word_result.get('rules', []):
                print(f"      - rule: {rule.get('rule')}")
                print(f"        name: {rule.get('name')}")
                print(f"        desc: {rule.get('description')}")
        
        # Karakter breakdown untuk debugging
        print(f"\n   📝 Karakter breakdown:")
        chars = list(text)
        for i, ch in enumerate(chars):
            hex_code = hex(ord(ch))
            hex_code_str = hex_code.replace('0x', '')
            print(f"      {i}: '{ch}' (U+{hex_code_str})")
        
        print(f"\n{'─' * 50}")


if __name__ == "__main__":
    print("\n🚀 ENGINE TAJWID TERBARU - DETAILED TESTING\n")
    
    # Test mad dengan log lengkap
    passed, failed, failed_cases = test_mad_detailed()
    
    # Analisa khusus untuk teks yang fail
    if failed_cases:
        analyze_specific_texts()
    
    # Rekomendasi perbaikan
    print("\n" + "=" * 70)
    print("REKOMENDASI PERBAIKAN")
    print("=" * 70)
    
    if "الم" in str(failed_cases) or "كهيعص" in str(failed_cases):
        print("\n1. Untuk huruf muqatha'ah (الم, كهيعص):")
        print("   - Perlu deteksi khusus untuk huruf di awal surah")
        print("   - Setiap huruf dibaca panjang 6 harakat (mad lazim mukhaffaf harfi)")
    
    if "الضَّالِّينَ" in str(failed_cases):
        print("\n2. Untuk mad lazim mutsaqqal:")
        print("   - Deteksi huruf mad + tasydid (alif + lam + tasydid)")
        print("   - Perlu perbaikan di fungsi check_mad()")
    
    if "قُوا أَنْفُسَكُمْ" in str(failed_cases):
        print("\n3. Untuk mad jaiz munfasil:")
        print("   - Deteksi waw sukun di akhir kata + hamzah di awal kata berikutnya")
        print("   - Perbaiki logika 'after_char is None' dengan next_word")
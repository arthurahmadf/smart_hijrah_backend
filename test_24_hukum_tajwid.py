# test_tajwid_24_hukum.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hijrah.settings')
django.setup()

from main.utils_tilawah.tajwid_engine import analyze_tajwid


def run_tests():
    """Test case untuk 24 hukum tajwid"""
    
    test_cases = [
        # ==================== 1. IZHAR HALQI ====================
        {
            'label': 'Izhar Halqi - nun mati + ain',
            'text': 'مِنۡ عِلۡمٍ',
            'must_have': ['izhar_halqi'],
            'must_not': []
        },
        {
            'label': 'Izhar Halqi - tanwin + hamzah',
            'text': 'سَمِيعٌ أَحَدٌ',
            'must_have': ['izhar_halqi'],
            'must_not': []
        },
        
        # ==================== 2. IDGHAM BIGHUNNAH ====================
        {
            'label': 'Idgham Bighunnah - nun + ya',
            'text': 'مِن يَقُولُ',
            'must_have': ['idgham_bighunnah'],
            'must_not': []
        },
        {
            'label': 'Idgham Bighunnah - nun + mim (dengan tasydid)',
            'text': 'مِن مَّاءٍ',
            'must_have': ['idgham_bighunnah'],
            'must_not': []
        },
        
        # ==================== 3. IDGHAM BILAGHUNNAH ====================
        {
            'label': 'Idgham Bilaghunnah - nun + lam',
            'text': 'مِن لَّدُنۡهُ',
            'must_have': ['idgham_bilaghunnah'],
            'must_not': []
        },
        {
            'label': 'Idgham Bilaghunnah - tanwin + ra',
            'text': 'غَفُورٞ رَّحِيمٌ',
            'must_have': ['idgham_bilaghunnah'],
            'must_not': []
        },
        
        # ==================== 4. IQLAB ====================
        {
            'label': 'Iqlab - nun mati Uthmani + ba',
            'text': 'مِنۢ بَعۡدِ',
            'must_have': ['iqlab'],
            'must_not': []
        },
        {
            'label': 'Iqlab - tanwin + ba',
            'text': 'سَمِيعٌۢ بَصِيرٌ',
            'must_have': ['iqlab'],
            'must_not': []
        },
        
        # ==================== 5. IKHFA HAQIQI ====================
        {
            'label': 'Ikhfa Haqiqi - nun mati + ta',
            'text': 'كُنتُمۡ',
            'must_have': ['ikhfa_haqiqi'],
            'must_not': []
        },
        {
            'label': 'Ikhfa Haqiqi - nun mati + kaf',
            'text': 'مِن كُلِّ',
            'must_have': ['ikhfa_haqiqi'],
            'must_not': []
        },
        {
            'label': 'Ikhfa Haqiqi - tanwin + fa',
            'text': 'يَوۡمَئِذٍ فَوَيۡلٞ',
            'must_have': ['ikhfa_haqiqi'],
            'must_not': []
        },
        
        # ==================== 6. IKHFA SYAFAWI (MIM MATI) ====================
        {
            'label': 'Ikhfa Syafawi - mim mati + ba',
            'text': 'هُمۡ بِٱلۡأٓخِرَةِ',
            'must_have': ['ikhfa_syafawi'],
            'must_not': []
        },
        
        # ==================== 7. IDGHAM MIMI (MIM MATI) ====================
        {
            'label': 'Idgham Mimi - mim mati + mim',
            'text': 'لَهُم مَّغۡفِرَةٌ',
            'must_have': ['idgham_mimi'],
            'must_not': []
        },
        
        # ==================== 8. IZHAR SYAFAWI (MIM MATI) ====================
        {
            'label': 'Izhar Syafawi - mim mati + waw',
            'text': 'هُمۡ وَٱللَّهُ',
            'must_have': ['izhar_syafawi'],
            'must_not': []
        },
        {
            'label': 'Izhar Syafawi - mim mati + ya',
            'text': 'هُمۡ يَعۡلَمُونَ',
            'must_have': ['izhar_syafawi'],
            'must_not': []
        },
        
        # ==================== 9. QALQALAH SUGRA ====================
        {
            'label': 'Qalqalah Sugra - qaf sukun tengah',
            'text': 'يَقۡدِرُ',
            'must_have': ['qalqalah_sugra'],
            'must_not': ['qalqalah_kubra']
        },
        {
            'label': 'Qalqalah Sugra - ba sukun tengah',
            'text': 'يَبۡصُرُونَ',
            'must_have': ['qalqalah_sugra'],
            'must_not': ['qalqalah_kubra']
        },
        
        # ==================== 10. QALQALAH KUBRA ====================
        {
            'label': 'Qalqalah Kubra - dal akhir kata',
            'text': 'وَقَدۡ',
            'must_have': ['qalqalah_kubra'],
            'must_not': ['qalqalah_sugra']
        },
        {
            'label': 'Qalqalah Kubra - qaf akhir ayat',
            'text': 'ٱلۡفَلَقِ',
            'must_have': ['qalqalah_kubra'],
            'must_not': ['qalqalah_sugra']
        },
        
        # ==================== 11. GHUNNAH ====================
        {
            'label': 'Ghunnah - nun tasydid',
            'text': 'إِنَّ',
            'must_have': ['ghunnah'],
            'must_not': []
        },
        {
            'label': 'Ghunnah - mim tasydid',
            'text': 'ثُمَّ',
            'must_have': ['ghunnah'],
            'must_not': []
        },
        {
            'label': 'Ghunnah - TIDAK ada saat nun tanpa shadda',
            'text': 'نَعِيمٍ',
            'must_have': [],
            'must_not': ['ghunnah']
        },
        
        # ==================== 12. ALIF LAM SYAM SIAH ====================
        {
            'label': 'Alif Lam Syamsiah - lam + dzal',
            'text': 'ٱلَّذِينَ',
            'must_have': ['alif_lam_syamsiah'],
            'must_not': ['alif_lam_qamariah']
        },
        {
            'label': 'Alif Lam Syamsiah - lam + ra',
            'text': 'ٱلرَّحۡمَٰنِ',
            'must_have': ['alif_lam_syamsiah'],
            'must_not': ['alif_lam_qamariah']
        },
        
        # ==================== 13. ALIF LAM QAMARIAH ====================
        {
            'label': 'Alif Lam Qamariah - lam + mim',
            'text': 'ٱلۡمُؤۡمِنِينَ',
            'must_have': ['alif_lam_qamariah'],
            'must_not': ['alif_lam_syamsiah']
        },
        {
            'label': 'Alif Lam Qamariah - lam + ba',
            'text': 'ٱلۡبَيۡتُ',
            'must_have': ['alif_lam_qamariah'],
            'must_not': ['alif_lam_syamsiah']
        },
        
        # ==================== 14. MAD ASLI ====================
        {
            'label': 'Mad Asli - alif',
            'text': 'قَالَ رَبُّ',  # 2 kata, bukan 1
            'must_have': ['mad_asli'],
            'must_not': ['mad_aridh_lissukun']
        },
        {
            'label': 'Mad Asli - waw',
            'text': 'يَقُولُ رَبُّ',  # 2 kata
            'must_have': ['mad_asli'],
            'must_not': ['mad_aridh_lissukun']
        },
        {
            'label': 'Mad Asli - ya',
            'text': 'فِي رَبِّ',  # 2 kata
            'must_have': ['mad_asli'],
            'must_not': ['mad_aridh_lissukun']
        },
        
        # ==================== 15. MAD WAJIB MUTTASIL ====================
        {
            'label': 'Mad Wajib Muttasil - alif + hamzah',
            'text': 'جَآءَ',
            'must_have': ['mad_wajib_muttasil'],
            'must_not': ['mad_asli']
        },
        {
            'label': 'Mad Wajib Muttasil - waw + hamzah',
            'text': 'سُوءَ',
            'must_have': ['mad_wajib_muttasil'],
            'must_not': ['mad_asli']
        },
        
        # ==================== 16. MAD JAIZ MUNFASIL ====================
        {
            'label': 'Mad Jaiz Munfasil - alif akhir + hamzah awal',
            'text': 'بِمَا أُنزِلَ',
            'must_have': ['mad_jaiz_munfasil'],
            'must_not': ['mad_asli']
        },
        {
            'label': 'Mad Jaiz Munfasil - waw akhir + hamzah awal',
            'text': 'قُوا أَنفُسَكُمۡ',
            'must_have': ['mad_jaiz_munfasil'],
            'must_not': ['mad_asli']
        },
        
        # ==================== 17. MAD LAZIM MUTSAQQAL ====================
        {
            'label': 'Mad Lazim Mutsaqqal',
            'text': 'ٱلضَّآلِّينَ',
            'must_have': ['mad_lazim_mutsaqqal'],
            'must_not': ['mad_asli']
        },
        
        # ==================== 18. MAD LAZIM MUKHAFFAF ====================
        {
            'label': 'Mad Lazim Mukhaffaf - huruf muqathaah',
            'text': 'الٓمٓ',
            'must_have': ['mad_lazim_mukhaffaf'],
            'must_not': ['mad_asli']
        },
        {
            'label': 'Mad Lazim Mukhaffaf - kalimi',
            'text': 'ءَآلۡـَٰٔنَ',
            'must_have': ['mad_lazim_mukhaffaf'],
            'must_not': ['mad_asli']
        },
        
        # ==================== 19. MAD ARIDH LISSUKUN ====================
        {
            'label': 'Mad Aridh Lissukun - waw di akhir ayat',
            'text': 'يَعۡلَمُونَ',
            'must_have': ['mad_aridh_lissukun'],
            'must_not': ['mad_asli']
        },
        {
            'label': 'Mad Aridh Lissukun - alif di akhir ayat',
            'text': 'مَٰلِكَا',
            'must_have': ['mad_aridh_lissukun'],
            'must_not': ['mad_asli']
        },
        
        # ==================== 20. MAD LIN ====================
        {
            'label': 'Mad Lin - waw sukun + fathah',
            'text': 'خَوۡفٌ',
            'must_have': ['mad_lin'],
            'must_not': []
        },
        {
            'label': 'Mad Lin - ya sukun + fathah',
            'text': 'بَيۡتٌ',
            'must_have': ['mad_lin'],
            'must_not': []
        },
        
        # ==================== 21. MAD IWAD ====================
        {
            'label': 'Mad Iwad - tanwin fathah di akhir ayat',
            'text': 'عَلِيمًا',
            'must_have': ['mad_iwad'],
            'must_not': ['mad_asli', 'mad_aridh_lissukun']
        },
        
        # ==================== 22. IDGHAM MUTAMATSILAIN ====================
        {
            'label': 'Idgham Mutamatsilain - qad + dal',
            'text': 'قَدۡ دَخَلُواْ',
            'must_have': ['idgham_mutamatsilain'],
            'must_not': []
        },
        {
            'label': 'Idgham Mutamatsilain - bal + lam',
            'text': 'بَل لَّا',
            'must_have': ['idgham_mutamatsilain'],
            'must_not': []
        },
        {
            'label': 'Idgham Mutamatsilain - nun + nun (prioritas bighunnah)',
            'text': 'مِن نَّعِيمٍ',
            'must_have': ['idgham_bighunnah'],
            'must_not': ['idgham_mutamatsilain']
        },
        
        # ==================== 23. IDGHAM MUTAJANISAIN ====================
        {
            'label': 'Idgham Mutajanisain - dal + ta',
            'text': 'قَدۡ تَّبَيَّنَ',
            'must_have': ['idgham_mutajanisain'],
            'must_not': []
        },
        {
            'label': 'Idgham Mutajanisain - ba + mim',
            'text': 'ٱرۡكَب مَّعَنَا',
            'must_have': ['idgham_mutajanisain'],
            'must_not': []
        },
        
        # ==================== 24. IDGHAM MUTAQARIBAIN ====================
        {
            'label': 'Idgham Mutaqaribain - qaf + kaf',
            'text': 'نَخۡلُقْ كُّم',
            'must_have': ['idgham_mutaqaribain'],
            'must_not': []
        },
        {
            'label': 'Idgham Mutaqaribain - lam + ra',
            'text': 'قُل رَّبِّ',
            'must_have': ['idgham_mutaqaribain'],
            'must_not': []
        },
        {
            'label': 'Idgham Mutaqaribain - TIDAK ada saat nun + lam (prioritas bilaghunnah)',
            'text': 'مِن لَّدُنۡهُ',
            'must_have': ['idgham_bilaghunnah'],
            'must_not': ['idgham_mutaqaribain']
        },
        
        # ==================== False Positive Checks ====================
        {
            'label': 'FP - nun hidup tidak jadi nun mati',
            'text': 'نَعِيمٍ',
            'must_have': [],
            'must_not': ['ikhfa_haqiqi', 'idgham_bighunnah']
        },
        {
            'label': 'FP - mim hidup tidak jadi mim mati',
            'text': 'مَلِكِ',
            'must_have': [],
            'must_not': ['izhar_syafawi']
        },
    ]
    
    print("=" * 70)
    print("TEST 24 HUKUM TAJWID")
    print("=" * 70)
    
    passed = 0
    failed = 0
    fail_details = []
    
    for tc in test_cases:
        result = analyze_tajwid(tc['text'])
        
        detected = []
        for word_result in result:
            for rule in word_result.get('rules', []):
                detected.append(rule.get('rule'))
        
        # Remove duplicates
        detected = list(set(detected))
        
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
        
        if ok:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
            fail_details.append({
                'label': tc['label'],
                'text': tc['text'],
                'expected': tc['must_have'],
                'detected': detected,
                'reason': fail_reason
            })
        
        print(f"{status} | {tc['label']}")
        if not ok:
            print(f"       Text: {tc['text']}")
            print(f"       Expected: {tc['must_have']}")
            print(f"       Detected: {detected}")
            print(f"       Reason: {fail_reason}")
    
    print("\n" + "=" * 70)
    print(f"HASIL: {passed} PASS, {failed} FAIL dari {len(test_cases)} test")
    print("=" * 70)
    
    if fail_details:
        print("\n❌ DETAIL FAIL:")
        for fd in fail_details:
            print(f"  - {fd['label']}")
            print(f"    Text: {fd['text']}")
            print(f"    Expected: {fd['expected']}")
            print(f"    Detected: {fd['detected']}")
            print(f"    Reason: {fd['reason']}")
            print()
    
    return passed, failed


if __name__ == "__main__":
    run_tests()
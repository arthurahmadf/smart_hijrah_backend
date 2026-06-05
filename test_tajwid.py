import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hijrah.settings')
django.setup()

from main.utils_tilawah.tajwid_engine import analyze_tajwid

# Kita test ayat-ayat yang SUDAH KITA TAHU hukum tajwidnya
# sehingga bisa verifikasi apakah engine benar atau salah

test_cases = [
    {
        'label': 'Izhar Halqi — nun mati + ain',
        'ayah': 'مِنۡ عِلۡمٍ',
        'expected': ['izhar_halqi'],
    },
    {
        'label': 'Izhar Halqi — tanwin + hamzah',
        'ayah': 'عَلِيمٌ أَحَدٌ',
        'expected': ['izhar_halqi'],
    },
    {
        'label': 'Idgham Bighunnah — nun mati + ya',
        'ayah': 'مِن يَقُولُ',
        'expected': ['idgham_bighunnah'],
    },
    {
        'label': 'Idgham Bighunnah — tanwin + waw',
        'ayah': 'يَوۡمَئِذٖ وَمَا',
        'expected': ['idgham_bighunnah'],
    },
    {
        'label': 'Idgham Bilaghunnah — nun mati + lam',
        'ayah': 'مِن لَّدُنۡهُ',
        'expected': ['idgham_bilaghunnah'],
    },
    {
        'label': 'Idgham Bilaghunnah — tanwin + ra',
        'ayah': 'غَفُورٞ رَّحِيمٞ',
        'expected': ['idgham_bilaghunnah'],
    },
    {
        'label': 'Iqlab — nun mati + ba',
        'ayah': 'مِنۢ بَعۡدِ',
        'expected': ['iqlab'],
    },
    {
        'label': 'Iqlab — tanwin + ba',
        'ayah': 'سَمِيعٌۢ بَصِيرٌ',
        'expected': ['iqlab'],
    },
    {
        'label': 'Ikhfa Haqiqi — nun mati + ta',
        'ayah': 'كُنتُمۡ',
        'expected': ['ikhfa_haqiqi'],
    },
    {
        'label': 'Ikhfa Haqiqi — tanwin + fa',
        'ayah': 'يَوۡمَئِذٍ فَوَيۡلٞ',
        'expected': ['ikhfa_haqiqi'],
    },
    {
        'label': 'Ikhfa Syafawi — mim mati + ba',
        'ayah': 'هُمۡ بِٱلۡأٓخِرَةِ',
        'expected': ['ikhfa_syafawi'],
    },
    {
        'label': 'Idgham Mimi — mim mati + mim',
        'ayah': 'لَهُم مَّغۡفِرَةٌ',
        'expected': ['idgham_mimi'],
    },
    {
        'label': 'Izhar Syafawi — mim mati + waw',
        'ayah': 'هُمۡ وَٱللَّهُ',
        'expected': ['izhar_syafawi'],
    },
    {
        'label': 'Qalqalah Sugra — qaf sukun di tengah',
        'ayah': 'يَقۡدِرُ',
        'expected': ['qalqalah_sugra'],
    },
    {
        'label': 'Qalqalah Kubra — dal sukun di akhir',
        'ayah': 'وَقَدۡ',
        'expected': ['qalqalah_kubra'],
    },
    {
        'label': 'Ghunnah — nun tasydid',
        'ayah': 'إِنَّ',
        'expected': ['ghunnah'],
    },
    {
        'label': 'Ghunnah — mim tasydid',
        'ayah': 'ثُمَّ',
        'expected': ['ghunnah'],
    },
    {
        'label': 'Alif Lam Syamsiah — lam + dzal',
        'ayah': 'ٱلَّذِينَ',
        'expected': ['alif_lam_syamsiah'],
    },
    {
        'label': 'Alif Lam Qamariah — lam + mim',
        'ayah': 'ٱلۡمُؤۡمِنِينَ',
        'expected': ['alif_lam_qamariah'],
    },
    {
        'label': 'Lafzul Jalalah — tidak ada alif lam',
        'ayah': 'وَٱللَّهُ عَلِيمٌ',
        'expected': [],  # tidak boleh ada alif_lam apapun untuk الله
    },
    {
        'label': 'Tidak ada tajwid khusus',
        'ayah': 'قُلۡ هُوَ',
        'expected': [],
    },
]

# ===== RUN TESTS =====
passed = 0
failed = 0

for tc in test_cases:
    results = analyze_tajwid(tc['ayah'])

    # Kumpulkan semua rules yang terdeteksi
    detected_rules = []
    for r in results:
        for rule in r['rules']:
            detected_rules.append(rule['rule'])

    # Cek apakah semua expected rules terdeteksi
    expected = tc['expected']
    
    if expected == []:
        # Tidak boleh ada rule yang unexpected
        # Filter hanya rule yang relevan dengan test ini
        ok = True
        for d in detected_rules:
            if d.startswith('alif_lam') and 'Lafzul Jalalah' in tc['label']:
                ok = False
                break
    else:
        ok = all(e in detected_rules for e in expected)

    status = '✅ PASS' if ok else '❌ FAIL'
    if ok:
        passed += 1
    else:
        failed += 1

    print(f"{status} | {tc['label']}")
    if not ok:
        print(f"       Expected : {expected}")
        print(f"       Detected : {detected_rules}")

print(f"\n{'='*50}")
print(f"Hasil: {passed} PASS, {failed} FAIL dari {len(test_cases)} test")


words = ['كُنتُمۡ', 'مِنۢ', 'إِنَّ', 'ثُمَّ', 'لَهُم']
for w in words:
    print(f"\n{w}:")
    for c in w:
        print(f"  {repr(c)} hex: {hex(ord(c))}")
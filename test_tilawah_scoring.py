# test_tilawah_scoring.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hijrah.settings')
django.setup()

from main.utils_tilawah.feedback_builder import build_feedback


def test_scoring():
    """Test case untuk verifikasi perhitungan skor"""
    
    test_cases = [
        {
            'label': 'Bacaan sempurna - ayat dengan mad_asli',
            'ref': 'ٱلۡفَلَقِ',
            'trans': 'ٱلۡفَلَقِ',
            'expected': {'word_accuracy': 100.0, 'tajwid_score': 100.0}
        },
        {
            'label': 'Bacaan sempurna - ayat panjang',
            'ref': 'بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ',
            'trans': 'بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ',
            'expected': {'word_accuracy': 100.0, 'tajwid_score': 100.0}
        },
    ]

    print("=" * 70)
    print("TEST TILAWAH SCORING (DENGAN DEBUG)")
    print("=" * 70)

    for tc in test_cases:
        result = build_feedback(tc['ref'], tc['trans'])
        
        print(f"\n📌 {tc['label']}")
        print(f"   REF: {tc['ref']}")
        print(f"   TRANS: {tc['trans']}")
        print(f"   word_accuracy: {result['word_accuracy']}%")
        print(f"   tajwid_score: {result['tajwid_score']}%")
        
        # === DEBUG: Lihat feedback items ===
        print(f"\n   🔍 FEEDBACK ITEMS ({len(result['ai_feedback'])} items):")
        for item in result['ai_feedback']:
            print(f"      - id: {item['id']}")
            print(f"        type: {item['type']}")  # <-- INI YANG PENTING
            print(f"        arabic: {item['arabic'][:50]}...")
            print(f"        caption: {item.get('caption')}")
        
        print("\n" + "-" * 40)

if __name__ == "__main__":
    test_scoring()
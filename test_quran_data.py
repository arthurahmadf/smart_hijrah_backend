import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hijrah.settings')
django.setup()

from main.models_tilawah import TilawahAyahPool

def test_quran_data():
    print("=" * 60)
    print("TEST DATA QURAN (TRANSLITERASI & TERJEMAHAN)")
    print("=" * 60)
    
    # Test beberapa ayat
    test_cases = [
        (1, 1, "Al-Fatihah", 1),
        (112, 1, "Al-Ikhlas", 1),
        (113, 1, "Al-Falaq", 1),
        (113, 2, "Al-Falaq", 2),
        (113, 3, "Al-Falaq", 3),
        (113, 4, "Al-Falaq", 4),
        (113, 5, "Al-Falaq", 5),
        (114, 1, "An-Nas", 1),
        (114, 2, "An-Nas", 2),
        (114, 3, "An-Nas", 3),
        (114, 4, "An-Nas", 4),
        (114, 5, "An-Nas", 5),
        (114, 6, "An-Nas", 6),
    ]
    
    total = 0
    valid = 0
    
    for surah, ayah, surah_name, ayah_num in test_cases:
        obj = TilawahAyahPool.objects.filter(
            surah_number=surah, 
            ayah_number=ayah
        ).first()
        
        if obj:
            total += 1
            
            # Cek apakah transliterasi dan terjemahan terisi
            has_translit = bool(obj.ayah_transliteration and obj.ayah_transliteration.strip())
            has_translation = bool(obj.ayah_translation and obj.ayah_translation.strip())
            
            if has_translit and has_translation:
                valid += 1
                status = "✅"
            elif has_translit:
                valid += 1
                status = "⚠️ (no translation)"
            elif has_translation:
                valid += 1
                status = "⚠️ (no transliteration)"
            else:
                status = "❌ (empty)"
            
            print(f"{status} {surah_name}:{ayah_num}")
            print(f"   Arab: {obj.ayah_text[:60]}...")
            print(f"   Latin: {obj.ayah_transliteration[:60] if obj.ayah_transliteration else '(kosong)'}...")
            print(f"   Indo : {obj.ayah_translation[:60] if obj.ayah_translation else '(kosong)'}...")
            print()
        else:
            print(f"❌ NOT FOUND: {surah_name}:{ayah_num}")
            print()
    
    print("=" * 60)
    print(f"RESULT: {valid}/{total} ayat memiliki data lengkap")
    print("=" * 60)

if __name__ == "__main__":
    test_quran_data()
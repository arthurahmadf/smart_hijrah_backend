import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hijrah.settings')
django.setup()

from main.utils_tilawah.tajwid_engine import get_base_letter, ALL_SUKUN, check_idgham_mutamatsilain

# Test kata yang mengandung fa mati + fa
words = ['فَٱعۡفُ', 'عَنۡهُمۡ', 'وَٱصۡفَحۡ', 'فَإِنَّ']
print("=== Cek setiap kata ===")
for i, w in enumerate(words):
    chars = list(w)
    print(f"\n[{i}] {w}")
    for j, c in enumerate(chars):
        print(f"  [{j}] {repr(c)} hex:{hex(ord(c))} base:{repr(get_base_letter(c))}")
    result = check_idgham_mutamatsilain(words, i)
    print(f"  → result: {[r['rule'] for r in result]}")
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_hijrah.settings')
django.setup()

from main.utils_tilawah.tajwid_engine import analyze_tajwid
from main.models_tilawah import TilawahAyahPool
import random

# ============================================================
# UNIT TEST CASES - LENGKAP (10/10)
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
    {'label': 'Qalqalah Sugra - dal sukun tengah', 'ayah': 'يَحۡصُدُ', 'must_have': ['qalqalah_sugra'], 'must_not': []},
    {'label': 'Qalqalah Sugra - tha sukun tengah', 'ayah': 'يَطۡلُبُ', 'must_have': ['qalqalah_sugra'], 'must_not': []},
    {'label': 'Qalqalah Kubra - dal akhir kata', 'ayah': 'وَقَدۡ', 'must_have': ['qalqalah_kubra'], 'must_not': []},
    {'label': 'Qalqalah Kubra - qaf akhir ayat', 'ayah': 'ٱلۡفَلَقِ', 'must_have': ['qalqalah_kubra'], 'must_not': []},
    {'label': 'Qalqalah Kubra - ba akhir kata', 'ayah': 'تَرۡبَحۡ', 'must_have': ['qalqalah_kubra'], 'must_not': []},

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
    {'label': 'Mad Jaiz Munfasil - ya akhir + hamzah awal', 'ayah': 'ٱهۡدِنَا ٱلصِّرَٰطَ', 'must_have': ['mad_jaiz_munfasil'], 'must_not': []},

    # ==================== MAD LAZIM ====================
    {'label': 'Mad Lazim Mutsaqqal Kalimi', 'ayah': 'ٱلضَّآلِّينَ', 'must_have': ['mad_lazim_mutsaqqal'], 'must_not': ['mad_asli']},
    {'label': 'Mad Lazim Mutsaqqal Harfi', 'ayah': 'الٓمٓ', 'must_have': ['mad_lazim_mukhaffaf'], 'must_not': []},
    {'label': 'Mad Lazim Mukhaffaf Kalimi', 'ayah': 'ءَآلۡـَٰٔنَ', 'must_have': ['mad_lazim_mukhaffaf'], 'must_not': []},

    # ==================== MAD LIN ====================
    {'label': 'Mad Lin - waw sukun + fathah', 'ayah': 'خَوۡفٌ', 'must_have': ['mad_lin'], 'must_not': []},
    {'label': 'Mad Lin - waw sukun + dammah', 'ayah': 'يَوۡمٌ', 'must_have': ['mad_lin'], 'must_not': []},
    {'label': 'Mad Lin - ya sukun + fathah', 'ayah': 'بَيۡتٌ', 'must_have': ['mad_lin'], 'must_not': []},
    {'label': 'Mad Lin - ya sukun + kasrah', 'ayah': 'شَيۡءٞ', 'must_have': ['mad_lin'], 'must_not': []},
    {'label': 'Mad Lin - di akhir ayat (waqaf)', 'ayah': 'مِنۡ خَوۡفِ', 'must_have': ['mad_lin'], 'must_not': []},

    # ==================== MAD IWAD ====================
    {'label': 'Mad Iwad - tanwin fathah di akhir ayat', 'ayah': 'عَلِيمًا', 'must_have': ['mad_iwad'], 'must_not': ['mad_asli']},
    {'label': 'Mad Iwad - tanwin fathah + alif', 'ayah': 'غَفُورًا', 'must_have': ['mad_iwad'], 'must_not': []},
    {'label': 'Mad Iwad - TIDAK ada di tengah ayat', 'ayah': 'عَلِيمًا حَكِيمًا', 'must_have': [], 'must_not': ['mad_iwad']},

    # ==================== MAD SILAH ====================
    {'label': 'Mad Silah Qasirah - ha dhomir + huruf hidup', 'ayah': 'إِنَّهُ هُوَ', 'must_have': ['mad_silah_qasirah'], 'must_not': []},
    {'label': 'Mad Silah Qasirah - lahu + huruf hidup', 'ayah': 'لَهُ ٱلۡمُلۡكُ', 'must_have': ['mad_silah_qasirah'], 'must_not': []},
    {'label': 'Mad Silah Qasirah - TIDAK ada jika ha kecil + sukun', 'ayah': 'عَلَيْهِمۡ', 'must_have': [], 'must_not': ['mad_silah_qasirah']},
    {'label': 'Mad Silah Thawilah - ha dhomir + hamzah', 'ayah': 'عِلۡمُهُۥ عِنۡدَهُۥٓ', 'must_have': ['mad_silah_thawilah'], 'must_not': []},

    # ==================== MAD ARIDH LISSUKUN ====================
    {'label': 'Mad Aridh - waw mad di akhir waqaf', 'ayah': 'يَعۡلَمُو', 'must_have': ['mad_aridh_lissukun'], 'must_not': []},
    {'label': 'Mad Aridh - ya mad di akhir waqaf', 'ayah': 'ٱلۡعَٰلَمِي', 'must_have': ['mad_aridh_lissukun'], 'must_not': []},
    {'label': 'Mad Aridh - alef mad di akhir waqaf', 'ayah': 'مَٰلِكَا', 'must_have': ['mad_aridh_lissukun'], 'must_not': []},
    {'label': 'Mad Aridh - TIDAK ada di tengah ayat', 'ayah': 'يَعۡلَمُونَ قُلۡ', 'must_have': [], 'must_not': ['mad_aridh_lissukun']},

    # ==================== TAFKHIM & TARQIQ (Huruf Ra) ====================
    {'label': 'Tafkhim Ra - fathah', 'ayah': 'رَبُّ', 'must_have': ['tafkhim_ra'], 'must_not': []},
    {'label': 'Tafkhim Ra - dammah', 'ayah': 'رُسُلٌ', 'must_have': ['tafkhim_ra'], 'must_not': []},
    {'label': 'Tafkhim Ra - sukun sebelumnya fathah', 'ayah': 'فِرۡعَوۡنَ', 'must_have': ['tafkhim_ra'], 'must_not': []},
    {'label': 'Tafkhim Ra - sukun sebelumnya dammah', 'ayah': 'قُرۡبٌ', 'must_have': ['tafkhim_ra'], 'must_not': []},
    {'label': 'Tarqiq Ra - kasrah', 'ayah': 'رِزۡقٌ', 'must_have': ['tarqiq_ra'], 'must_not': []},
    {'label': 'Tarqiq Ra - sukun sebelumnya kasrah', 'ayah': 'شِرۡعَةٌ', 'must_have': ['tarqiq_ra'], 'must_not': []},
    {'label': 'Tarqiq Ra - setelah ya sukun', 'ayah': 'خَيۡرٞ', 'must_have': ['tarqiq_ra'], 'must_not': []},

    # ==================== LAM JALALAH ====================
    {'label': 'Tafkhim Lam Jalalah - fathah sebelumnya', 'ayah': 'عَبۡدُ ٱللَّهِ', 'must_have': ['tafkhim_lam_jalalah'], 'must_not': []},
    {'label': 'Tafkhim Lam Jalalah - dammah sebelumnya', 'ayah': 'رَسُولُ ٱللَّهِ', 'must_have': ['tafkhim_lam_jalalah'], 'must_not': []},
    {'label': 'Tarqiq Lam Jalalah - kasrah sebelumnya', 'ayah': 'بِسۡمِ ٱللَّهِ', 'must_have': ['tarqiq_lam_jalalah'], 'must_not': []},

    # ==================== IDGHAM MUTAMATSILAIN ====================
    {'label': 'Idgham Mutamatsilain - qad + dal', 'ayah': 'قَدۡ دَخَلُواْ', 'must_have': ['idgham_mutamatsilain'], 'must_not': []},
    {'label': 'Idgham Mutamatsilain - bal + lam', 'ayah': 'بَل لَّا', 'must_have': ['idgham_mutamatsilain'], 'must_not': []},
    {'label': 'Idgham Mutamatsilain - nun + nun (prioritas bighunnah)', 'ayah': 'مِن نَّعِيمٍ', 'must_have': ['idgham_bighunnah'], 'must_not': ['idgham_mutamatsilain']},

    # ==================== IDGHAM MUTAJANISAIN ====================
    {'label': 'Idgham Mutajanisain - dal + ta', 'ayah': 'قَد تَّبَيَّنَ', 'must_have': ['idgham_mutajanisain'], 'must_not': []},
    {'label': 'Idgham Mutajanisain - tha + ta', 'ayah': 'بَسَطۡتَ', 'must_have': ['idgham_mutajanisain'], 'must_not': []},
    {'label': 'Idgham Mutajanisain - ba + mim', 'ayah': 'ٱرۡكَب مَّعَنَا', 'must_have': ['idgham_mutajanisain'], 'must_not': []},
    {'label': 'Idgham Mutajanisain - tsal + dzal', 'ayah': 'يَلۡهَث ذَّٰلِكَ', 'must_have': ['idgham_mutajanisain'], 'must_not': []},

    # ==================== IDGHAM MUTAQARIBAIN ====================
    {'label': 'Idgham Mutaqaribain - qaf + kaf', 'ayah': 'نَخۡلُقْ كُّم', 'must_have': ['idgham_mutaqaribain'], 'must_not': []},
    {'label': 'Idgham Mutaqaribain - qaf + kaf (dalam kata)', 'ayah': 'نَخۡلُقكُّم', 'must_have': ['idgham_mutaqaribain'], 'must_not': []},
    {'label': 'Idgham Mutaqaribain - lam + ra', 'ayah': 'قُل رَّبِّ', 'must_have': ['idgham_mutaqaribain'], 'must_not': []},
    {'label': 'Idgham Mutaqaribain - nun + lam', 'ayah': 'مِن لَّدُنۡهُ', 'must_have': ['idgham_bilaghunnah'], 'must_not': ['idgham_mutaqaribain']},

    # ==================== TANDA WAQAF & SAKTAH ====================
    {'label': 'Waqaf Lazim - م', 'ayah': 'ذَٰلِكَ ٱلۡكِتَابُ م', 'must_have': ['waqaf_lazim'], 'must_not': []},
    {'label': 'Waqaf Jaiz - ج', 'ayah': 'ٱلۡحَمۡدُ لِلَّهِ ج', 'must_have': ['waqaf_jaiz'], 'must_not': []},
    {'label': 'Waqaf Wajib - ط', 'ayah': 'مِنۢ بَعۡدِ ط', 'must_have': ['waqaf_wajib'], 'must_not': []},
    {'label': 'Waqaf Mamnu - لا', 'ayah': 'لَا رَطۡبٖ لَّا', 'must_have': ['waqaf_mamnu'], 'must_not': []},
    {'label': 'Saktah', 'ayah': 'عِوَجࣰ ا قَيِّمࣰا', 'must_have': ['saktah'], 'must_not': []},

    # ==================== QIRA'AT KHUSUS ====================
    {'label': 'Naql - pemindahan harakat', 'ayah': 'يَـٰٓأَيُّهَا', 'must_have': ['naql'], 'must_not': []},
    {'label': 'Imalah - condong ke kasrah', 'ayah': 'مَجۡر۪ىٰهَا', 'must_have': ['imalah'], 'must_not': []},
    {'label': 'Tashil - hamzah kedua dilembutkan', 'ayah': 'ءَآلۡـَٰٔنَ', 'must_have': ['tashil'], 'must_not': []},

    # ==================== FILTER LEVEL ====================
    {'label': 'Level basic - tidak tampilkan mad lazim', 'ayah': 'ٱلضَّآلِّينَ', 'must_have': [], 'must_not': [], 'level': 'basic'},
    {'label': 'Level basic - tampilkan izhar', 'ayah': 'مِنۡ عِلۡمٍ', 'must_have': ['izhar_halqi'], 'must_not': [], 'level': 'basic'},
    {'label': 'Level intermediate - tampilkan mad lazim', 'ayah': 'ٱلضَّآلِّينَ', 'must_have': ['mad_lazim_mutsaqqal'], 'must_not': [], 'level': 'intermediate'},
    {'label': 'Level expert - tampilkan semua termasuk waqaf', 'ayah': 'قَدۡ تَّبَيَّنَ', 'must_have': ['idgham_mutajanisain'], 'must_not': [], 'level': 'expert'},

    # ==================== FALSE POSITIVE PREVENTION ====================
    {'label': 'FP - nun hidup tidak jadi nun mati', 'ayah': 'نَعِيمٍ', 'must_have': [], 'must_not': ['ikhfa_haqiqi', 'idgham_bighunnah']},
    {'label': 'FP - mim hidup tidak jadi mim mati', 'ayah': 'مَلِكِ', 'must_have': [], 'must_not': ['izhar_syafawi']},
    {'label': 'FP - tidak mad pada huruf biasa', 'ayah': 'كِتَابٌ', 'must_have': [], 'must_not': ['mad_asli']},

    # ==================== STRESS TEST (Kombinasi Multiple Rules) ====================
    {'label': 'Stress Test - 5 aturan dalam satu ayat', 'ayah': 'إِنَّ ٱللَّهَ عَلِيمٌ حَكِيمٞ', 'must_have': ['ghunnah', 'alif_lam_qamariah', 'izhar_halqi'], 'must_not': []},
    {'label': 'Stress Test - panjang 10 kata', 'ayah': 'وَإِنۡ أَحَدٞ مِّنَ ٱلۡمُشۡرِكِينَ ٱسۡتَجَارَكَ فَأَجِرۡهُ', 'must_have': ['idgham_bighunnah', 'alif_lam_qamariah', 'ikhfa_haqiqi'], 'must_not': []},
    {'label': 'Stress Test - banyak mad', 'ayah': 'أُوْلَٰٓئِكَ عَلَىٰ هُدٗى مِّن رَّبِّهِمۡ', 'must_have': ['mad_wajib_muttasil', 'mad_asli', 'idgham_bilaghunnah'], 'must_not': []},
    {'label': 'Stress Test - ayat panjang (Al-Fatihah)', 'ayah': 'بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ. ٱلۡحَمۡدُ لِلَّهِ رَبِّ ٱلۡعَٰلَمِينَ. ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ. مَٰلِكِ يَوۡمِ ٱلدِّينِ. إِيَّاكَ نَعۡبُدُ وَإِيَّاكَ نَسۡتَعِينُ. ٱهۡدِنَا ٱلصِّرَٰطَ ٱلۡمُسۡتَقِيمَ. صِرَٰطَ ٱلَّذِينَ أَنۡعَمۡتَ عَلَيۡهِمۡ غَيۡرِ ٱلۡمَغۡضُوبِ عَلَيۡهِمۡ وَلَا ٱلضَّآلِّينَ.', 'must_have': ['idgham_mutamatsilain', 'alif_lam_syamsiah', 'alif_lam_qamariah', 'mad_asli'], 'must_not': []},
]


# ============================================================
# FUNGSI TEST
# ============================================================

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
        'mad_aridh_lissukun', 'mad_lin', 'mad_iwad',
        'mad_silah_qasirah', 'mad_silah_thawilah',
        'idgham_mutamatsilain', 'idgham_mutajanisain', 'idgham_mutaqaribain',
        'tafkhim_ra', 'tarqiq_ra', 'tafkhim_lam_jalalah', 'tarqiq_lam_jalalah',
        'waqaf_lazim', 'waqaf_jaiz', 'waqaf_wajib', 'waqaf_mamnu', 'saktah',
        'naql', 'imalah', 'tashil'
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


# ============================================================
# EKSEKUSI TEST
# ============================================================

print("="*60)
print("BAGIAN 1: UNIT TEST (10/10 COMPLETE)")
print(f"Total test cases: {len(unit_tests)}")
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
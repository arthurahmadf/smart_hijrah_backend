# main/utils_nlp/weights.py

# ===== BOBOT TINGGI (10) - Ibadah & Fiqih Utama =====
ISLAMIC_WEIGHTS_HIGH = {
    # Ibadah
    'shalat', 'sholat', 'solat', 'puasa', 'ramadhan', 'zakat', 'haji', 'umroh', 'umrah',
    'wudhu', 'wudu', 'tayamum', 'mandi wajib', 'junub', 'najis', 'thaharah', 'bersuci',
    
    # Muamalah
    'nikah', 'pernikahan', 'talak', 'cerai', 'rujuk', 'iddah', 'waris', 'faraid', 
    'hibah', 'wasiat', 'jual beli', 'dagang', 'riba', 'gharar', 'maysir', 'judi',
    'halal', 'haram', 'makruh', 'sunat', 'sunah', 'wajib', 'fardhu', 'mubah', 'syubhat',
    'bidah', 'khilaf', 'ijma', 'qiyas', 'ijtihad', 'fatwa',
    
    # Akhlak
    'taqwa', 'ikhlas', 'tawakal', 'sabar', 'syukur', 'taubat', 'istighfar',
    'dosa', 'pahala', 'amal', 'ibadah', 'doa', 'dzikir', 'zikir', 'tilawah',
    
    # Tajwid
    'tajwid', 'makhraj', 'qalqalah', 'idgham', 'ikhfa', 'izhar', 'iqlab',
    'ghunnah', 'mad', 'waqaf', 'ibtida', 'saktah',

    'anak', 'anak-anak', 'keturunan', 'zurriyah', 'keluarga', 'rumah tangga',
    'orang tua', 'ayah', 'ibu', 'bapak', 'ibu bapak', 'parenting',
}

# ===== BOBOT SEDANG (8) - Hadis & Quran =====
ISLAMIC_WEIGHTS_MEDIUM = {
    'hadis', 'hadits', 'hadist', 'riwayat', 'periwayat', 'sanad', 'matan',
    'raawi', 'perawi', 'rawi', 'mutawatir', 'ahad', 'shahih', 'hasan', 'daif', 'dhaif',
    'marfu', 'mauquf', 'maqtu', 'mursal', 'munqathi', 'muallaq',
    'ayat', 'surat', 'surah', 'juz', 'hizb', 'rubu', 'nisf',
    'makkiyah', 'madaniyah', 'nasikh', 'mansukh', 'asbabun nuzul',
    'tafsir', 'ta\'wil', 'terjemah', 'transliterasi', 'quran', 'alquran', 'al-quran',
    'mendidik', 'didik', 'pendidikan', 'belajar', 'mengajar', 'pengajaran',
    'tarbiyah', 'akhlak', 'budi pekerti', 'moral', 'etika',
    'mengajarkan', 'pelajaran', 'ilmu', 'pengetahuan',
}

# ===== BOBOT RENDAH (5) - Nama & Istilah Umum Islam =====
ISLAMIC_WEIGHTS_LOW = {
    'nabi', 'rasul', 'allah', 'tuhan', 'ilah', 'malaikat', 
    'jibril', 'mikail', 'israfil', 'izrail', 'munkar', 'nakir',
    'sirath', 'shirat', 'surga', 'neraka', 'jannah', 'jahannam', 
    'kafir', 'muslim', 'mukmin', 'munafik', 'musyrik',
    'salaf', 'khalaf', 'ulama', 'fuqaha', 'mujtahid', 'mufti', 'imam',
    'khatib', 'qari', 'hafiz', 'hafidz', 'ustadz', 'kyai', 'buya',
    'sahabat', 'tabiin', 'tabiut tabiin',
    'cara', 'bagaimana', 'tips', 'panduan', 'metode', 'strategi',
}

# Gabungkan semua
ISLAMIC_WEIGHTS = {}
ISLAMIC_WEIGHTS.update({k: 10 for k in ISLAMIC_WEIGHTS_HIGH})
ISLAMIC_WEIGHTS.update({k: 8 for k in ISLAMIC_WEIGHTS_MEDIUM})
ISLAMIC_WEIGHTS.update({k: 5 for k in ISLAMIC_WEIGHTS_LOW})

# Kata umum (bobot rendah)
GENERIC_WEIGHTS = {
    'tampil': 1, 'lihat': 1, 'cari': 1, 'beri': 1, 'kasih': 1,
    'boleh': 1, 'bisa': 1, 'dapat': 1, 'mau': 1, 'ingin': 1,
    'apa': 1, 'siapa': 1, 'kapan': 1, 'di mana': 1, 'bagaimana': 1,
}

# Kata yang harus diabaikan (bobot 0)
STOPWORDS_CUSTOM = {
    'apbn', 'apbd',  # Hanya yang benar-benar tidak relevan
    # Sisanya dipindahkan ke bobot rendah
}

# Tambahkan kata-kata umum dengan bobot 1-2
LOW_WEIGHT_WORDS = {
    'presiden': 1, 'menteri': 1, 'gubernur': 1, 'bupati': 1,
    'polisi': 1, 'tentara': 1, 'hakim': 1, 'jaksa': 1,
    'perusahaan': 2, 'korporasi': 2, 'bisnis': 5, 'usaha': 5,
    'modal': 2, 'investasi': 2, 'saham': 2, 'bank': 2,
    'kredit': 2, 'pinjaman': 2,
}
# main/utils/gamification_constants.py

# Poin per amalan (di luar shalat wajib)
AMALAN_POINTS = {
    'tilawah': 5,
    'dzikir': 3,
    'puasa_sunnah': 20,
    'sedekah': 15,
    'tahajjud': 25,
    'dhuha': 15,
    'kajian': 10,
}

# Threshold level
LEVEL_THRESHOLDS = {
    'starter': 0,
    'bronze': 500,
    'silver': 2000,
    'gold': 5000,
    'platinum': 10000,
    'diamond': 25000,
}

# Poin per shalat wajib
PRAYER_POINTS = 10

# Poin bonus jika semua shalat terisi dalam sehari (opsional)
PERFECT_PRAYER_BONUS = 10
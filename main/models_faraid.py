from django.db import models
from django.conf import settings

class InheritanceSession(models.Model):
    """Menyimpan sesi perhitungan waris user"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inheritance_sessions')
    total_assets = models.DecimalField(max_digits=15, decimal_places=2, help_text="Total harta warisan (Rp)")
    funeral_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Biaya perawatan jenazah")
    debt = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Hutang pewaris")
    will = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Wasiat (maks 1/3 dari sisa)")
    result_data = models.JSONField(default=dict, help_text="Hasil perhitungan lengkap")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'faraid_inheritance_session'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Inheritance #{self.id} - {self.user.username}"


class Heir(models.Model):
    """Data master ahli waris"""
    GENDER_CHOICES = [
        ('M', 'Laki-laki'),
        ('F', 'Perempuan'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=[('L', 'Laki-laki'), ('P', 'Perempuan')])
    priority = models.IntegerField(default=0, help_text="Prioritas hijab, semakin kecil semakin tinggi")
    default_share = models.CharField(max_length=10, blank=True, null=True, help_text="Bagian default: 1/2, 1/4, 1/8, 2/3, 1/3, 1/6, ashabah")
    is_ashabah = models.BooleanField(default=False, help_text="Apakah termasuk ashabah (mendapat sisa)")
    
    class Meta:
        db_table = 'faraid_heir_master'
        ordering = ['priority']
    
    def __str__(self):
        return self.name


class HeirBlock(models.Model):
    """Aturan hijab (siapa menghalangi siapa)"""
    blocker = models.ForeignKey(Heir, on_delete=models.CASCADE, related_name='blocks')
    blocked = models.ForeignKey(Heir, on_delete=models.CASCADE, related_name='blocked_by')
    
    class Meta:
        db_table = 'faraid_heir_block'
        unique_together = ('blocker', 'blocked')
    
    def __str__(self):
        return f"{self.blocker.name} menghalangi {self.blocked.name}"
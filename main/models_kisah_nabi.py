from django.db import models

class KisahNabi(models.Model):
    """Model untuk kisah para nabi"""
    prophet_name = models.CharField(max_length=100)  # nama nabi (adam, ibrahim, dll)
    total_read_count = models.IntegerField(default=0)
    main_cover = models.ImageField(upload_to='kisah_nabi/covers/', null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'kisah_nabi'
        ordering = ['id']
    
    def __str__(self):
        return f"Kisah Nabi {self.prophet_name}"

class KisahNabiEpisode(models.Model):
    """Episode untuk setiap kisah nabi"""
    kisah_nabi = models.ForeignKey(KisahNabi, on_delete=models.CASCADE, related_name='episodes')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    doc_url = models.URLField(max_length=500, blank=True, null=True)  # URL ke file PDF
    cover_url = models.URLField(max_length=500, blank=True, null=True)
    order = models.IntegerField(default=0)  # urutan episode
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'kisah_nabi_episode'
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.kisah_nabi.prophet_name} - {self.title}"

class KisahNabiReadLog(models.Model):
    """Log untuk mencatat setiap kali user membaca kisah nabi"""
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='kisah_read_logs')
    kisah_nabi = models.ForeignKey(KisahNabi, on_delete=models.CASCADE, related_name='read_logs')
    episode = models.ForeignKey(KisahNabiEpisode, on_delete=models.CASCADE, related_name='read_logs', null=True, blank=True)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'kisah_nabi_read_log'
    
    def __str__(self):
        return f"{self.user.username} read {self.kisah_nabi.prophet_name}"
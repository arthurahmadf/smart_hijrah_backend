from django.db import models
from django.conf import settings

class KelasTahfidz(models.Model):
    """Kelas untuk belajar mengaji Al-Quran"""
    title = models.CharField(max_length=255)
    description = models.TextField()
    duration_in_seconds = models.IntegerField()  # Durasi total kelas dalam detik
    banner = models.ImageField(upload_to='kelas_banners/', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_dewasa = models.BooleanField(default=True)  # True: dewasa, False: anak-anak
    lecturer_id = models.IntegerField()  # ID dari user (ustadz)
    lecturer_name = models.CharField(max_length=255)
    enroll_count = models.IntegerField(default=0)
    learning_materials = models.JSONField(default=list)  # List materi seperti ["Tajwid", "Tahsin"]
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ngaji_kelas_tahfidz'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class KelasSchedule(models.Model):
    """Jadwal untuk kelas tahfidz"""
    kelas = models.ForeignKey(KelasTahfidz, on_delete=models.CASCADE, related_name='schedules')
    days = models.JSONField(default=list)  # List hari ["senin", "rabu"]
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_in_seconds = models.IntegerField()
    enrolled_students = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'ngaji_kelas_schedule'
    
    def __str__(self):
        return f"{self.kelas.title} - {self.days}"

class KelasEnrollment(models.Model):
    """Pendaftaran user ke kelas tahfidz"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kelas_enrollments')
    kelas = models.ForeignKey(KelasTahfidz, on_delete=models.CASCADE, related_name='enrollments')
    selected_schedule = models.ForeignKey(KelasSchedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments')
    
    # Data pendaftar
    nama_lengkap = models.CharField(max_length=255)
    jenis_kelamin = models.CharField(max_length=10, choices=[('laki-laki', 'Laki-laki'), ('perempuan', 'Perempuan')])
    usia_in_tahun = models.IntegerField()
    
    # Data orang tua (jika peserta adalah anak-anak)
    parent_name = models.CharField(max_length=255, blank=True, null=True)
    parent_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Alamat
    address = models.TextField()
    
    # Tingkat kemampuan ngaji
    ngaji_level = models.IntegerField(help_text="1=Beginner, 2=Basic, 3=Intermediate, 4=Advanced")
    
    # Status
    is_dewasa = models.BooleanField(default=True)
    is_private = models.BooleanField(default=False)
    
    enrollment_status = models.CharField(
        max_length=20, 
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled')
        ],
        default='pending'
    )
    
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ngaji_kelas_enrollment'
        unique_together = ('user', 'kelas')
    
    def __str__(self):
        return f"{self.user.username} - {self.kelas.title}"


class Pelajaran(models.Model):
    """Learning path / program pembelajaran"""
    name = models.CharField(max_length=255)
    description = models.TextField()
    step = models.IntegerField(default=1)  # Urutan step
    course_total = models.IntegerField(default=0)  # Total pelajaran dalam program
    course_finished = models.IntegerField(default=0)  # Pelajaran yang sudah diselesaikan user
    
    class Meta:
        db_table = 'ngaji_pelajaran'
        ordering = ['step']
    
    def __str__(self):
        return self.name

class DetailPelajaran(models.Model):
    """Detail pelajaran dalam learning path (step by step)"""
    pelajaran = models.ForeignKey(Pelajaran, on_delete=models.CASCADE, related_name='details')
    name = models.CharField(max_length=255)
    step = models.IntegerField()
    arabic_text_icon = models.CharField(max_length=255, blank=True, null=True)  # Contoh: "ا ب ت ث"
    is_finished = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'ngaji_detail_pelajaran'
        ordering = ['step']
    
    def __str__(self):
        return f"{self.pelajaran.name} - {self.name}"

class MateriPelajaran(models.Model):
    """Materi spesifik untuk setiap detail pelajaran (contoh: Huruf Alif)"""
    detail_pelajaran = models.ForeignKey(DetailPelajaran, on_delete=models.CASCADE, related_name='materi')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    arabic = models.CharField(max_length=50)  # Huruf arab
    latin = models.CharField(max_length=50)  # Tulisan latin
    audio_url = models.URLField(max_length=500, blank=True, null=True)  # URL audio makhraj
    
    order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'ngaji_materi_pelajaran'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.title} - {self.arabic}"
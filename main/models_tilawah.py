from __future__ import annotations

import hashlib
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models, transaction
from django.db.models import F, Q
from django.utils import timezone
from pgvector.django import VectorField


LEVEL_CHOICES = [
    ("basic", "Basic"),
    ("intermediate", "Intermediate"),
    ("expert", "Expert"),
]


class TilawahLevelSource(models.TextChoices):
    LEGACY = "legacy", "Legacy"
    ENGINE = "engine", "Engine"
    MANUAL = "manual", "Manual"


class TajwidDisplayGroup(models.TextChoices):
    NUN_TANWIN = "nun_tanwin", "Nun Mati dan Tanwin"
    MIM_SAKINAH = "mim_sakinah", "Mim Sakinah"
    MAD = "mad", "Mad"
    QALQALAH = "qalqalah", "Qalqalah"
    GHUNNAH = "ghunnah", "Ghunnah"
    ALIF_LAM = "alif_lam", "Alif Lam"
    IDGHAM = "idgham", "Idgham"
    TAFKHIM_TARQIQ = "tafkhim_tarqiq", "Tafkhim dan Tarqiq"
    WAQF = "waqf", "Waqaf"
    ORTHOGRAPHIC = "orthographic", "Ortografis"


class TajwidAppliesWhen(models.TextChoices):
    WASL = "wasl", "Wasal"
    WAQF = "waqf", "Waqaf"
    BOTH = "both", "Keduanya"
    CONTEXTUAL = "contextual", "Kontekstual"
    PROFILE_DEPENDENT = "profile_dependent", "Bergantung Profil"


class TajwidDefaultAppliesWhen(models.TextChoices):
    WASL = "wasl", "Wasal"
    WAQF = "waqf", "Waqaf"
    BOTH = "both", "Keduanya"
    CONTEXTUAL = "contextual", "Kontekstual"


class TajwidAssessmentFamily(models.TextChoices):
    ARTICULATION = "articulation", "Artikulasi"
    ASSIMILATION = "assimilation", "Asimilasi"
    NASALIZATION = "nasalization", "Dengung"
    DURATION = "duration", "Durasi"
    RELEASE = "release", "Pelepasan Bunyi"
    RESONANCE = "resonance", "Resonansi"
    PAUSE = "pause", "Jeda"
    RENDER_ONLY = "render_only", "Tampilan Saja"


class TajwidReadingMode(models.TextChoices):
    AYAH = "ayah", "Tampilan Ayat"
    WASL = "wasl", "Wasal"
    WAQF = "waqf", "Waqaf"


class TajwidAnnotationSetStatus(models.TextChoices):
    GENERATED = "generated", "Generated"
    VALIDATED = "validated", "Validated Otomatis"
    NEEDS_REVIEW = "needs_review", "Perlu Review"
    VERIFIED = "verified", "Terverifikasi Ahli"
    PUBLISHED = "published", "Published"
    FAILED = "failed", "Failed"


COLOR_VALIDATOR = RegexValidator(
    regex=r"^0xFF[0-9A-F]{6}$",
    message="Warna harus menggunakan format Flutter 0xFFAABBCC.",
)

RULE_CODE_VALIDATOR = RegexValidator(
    regex=r"^[a-z0-9_]+$",
    message="Kode hukum hanya boleh berisi huruf kecil, angka, dan underscore.",
)

ENGINE_VERSION_VALIDATOR = RegexValidator(
    regex=r"^[A-Za-z0-9._+-]+$",
    message="Versi engine mengandung karakter yang tidak valid.",
)

SHA256_VALIDATOR = RegexValidator(
    regex=r"^[0-9a-f]{64}$",
    message="source_text_hash harus berupa SHA-256 lowercase sepanjang 64 karakter.",
)



def calculate_ayah_text_hash(ayah_text: str) -> str:
    """Hash stabil untuk memastikan anotasi dibuat dari teks ayat yang tepat."""

    return hashlib.sha256((ayah_text or "").encode("utf-8")).hexdigest()


class TilawahSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    surah_number = models.IntegerField()
    surah_name = models.CharField(max_length=100)
    ayah_number = models.IntegerField()
    ayah_text = models.TextField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    tajwid_score = models.FloatField(null=True, blank=True)
    word_accuracy = models.FloatField(null=True, blank=True)
    audio_file = models.FileField(
        upload_to="tilawah_audio/",
        null=True,
        blank=True,
    )
    transcript = models.TextField(null=True, blank=True)
    feedback_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.surah_name}:{self.ayah_number}"


class TilawahAyahPool(models.Model):
    surah_number = models.IntegerField()
    surah_name = models.CharField(max_length=100)
    surah_name_id = models.CharField(max_length=100, blank=True, null=True)
    ayah_number = models.IntegerField()
    ayah_text = models.TextField()
    ayah_transliteration = models.TextField(blank=True, null=True)
    ayah_translation = models.TextField(blank=True, null=True)
    juz = models.IntegerField(blank=True, null=True)

    embedding = VectorField(dimensions=1024, null=True, blank=True)
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default="basic",
    )

    # Metadata klasifikasi level. Field `level` lama tetap dipertahankan agar
    # response dan query frontend tidak berubah. Nilainya baru akan diperbarui
    # setelah difficulty engine lolos audit corpus dan dry-run diff.
    level_source = models.CharField(
        max_length=16,
        choices=TilawahLevelSource.choices,
        default=TilawahLevelSource.LEGACY,
    )
    level_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    level_engine_version = models.CharField(
        max_length=32,
        blank=True,
        default="",
        validators=[ENGINE_VERSION_VALIDATOR],
    )
    level_metrics = models.JSONField(default=dict, blank=True)
    level_is_verified = models.BooleanField(default=False)
    level_updated_at = models.DateTimeField(null=True, blank=True)

    audio_url = models.URLField(blank=True, null=True)

    class Meta:
        db_table = "tilawah_ayah_pool"
        ordering = ["surah_number", "ayah_number"]
        unique_together = ("surah_number", "ayah_number")
        constraints = [
            models.CheckConstraint(
                condition=Q(surah_number__gte=1, surah_number__lte=114),
                name="ck_tilawah_ayah_surah_range",
            ),
            models.CheckConstraint(
                condition=Q(ayah_number__gte=1),
                name="ck_tilawah_ayah_number_positive",
            ),
        ]
        indexes = [
            models.Index(
                fields=["level", "surah_number"],
                name="idx_tilawah_level_surah",
            ),
        ]

    def __str__(self):
        return f"{self.surah_name}:{self.ayah_number} ({self.level})"


class TilawahTajwidRule(models.Model):
    """Katalog database untuk rule yang didefinisikan di rule catalog."""

    code = models.CharField(
        max_length=64,
        unique=True,
        validators=[RULE_CODE_VALIDATOR],
    )
    name = models.CharField(max_length=100)
    display_group = models.CharField(
        max_length=32,
        choices=TajwidDisplayGroup.choices,
    )
    description = models.TextField()
    color = models.CharField(
        max_length=10,
        validators=[COLOR_VALIDATOR],
    )
    priority = models.PositiveSmallIntegerField(default=100)
    default_applies_when = models.CharField(
        max_length=16,
        choices=TajwidDefaultAppliesWhen.choices,
    )
    assessment_family = models.CharField(
        max_length=24,
        choices=TajwidAssessmentFamily.choices,
    )
    supported_levels = models.JSONField(default=list)
    expected_features = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tilawah_tajwid_rule"
        ordering = ["priority", "code"]
        indexes = [
            models.Index(
                fields=["display_group", "is_active"],
                name="idx_tajwid_rule_group_active",
            ),
        ]

    def clean(self):
        super().clean()

        supported_levels = self.supported_levels or []
        if not isinstance(supported_levels, list):
            raise ValidationError(
                {"supported_levels": "supported_levels harus berupa list."}
            )

        valid_levels = {value for value, _label in LEVEL_CHOICES}
        invalid_levels = set(supported_levels) - valid_levels
        if invalid_levels:
            raise ValidationError(
                {
                    "supported_levels": (
                        "Level tidak valid: "
                        + ", ".join(sorted(invalid_levels))
                    )
                }
            )

        if not isinstance(self.expected_features or {}, dict):
            raise ValidationError(
                {"expected_features": "expected_features harus berupa object JSON."}
            )

    def __str__(self):
        return f"{self.name} ({self.code})"


class TilawahAyahTajwidAnnotationSet(models.Model):
    """
    Satu hasil generasi anotasi untuk satu ayat dan satu versi engine.

    Hasil baru selalu dibuat sebagai nonaktif. Set PUBLISHED dapat berupa
    candidate beta yang belum diverifikasi ahli; status verifikasi disimpan
    pada annotation.is_verified dan verified_at. Seed baru tidak boleh
    menggantikan set yang sudah disentuh ahli tanpa tindakan manual.
    """

    ayah = models.ForeignKey(
        TilawahAyahPool,
        related_name="tajwid_annotation_sets",
        on_delete=models.CASCADE,
    )
    engine_version = models.CharField(
        max_length=32,
        validators=[ENGINE_VERSION_VALIDATOR],
    )
    reading_mode = models.CharField(
        max_length=8,
        choices=TajwidReadingMode.choices,
        default=TajwidReadingMode.AYAH,
    )
    source_text_hash = models.CharField(
        max_length=64,
        validators=[SHA256_VALIDATOR],
    )
    status = models.CharField(
        max_length=16,
        choices=TajwidAnnotationSetStatus.choices,
        default=TajwidAnnotationSetStatus.GENERATED,
    )
    is_active = models.BooleanField(default=False)
    is_safe_to_persist = models.BooleanField(default=False)
    annotation_count = models.PositiveIntegerField(default=0)
    issues = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True, default="")

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="reviewed_tajwid_annotation_sets",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tilawah_ayah_tajwid_annotation_set"
        ordering = ["ayah_id", "-generated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "ayah",
                    "engine_version",
                    "source_text_hash",
                    "reading_mode",
                ],
                name="uq_tajwid_set_ayah_engine_hash_mode",
            ),
            models.UniqueConstraint(
                fields=["ayah", "reading_mode"],
                condition=Q(is_active=True),
                name="uq_tajwid_set_one_active_per_mode",
            ),
            models.CheckConstraint(
                condition=Q(is_active=False)
                | Q(status=TajwidAnnotationSetStatus.PUBLISHED),
                name="ck_tajwid_set_active_must_published",
            ),
        ]
        indexes = [
            models.Index(
                fields=["ayah", "reading_mode", "is_active"],
                name="idx_taj_set_ayah_mode_act",
            ),
            models.Index(
                fields=["status", "engine_version"],
                name="idx_tajwid_set_status_engine",
            ),
        ]

    def clean(self):
        super().clean()

        if not isinstance(self.issues or [], list):
            raise ValidationError({"issues": "issues harus berupa list JSON."})

        if self.is_active and self.status != TajwidAnnotationSetStatus.PUBLISHED:
            raise ValidationError(
                {"is_active": "Hanya annotation set PUBLISHED yang boleh aktif."}
            )

        if self.status in {
            TajwidAnnotationSetStatus.VALIDATED,
            TajwidAnnotationSetStatus.VERIFIED,
            TajwidAnnotationSetStatus.PUBLISHED,
        } and not self.is_safe_to_persist:
            raise ValidationError(
                {
                    "status": (
                        "Annotation set yang belum aman tidak boleh berstatus "
                        "validated, verified, atau published."
                    )
                }
            )

        error_issues = [
            issue
            for issue in (self.issues or [])
            if isinstance(issue, dict) and issue.get("severity") == "error"
        ]
        if self.status == TajwidAnnotationSetStatus.PUBLISHED and error_issues:
            raise ValidationError(
                {"issues": "Annotation set dengan issue error tidak boleh published."}
            )

    @property
    def has_expert_review(self) -> bool:
        """True bila set pernah direview atau memiliki annotation terverifikasi."""

        if self.verified_at is not None:
            return True
        if not self.pk:
            return False
        return self.annotations.filter(is_verified=True).exists()

    @property
    def verification_state(self) -> str:
        """Ringkasan state untuk admin tanpa menambah field database."""

        if not self.pk:
            return "unverified"
        total = self.annotations.count()
        verified = self.annotations.filter(is_verified=True).count()
        if self.verified_at is not None and verified == total:
            return "verified"
        if self.verified_at is not None or verified > 0:
            return "partial"
        return "unverified"

    @property
    def current_source_text_hash(self) -> str:
        return calculate_ayah_text_hash(self.ayah.ayah_text)

    @property
    def is_stale(self) -> bool:
        return self.source_text_hash != self.current_source_text_hash

    @transaction.atomic
    def publish_and_activate(self, *, reviewed_by=None, notes: str | None = None):
        """Publish set ini dan nonaktifkan set lama untuk ayat/mode yang sama."""

        self.full_clean()

        if not self.is_safe_to_persist:
            raise ValidationError("Annotation set belum aman untuk dipublish.")
        if self.is_stale:
            raise ValidationError(
                "Teks ayat telah berubah sejak anotasi dibuat. Generate ulang dahulu."
            )

        error_issues = [
            issue
            for issue in (self.issues or [])
            if isinstance(issue, dict) and issue.get("severity") == "error"
        ]
        if error_issues:
            raise ValidationError(
                "Annotation set masih memiliki issue berlevel error."
            )

        now = timezone.now()
        type(self).objects.filter(
            ayah=self.ayah,
            reading_mode=self.reading_mode,
            is_active=True,
        ).exclude(pk=self.pk).update(is_active=False)

        self.status = TajwidAnnotationSetStatus.PUBLISHED
        self.is_active = True
        self.published_at = now
        if reviewed_by is not None:
            self.reviewed_by = reviewed_by
        if notes is not None:
            self.notes = notes
        self.save(
            update_fields=[
                "status",
                "is_active",
                "published_at",
                "reviewed_by",
                "notes",
                "updated_at",
            ]
        )
        return self

    def __str__(self):
        return (
            f"{self.ayah} - {self.engine_version} "
            f"[{self.reading_mode}/{self.status}]"
        )


class TilawahAyahTajwidAnnotation(models.Model):
    """Satu hukum tajwid yang terikat ke rentang grapheme teks ayat."""

    annotation_set = models.ForeignKey(
        TilawahAyahTajwidAnnotationSet,
        related_name="annotations",
        on_delete=models.CASCADE,
    )
    rule = models.ForeignKey(
        TilawahTajwidRule,
        related_name="ayah_annotations",
        on_delete=models.PROTECT,
    )

    word_index = models.PositiveIntegerField()
    next_word_index = models.PositiveIntegerField(null=True, blank=True)

    start_grapheme = models.PositiveIntegerField()
    end_grapheme = models.PositiveIntegerField()
    start_codepoint = models.PositiveIntegerField()
    end_codepoint = models.PositiveIntegerField()
    arabic_segment = models.TextField()

    applies_when = models.CharField(
        max_length=18,
        choices=TajwidAppliesWhen.choices,
    )
    expected_features = models.JSONField(default=dict, blank=True)
    locator_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=1,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    locator_method = models.CharField(max_length=64)
    metadata = models.JSONField(default=dict, blank=True)

    is_verified = models.BooleanField(default=False)
    verification_note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tilawah_ayah_tajwid_annotation"
        ordering = [
            "annotation_set_id",
            "start_grapheme",
            "end_grapheme",
            "rule_id",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "annotation_set",
                    "rule",
                    "start_grapheme",
                    "end_grapheme",
                    "applies_when",
                ],
                name="uq_tajwid_annotation_set_rule_span_mode",
            ),
            models.CheckConstraint(
                condition=Q(end_grapheme__gt=F("start_grapheme")),
                name="ck_tajwid_annotation_grapheme_range",
            ),
            models.CheckConstraint(
                condition=Q(end_codepoint__gt=F("start_codepoint")),
                name="ck_tajwid_annotation_codepoint_range",
            ),
            models.CheckConstraint(
                condition=Q(locator_confidence__gte=0)
                & Q(locator_confidence__lte=1),
                name="ck_tajwid_annotation_confidence",
            ),
            models.CheckConstraint(
                condition=Q(next_word_index__isnull=True)
                | Q(next_word_index__gt=F("word_index")),
                name="ck_tajwid_annotation_next_word",
            ),
        ]
        indexes = [
            models.Index(
                fields=["annotation_set", "start_grapheme"],
                name="idx_taj_ann_set_start",
            ),
            models.Index(
                fields=["rule", "is_verified"],
                name="idx_taj_ann_rule_verified",
            ),
        ]

    def clean(self):
        super().clean()

        if not self.arabic_segment:
            raise ValidationError(
                {"arabic_segment": "arabic_segment tidak boleh kosong."}
            )

        if not isinstance(self.expected_features or {}, dict):
            raise ValidationError(
                {"expected_features": "expected_features harus berupa object JSON."}
            )

        if not isinstance(self.metadata or {}, dict):
            raise ValidationError({"metadata": "metadata harus berupa object JSON."})

        # Validasi substring terhadap teks sumber hanya dilakukan ketika semua
        # offset tersedia dan relasi annotation_set telah terpasang.
        if self.annotation_set_id:
            ayah_text = self.annotation_set.ayah.ayah_text
            expected_segment = ayah_text[self.start_codepoint:self.end_codepoint]
            if expected_segment != self.arabic_segment:
                raise ValidationError(
                    {
                        "arabic_segment": (
                            "arabic_segment tidak identik dengan rentang "
                            "start_codepoint:end_codepoint pada teks ayat."
                        )
                    }
                )

    def __str__(self):
        return (
            f"{self.annotation_set.ayah} - {self.rule.code} "
            f"[{self.start_grapheme}:{self.end_grapheme}]"
        )

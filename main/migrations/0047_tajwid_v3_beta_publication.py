from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0046_tilawah_tajwid_schema"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tilawahayahtajwidannotation",
            name="applies_when",
            field=models.CharField(
                choices=[
                    ("wasl", "Wasal"),
                    ("waqf", "Waqaf"),
                    ("both", "Keduanya"),
                    ("contextual", "Kontekstual"),
                    ("profile_dependent", "Bergantung Profil"),
                ],
                max_length=18,
            ),
        ),
    ]

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0039_tuntunanshalatblock_delete_tuntunanshalatimage_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='tuntunanshalatpage',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='tuntunanshalatpage',
            name='tuntunan',
        ),
        migrations.AddField(
            model_name='tuntunanshalat',
            name='content',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tuntunanshalat',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tuntunanshalat',
            name='excerpt',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tuntunanshalat',
            name='hero_image',
            field=models.ImageField(blank=True, null=True, upload_to='tuntunan_shalat/hero_images/'),
        ),
        migrations.AddField(
            model_name='tuntunanshalat',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.DeleteModel(
            name='TuntunanShalatBlock',
        ),
        migrations.DeleteModel(
            name='TuntunanShalatPage',
        ),
    ]
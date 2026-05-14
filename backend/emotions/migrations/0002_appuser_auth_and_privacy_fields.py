from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("emotions", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="appuser",
            name="password_hash",
            field=models.CharField(blank=True, default="", max_length=128, verbose_name="密码哈希"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="appuser",
            name="signature",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="个性签名"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="appuser",
            name="anonymous_mode",
            field=models.BooleanField(default=False, verbose_name="是否匿名模式"),
        ),
        migrations.AddField(
            model_name="appuser",
            name="emotion_encryption_enabled",
            field=models.BooleanField(default=False, verbose_name="情绪加密开关"),
        ),
    ]

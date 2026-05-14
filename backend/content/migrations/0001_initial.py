from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("emotions", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SystemConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=100, unique=True)),
                ("value", models.JSONField(default=dict)),
                ("description", models.TextField(blank=True)),
                ("is_public", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ("key",),
            },
        ),
        migrations.CreateModel(
            name="CompanionContent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "content_type",
                    models.CharField(
                        choices=[
                            ("phrase", "Phrase"),
                            ("advice", "Advice"),
                            ("music", "Music"),
                            ("article", "Article"),
                            ("breathing", "Breathing"),
                            ("template", "Template"),
                        ],
                        max_length=20,
                    ),
                ),
                ("title", models.CharField(max_length=120)),
                ("body", models.TextField(blank=True)),
                ("resource_url", models.URLField(blank=True, max_length=500)),
                ("weight", models.PositiveIntegerField(default=1)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "emotion_tag",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="companion_contents",
                        to="emotions.emotiontag",
                    ),
                ),
            ],
            options={
                "ordering": ("-weight", "id"),
            },
        ),
        migrations.AddIndex(
            model_name="systemconfig",
            index=models.Index(fields=["key", "is_public"], name="content_sys_key_2e8a16_idx"),
        ),
        migrations.AddIndex(
            model_name="companioncontent",
            index=models.Index(fields=["content_type", "is_active"], name="content_com_content_17cafe_idx"),
        ),
        migrations.AddIndex(
            model_name="companioncontent",
            index=models.Index(fields=["is_active", "weight"], name="content_com_is_acti_40b74c_idx"),
        ),
        migrations.AddIndex(
            model_name="companioncontent",
            index=models.Index(fields=["emotion_tag", "is_active"], name="content_com_emotion_a9ce7b_idx"),
        ),
    ]

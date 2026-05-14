from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("emotions", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TreeHolePost",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("anonymous_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("content", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("reject_reason", models.TextField(blank=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "emotion_tag",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="tree_hole_posts",
                        to="emotions.emotiontag",
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_tree_hole_posts",
                        to="emotions.appuser",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tree_hole_posts",
                        to="emotions.appuser",
                    ),
                ),
            ],
            options={
                "db_table": "moderation_tree_hole_post",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="TreeHoleComment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("anonymous_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("content", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "post",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to="moderation.treeholepost",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tree_hole_comments",
                        to="emotions.appuser",
                    ),
                ),
            ],
            options={
                "db_table": "moderation_tree_hole_comment",
                "ordering": ["created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="treeholepost",
            index=models.Index(fields=["status", "-created_at"], name="moderatio_status_6320f8_idx"),
        ),
        migrations.AddIndex(
            model_name="treeholepost",
            index=models.Index(fields=["emotion_tag", "status"], name="moderatio_emotion_4e42fe_idx"),
        ),
    ]

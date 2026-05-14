from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AdminOperationLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("admin_id", models.PositiveBigIntegerField(blank=True, db_index=True, null=True)),
                ("admin_username", models.CharField(blank=True, db_index=True, max_length=150)),
                ("action", models.CharField(db_index=True, max_length=100)),
                ("target_type", models.CharField(blank=True, db_index=True, max_length=100)),
                ("target_id", models.CharField(blank=True, db_index=True, max_length=100)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                "db_table": "analytics_admin_operation_log",
                "ordering": ("-created_at", "-id"),
            },
        ),
        migrations.CreateModel(
            name="FeatureUsageLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("feature", models.CharField(db_index=True, max_length=80)),
                ("user_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("action", models.CharField(db_index=True, max_length=80)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                "db_table": "analytics_feature_usage_log",
                "ordering": ("-created_at", "-id"),
            },
        ),
        migrations.AddIndex(
            model_name="adminoperationlog",
            index=models.Index(fields=["admin_id", "created_at"], name="analytics_aol_admin_time_idx"),
        ),
        migrations.AddIndex(
            model_name="adminoperationlog",
            index=models.Index(fields=["action", "created_at"], name="analytics_aol_action_time_idx"),
        ),
        migrations.AddIndex(
            model_name="adminoperationlog",
            index=models.Index(fields=["target_type", "target_id"], name="analytics_aol_target_idx"),
        ),
        migrations.AddIndex(
            model_name="featureusagelog",
            index=models.Index(fields=["feature", "created_at"], name="analytics_ful_feature_time_idx"),
        ),
        migrations.AddIndex(
            model_name="featureusagelog",
            index=models.Index(fields=["user_id", "created_at"], name="analytics_ful_user_time_idx"),
        ),
        migrations.AddIndex(
            model_name="featureusagelog",
            index=models.Index(fields=["action", "created_at"], name="analytics_ful_action_time_idx"),
        ),
    ]

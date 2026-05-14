from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AdminUser",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username", models.CharField(max_length=150, unique=True)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("password_hash", models.CharField(max_length=128)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("super_admin", "Super Admin"),
                            ("admin", "Admin"),
                            ("operator", "Operator"),
                        ],
                        default="admin",
                        max_length=32,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("disabled", "Disabled"),
                        ],
                        default="active",
                        max_length=32,
                    ),
                ),
                ("last_login_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "admin_users",
                "ordering": ["-created_at"],
            },
        ),
    ]

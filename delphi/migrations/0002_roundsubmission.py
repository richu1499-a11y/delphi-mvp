from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("delphi", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RoundSubmission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("panelist", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="round_submissions", to="delphi.panelist")),
                ("round", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="submissions", to="delphi.round")),
            ],
            options={
                "ordering": ["-submitted_at"],
                "unique_together": {("panelist", "round")},
            },
        ),
    ]

import uuid
from django.db import migrations


def generate_unique_tokens(apps, schema_editor):
    Panelist = apps.get_model('delphi', 'Panelist')
    for panelist in Panelist.objects.all():
        panelist.token = uuid.uuid4()
        panelist.save()


def reverse_tokens(apps, schema_editor):
    pass  # No need to reverse


class Migration(migrations.Migration):

    dependencies = [
        ('delphi', '0003_alter_study_options_and_more'),
    ]

    operations = [
        migrations.RunPython(generate_unique_tokens, reverse_tokens),
    ]
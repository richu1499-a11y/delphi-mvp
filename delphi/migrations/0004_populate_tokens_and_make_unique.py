import uuid
from django.db import migrations, models


def generate_unique_tokens(apps, schema_editor):
    """Generate a unique token for each panelist."""
    Panelist = apps.get_model('delphi', 'Panelist')
    for panelist in Panelist.objects.all():
        panelist.token = uuid.uuid4()
        panelist.save(update_fields=['token'])


def reverse_tokens(apps, schema_editor):
    """Reverse: set all tokens to null."""
    Panelist = apps.get_model('delphi', 'Panelist')
    Panelist.objects.all().update(token=None)


class Migration(migrations.Migration):

    dependencies = [
        ('delphi', '0003_add_panelist_token'),
    ]

    operations = [
        # Step 1: Populate unique tokens for all existing panelists
        migrations.RunPython(generate_unique_tokens, reverse_tokens),
        
        # Step 2: Now that all tokens are unique, add the unique constraint
        migrations.AlterField(
            model_name='panelist',
            name='token',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0004_assignment_comment_notification"),
    ]

    operations = [
        migrations.AddField(
            model_name="pitch",
            name="location",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
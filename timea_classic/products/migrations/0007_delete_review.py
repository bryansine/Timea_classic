# Generated by Django 5.1.3 on 2024-12-12 11:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_rename_content_review_review_text_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Review',
        ),
    ]

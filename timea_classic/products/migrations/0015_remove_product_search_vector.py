# Generated by Django 5.1.3 on 2025-03-20 15:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0014_product_search_vector_product_tags'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='search_vector',
        ),
    ]

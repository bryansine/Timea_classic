# Generated by Django 5.1.3 on 2025-03-11 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0012_remove_product_discount_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='discount_price',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Discounted price, if applicable.', max_digits=10, null=True),
        ),
    ]

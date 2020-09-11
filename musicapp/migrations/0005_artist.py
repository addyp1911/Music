# Generated by Django 3.0.8 on 2020-09-09 02:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('musicapp', '0004_songtrack_external_urls'),
    ]

    operations = [
        migrations.CreateModel(
            name='Artist',
            fields=[
                ('id', models.CharField(editable=False, max_length=100, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=1000, null=True)),
                ('external_urls', models.CharField(blank=True, max_length=100, null=True)),
                ('popularity', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'db_table': 'artists',
            },
        ),
    ]
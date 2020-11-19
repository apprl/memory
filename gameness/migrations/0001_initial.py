# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seed', models.CharField(max_length=100, verbose_name='Seed')),
                ('player', models.EmailField(max_length=254)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('score', models.DecimalField(decimal_places=3, default=0, max_digits=10, verbose_name='Point')),
                ('game_type', models.IntegerField(choices=[(1, 'Memory')], default=1, verbose_name='Game type')),
                ('active', models.BooleanField(default=False, verbose_name='Active')),
                ('finished', models.BooleanField(default=False, verbose_name='Finished')),
                ('playfield', models.TextField(default='{}')),
                ('average_time', models.DecimalField(decimal_places=3, default=0, max_digits=10, verbose_name='Average time for a round')),
            ],
        ),
        migrations.CreateModel(
            name='SuspectedGame',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('player', models.EmailField(max_length=254)),
                ('reason', models.TextField(verbose_name='Reason')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suspects', to='gameness.Game')),
            ],
        ),
        migrations.CreateModel(
            name='Turn',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='')),
                ('meta', models.TextField(default='{}')),
                ('is_match', models.BooleanField(default=False, verbose_name='Match')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='turns', to='gameness.Game')),
            ],
        ),
    ]

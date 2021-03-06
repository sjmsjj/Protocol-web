# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-18 17:38
from __future__ import unicode_literals

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0007_alter_validators_add_error_messages'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProtocolUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=30, unique=True, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.')], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=30, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
        ),
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField(blank=True, null=True)),
                ('note', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ['protocol', 'start_date'],
            },
        ),
        migrations.CreateModel(
            name='Protocol',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('ninstance', models.IntegerField(default=0)),
                ('last_updated', models.DateTimeField(blank=True, null=True)),
                ('is_public', models.BooleanField(default=False)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SharedProtocol',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('protocol', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='protocol.Protocol')),
                ('shared_from', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shared_from', to=settings.AUTH_USER_MODEL)),
                ('shared_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shared_to', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('day', models.IntegerField()),
                ('detail', models.TextField()),
                ('note', models.TextField(blank=True, null=True)),
                ('protocol', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='protocol.Protocol')),
            ],
            options={
                'ordering': ['protocol', 'day'],
            },
        ),
        migrations.AddField(
            model_name='experiment',
            name='protocol',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='experiments', to='protocol.Protocol'),
        ),
        migrations.AddField(
            model_name='experiment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='sharedprotocol',
            unique_together=set([('shared_from', 'shared_to', 'protocol')]),
        ),
        migrations.AlterUniqueTogether(
            name='protocol',
            unique_together=set([('user', 'name')]),
        ),
    ]

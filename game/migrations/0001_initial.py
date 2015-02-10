# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bid',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bid', models.PositiveSmallIntegerField(default=0, choices=[(1, b'Rik'), (2, b'Rik voor 9'), (3, b'Miserie'), (4, b'Rik voor 10'), (5, b'Rik voor 11'), (6, b'Open miserie met kaart'), (7, b'Open voor alles met kaart'), (8, b'Rik voor 12'), (9, b'Rik voor 12'), (10, b'Open miserie'), (11, b'Open voor alles'), (0, b'Pas')])),
                ('trump_suit', models.PositiveSmallIntegerField(blank=True, null=True, choices=[(0, b'w'), (1, b'e'), (2, b'r'), (3, b'q')])),
                ('mate_suit', models.PositiveSmallIntegerField(blank=True, null=True, choices=[(0, b'w'), (1, b'e'), (2, b'r'), (3, b'q')])),
                ('mate_card', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('player', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-bid'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.PositiveSmallIntegerField()),
                ('suit', models.PositiveSmallIntegerField(choices=[(0, b'w'), (1, b'e'), (2, b'r'), (3, b'q')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CardInHand',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('card', models.ForeignKey(to='game.Card')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('deck_initialized', models.BooleanField(default=False)),
                ('round_number', models.PositiveIntegerField(default=0, editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IsInDeck',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ordinal', models.PositiveSmallIntegerField()),
                ('card', models.ForeignKey(to='game.Card')),
                ('game', models.ForeignKey(to='game.Game')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IsPlaying',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('seat', models.PositiveSmallIntegerField()),
                ('accepted', models.BooleanField(default=False)),
                ('abandoned', models.BooleanField(default=False)),
                ('score', models.IntegerField(default=100)),
                ('needs_update', models.BooleanField(default=False)),
                ('cards', models.ManyToManyField(to='game.Card', through='game.CardInHand')),
                ('game', models.ForeignKey(to='game.Game')),
                ('player', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['seat'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlayedInTrick',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ordinal', models.PositiveSmallIntegerField()),
                ('card', models.ForeignKey(to='game.Card')),
                ('played_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Round',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('playing', models.BooleanField(default=False)),
                ('dealer', models.ForeignKey(related_name=b'games_dealing', to=settings.AUTH_USER_MODEL)),
                ('game', models.ForeignKey(related_name=b'rounds', to='game.Game')),
                ('highest_bid', models.ForeignKey(related_name=b'highest_for_round', blank=True, to='game.Bid', null=True)),
                ('mate', models.ForeignKey(related_name=b'mate_in_games', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-id',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Score',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.IntegerField()),
                ('player', models.ForeignKey(related_name=b'scores', to=settings.AUTH_USER_MODEL)),
                ('round', models.ForeignKey(related_name=b'scores', to='game.Round')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Trick',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.PositiveSmallIntegerField(default=0)),
                ('requested_suit', models.PositiveSmallIntegerField(default=None, null=True, blank=True, choices=[(0, b'w'), (1, b'e'), (2, b'r'), (3, b'q')])),
                ('collected', models.BooleanField(default=False)),
                ('cards', models.ManyToManyField(to='game.Card', through='game.PlayedInTrick')),
                ('leading_player', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('round', models.ForeignKey(related_name=b'tricks', to='game.Round')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='playedintrick',
            name='trick',
            field=models.ForeignKey(to='game.Trick'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='game',
            name='current_round',
            field=models.OneToOneField(related_name=b'game_current', null=True, default=None, blank=True, to='game.Round'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='game',
            name='deck',
            field=models.ManyToManyField(to='game.Card', through='game.IsInDeck'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='game',
            name='players',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='game.IsPlaying'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cardinhand',
            name='isplaying',
            field=models.ForeignKey(to='game.IsPlaying'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='card',
            unique_together=set([('number', 'suit')]),
        ),
        migrations.AddField(
            model_name='bid',
            name='round',
            field=models.ForeignKey(related_name=b'bids', to='game.Round'),
            preserve_default=True,
        ),
    ]

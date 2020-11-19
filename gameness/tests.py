# -*- coding: utf-8 -*-
__author__ = 'klaswikblad'

from django.test import TestCase
from django.urls import reverse
from django.conf import settings

from gameness.models import Game, Turn, SuspectedGame

import uuid
import json
import datetime
from model_mommy.mommy import make

class TestCreateGameAndTurns(TestCase):
    def setUp(self):
        start_date = datetime.date.today()
        stop_date = start_date + datetime.timedelta(days=10)

        self.player_email = "test@testsson.com"

    def test_start_game_round(self):
        url = reverse('contest_contest')

        response = self.client.get(url)
        signup = Game.objects.last().player
        self.assertEquals(response.status_code, 200)

        self.assertEquals(Game.objects.filter(player=signup).count(), 1)
        self.assertEquals(Game.objects.player_has_active_games(signup).count(), 1)
        game = Game.objects.active_game(signup)

        seed = 'd155dcffad1e448f8644d0381be70736' #uuid.uuid4().hex
        row = 4
        column = 3
        matrix, seconds = Game.generate_play_field(row, column, seed)

        playfield = [[0, 2, 5],[1, 4, 3],[3, 1, 4],[5, 2, 0]]
        for row in playfield:
            print(row)

        game.playfield = json.dumps(playfield)
        game.save()

        # First click
        url = reverse('contest_game_view',)
        response = self.client.post(url, data={'click': json.dumps({'row': 0, 'column': 0})})
        self.assertEquals(response.status_code, 200)

        # Second click
        response = self.client.post(url, data={'click': json.dumps({'row': 1, 'column': 1})})
        response_json = response.json()
        csrf_token = response_json['csrf_token']
        self.assertDictEqual(response.json(), {'success': True,
                                               'match': False,
                                               'csrf_token': csrf_token,
                                               'click': [{'row': 0, 'column': 0, 'card': 0},
                                                         {'row': 1, 'column': 1, 'card': 4}]}
                             )

        # Set which card should be turned
        play_set = [((0,0), (3,2)),((1,0), (2,1)), ((0,1), (3,1)), ((2,0), (1,2)), ((1,1), (2,2)), ((3,0), (0,2))]
        amount = len(play_set)
        index = 0
        for click1, click2 in play_set:
            response = self.client.post(url, data={'click': json.dumps({'row': click1[0], 'column': click1[1]})})

            self.assertEquals(response.status_code, 200)
            response_json = response.json()
            self.assertEquals(game.get_card_id(response_json['click'][0]), response_json['click'][0]['card'])

            response = self.client.post(url, data={'click': json.dumps({'row': click2[0], 'column': click2[1]})})
            self.assertEquals(response.status_code, 200)
            response_json = response.json()
            self.assertEquals(response_json['match'], True)

            for click in response_json['click']:
                self.assertEquals(game.get_card_id(click), click['card'])

            if amount == index:
                self.assertTrue(response_json['completed'])
            index += 1
        game = Game.objects.get(pk=game.pk)

        self.assertEquals(game.finished, True)
        self.assertEquals(game.active, False)

        self.assertFalse(Game.objects.player_has_active_games(signup))

        self.assertEquals(game.turns.count(), amount+1)
        print(f"The game score: {game.score}")
        self.assertTrue(game.score > 0 and game.score < 2000)

    def test_finish_active_games(self):
        player = "test1@test.com"

        game1 = make(Game, seed = uuid.uuid4().hex, player = player, game_type = Game.MEMORY, active = True, finished = False)
        game2 = make(Game, seed = uuid.uuid4().hex, player = player, game_type = Game.MEMORY, active = True, finished = False)
        game3 = make(Game, seed = uuid.uuid4().hex, player = player, game_type = Game.MEMORY, active = True, finished = False)
        game4 = make(Game, seed = uuid.uuid4().hex, player = player, game_type = Game.MEMORY, active = True, finished = True)
        game5 = make(Game, seed = uuid.uuid4().hex, player = player, game_type = Game.MEMORY, active = False, finished = False)

        active_games_pk = Game.objects.player_has_active_games(player).values_list("id", flat=True)
        self.assertTrue(active_games_pk)
        self.assertTrue( int(active_games_pk[0]) in [game1.pk, game2.pk, game3.pk])
        Game.objects.stop_active_games_for_player(player)
        self.assertFalse(Game.objects.player_has_active_games(player).values_list("id", flat=True))

    def test_has_active_rounds(self):
        game1 = make(Game, seed = uuid.uuid4().hex, player = self.player_email, game_type = Game.MEMORY, active = False, finished = False)
        game2 = make(Game, seed = uuid.uuid4().hex, player = self.player_email, game_type = Game.MEMORY, active = False, finished = False)
        self.assertFalse(Game.objects.player_has_active_games(self.player_email).exists())
        game3 = make(Game, seed = uuid.uuid4().hex, player = self.player_email, game_type = 1, active = True, finished = False)
        self.assertTrue(Game.objects.player_has_active_games(self.player_email).exists())

    def test_generate_play_field(self):
        seed = 'd155dcffad1e448f8644d0381be70736'
        row = 4
        column = 3
        matrix, seconds = Game.generate_play_field(row, column, seed)
        matrix = json.loads(matrix)

        for rows in matrix:
            print(rows)
        self.assertEquals(len(matrix), row )
        self.assertEquals(len(matrix[0]), column)
        self.assertEquals(matrix[1][0], 1)
        self.assertEquals(matrix[2][1], 2)

        """
        [0, 2, 5]
        [1, 4, 3]
        [3, 1, 4]
        [5, 2, 0]
        """

    def test_suspected_game(self):
        player = "test1@test.com"
        game = make(Game, seed=uuid.uuid4().hex, player=player, game_type=Game.MEMORY, active=False,
                     finished=False)

        # Creating two turns with mock data
        for turn in range(2):
            make(Turn, game=game, meta=json.dumps({'click': [{'row': 1, 'column': 1, 'card': 0},
                                                             {'row': 2, 'column': 2, 'card': 0}]}),
                 is_match=True)

        total_time = game.turns.first().created - game.turns.last().created
        game.average_time = (total_time / game.turns.count()).total_seconds()
        self.assertTrue(SuspectedGame.is_game_suspected(game))
        self.assertEquals(game.suspects.filter(player=player).count(), 1)
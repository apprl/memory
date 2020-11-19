# -*- coding: utf-8 -*-
__author__ = 'klaswikblad'

from django.db import models
from django.conf import settings

import time
import json
import logging
from decimal import Decimal

log = logging.getLogger(__name__)


class GameManager(models.Manager):

    def active_game(self, player):
        """
        Get the number of active games a player has
        :param player:
        :return:
        """
        actives = self.filter(active=True, finished=False, player=player )
        if actives.count() > 1:
            log.warning(f"User {player} has more than one active round.")
        return actives.latest("created")

    def get_highscores(self):
        """
        Get a list of all the scores in the contest sorted by highest score first
        :return:
        """
        return self.filter(active=False, finished=True).order_by("-score")

    def get_player_best_score(self, player):
        """
        Get the best score for a specific user
        :param player:
        :return:
        """
        return self.get_highscores().filter(player=player).first()

    def get_unique_highscores(self, num=5):
        """
        Returns a list of scores from unique participants
        :param contest:
        :param num:
        :return:
        """

        scores = self.get_highscores()
        # Purge all suspected games.
        # scores = self.get_highscores().annotate(suspected_games=Count('suspects')).exclude(suspected_games__gt=0)
        winnerlist = []
        emails = []

        # Distinct is not implemented in combination with annotate. so doing a poor mans version.
        for score in scores:
            if not score.player in emails:
                winnerlist.append(score)
                emails.append(score.player)
            if len(winnerlist) == num:
                break
        enough_winners = bool(len(winnerlist) >= num)
        if not enough_winners:
            log.info(u"There are not enough unique contestants to fill the winnerlist")
        return winnerlist, enough_winners

    def player_has_active_games(self, player):
        """
        Checks for whether the player has active games which has not been finished
        :param player:
        :return:
        """
        return self.filter(active=True, finished=False, player=player)

    def stop_active_games_for_player(self, player):
        """
        Filter any active games a player has and set them to inactive
        :param player:
        :return:
        """
        return self.player_has_active_games(player).update(active=False)


class Game(models.Model):
    MEMORY = 1

    seed = models.CharField('Seed', max_length=100) # Random seed for generating the playfield
    player = models.EmailField() # Email address identifying the player
    created = models.DateTimeField('Created', auto_now_add=True)
    score = models.DecimalField("Point", default=0, max_digits=10, decimal_places=3) # The calculated score after the round has been finished
    game_type = models.IntegerField("Game type", choices=((1, "Memory"),), default=MEMORY) # Which game type, as of now only Memory
    active = models.BooleanField("Active", default=False, null=False) # Indicates if the round is active or not
    finished = models.BooleanField("Finished", default=False, null=False) # Indicates if the player finished playing the round
    playfield = models.TextField(default="{}") # Json serialized representation of the board
    average_time = models.DecimalField("Average time for a round", default=0, max_digits=10, decimal_places=3)

    objects = GameManager()

    def total(self):
        return self.game_score()

    def game_score(self):
        """
        Doing formatting of the score
        :return:
        """
        score = self.score.quantize(Decimal('0.001'))
        return score if score > 0 else 0

    def calculate_score(self):
        """
        Method which calculates the score based on the amount of time, clicks and errors made.
        :return:
        """

        correct_award = 150
        turns_total = self.turns.count()
        turns_correct = self.turns.filter(is_match=True).count()
        seconds_left = (60.0 - (self.turns.last().created - self.turns.first().created).total_seconds()) or 0
        maxpoints = turns_correct * correct_award
        deduction_for_errors = correct_award * 0.11123

        maxpoints -= ((turns_total - turns_correct) * 2 * deduction_for_errors)
        maxpoints += seconds_left * 5.123214

        return Decimal(maxpoints)

    def set_finished(self):
        self.finished = True
        self.active = False

    def match(self, move):
        """
        Determine if the two clicks are matching the same card.
        :param move:
        :return:
        """
        click1 = move[0]
        click2 = move[1]

        if click1['row'] == click2['row'] and click1['column'] == click2['column']:
            raise Exception("Corrupt move") # "Move is the same"

        # Fetch the card id from playfield for the two different squares. If the id number in the two squares are the same
        # then we have a matching set of cards.
        id1 = self.get_card_id(click1)
        id2 = self.get_card_id(click2)
        move[0].update({'card': id1})
        move[1].update({'card': id2})
        return move, id1 == id2

    def get_card_id(self, click):
        """
        Get card id from row and column given the present playfield
        :param click: { 'row': 1, 'column': 1 }
        :return: True/ False
        """
        if not "row" in click or not "column" in click:
            log.warning(f"Illegal call to get_card_id with values: {click}")
            return False
        else:
            # Load the playfield matrix
            playfield = json.loads(self.playfield)
            return playfield[click['row']][click['column']]

    @staticmethod
    def generate_play_field(row, column, seed):
        """
        Generates the playfield matrix and store it in the game object as a string
        :param row: y rows
        :param column: x columns
        :param seed: seed to feed into the engine
        :return:
        """
        if hasattr(row, 'startswith'):
            row = int(row)

        if hasattr(column, 'startswith'):
            column = int(column)

        import random
        start_time = time.time()
        log.info("Start to generate playfield")
        matrix = []
        for i in range(row):
            matrix.append([None])
            tmplist = [None for tmp in range(column)]
            matrix[i] = tmplist
        squares = row * column

        pairs = squares // 2
        seed_list = [str(ord(i)) for i in seed]
        seed_int = int(''.join(seed_list))
        random.seed(a=seed_int)

        row1 = row2 = column1 = column2 = None
        for pair in range(pairs):
            still_looking = True
            while still_looking:
                row1 = divmod(random.randint(0, 1000), row)[1]
                column1 = divmod(random.randint(0, 1000), column)[1]

                row2 = divmod(random.randint(0, 1000), row)[1]
                column2 = divmod(random.randint(0, 1000), column)[1]
                if not (row1 == row2 and column1 == column2) and matrix[row1][column1] is None and matrix[row2][
                    column2] is None:
                    still_looking = False
            matrix[row1][column1] = pair
            matrix[row2][column2] = pair
            log.info("Pair {} found!".format(pair))
        stop_time = time.time() - start_time # Check the amount of time it takes
        log.info("Time for creating the playfield: {} s".format(stop_time))
        return json.dumps(matrix), stop_time

    def __unicode__(self):
        return "{}, {}".format(self.get_game_type_display(), self.player)

    class Meta:
        app_label="gameness"


class Turn(models.Model):
    """
    This model represents every two clicks = one round the user has performed.
    """
    created = models.DateTimeField('', auto_now_add=True)
    meta = models.TextField(default="{}") # Used to store json data containing information about each turn, for details check the tests
    game = models.ForeignKey(Game, related_name='turns', on_delete=models.CASCADE)
    is_match = models.BooleanField("Match", default=False) # Whether the turn resulted in a match

    class Meta:
        app_label="gameness"


class SuspectedGame(models.Model):
    """
    Model which categorizes a game as potentially suspected
    """

    game = models.ForeignKey(Game, blank=False, null=False, related_name='suspects',
                             on_delete=models.PROTECT) # Game which has been played in a suspected manner
    player = models.EmailField() # Player which has the suspected game
    reason = models.TextField("Reason") # Message for debug
    created = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def is_game_suspected(game):
        if game.average_time < settings.SUSPECTED_THRESHOLD:
            msg = f"The round {game.id} by {game.player} may be cheating. Average time for a round is {game.average_time}."
            SuspectedGame.objects.create(game=game, player=game.player, reason=msg)
            return True
        return False

    class Meta:
        app_label="gameness"
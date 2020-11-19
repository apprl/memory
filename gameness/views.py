# -*- coding: utf-8 -*-
import json
import logging
import uuid

from decimal import Decimal
from random import choice

from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.utils.encoding import smart_text
from django.views import View
from django.views.generic.base import ContextMixin, TemplateView

from gameness.models import Game

log = logging.getLogger(__name__)


def aquire_csrf(request):
    from django.template.context_processors import csrf
    return csrf(request)


class ContestGameView(View, ContextMixin):
    """
    Non visible view, gathers data during the time the games are played.
    """

    def post(self, request, *args, **kwargs):
        """
        Receive every click with coordinates and evaluate which card id should be shown and if the click pair has generated
        a match. Will add those parameters in the json returned to the frontend. One "round" consists of two clicks which
        are sent to this method for evaluation. The first click will be saved in the session and once we have two clicks a
        match will be attempted.

        Wants every move as a list of dicts which request.POST["click"] = {'click': {'row': y, 'column': x}}

        When it thinks the game is finished it sends the {'completed': True, 'score': <score>} parameters.

        :param request: Will contain "click" in the POST request.POST["click"]) object and will be storing variables in the session
        :param args:
        :param kwargs:
        :return: If the game is not completed it should return {'success': True/ False, 'click': {'row': 1, 'column': 1, card: <id>}, {'row': 2, 'column': 2, card: <id>}, 'match': True/ False})
                 If the game is completed, then return {'success': True, 'completed': True, 'score': <score>}
        """

        if not "game" in request.session:
            log.warning("Game id not found in session, severe error.")
            return JsonResponse({'success': False}, status=500)

        context = {"success": True}
        context.update(aquire_csrf(self.request))
        player = request.session["player"]
        game_id = request.session['game']

        # Basic instructions
        # Extract the click being reported
        # Check which card is at the position the click targeted (check
        # All full Turns (two clicks) should be serialized in the database as json
        # Check if there is a match if second click and save it

        try:
            game = Game.objects.get(pk=game_id, player=player, active=True, finished=False)
        except Game.DoesNotExist:
            context = {"success": False, "msg": "No active game session found."}

            log.info(
                f"User: {player} There is no active game associated with this session or the game in the session does not exists {game_id}.")
            return JsonResponse(context, status=404)

        # Part 1: Insert code here



        # Part 2: Check if the game has been finished and ifso,
            # Calculate a score save it to Game.score, see class methods
            # Fill in any relevant variables in the Game class
            # Finish the game off with cleaning up variables and call Game.set_finished()
            # Check whether the game was considered Suspected with the SuspectedGame class
            # if the Game is finished, return according to method documentation above

        if self.game_completed(game):
            request.session.pop("game")
            # Insert code here

        # Don't forget to update the csrf token
        if "csrf_token" in context.keys():
            context.update({"csrf_token": smart_text(context["csrf_token"])})

        return JsonResponse(context)

    def game_completed(self, game):
        """
        Method which checks if there are enough matched rounds to finish the game
        :param game: Game object
        :return: True/False whether the game is finished or not
        """
        return None

class ContestView(TemplateView):
    """
    Loads the page with the game on it. Doing basic initialization of the game.
    """
    template_name = "contest.html"

    def get_context_data(self, **kwargs):
        context = super(ContestView, self).get_context_data(**kwargs)
        player = choice(settings.USER_EMAILS)
        context["player"] = self.request.session["player"] = player
        self.request.session["game_id"] = uuid.uuid4().hex
        context.update(aquire_csrf(self.request))

        Game.objects.stop_active_games_for_player(player)

        if "game" in self.request.session:
            game_id = self.request.session.pop("game", None)
            log.warning(f"Found existing game in session, removing: {game_id}")

        if "click" in self.request.session:
            click = self.request.session.pop("click", None)
            log.warning(f"Found existing click in session, removing: {click}")

        seed = uuid.uuid4().hex
        dimensions = list(map(int, "2x3".split("x")))
        game = Game.objects.create(player=player, active=True, finished=False, game_type=Game.MEMORY, seed=seed,
                                   playfield=Game.generate_play_field(dimensions[0], dimensions[1], seed)[0])
        self.request.session["game"] = game.pk
        context.update(self.get_game_context(dimensions))

        return context

    def get_game_context(self, dimensions):
        context = {}
        game_name = "Memory"
        high_score_game = Game.objects.filter(player=self.request.session["player"], score__gt=0.0).order_by(
            "score").first()
        game_data = {
            "success": True,
            "name": "Memory",
            "best_score": high_score_game.score if high_score_game else Decimal("0.0"),
            "rows": dimensions[0],
            "cols": dimensions[1],
            "pieces": [static(f"img/memory/stack/{i}.jpg") for i in range(1, 11)],
            "backPiece": static("img/memory/card-backside-default.png"),
            "font_url": static("games/fonts/press-start-2p.css"),
            "font_family": "Press Start 2P",
            "audio_win": static("games/sfx/memory-win.wav"),
            "audio_hit": static("games/sfx/memory-hit.wav"),
            "audio_miss": static("games/sfx/memory-miss.wav")
        }
        context["game_data"] = json.dumps(game_data, cls=DjangoJSONEncoder)
        context["game_name"] = game_name
        return context


class ContestHighscoreView(TemplateView):
    """
    Contest Highscoreview shows a page with the players highscore and a complete highscore list.
    """

    template_name = "highscore.html"

    def get_context_data(self, **kwargs):
        context = super(ContestHighscoreView, self).get_context_data(**kwargs)
        context["player"] = self.request.session["player"]
        context["best_score"] = Game.objects.get_player_best_score(context["player"])
        context["highscores"] = Game.objects.get_highscores()[:5]
        context["unique_highscores"], _ = Game.objects.get_unique_highscores()[:5]
        return context

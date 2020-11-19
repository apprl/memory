"""gameness URL Configuration"""

from django.contrib import admin
from django.urls import include, path

from gameness.views import ContestView, ContestGameView, ContestHighscoreView

urlpatterns = [
    path(r'', ContestView.as_view(), name='contest_contest'),
    path('contests/api/', ContestGameView.as_view(), name='contest_game_view'),
    path('contests/highscore/', ContestHighscoreView.as_view(), name='contest_highscore'),
    path('admin/', admin.site.urls),
]

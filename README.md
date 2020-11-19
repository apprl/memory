# memory

Memory game is completed when all the pairs has been found. 

When starting up the javascript will generate the playfield in the form of a matrix which dimensions are generated on the server side. Every time the player is clicking on a card a request with the details of which card was being clicked is sent to the backend and the backend keeps track of the turns, saving the clicks in pairs of two in the Turn model.

When all the pairs has been completed a score is calculated and the player is sent to a highscore screen where given the option to play again is available. 

The game can be tested here http://memory.apparelrow.com/

#### Instructions
Clone the repo and setup the django project. It is designed to run on Django 2.2.17 and Python 3.9.
Run the tests (which will fail).

The views.py file will contain the view essential for the game. 

The instructions are:
 - Make the game work again by implementing the ContestGameView.post method.
 - After each game the player is sent to the highscore view. Right now it is listing the 10 best scores regardless if the scores comes from the same player. Make it so only unique players are represented
 - Add a SuspectedGame entry connected to the Game if the average time for playing a round is lower than 1.5 seconds.
 - In the highscore list, implement it so that all players who has *_more than one_* SuspectedGame record are disqualified. 
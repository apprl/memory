var GAME_SCALE = 0.9;
var GAME_WIDTH = 800 * GAME_SCALE;
var GAME_HEIGHT = 600 * GAME_SCALE;
var game;
var startTime = 0;
var turns = 0;
var done = false;

function getUrl (page) {
    return ["", "contests", page, ""].join("/")
}

function preload () {
    game.load.crossOrigin = 'anonymous';
    game.load.image('back', gameData.backPiece);

    gameData.pieces.forEach(function (piece) {
        game.load.image(piece, piece);
    });

    game.load.audio('win', gameData.audio_win);
    game.load.audio('match', gameData.audio_hit);
    game.load.audio('miss', gameData.audio_miss);
}

var pieces = [];
var selectedPiece;
var throttled = false;

function onClick (piece) {
    // Is this the first click? If so, set startTime
    if (!startTime) {
        startTime = Date.now();
    }

    // Ignore click if already showing front of piece, or if clicks are throttled
    if (piece.showFront || throttled) {
        return;
    }

    $.post(
        getUrl("api"),
        {
            csrfmiddlewaretoken: gameData.csrfToken,
            click: JSON.stringify({
                row: piece.row,
                column: piece.col
            })
        },
        function (response) {
            var click = response.click.pop();

            var cardIndex = click.card;
            piece.show(gameData.pieces[cardIndex]);

            // Is first click?
            if (!selectedPiece) {
                selectedPiece = piece;
                return;
            }

            // Increase number of turns
            turns++;

            // Game completed?
            if (response.completed) {
                onComplete();
            } else if (!response.match) { // Not a matching piece?
                throttled = true;

                game.sound.play('miss');

                // Wait a while before hiding pieces
                setTimeout(function () {
                    piece.hide();
                    selectedPiece.hide();
                    selectedPiece = null;
                    throttled = false;
                }, 1000);
            } else { // Match!
                selectedPiece = null;

                game.sound.play('match');
            }
        }
    )
}

function onComplete () {
    done = true;

    game.sound.play('win');

    var lastTween;
    for (var i = 0; i < pieces.length; i++) {
        lastTween = game.add.tween(pieces[i]).to({alpha: 0.2}, 500, Phaser.Easing.Linear.None, true, 0, 0, false);
    }

    var bar = game.add.graphics();
    bar.beginFill(0x000000, 0.7);
    bar.drawRect(0, GAME_HEIGHT / 2 - 50, GAME_WIDTH, 100);
    bar.alpha = 0;

    var style = {
        font: "bold 32px Press Start 2P",
        fill: "#fff",
        boundsAlignH: "center",
        boundsAlignV: "middle"
    };

    text = game.add.text(0, 0, splash_text, style);
    text.setTextBounds(0, GAME_HEIGHT / 2 - 50, GAME_WIDTH, 100);
    text.alpha = 0;

    game.add.tween(bar).to({alpha: 1}, 500, Phaser.Easing.Linear.None, true, 0, 0, false);
    game.add.tween(text).to({alpha: 1}, 500, Phaser.Easing.Linear.None, true, 0, 0, false);

    // Wait a little and then redirect to highscore page
    setTimeout(function () {
        document.location.href = getUrl("highscore");
    }, 5000);
}

function create () {
    var piecePadding = 10 * GAME_SCALE;

    var numRows = gameData.rows;
    var numCols = gameData.cols;

    var topPadding = 70 * GAME_SCALE;
    var bottomPadding = 20 * GAME_SCALE;
    var maybeRowSize = (GAME_HEIGHT - topPadding - bottomPadding - (numRows - 1) * piecePadding) / numRows;

    var sidePadding = 30 * GAME_SCALE;
    var maybeColSize = (GAME_WIDTH - sidePadding * 3 - (numCols - 1) * piecePadding) / numCols;

    // Choose the smallest potential size to make sure the cards fit
    var pieceSize = Math.min(maybeRowSize, maybeColSize);
    // Calculate the card scale for the images to fit the cards
    var pieceScale = pieceSize / 160;
    // Based on the card size, calculate edge paddings
    var realSidePadding = (GAME_WIDTH - (pieceSize + piecePadding) * numCols) / 2;
    var realTopPadding = 50 + (GAME_HEIGHT - 50 - (pieceSize + piecePadding) * numRows) / 2;

    game.stage.backgroundColor = '#182d3b';

    for (var row = 0; row < numRows; row++) {
        for (var col = 0; col < numCols; col++) {
            var x = pieceSize * col + col * piecePadding + realSidePadding;
            var y = pieceSize * row + row * piecePadding + realTopPadding;

            pieces.push(new Piece(game, row, col, x, y, onClick, pieceScale));
        }
    }

    game.scale.compatibility.scrollTo = false;
    game.scale.scaleMode = Phaser.ScaleManager.aspectRatio;
    game.scale.setShowAll();
    game.scale.refresh();
}

/* Piece object */
function Piece (game, row, col, x, y, clickHandler, scale) {
    Phaser.Sprite.call(this, game, x, y, 'back');

    this.scale.setTo(scale, scale);

    this.row = row;
    this.col = col;

    this.clickHandler = clickHandler;
    this.showFront = false;

    this.inputEnabled = true;
    this.input.useHandCursor = true;

    this.events.onInputDown.add(this.click, this);

    game.add.existing(this);
}

Piece.prototype = Object.create(Phaser.Sprite.prototype);
Piece.prototype.constructor = Piece;

Piece.prototype.show = function (sprite) {
    this.showFront = true;
    this.loadTexture(sprite, 0);
};

Piece.prototype.hide = function () {
    this.showFront = false;
    this.loadTexture('back', 0);
};

Piece.prototype.click = function () {
    this.clickHandler(this);
};

var fontStyle = {
    font: "22px " + gameData.font_family,
    fill: "#fff"
};

function lazyPadder (num) {
    if (num < 10) {
        return "0" + num;
    } else {
        return num;
    }
}

var time = "00:00:00";
var textElements = [];

function render () {
    textElements.forEach(function (textElement) {
        textElement.destroy();
    });


    if (startTime && !done) {
        // Time diff in seconds
        var timeDiffHundreds = Math.floor((Date.now() - startTime) / 10);
        var hundreds = timeDiffHundreds % 100;
        var timeDiff = Math.floor(timeDiffHundreds / 100);
        var seconds = timeDiff % 60;
        var minutes = (timeDiff - seconds) / 60;

        time = "" + lazyPadder(minutes) + ":" + lazyPadder(seconds) + ":" + lazyPadder(hundreds);
    }

    // Add texts
    textElements = [
        game.add.text(20 * GAME_SCALE, 20 * GAME_SCALE, gameData.name, fontStyle),
        game.add.text(260 * GAME_SCALE, 20 * GAME_SCALE, time_text, fontStyle),
        game.add.text(360 * GAME_SCALE, 20 * GAME_SCALE, time, fontStyle),
        game.add.text(610 * GAME_SCALE, 20 * GAME_SCALE, round_text, fontStyle),
        game.add.text(730 * GAME_SCALE, 20 * GAME_SCALE, lazyPadder(turns), fontStyle)
    ];

    game.scale.setShowAll();
    game.scale.refresh();
}

WebFont.load({
    custom: {
        families: [gameData.font_family],
        urls: [gameData.font_url]
    },
    active: function () {
        // Start game when font has loaded
        game = new Phaser.Game(GAME_WIDTH, GAME_HEIGHT, Phaser.AUTO, 'game', {
            preload: preload,
            create: create,
            render: render
        });
    }
});

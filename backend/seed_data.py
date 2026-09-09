"""
Capstone Backend — Game Bank Seeder
===================================================
Seeds 22 top popular and classic board games into Tabletop Sage:
- Writes comprehensive, sectioned rulebook documents to docs/
- Creates or updates BoardGame records in SQLite with rich discovery metadata
- Vector indexes all rulebook chunks into ChromaDB for RAG retrieval

Run:
    python seed_data.py
"""

import os
from pathlib import Path

try:
    import models
    from auth import hash_password
    from database import Base, SessionLocal, engine
    from rag_pipeline import ingest_rulebook
except ImportError:
    from . import models
    from .auth import hash_password
    from .database import Base, SessionLocal, engine
    from .rag_pipeline import ingest_rulebook

BASE_DIR = Path(__file__).resolve().parent
DOCS_STORAGE_PATH = Path(os.getenv("DOCS_STORAGE_PATH", str(BASE_DIR / "docs")))
DOCS_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

GAMES_DATA = [
    # ── CLASSIC & FAMILY GAMES ────────────────────────────────────────────────
    {
        "name": "Chess",
        "description": "The ultimate two-player abstract strategy game of tactics, positional play, and checkmating the opponent's king.",
        "min_players": 2,
        "max_players": 2,
        "min_age": 6,
        "estimated_playtime": 30,
        "complexity": "Medium",
        "category": "Abstract Strategy",
        "publisher": "Public Domain",
        "year_published": 600,
        "filename": "chess_rules.txt",
        "rulebook": """# Chess Official Rules & Guide

## Game Overview & Objective
Chess is a two-player strategy board game played on an 8x8 checkered board of 64 squares. The ultimate objective is to checkmate the opponent's king, placing it under an unavoidable threat of capture on the following turn.

## Board Setup & Piece Placement
1. The board is positioned so that each player has a light-colored square on their bottom-right corner ("white on right").
2. White pieces occupy ranks 1 and 2; Black pieces occupy ranks 7 and 8.
3. Back Rank Setup (from left to right for White): Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook.
4. "Queen on her color": White Queen on White square (d1), Black Queen on Black square (d8).
5. Front Rank: 8 Pawns fill the entire second rank directly in front of the major and minor pieces.

## Piece Movements & Rules
- **King**: Moves exactly 1 square in any direction (horizontally, vertically, or diagonally). Cannot move into a square attacked by enemy pieces.
- **Queen**: The most powerful piece. Moves any number of unoccupied squares in any direction (horizontal, vertical, or diagonal).
- **Rook**: Moves any number of unoccupied squares horizontally or vertically.
- **Bishop**: Moves any number of unoccupied squares diagonally. Remains on squares of its starting color throughout the game.
- **Knight**: Moves in an 'L' shape (2 squares in one cardinal direction, then 1 square perpendicular). The only piece that can jump over other pieces.
- **Pawn**: Moves forward 1 square (or optionally 2 squares on its very first move). Captures diagonally forward 1 square. Never moves backward.

## Special Rules
### Castling
A defensive maneuver involving the King and one Rook on the same rank. The King moves 2 squares toward the Rook, and that Rook hops over the King to the adjacent square.
**Requirements**:
1. Neither the King nor the chosen Rook has moved prior in the game.
2. All squares between the King and Rook are completely empty.
3. The King is not currently in check, does not pass through check, and does not land in check.

### En Passant
When a pawn advances 2 squares from its starting position and lands adjacent to an enemy pawn on the same rank, the enemy pawn may capture it diagonally forward as if it had only advanced 1 square. Must be claimed immediately on the very next turn.

### Pawn Promotion
When a pawn reaches the opposite end of the board (rank 8 for White, rank 1 for Black), it is immediately replaced by a Queen, Rook, Bishop, or Knight of the player's choice.

## Check, Checkmate, and Draws
- **Check**: The King is under direct attack by an enemy piece. The defending player must immediately escape check by moving the king, capturing the attacking piece, or blocking the attack.
- **Checkmate**: The King is in check and has no legal move to escape. The player delivering checkmate wins immediately.
- **Stalemate (Draw)**: The player whose turn it is has no legal moves and their King is NOT in check.
- **Other Draws**: Insufficient material (e.g. King vs King, King & Bishop vs King), Threefold repetition of position, or 50-move rule without captures or pawn moves.
""",
    },
    {
        "name": "Backgammon",
        "description": "One of the oldest known two-player board games combining strategy and probability as players race their checkers around the board.",
        "min_players": 2,
        "max_players": 2,
        "min_age": 8,
        "estimated_playtime": 30,
        "complexity": "Light / Casual",
        "category": "Abstract Strategy",
        "publisher": "Public Domain",
        "year_published": 1920,
        "filename": "backgammon_rules.txt",
        "rulebook": """# Backgammon Official Rules & Reference

## Game Overview & Objective
Backgammon is a two-player game played on a board with 24 narrow triangles called points. Each player commands 15 checkers. The objective is to move all of your checkers into your home board and then bear them off. The first player to bear off all 15 checkers wins.

## Board Setup & Starting Positions
The 24 points are numbered 1 to 24 from each player's perspective. Checkers are arranged as follows:
- 2 checkers on Point 24
- 5 checkers on Point 13
- 3 checkers on Point 8
- 5 checkers on Point 6
Players move checkers in opposing directions: Player 1 moves counter-clockwise from point 24 toward point 1 (their home board), while Player 2 moves clockwise from point 1 toward point 24.

## Turn Sequence & Movement
1. **Roll Dice**: Both players roll one die to determine who goes first. On normal turns, the active player rolls both dice.
2. **Move Checkers**: The numbers on the two dice constitute separate moves. For example, rolling 3 and 5 allows moving one checker 3 points and another 5 points, or a single checker 8 points total (if intermediate points are open).
3. **Doubles**: If a player rolls doubles (e.g. 4-4), they play the rolled number four times (e.g. four moves of 4).
4. **Open Points**: A checker may only land on an open point—a point with no opposing checkers, or with only 1 opposing checker (a blot). A point with 2 or more opposing checkers is "made" (blocked).

## Hitting and Entering
- **Blot**: A lone checker on a point.
- **Hitting**: When a checker lands on an opponent's blot, the opponent's checker is hit and placed onto the central Bar.
- **Entering from the Bar**: Any checker on the Bar must re-enter the opponent's home board (points 19–24) before any other checkers can be moved. If the corresponding entry point is blocked, the turn is forfeited.

## Bearing Off
Once all 15 of a player's checkers are safely inside their Home Board (points 1 to 6), they may begin "bearing off"—removing checkers from the board by rolling numbers corresponding to the points where checkers reside.

## Scoring & Victory
- **Single Win**: The winner bears off all 15 checkers before the loser bears off theirs (1 point).
- **Gammon**: If the loser has not borne off a single checker, the winner earns 2 points (double win).
- **Backgammon**: If the loser has not borne off a checker and still has a checker on the bar or in the winner's home board, the winner earns 3 points (triple win).
""",
    },
    {
        "name": "Monopoly",
        "description": "The iconic fast-dealing property trading board game of buying, renting, and building real estate monopolies to bankrupt your rivals.",
        "min_players": 2,
        "max_players": 8,
        "min_age": 8,
        "estimated_playtime": 90,
        "complexity": "Light / Casual",
        "category": "Family",
        "publisher": "Hasbro",
        "year_published": 1935,
        "filename": "monopoly_rules.txt",
        "rulebook": """# Monopoly Official Rulebook

## Objective of the Game
The objective of Monopoly is to become the wealthiest player through buying, renting, and trading properties, ultimately forcing all opponents into bankruptcy.

## Game Setup
1. Place the board on a flat table. Stack Chance and Community Chest cards on their designated board spaces.
2. Each player chooses a token and receives starting cash of $1,500:
   - 2 x $500, 2 x $100, 2 x $50, 6 x $20, 5 x $10, 5 x $5, 5 x $1.
3. One player is chosen as the Banker to manage deeds, houses, hotels, and bank funds.

## Playing Your Turn
1. Roll both six-sided dice. Move your token clockwise around the board that number of spaces.
2. Take action based on the space landed upon (Buy unowned property, pay rent, draw Chance/Community Chest, pay taxes, or Go to Jail).
3. **Rolling Doubles**: If you roll doubles, you take another turn immediately. If you roll doubles three times in succession, you must Go to Jail immediately without completing your third turn.

## Board Spaces & Actions
- **Unowned Property**: If you land on an unowned street, railroad, or utility, you may buy it from the Bank at the listed board price. If you decline to buy it, the Banker must immediately auction it to the highest bidder starting at $10.
- **Owned Property**: You must pay rent to the owner as indicated on the Title Deed. If the owner owns all properties in that color group (monopoly), unimproved rent is doubled.
- **Passing GO**: Collect $200 from the Bank each time you pass or land directly on GO.
- **Income Tax / Luxury Tax**: Pay the designated fee directly to the Bank.
- **Free Parking**: An official rest space. No money is awarded from Free Parking according to official rules (the common house rule of placing tax/fines in the middle is not part of standard rules).

## Building Houses and Hotels
- Once you own all properties of a color group, you may purchase houses from the Bank at the price printed on the deed.
- You must build evenly across the color group (you cannot build a second house on one property until all properties in that group have at least one house).
- 4 Houses on a property can be upgraded to 1 Hotel by paying the hotel price and returning the 4 houses to the Bank.

## Jail Rules
You go to Jail if:
1. You land on the "Go to Jail" space.
2. You draw a "Go Directly to Jail" card.
3. You roll doubles 3 times in one turn.

**To Get Out of Jail**:
1. Roll doubles on any of your next 3 turns.
2. Pay a $50 fine before rolling on either of your next 2 turns.
3. Use a "Get Out of Jail Free" card.
*While in Jail, you can still collect rent, trade properties, and build houses.*

## Bankruptcy & Winning
- If you owe more money or rent than you can raise through mortgaging properties and selling buildings, you must declare bankruptcy.
- If you owe another player, all your remaining assets and deeds transfer to that player.
- The last remaining player with money and property wins the game!
""",
    },
    {
        "name": "Uno",
        "description": "The world's most beloved colorful card-shedding party game of matching numbers, tactical action cards, and shouting 'UNO!'.",
        "min_players": 2,
        "max_players": 10,
        "min_age": 7,
        "estimated_playtime": 20,
        "complexity": "Light / Casual",
        "category": "Card Game",
        "publisher": "Mattel",
        "year_published": 1971,
        "filename": "uno_rules.txt",
        "rulebook": """# UNO Official Rules & Card Guide

## Game Overview & Objective
UNO is a fast-paced shedding card game for 2 to 10 players. The objective is to be the first player to discard all cards in your hand by matching color, number, or symbol with the top card of the Discard Pile.

## Setup & Dealing
1. Shuffle the 108-card deck. Each player is dealt 7 cards face down.
2. Place the remaining cards face down to form the Draw Pile.
3. Flip the top card of the Draw Pile face up to start the Discard Pile.
4. The player to the dealer's left goes first; play proceeds clockwise.

## Gameplay & Matching
On your turn, match the top card of the Discard Pile by:
- **Color**: Play a card of the same color (Red, Blue, Green, Yellow).
- **Number**: Play a card with the same digit (0 through 9).
- **Symbol / Action**: Play a matching action card (Skip, Reverse, Draw 2).
- **Wild Card**: Play a Wild or Wild Draw 4 card on any turn.

If you have no playable card, you must draw 1 card from the Draw Pile. If the drawn card is playable, you may play it immediately; otherwise, your turn ends.

## Action Cards
- **Draw Two (+2)**: Next player must draw 2 cards and forfeits their turn.
- **Reverse**: Reverses the direction of play (clockwise becomes counter-clockwise and vice versa). In 2-player games, Reverse acts like a Skip.
- **Skip**: The next player is skipped and loses their turn.
- **Wild**: Allows the active player to choose the active color for subsequent play.
- **Wild Draw Four (+4)**: The active player chooses the new color, and the next player must draw 4 cards and forfeit their turn. *Rule: Can only be legally played if you do NOT have a card matching the current color.*

## Common Rules Disputes & Official Clarifications
1. **Stacking Draw Cards**: Under official Mattel UNO rules, Draw Two (+2) and Wild Draw Four (+4) cards **CANNOT be stacked**. You cannot play a +2 on top of a +2 to pass the penalty to the next player.
2. **Calling "UNO!"**: When you play your second-to-last card and hold exactly 1 card remaining, you must shout "UNO!" before the next player takes their turn. If caught by an opponent before the next turn starts, you must draw 2 penalty cards.
3. **Playing on a Draw 4**: A player forced to draw cards by a +2 or +4 cannot play a card on that same turn.

## Winning & Scoring
The first player to get rid of all their cards wins the round. The winner scores points for cards remaining in opponents' hands:
- Number cards (0–9): Face value (0 to 9 points)
- Draw Two, Reverse, Skip: 20 points each
- Wild, Wild Draw Four: 50 points each
First player to reach 500 points wins the overall game.
""",
    },
    {
        "name": "Scrabble",
        "description": "The classic crossword word game where letter tiles are arranged on a grid to score high points with premium bonus squares.",
        "min_players": 2,
        "max_players": 4,
        "min_age": 8,
        "estimated_playtime": 60,
        "complexity": "Medium",
        "category": "Family",
        "publisher": "Hasbro",
        "year_published": 1938,
        "filename": "scrabble_rules.txt",
        "rulebook": """# Scrabble Official Rules & Scoring Guide

## Game Overview & Objective
Scrabble is a word game for 2 to 4 players played on a 15x15 grid. Players construct interconnected words crossword-style using letter tiles with varying point values. The player with the highest cumulative score at the end wins.

## Setup
1. Place the board on the table. Place all 100 letter tiles into the cloth tile bag.
2. Each player draws 1 tile; closest to 'A' goes first (Blank beats 'A'). Return drawn tiles to the bag.
3. Each player draws 7 tiles from the bag and places them on their rack, hidden from opponents.

## Turn Actions
On your turn, choose ONE of three actions:
1. **Play a Word**: Place 1 or more tiles on the board in a single horizontal or vertical line to form complete, valid words.
2. **Exchange Tiles**: Discard any number of tiles face down, draw equal replacements from the bag, and return discarded tiles to the bag (ends your turn).
3. **Pass**: Pass your turn without scoring.

## Placement Rules
- **First Word**: Must be at least 2 letters long and must cover the center star square (which acts as a Double Word Score).
- **Subsequent Words**: Must connect to existing board words either by extending a word, forming a right-angle word, or creating parallel adjacent words.
- All newly created words on the turn must be valid in the chosen dictionary.

## Scoring & Premium Squares
- Letter values range from 1 (common vowels like E, A) to 10 (Q, Z). Blanks score 0 points.
- **Premium Letter Squares**: Light Blue = Double Letter Score (DLS); Dark Blue = Triple Letter Score (TLS). Multiplies only the letter on that square.
- **Premium Word Squares**: Pink = Double Word Score (DWS); Red = Triple Word Score (TWS). Multiplies the entire word score.
- **Bingo (50-Point Bonus)**: If a player uses all 7 tiles from their rack in a single turn, they earn 50 bonus points added after calculating word multipliers.

## Challenges
If an opponent questions a newly played word, they may challenge it before the next player takes a turn:
- If any played word is invalid, the active player removes their tiles, scores 0, and loses their turn.
- If all challenged words are valid, the play stands and the challenger loses their next turn (under tournament rules).

## Ending the Game
The game ends when all tiles have been drawn from the bag and one player uses all tiles on their rack, or when all players pass twice consecutively. Remaining tile values on racks are subtracted from each player's total.
""",
    },
    {
        "name": "Clue (Cluedo)",
        "description": "The classic murder mystery board game of deduction, secret passages, and determining who did it, where, and with what weapon.",
        "min_players": 2,
        "max_players": 6,
        "min_age": 8,
        "estimated_playtime": 45,
        "complexity": "Light / Casual",
        "category": "Family",
        "publisher": "Hasbro",
        "year_published": 1949,
        "filename": "clue_rules.txt",
        "rulebook": """# Clue (Cluedo) Official Rules & Guide

## Objective
Mr. Boddy (Dr. Black) has been murdered in Tudor Mansion. Players must deduce the three confidential details hidden in the Case File envelope:
1. **The Murderer** (Which suspect?)
2. **The Weapon** (Which weapon?)
3. **The Crime Scene** (Which room?)

## Setup
1. Separate cards into 3 decks: Suspects (6), Weapons (6), and Rooms (9).
2. Without looking, place 1 Suspect, 1 Weapon, and 1 Room card into the "Case File Confidential" envelope and place it in the center of the board.
3. Shuffle all remaining cards together and deal them out evenly to all players.
4. Each player marks their private Detective Notebook with the cards dealt to them (these cannot be in the envelope).
5. Place suspect tokens and miniature weapons in their starting locations. Miss Scarlett always goes first.

## Moving Across the Mansion
On your turn, roll the dice and move your token through hallways toward rooms, or use a **Secret Passage** (e.g. Kitchen <-> Study, Conservatory <-> Lounge) without rolling.

## Making a Suggestion
When your token enters a room, you may make a suggestion involving that room:
- *Example: "I suggest the crime was committed by Colonel Mustard in the Lounge with the Candlestick."*
- Bring the suspect token and weapon miniature into that room.
- The player to your left checks their hand: if they hold one of the three suggested cards, they must secretly show ONE card to you. If they have none, the next player to the left must try to disprove the suggestion.
- Once one card is shown to you, no other players show cards. Cross that card off in your detective notebook.

## Making an Accusation (Winning or Losing)
When you are confident you know the contents of the envelope:
1. State your final accusation on your turn: *"I accuse Professor Plum with the Wrench in the Library."*
2. Secretly look at the 3 cards inside the Case File envelope.
3. **If correct**: Reveal the cards to all players—you win the game!
4. **If incorrect**: Place the cards back in the envelope. You are eliminated from making moves or suggestions, but you must keep your cards to disprove other players' future suggestions.
""",
    },
    {
        "name": "Risk",
        "description": "The classic global domination war game of strategic alliances, troop deployments, and high-stakes dice battles across continents.",
        "min_players": 2,
        "max_players": 6,
        "min_age": 10,
        "estimated_playtime": 120,
        "complexity": "Medium",
        "category": "Strategy",
        "publisher": "Hasbro",
        "year_published": 1959,
        "filename": "risk_rules.txt",
        "rulebook": """# Risk Official Global Domination Rules

## Game Overview & Objective
Risk is a strategic territory conquest game played on a political world map divided into 42 territories across 6 continents. The objective is to conquer the entire world by occupying all 42 territories and eliminating all opponents.

## Turn Structure
Every turn consists of three distinct phases in order:
1. **Draft Reinforcements**: Receive and place new armies.
2. **Combat & Invasions**: Attack adjacent enemy territories.
3. **Fortify (Tactical Move)**: Shift troops between connected friendly territories.

## Phase 1: Receiving Reinforcements
Count your total occupied territories and divide by 3 (rounded down, minimum 3 armies).
- **Continent Control Bonuses**:
  - Asia: +7 armies
  - North America: +5 armies
  - Europe: +5 armies
  - Africa: +3 armies
  - South America: +2 armies
  - Australia: +2 armies
- **Card Sets**: Turn in a set of 3 matching cards (e.g. 3 infantry, 3 cavalry, 3 artillery) or 1 of each to receive escalating army reinforcements.

## Phase 2: Attacking & Dice Combat
You may attack an adjacent enemy territory if your territory has at least 2 armies (1 must remain behind to guard).
- **Attacker Rolls**: Up to 3 red dice (must have 1 more army than dice rolled).
- **Defender Rolls**: Up to 2 white dice (based on armies stationed in the territory).
- **Battle Resolution**:
  - Compare highest attacker die to highest defender die.
  - Compare second-highest attacker die to second-highest defender die.
  - **Ties**: **The Defender wins all ties!**
  - The loser of each comparison removes 1 army.
- **Conquest**: When all defending armies are eliminated, the attacker moves at least as many armies as dice rolled into the conquered territory.

## Conquering Territories & Drawing Cards
If you conquer at least one territory on your turn, you draw 1 Risk card at the end of your combat phase (maximum 1 card per turn).

## Eliminating Opponents
If you eliminate an opponent by conquering their last remaining territory, you immediately seize all of their Risk cards. If this gives you 6 or more cards, you must immediately trade in sets.
""",
    },
    {
        "name": "Battleship",
        "description": "The classic naval combat coordinate guessing game of stealth fleet placement and sinking enemy ships.",
        "min_players": 2,
        "max_players": 2,
        "min_age": 7,
        "estimated_playtime": 25,
        "complexity": "Light / Casual",
        "category": "Abstract Strategy",
        "publisher": "Hasbro",
        "year_published": 1967,
        "filename": "battleship_rules.txt",
        "rulebook": """# Battleship Official Naval Combat Rules

## Game Overview & Objective
Battleship is a two-player naval combat guessing game. Each player secretly positions a fleet of 5 ships on a 10x10 coordinate grid. Players take turns firing shots by calling grid coordinates to find and sink all 5 enemy ships. The first player to sink all opponent ships wins.

## Fleet Composition & Grid Placement
Each player has 5 ships occupying consecutive grid holes:
1. **Carrier**: 5 holes
2. **Battleship**: 4 holes
3. **Cruiser**: 3 holes
4. **Submarine**: 3 holes
5. **Destroyer**: 2 holes

**Placement Rules**:
- Ships must be placed horizontally or vertically.
- **No diagonal placement** is permitted.
- Ships cannot overlap or extend beyond the 10x10 (A-J, 1-10) grid boundaries.
- Ship positions cannot be altered once the game begins.

## Turn Sequence
1. Player 1 calls out a target coordinate (e.g., "B-4").
2. Player 2 checks their Ocean Grid (where their ships are located) and announces:
   - **"Hit!"** if a ship occupies that coordinate (insert a red peg into the ship).
   - **"Miss!"** if no ship is located there (insert a white peg in that ocean hole).
3. Player 1 records the result on their upper Target Grid (red peg for Hit, white peg for Miss).
4. When all holes of a ship have been hit, the defender must announce: *"You sank my [Ship Name]!"*
5. Turn passes to Player 2.

## Winning the Game
The game ends immediately when a player sinks all 5 of their opponent's ships (total of 17 hits).
""",
    },
    {
        "name": "Yahtzee",
        "description": "The classic dice-rolling game of probability, pushing your luck, and scoring 5-of-a-kind Yahtzees across 13 scoring categories.",
        "min_players": 1,
        "max_players": 10,
        "min_age": 8,
        "estimated_playtime": 30,
        "complexity": "Light / Casual",
        "category": "Dice",
        "publisher": "Hasbro",
        "year_published": 1956,
        "filename": "yahtzee_rules.txt",
        "rulebook": """# Yahtzee Official Rules & Scorecard Guide

## Objective
The objective of Yahtzee is to score the highest total points by rolling 5 dice to make specific scoring combinations across 13 rounds.

## Turn Rules (3 Rolls per Turn)
1. **First Roll**: Roll all 5 dice.
2. **Second & Third Rolls**: You may set aside any "keeper" dice and reroll the remaining dice up to 2 additional times.
3. **Score Selection**: At the end of your turn, you MUST fill in exactly one open category on your score sheet, even if it scores 0 points.

## Scorecard Categories
### Upper Section (Sum of matching dice)
- **Aces (Ones)**: Total of all 1s rolled.
- **Twos, Threes, Fours, Fives, Sixes**: Total of corresponding matching numbers.
- **Upper Section Bonus**: If the total score of the Upper Section is 63 or higher, add a **35-point bonus**.

### Lower Section (Poker-style combinations)
- **3 of a Kind**: At least 3 matching dice. Scores sum of all 5 dice.
- **4 of a Kind**: At least 4 matching dice. Scores sum of all 5 dice.
- **Full House**: 3 of one number and 2 of another. Scores **25 points**.
- **Small Straight**: Sequence of 4 consecutive dice (e.g., 1-2-3-4 or 2-3-4-5). Scores **30 points**.
- **Large Straight**: Sequence of 5 consecutive dice (1-2-3-4-5 or 2-3-4-5-6). Scores **40 points**.
- **Yahtzee (5 of a Kind)**: All 5 dice show the same number. Scores **50 points**.
- **Chance**: Any combination of dice. Scores sum of all 5 dice.

## Yahtzee Bonus & Joker Rules
If you roll an additional Yahtzee after scoring 50 in the Yahtzee box, you score a **100-point Yahtzee Bonus**. You then use the roll as a Joker in the appropriate Upper or Lower section category.

## Winning
After 13 rounds, all boxes are filled. The player with the highest grand total (Upper score + Bonus + Lower score + Yahtzee bonuses) wins.
""",
    },
    {
        "name": "Connect 4",
        "description": "The rapid two-player vertical checkers game of dropping discs to connect four in a row horizontally, vertically, or diagonally.",
        "min_players": 2,
        "max_players": 2,
        "min_age": 6,
        "estimated_playtime": 10,
        "complexity": "Light / Casual",
        "category": "Abstract Strategy",
        "publisher": "Hasbro",
        "year_published": 1974,
        "filename": "connect4_rules.txt",
        "rulebook": """# Connect 4 Official Rules

## Objective
Connect 4 is a two-player connection game played on a vertical 7-column by 6-row grid. The objective is to be the first player to form a continuous line of 4 checkers of your color horizontally, vertically, or diagonally.

## Setup
1. Stand the grid upright between the two players. Ensure the bottom slide bar is locked in place.
2. One player takes the 21 Yellow checkers; the other takes the 21 Red checkers.
3. Yellow goes first.

## Gameplay
1. On your turn, drop one of your colored checkers down any of the 7 open columns.
2. The checker falls straight down to occupy the lowest available space within that column.
3. Players alternate turns dropping one checker at a time.

## Winning the Game
The game ends immediately when a player connects 4 of their colored checkers in a row:
- **Horizontal**: 4 in the same row.
- **Vertical**: 4 stacked in the same column.
- **Diagonal**: 4 aligned diagonally across rows and columns.

If all 42 slots are filled and neither player has achieved 4 in a row, the game is a draw.
""",
    },

    # ── MODERN HITS & STRATEGY BESTSELLERS ────────────────────────────────────
    {
        "name": "Catan",
        "description": "The classic civilization island-building game of resource harvesting, trading, building settlements, and avoiding the robber.",
        "min_players": 3,
        "max_players": 4,
        "min_age": 10,
        "estimated_playtime": 75,
        "complexity": "Medium",
        "category": "Strategy",
        "publisher": "KOSMOS",
        "year_published": 1995,
        "filename": "catan_rules.txt",
        "rulebook": """# Catan (Settlers of Catan) Official Rules

## Objective
Be the first settler to reach 10 Victory Points on your turn through building settlements, upgrading cities, constructing roads, and purchasing development cards.

## Setup & Starting Placement
1. Build the island with 19 terrain hexes (Forest, Hills, Pasture, Fields, Mountains, Desert) surrounded by ocean harbor frames.
2. Place number tokens (2 through 12, excluding 7) onto the hexes. Place the Robber figure on the Desert hex.
3. Each player starts with 5 settlements, 4 cities, and 15 roads.
4. Starting settlement Snake Draft: Player 1 places 1 settlement + 1 road, continuing clockwise to Player 4, who places 2 settlements + 2 roads, and then back counter-clockwise to Player 1.
5. Collect starting resource cards from the hexes adjacent to your second placed settlement.

## Turn Sequence
Every turn consists of three distinct phases:
1. **Roll for Resources**: Roll 2 dice. The hexes matching the sum produce 1 resource card per adjacent settlement (and 2 resources per adjacent city).
   - **Rolling a 7 (The Robber)**: No hexes produce. Any player holding more than 7 resource cards must discard half (rounded down). The active player moves the Robber to any hex and steals 1 random resource card from an adjacent player.
2. **Trading**: Trade resource cards with other players, or trade with the bank (4:1 standard maritime trade, or 3:1 / 2:1 at specialized harbors).
3. **Building**: Spend resources to build:
   - **Road**: 1 Wood + 1 Brick (connects settlements/cities).
   - **Settlement**: 1 Wood + 1 Brick + 1 Sheep + 1 Wheat (Worth 1 Victory Point; must obey the *Distance Rule*—at least 2 road segments away from any other settlement).
   - **City**: 3 Ore + 2 Wheat (Upgrades an existing settlement; produces double resources; worth 2 Victory Points).
   - **Development Card**: 1 Ore + 1 Sheep + 1 Wheat (Knights, Year of Plenty, Monopoly, Road Building, Victory Points).

## Special Bonuses & Victory Points
- **Longest Road**: 2 Victory Points awarded to the first player to build a continuous road of at least 5 segments.
- **Largest Army**: 2 Victory Points awarded to the first player to reveal 3 Knight cards.
- **Winning**: First player to reach 10 Victory Points on their turn wins immediately.
""",
    },
    {
        "name": "Ticket to Ride",
        "description": "A cross-country train adventure where players collect colored train cards to claim railway routes connecting cities across North America.",
        "min_players": 2,
        "max_players": 5,
        "min_age": 8,
        "estimated_playtime": 45,
        "complexity": "Light / Casual",
        "category": "Strategy",
        "publisher": "Days of Wonder",
        "year_published": 2004,
        "filename": "ticket_to_ride_rules.txt",
        "rulebook": """# Ticket to Ride Official Rules

## Objective
Score the most points by claiming railway routes between adjacent cities, connecting distant destination cities shown on Destination Tickets, and building the longest continuous path of routes.

## Setup
1. Place the board map of North America in the center.
2. Each player takes 45 colored plastic train cars and a matching scoring marker.
3. Deal 4 Train Car cards to each player. Place 5 face-up cards next to the deck.
4. Deal 3 Destination Ticket cards to each player (players must keep at least 2).

## Turn Actions (Choose ONE of Three)
On your turn, you must perform exactly ONE action:
1. **Draw Train Car Cards**: Take 2 cards. You may take face-up cards or blind draw from the top of the deck.
   - *Locomotives (Wild)*: If you take a face-up Locomotive, it counts as your entire draw turn (you cannot take a second card).
2. **Claim a Route**: Play a set of cards matching the color and length of the route on the board, and place your plastic trains on that route. Score instant points based on route length:
   - 1 car: 1 pt | 2 cars: 2 pts | 3 cars: 4 pts | 4 cars: 7 pts | 5 cars: 10 pts | 6 cars: 15 pts.
   - Gray routes can be claimed using a set of any single color.
   - Double routes can only be used in 4-player and 5-player games.
3. **Draw Destination Tickets**: Draw 3 new Destination Tickets from the deck. You must keep at least 1.

## End Game & Scoring
- When any player's stock of trains drops to 2 or fewer cars, every player (including that player) gets one final turn.
- **Final Scoring**:
  - Add points scored during the game from claimed routes.
  - Add points for completed Destination Tickets.
  - **Deduct points** for any uncompleted Destination Tickets.
  - Award +10 bonus points for the **Longest Continuous Route**.
- The player with the highest score wins!
""",
    },
    {
        "name": "Wingspan",
        "description": "A relaxing yet competitive bird-collection engine-building board game of attracting beautiful birds to wildlife habitats.",
        "min_players": 1,
        "max_players": 5,
        "min_age": 10,
        "estimated_playtime": 60,
        "complexity": "Medium",
        "category": "Strategy",
        "publisher": "Stonemaier Games",
        "year_published": 2019,
        "filename": "wingspan_rules.txt",
        "rulebook": """# Wingspan Official Rules & Gameplay Guide

## Objective
You are bird enthusiasts seeking to discover and attract the best birds to your network of wildlife preserves across four rounds. Score points from birds played, bonus cards, end-of-round goals, eggs laid, food cached, and tucked cards.

## Preserves & Habitats
Each player mat has three distinct wildlife habitats:
1. **Forest (Gain Food)**: Activates food gathering from the birdfeeder dice tower.
2. **Grassland (Lay Eggs)**: Activates egg laying on bird cards.
3. **Wetlands (Draw Bird Cards)**: Activates drawing new bird cards from the deck/tray.

## Turn Actions (Choose ONE per Turn)
Place an action cube on the leftmost available slot of the chosen action:
1. **Play a Bird from Hand**: Pay the bird's food cost and egg cost (if placing beyond column 1) to place it in its eligible habitat.
2. **Gain Food & Activate Forest Birds**: Take food dice from the feeder, then activate all brown "When Activated" powers on birds in your Forest row moving from right to left.
3. **Lay Eggs & Activate Grassland Birds**: Take egg miniatures from the supply and place them on bird cards up to their egg capacities, then activate brown powers in your Grassland row.
4. **Draw Cards & Activate Wetland Birds**: Draw bird cards, then activate brown powers in your Wetlands row.

## Bird Powers
- **Brown Powers**: Trigger each time you take the habitat's core action.
- **Pink Powers**: Trigger once between your turns when an opponent takes a specific action.
- **White Powers**: Trigger once immediately when played.
- **Yellow / Game End Powers**: Evaluated during final scoring.

## End of Round & Scoring
At the end of each round (4 rounds total):
1. Score the end-of-round goal tile.
2. Discard all remaining action cubes and place 1 cube on the round goal slot (meaning you get 1 fewer action turn in each subsequent round: 8, 7, 6, 5 actions).
3. Reset face-up bird tray cards.
Highest total score across all bird points, eggs, caches, and goals wins.
""",
    },
    {
        "name": "Codenames",
        "description": "The ultimate team party word game where two rival spymasters give one-word clues to contact secret agents on a 5x5 grid.",
        "min_players": 4,
        "max_players": 8,
        "min_age": 10,
        "estimated_playtime": 15,
        "complexity": "Light / Casual",
        "category": "Party",
        "publisher": "Czech Games Edition",
        "year_published": 2015,
        "filename": "codenames_rules.txt",
        "rulebook": """# Codenames Official Rules & Spymaster Guide

## Objective
Two rival teams (Red and Blue) compete to make contact with all of their secret field agents first. Spymasters give one-word clues that point to multiple words on the board while avoiding the lethal Assassin card.

## Setup
1. Lay out 25 random Codename word cards in a 5x5 grid.
2. Spymasters sit on one side of the table facing the Keycard; team operatives sit on the opposite side.
3. The Keycard reveals 25 colored squares corresponding to the grid:
   - 8 Blue agents, 8 Red agents (1 team has 9 cards and goes first)
   - 7 Innocent bystanders (Tan/Neutral)
   - 1 Assassin (Black)

## Spymaster Clue Giving
On your team's turn, give a clue consisting of **exactly ONE word** and **ONE number**:
- *Example: "River: 2" (suggesting two cards related to rivers, like 'Amazon' and 'Bank').*
- **Clue Restrictions**:
  - The clue must relate to the meaning of the words, not letters or spelling.
  - You cannot use any word currently visible on the table.
  - You cannot give clues like "Starts with B" or mention letters.

## Operative Guessing
1. Operatives discuss and touch one card to make a guess.
2. Spymaster covers the touched card with the matching identity tile:
   - **Friendly Agent**: Correct! The team may make another guess (up to Number + 1 total guesses).
   - **Neutral Bystander**: Turn ends immediately.
   - **Enemy Agent**: Turn ends immediately; helps the opposing team!
   - **The Assassin**: **GAME OVER!** The team that touches the Assassin loses immediately.

## Winning
A team wins immediately when all of their agent cards are covered, or when the opposing team touches the Assassin.
""",
    },
    {
        "name": "Pandemic",
        "description": "A tense cooperative board game where players act as disease control specialists working together to discover cures before global outbreaks occur.",
        "min_players": 2,
        "max_players": 4,
        "min_age": 8,
        "estimated_playtime": 45,
        "complexity": "Medium",
        "category": "Cooperative",
        "publisher": "Z-Man Games",
        "year_published": 2008,
        "filename": "pandemic_rules.txt",
        "rulebook": """# Pandemic Official Cooperative Rules

## Objective
Players work together as members of a disease control team to discover cures for 4 deadly diseases (Blue, Yellow, Black, Red) threatening the globe before outbreaks spiral out of control.

## Turn Structure (4 Actions, Draw Cards, Infect Cities)
Each player's turn consists of three phases in order:
### Phase 1: Take 4 Actions
Combine any of the following actions:
- **Drive / Ferry**: Move to an adjacent connected city.
- **Direct Flight**: Discard a city card to fly directly to that city.
- **Charter Flight**: Discard the card matching your current city to fly anywhere.
- **Shuttle Flight**: Move between any two research stations.
- **Treat Disease**: Remove 1 disease cube from your current city (removes all cubes of that color if the disease is cured).
- **Share Knowledge**: Give or take the card matching your current city to/from a teammate in the same city.
- **Build Research Station**: Discard current city card to place a research station.
- **Discover a Cure**: At any research station, discard 5 matching color city cards to cure that disease.

### Phase 2: Draw 2 Player Cards
- Draw 2 cards from the Player Deck. Hand limit is 7 cards.
- **Epidemic Card**:
  1. *Increase*: Advance the Infection Rate marker by 1.
  2. *Infect*: Draw bottom card of Infection deck; put 3 cubes on that city.
  3. *Intensify*: Shuffle the Infection Discard Pile and place it back on top of the Infection Deck!

### Phase 3: Infect Cities
Flip infection cards equal to the current Infection Rate. Add 1 disease cube to each drawn city.
- **Outbreaks**: If a city already has 3 cubes of that color and must receive another, an **Outbreak** occurs: advance the Outbreak track by 1 and place 1 cube on every adjacent connected city (can trigger chain outbreaks!).

## Victory and Defeat
- **Victory (Win)**: The team wins immediately once cures for all 4 diseases are discovered (eradicating all cubes is not required).
- **Defeat (Lose)**: The team loses if:
  1. 8 Outbreaks occur (Outbreak marker reaches skull).
  2. A disease needs cubes added but none remain in the supply.
  3. The Player Deck runs out of cards.
""",
    },
    {
        "name": "Carcassonne",
        "description": "The award-winning medieval tile-placement game of claiming roads, fortifying cities, building monasteries, and farming fields with meeples.",
        "min_players": 2,
        "max_players": 5,
        "min_age": 7,
        "estimated_playtime": 35,
        "complexity": "Light / Casual",
        "category": "Strategy",
        "publisher": "Z-Man Games",
        "year_published": 2000,
        "filename": "carcassonne_rules.txt",
        "rulebook": """# Carcassonne Official Rules & Scoring Guide

## Objective
Players draw and place medieval land tiles to build an evolving map of roads, cities, monasteries, and farms, deploying followers (meeples) to score points.

## Turn Sequence
On your turn, complete these three actions in order:
1. **Draw and Place a Tile**: Draw 1 face-down landscape tile and place it adjacent to existing tiles. Road edges must connect to roads, city edges to cities, and fields to fields.
2. **Deploy a Meeple (Optional)**: Place 1 meeple from your supply onto the newly placed tile as a:
   - **Highwayman** on a road segment
   - **Knight** in a city segment
   - **Monk** in a monastery
   - **Farmer** in a field (laid flat, stays until end game)
   *Rule: You cannot place a meeple on a feature that already has another meeple (though separate features may merge later).*
3. **Score Completed Features**: Evaluate any completed features and return meeples to players.

## Scoring Completed Features
- **Completed Road**: Closed at both ends by crossroads, cities, or monasteries. Scores **1 point per tile**.
- **Completed City**: Completely surrounded by city walls with no open gaps. Scores **2 points per tile** + **2 points per pennant/shield**.
- **Completed Monastery**: Completely surrounded by 8 adjacent tiles (9 tiles total). Scores **9 points**.

## Majority Rule & Shared Scoring
If multiple meeples occupy a merged feature, the player with the most meeples scores full points. In case of a tie, all tied players score full points.

## End Game & Farm Scoring
When all tiles have been placed:
- Incomplete roads, cities, and monasteries score partial points (1 pt per tile/shield).
- **Farmers & Fields**: Each farmer scores **3 points** for every completed city touching their continuous pasture/field.
Player with the highest total points wins.
""",
    },
    {
        "name": "Splendor",
        "description": "The fast-paced Renaissance gem-merchant game of drafting jewel tokens, acquiring development cards, and attracting noble patrons.",
        "min_players": 2,
        "max_players": 4,
        "min_age": 10,
        "estimated_playtime": 30,
        "complexity": "Light / Casual",
        "category": "Strategy",
        "publisher": "Space Cowboys",
        "year_published": 2014,
        "filename": "splendor_rules.txt",
        "rulebook": """# Splendor Official Rules & Card Guide

## Objective
As wealthy Renaissance gem merchants, players collect gem chips and purchase development cards to build prestige, gain permanent gem discounts, and attract noble visitors. The first player to reach 15 prestige points triggers the final round.

## Setup
1. Arrange development cards into 3 tiers (Tier 1: Green, Tier 2: Yellow, Tier 3: Blue) and reveal 4 face-up cards from each tier.
2. Place gem tokens (Emerald, Sapphire, Ruby, Diamond, Onyx) and Gold wild tokens in stacks.
3. Reveal Noble tiles equal to number of players + 1.

## Turn Actions (Choose ONE of Four)
1. **Take 3 Different Gem Tokens**: Take 3 gem tokens of different colors from the supply (token limit is 10).
2. **Take 2 Identical Gem Tokens**: Take 2 tokens of the same color (only allowed if the stack has at least 4 tokens).
3. **Reserve a Card & Take 1 Gold**: Take 1 face-up or blind development card into your private reserve (max 3 reserved cards) and gain 1 Gold (wild) token.
4. **Purchase a Development Card**: Pay the required gem token cost minus the permanent gem bonuses provided by cards already in your tableau.

## Noble Visits
At the end of your turn, check if your owned development cards meet the requirements of any visible Noble tile (e.g. 3 Diamond cards + 3 Sapphire cards). If qualified, that Noble visits you, awarding **3 prestige points** (max 1 noble visit per turn).

## Winning the Game
When a player reaches 15 or more prestige points, the current round finishes so all players have had an equal number of turns. The player with the highest prestige points wins.
""",
    },
    {
        "name": "7 Wonders",
        "description": "A simultaneous card-drafting civilization game where leaders develop architectural wonders, military prowess, and commerce across three ancient ages.",
        "min_players": 3,
        "max_players": 7,
        "min_age": 10,
        "estimated_playtime": 30,
        "complexity": "Medium",
        "category": "Strategy",
        "publisher": "Repos Production",
        "year_published": 2010,
        "filename": "seven_wonders_rules.txt",
        "rulebook": """# 7 Wonders Official Drafting & Civilization Rules

## Objective
Lead one of the 7 great cities of the ancient world across 3 distinct Ages. Draft cards to harvest resources, construct architectural wonder stages, advance scientific discoveries, expand commercial trade, and build military supremacy.

## Gameplay & Card Drafting
Each Age consists of 6 turns played simultaneously:
1. Each player is dealt 7 cards from the current Age deck.
2. **Choose a Card**: All players simultaneously pick 1 card to play and place it face down.
3. **Reveal & Play**: Players reveal their cards and execute ONE of three actions:
   - **Build the Structure**: Pay its resource/coin cost and add it to your city tableau.
   - **Build a Wonder Stage**: Pay the wonder stage cost and tuck the card under your wonder board.
   - **Discard for 3 Coins**: Discard the card to the bank to gain 3 gold coins.
4. **Pass Hand**: Pass the remaining cards to your neighbor (Clockwise in Age I and III, Counter-clockwise in Age II).

## Structure Categories & Card Colors
- **Brown (Raw Materials)**: Wood, Stone, Clay, Ore.
- **Grey (Manufactured Goods)**: Glass, Loom (Cloth), Papyrus.
- **Blue (Civilian Structures)**: Direct Victory Points.
- **Yellow (Commercial)**: Coins, trading discounts with neighbors, and resource generation.
- **Red (Military)**: Shields used for end-of-Age conflicts.
- **Green (Scientific Structures)**: Symbols (Tablet, Compass, Gear) scored exponentially.
- **Purple (Guilds - Age III)**: End-game scoring bonuses based on neighbor city achievements.

## End of Age Military Conflict
At the end of each Age, compare your total Red shields to your immediate Left and Right neighbors:
- Defeat awards -1 point token.
- Victory awards +1 point (Age I), +3 points (Age II), or +5 points (Age III).

## Final Scoring
Sum points from Wonder stages, Civilian structures, Commercial cards, Guilds, Scientific combinations, Military conflict tokens, and remaining coins (1 VP per 3 coins). Highest score wins.
""",
    },
    {
        "name": "Azul",
        "description": "A gorgeous abstract tile-drafting strategy game inspired by Moorish ceramic azulejos to decorate the Royal Palace of Evora.",
        "min_players": 2,
        "max_players": 4,
        "min_age": 8,
        "estimated_playtime": 35,
        "complexity": "Light / Casual",
        "category": "Abstract Strategy",
        "publisher": "Plan B Games",
        "year_published": 2017,
        "filename": "azul_rules.txt",
        "rulebook": """# Azul Official Rules & Tile Placement Guide

## Objective
Players compete as artisan tile-layers decorating the walls of the Royal Palace of Evora. Draft beautiful glazed ceramic tiles from factory displays to complete pattern lines, transfer tiles to your wall, and earn adjacency bonuses while avoiding floor penalty points.

## Setup
1. Each player receives a player board. Place the score marker on 0.
2. Place Factory displays in a circle (5 for 2 players, 7 for 3 players, 9 for 4 players).
3. Fill each factory display with 4 random tiles from the bag. Place the "1" First Player token in the center table pool.

## Round Phase 1: Factory Offer (Tile Drafting)
On your turn, choose ONE factory display or the center table pool:
- Pick **all tiles of ONE color** from the chosen display.
- Push all remaining unchosen tiles from that display into the center table pool.
- If drawing from the center pool for the first time, take the "1" First Player token and place it on your floor line (scores -1 point penalty).
- Place drafted tiles into ONE pattern line row (rows 1 to 5) on your player board. Excess tiles spill over onto the Floor penalty line.

## Round Phase 2: Wall Tiling & Scoring
Once all factories and center tiles have been drafted:
1. For each completed pattern line (row filled with matching tiles):
   - Move 1 tile to the matching colored space on that row of your wall grid.
   - Discard the remaining tiles from that pattern line into the box lid.
2. **Adjacency Scoring**:
   - 1 point for the placed tile.
   - +1 point for each consecutive horizontally connected tile.
   - +1 point for each consecutive vertically connected tile.
3. Deduct points for any tiles on your Floor line, then clear the floor line.

## End Game & Final Bonuses
The game ends after the round in which at least one player completes a full horizontal row of 5 tiles on their wall.
**End-Game Bonuses**:
- **Complete Horizontal Row**: +2 points each
- **Complete Vertical Column**: +7 points each
- **All 5 Tiles of One Color**: +10 points each
Highest total score wins.
""",
    },
    {
        "name": "Secret Hitler",
        "description": "A fast-paced social deduction and political intrigue party game pitting Liberals against Fascists in 1930s Germany.",
        "min_players": 5,
        "max_players": 10,
        "min_age": 13,
        "estimated_playtime": 45,
        "complexity": "Medium",
        "category": "Party",
        "publisher": "Goat, Wolf & Cabbage",
        "year_published": 2016,
        "filename": "secret_hitler_rules.txt",
        "rulebook": """# Secret Hitler Official Social Deduction Rules

## Objective
Players are divided secretly into two teams: **Liberals** (majority) and **Fascists** (including Secret Hitler).
- **Liberals Win** if: 5 Liberal policies are enacted OR Secret Hitler is assassinated.
- **Fascists Win** if: 6 Fascist policies are enacted OR Secret Hitler is elected Chancellor after 3 Fascist policies have passed.

## Night Phase Setup
1. Deal secret identity cards and role envelopes: Liberals know only themselves; Fascists open their eyes and identify each other; Hitler keeps eyes closed but puts a thumb up to identify themselves to the Fascists (in 5–6 player games, Hitler knows the single other Fascist).

## Election Phase
1. **Presidential Nominee**: The Presidency passes clockwise each turn.
2. **Chancellor Nomination**: The President nominates an eligible Chancellor candidate (cannot be the previous President or Chancellor in 6+ player games).
3. **Vote (Ja! / Nein!)**: All players reveal voting cards simultaneously:
   - If a majority votes **Ja!**: The government is elected; proceed to the Legislative Session.
   - If 50% or more vote **Nein!**: The election fails, election tracker advances by 1, and the Presidency passes. If 3 elections fail in a row, the top policy of the deck is enacted immediately.

## Legislative Session
1. The President draws 3 policy tiles from the deck secretly, discards 1 face down, and hands the remaining 2 to the Chancellor.
2. The Chancellor discards 1 tile face down and enacts the remaining policy onto the corresponding board.
*No communication or gestures are allowed during the legislative session.*

## Executive Powers (Unlocked on Fascist Board)
When specific Fascist policies are enacted, the President must execute the unlocked power:
- **Investigate Loyalty**: Secretly check an opponent's party membership card (Liberal or Fascist; does not reveal if they are Hitler).
- **Special Election**: Choose the next Presidential nominee.
- **Policy Peek**: View the top 3 cards of the policy deck.
- **Execution**: Eliminate one player from the game permanently!

## Winning the Game
The game concludes immediately when either victory condition is triggered.
""",
    },
    {
        "name": "King of Tokyo",
        "description": "A fast-paced push-your-luck dice-battling party game where mutant monsters smash opponents and destroy Tokyo.",
        "min_players": 2,
        "max_players": 6,
        "min_age": 8,
        "estimated_playtime": 30,
        "complexity": "Light / Casual",
        "category": "Dice",
        "publisher": "IELLO",
        "year_published": 2011,
        "filename": "king_of_tokyo_rules.txt",
        "rulebook": """# King of Tokyo Official Rules

## Objective
Play as giant mutated monsters (Gigazaur, Alienoid, Cyber Bunny, The King) battling for supremacy. Win by being the first monster to reach **20 Victory Points** OR by being the **last monster standing** after eliminating all opponents.

## Setup & Tokyo City
Place the Tokyo board in the center. In 2–4 player games, only Tokyo City is used. In 5–6 player games, Tokyo Bay is also opened when Tokyo City is occupied.
- Starting Life Points: 10
- Starting Victory Points: 0

## Turn Sequence
On your turn, execute these phases in order:
### 1. Roll Dice (Up to 3 Rolls)
Roll all 6 custom dice. Set aside any keepers and reroll the rest up to 2 additional times.

### 2. Resolve Dice
- **1, 2, 3**: Sets of three identical numbers score that many Victory Points (+1 point for each additional matching number).
- **Claw (Attack)**:
  - If you are **Outside Tokyo**: You deal 1 damage to all monsters Inside Tokyo.
  - If you are **Inside Tokyo**: You deal 1 damage to ALL monsters Outside Tokyo!
- **Heart (Heal)**: Gain 1 Life point (monsters Inside Tokyo CANNOT heal using hearts!).
- **Lightning (Energy)**: Gain 1 Energy cube per lightning bolt to purchase Power cards.

### 3. Enter Tokyo
If Tokyo City is empty at the end of your attack phase, you MUST enter Tokyo (scores +1 Victory Point upon entering, and +2 Victory Points if you start your turn inside Tokyo).

### 4. Yielding Tokyo
When a monster inside Tokyo takes damage from an attack, they may choose to yield Tokyo and retreat outside, forcing the attacking monster to enter.

### 5. Buy Power Cards
Spend Energy cubes to purchase face-up Power cards for permanent abilities or instant special actions.

## Winning
The game ends immediately when a monster reaches 20 Victory Points or when all other monsters reach 0 Life points.
""",
    },
    {
        "name": "Coup",
        "description": "A bluffing and social deduction card game of influence, assassinations, stealing coins, and eliminating rival families.",
        "min_players": 2,
        "max_players": 6,
        "min_age": 10,
        "estimated_playtime": 15,
        "complexity": "Light / Casual",
        "category": "Card Game",
        "publisher": "Indie Boards & Cards",
        "year_published": 2012,
        "filename": "coup_rules.txt",
        "rulebook": """# Coup Official Rules & Character Actions

## Objective
In a dystopian near-future city-state run by corrupt corporations, you command influence through two secret character cards. Bluff, deduce, and assassinate opponents to be the last surviving player with influence remaining.

## Setup
1. The deck contains 15 cards (3 copies of 5 characters: Duke, Assassin, Captain, Ambassador, Contessa).
2. Deal 2 face-down influence cards and 2 treasury coins to each player.
3. If a player loses an influence, they must reveal 1 card face up (it is dead). When both cards are revealed, the player is eliminated.

## General Actions (Any Character)
- **Income**: Take 1 coin from the treasury (cannot be blocked).
- **Foreign Aid**: Take 2 coins (can be blocked by the Duke).
- **Coup**: Pay 7 coins to launch a coup against a rival player, forcing them to lose 1 influence immediately (cannot be blocked or challenged). *If you start your turn with 10 or more coins, you MUST launch a Coup.*

## Character Actions & Counteractions (Can be Bluffed!)
- **Duke**:
  - *Action*: Take **Tax** (3 coins from treasury).
  - *Counteraction*: Blocks Foreign Aid.
- **Assassin**:
  - *Action*: Pay 3 coins to **Assassinate** a chosen player (forces them to lose 1 influence).
- **Captain**:
  - *Action*: **Steal** 2 coins from another player.
  - *Counteraction*: Blocks Steal attempts.
- **Ambassador**:
  - *Action*: Draw 2 cards from court deck, exchange with your hidden hand, and return 2 cards.
  - *Counteraction*: Blocks Steal attempts.
- **Contessa**:
  - *Counteraction*: **Blocks Assassinations**.

## Challenges & Bluffing
Any player may challenge a claimed action or counteraction before it resolves:
- **If the actor was Bluffing**: The challenged actor loses 1 influence immediately.
- **If the actor was Honest**: The actor reveals the claimed card, shuffles it into the deck, draws a replacement, and the **Challenger loses 1 influence** for falsely accusing!
The last player with remaining hidden influence wins.
""",
    },
]


def seed_all_games():
    """Seed the database with all 22 board games and index rulebooks into ChromaDB."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Ensure default demo / system user exists
        admin_user = db.query(models.User).filter(models.User.id == 1).first()
        if not admin_user:
            admin_user = models.User(
                id=1,
                username="demoadmin",
                hashed_password=hash_password("adminpassword123"),
                role="admin",
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

        total_seeded = 0
        total_chunks = 0

        for game_info in GAMES_DATA:
            name = game_info["name"]
            filename = game_info["filename"]
            file_path = DOCS_STORAGE_PATH / filename

            # 1. Write the structured rulebook document
            file_path.write_text(game_info["rulebook"].strip(), encoding="utf-8")

            # 2. Check if BoardGame record exists in database
            existing_game = (
                db.query(models.BoardGame)
                .filter(models.BoardGame.name.ilike(name))
                .first()
            )

            if existing_game:
                # Update metadata
                existing_game.description = game_info["description"]
                existing_game.min_players = game_info["min_players"]
                existing_game.max_players = game_info["max_players"]
                existing_game.min_age = game_info["min_age"]
                existing_game.estimated_playtime = game_info["estimated_playtime"]
                existing_game.complexity = game_info["complexity"]
                existing_game.category = game_info["category"]
                existing_game.publisher = game_info["publisher"]
                existing_game.year_published = game_info["year_published"]
                existing_game.filename = filename
                existing_game.status = "active"
                db.commit()
                db.refresh(existing_game)
                target_game = existing_game
            else:
                new_game = models.BoardGame(
                    name=name,
                    description=game_info["description"],
                    min_players=game_info["min_players"],
                    max_players=game_info["max_players"],
                    min_age=game_info["min_age"],
                    estimated_playtime=game_info["estimated_playtime"],
                    complexity=game_info["complexity"],
                    category=game_info["category"],
                    publisher=game_info["publisher"],
                    year_published=game_info["year_published"],
                    filename=filename,
                    uploaded_by_user_id=admin_user.id,
                    status="active",
                )
                db.add(new_game)
                db.commit()
                db.refresh(new_game)
                target_game = new_game

            # 3. Ingest rulebook into ChromaDB
            chunks_count = ingest_rulebook(
                file_path=file_path,
                game_id=target_game.id,
                game_name=target_game.name,
            )
            total_chunks += chunks_count
            total_seeded += 1
            print(f"✓ Seeded '{target_game.name}' (id={target_game.id}, {chunks_count} chunks indexed)")

        print(f"\n🎉 Successfully seeded {total_seeded} board games with {total_chunks} total vector chunks!")

    except Exception as exc:
        db.rollback()
        print(f"❌ Error seeding games: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all_games()

Rikker
======

An online application allowing people to play the trick taking card game 'Rikken' against each other online.

##### Play the game
You can play a current version of the game at [http://gargamel1989.pythonanywhere.com/](http://gargamel1989.pythonanywhere.com/)

#### Latest Release: Alpha (v0.1)

###### What works
* Registration
* Invite other registered players to play a game with you
* Spot not filled by real players will be taken by bots. These bots will follow the game rules, but are
otherwise extremely dumb
* Game field is updated when other players take an action
* Play multiple rounds of rikken against your opponents
* Game types implemented:
  * Rikken (and Overrikken)
  * Miserie (1 person at a time)

###### What doesn't work yet
* Multiple people playing the same games (Miserie, voor alles, ...)
* Requesting cards for complicated game types (Open miserie with card, open voor alles with card, ...)
* Open opponent cards in open game types (Open miserie, open voor alles, ...)
 
Planned features:
* Implement complicated game types
* Fix bugs
* Finish scoring system (some games are not accurately scored)
* Make bots smarter (machine learning project?)
* Update portal with ajax updates
* Show a game history on the portal
* Show release notes on portal bottom
* Notify players when the game is waiting for actions by other players

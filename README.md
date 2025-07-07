# OpenLionheart

The historic medieval battle board game “Lionheart” transformed into python3 for PC . 

Includes various modes with even special units, the classic “panic” in the dice is working in the units on the game board. I have also added a bot so you can play on your own.

Years ago “[someone](https://code.google.com/archive/p/open-lionheart/)” had started to create a base in python2 however then never finished the project (“[copy here](https://github.com/HieuLsw/open-lionheart)”).

So I decided to rewrite it all in python3 adding all the functionality of the original board game.


### Dependencies

```pip install pyglet==1.4.10 cocos2d```

## Installation

GNU/Linux     ```./install_OpenLionheart.sh``` (Adds shortcut with icon to main menu)

### Usage
On linux if you used the installer you will find it in the main menu.

If you want to start it manually type in the terminal

```python3 lionheart.py```

On windows just make two clicks on "RunWindows.bat" or in Italian "AvviaWindows.bat"

If you want to start it manually type in the cmd

```python lionheart.py```

### ScreenShot

![alt text](https://github.com/MoonDragon-MD/OpenLionheart/blob/main/img/eng.jpg?raw=true)

![alt text](https://github.com/MoonDragon-MD/OpenLionheart/blob/main/img/ita.jpg?raw=true)

### Guide

A pdf with the original rules is included, regarding the new units I added in expert mode:

- Wall of Shields : the unit behind the wall of shields will be protected from arrow attacks (you won't be able to attack them but you will be able to take down the wall of shields)

- Crossbowmen : yes in the Middle Ages there were also them and they were deadly against the armor of knights, in fact I have set that each hit counts for two, so you will be able to take down a knight with one hit

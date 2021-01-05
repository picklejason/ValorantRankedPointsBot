# ValorantRankedPointsBot
Discord bot that shows ranked point movement using Valorant's Private/In-Game API

Huge thanks and credit to [RumbleMike](https://github.com/RumbleMike) for his ValorantStreamOverlay and his docs on Valorant's Private/In-Game API. This project was heavily inspired by his work.

This bot is currently not hosted publicly as it can have access to your Valorant login info. But feel free to look at and modify the code. If you have any questions or feedback please message me on discord (PickleJason#5293).

## Features
![example](https://i.gyazo.com/f66181e28dda3da4915c2889a333bf9a.png)

## How it works
1. DM the bot your login info using the command `-login [username] [password]`. (Sends a webrequest to Valorant API to get and save your Valorant player ID (does not save your username or password but it is possible to access it) and links it to your discord ID)
3. Use the command `-profile` to view your ranked points and recent matches (sends webrequest to Valorant API and returns json where it is then parsed and displayed)
4. It is also possible to view other members profile if they have logged in by mentioning them after the command `-profile @<user_id>`

**This method requires your Valorant login info so do not trust random programs/bots unless you host it yourself or know it is safe.**

## To-dos
* Way to obtain Valorant player ID without having access to login info
* Add optional tracking feature to automatically send updates when match is completed
* Use external database (sql)

## Setup

* Install requirements

`python -m pip install -r requirements.txt`

* Store discord token in .env

`DISCORD_TOKEN=<token>`
* Enter any Valorant username and password (Feel free to create a new one if you don't want to use your main) into info.json

`"admin": {
        "username": "username",
        "password": "password"
    }`

* Run the bot

`python bot.py`

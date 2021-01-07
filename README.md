# ValorantRankedPointsBot
Discord bot that shows ranked point movement using Valorant's Private/In-Game API

Huge thanks and credit to [RumbleMike](https://github.com/RumbleMike) for his ValorantStreamOverlay and his docs on Valorant's Private/In-Game API. This project was heavily inspired by his work.

This bot is currently not hosted publicly as it can have access to your Valorant login info. But feel free to look at and modify the code. If you have any questions or feedback please message me on discord (PickleJason#5293).

## Features
![example](https://i.gyazo.com/f66181e28dda3da4915c2889a333bf9a.png)

## How it works
1. DM the bot your login info using the command `-login [username] [password]`. (Sends a webrequest to Valorant API to get and save your Valorant player ID (does not save your username or password but it is possible to access it) and links it to your discord ID)

If you know your player ID you can skip this step and use the command `-link [player ID]` to directly link your player ID to your discord ID without having to input login. If you are on Windows you can find your player ID in your Valorant config folder. To access this, open up the Run box using Windows key + R and enter %localappdata%, then go to VALORANT > Saved > Config. Your player ID should be the name of one of the folders. If you have logged in to multiple accounts, your main account should be the one with the earliest date modified.

3. Use the command `-profile` to view your ranked points and recent matches (sends webrequest to Valorant API and returns json where it is then parsed and displayed)
4. It is also possible to view other members profile if they have logged in by mentioning them after the command `-profile @<user_id>`
5. If you would like to track a user and have automatic rank point updates you can use the `-track @<user_id>` command. This checks for any new competitive games played by the tracked user every minute. The user must have their player ID linked and have used `-profile` at least once. The update will be dm'ed to you after their game is finished. Use `-untrack` to stop tracking.

**This method requires your Valorant login info so do not trust random programs/bots unless you host it yourself or know it is safe.**

## Setup

* Install requirements
```
python -m pip install -r requirements.txt
```
* Store discord token in .env
```
DISCORD_TOKEN=<token>
```
* Enter and store any Valorant username and password (Feel free to create a new one if you don't want to use your main) in .env
```
USERNAME=<username>
PASSWORD=<password>
```
* Run the bot
```
python bot.py
```

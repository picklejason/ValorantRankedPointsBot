# ValorantRankedPointsBot
Discord bot that shows ranked point movement using Valorant's Private/In-Game API

Huge thanks and credit to [RumbleMike](https://github.com/RumbleMike) for his ValorantStreamOverlay and his docs on Valorant's Private/In-Game API. This project was heavily inspired by his work.

This bot is currently not hosted publicly as it can have access to your Valorant login info. But feel free to look at and modify the code. If you have any questions or feedback please message me on discord (PickleJason#5293).

## Features
![example](https://i.gyazo.com/39ca2ddb4c786c1ccb1ee50cfabf148d.png)

**This method requires your Valorant login info so do not trust random programs/bots unless you host it yourself or know it is safe.**

## Usage
```
-login [username] [password] / -link [player ID]
```
Use `-login` to link your Valorant player ID with your Discord ID through RSO.

Use `-link` to directly link your player ID to your discord ID without having to input login. If you are on Windows you can find your player ID in your Valorant config folder. To access this, open up the Run box using Windows key + R and enter %localappdata%, then go to VALORANT > Saved > Config. Your player ID should be the name of one of the folders. If you have logged in to multiple accounts, your main account should be the one with the earliest date modified.
```
-profile <!@user_id>
```
View ranked points and recent matches of user (sends webrequest to Valorant API and returns JSON where it is then parsed and displayed). React to display graph of ELO history.
```
-track <!@user_id> | -untrack
```
Track user to auto receive rank point update once they finish a new competitive match through DM. Use `-untrack` to stop tracking.

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
USER_NAME=<username>
PASSWORD=<password>
```
* Enter database url in .env (optional)
```
DATABASE_URL=<URL>
```
* Run the bot
```
python bot.py
```

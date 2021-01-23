import resources as res
import valorant_api as val
import trn_api as trn
import database as db

import asyncio
import os
import io
import asyncio
import json
import traceback
import discord
import math
import time
import numpy as np
import matplotlib.pyplot as plt
from discord.ext import commands, tasks
from dotenv import load_dotenv
from datetime import datetime, date
from matplotlib.collections import LineCollection

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
USERNAME = os.getenv("USER_NAME")
PASSWORD = os.getenv("PASSWORD")

bot = commands.Bot(command_prefix="-")


@bot.event
async def on_ready():
    print("Bot connected.")
    relog.start()
    send_update.start()


@tasks.loop(seconds=3600)
async def relog():
    _, headers = await val.run(USERNAME, PASSWORD)
    headers["X-Riot-ClientVersion"] = "release-02.01-shipping-6-511946"
    headers[
        "X-Riot-ClientPlatform"
    ] = "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9"
    with open("headers.json", "w") as f:
        json.dump({"headers": headers}, f, indent=4)
    print("Refreshed Tokens")


@tasks.loop(seconds=60)
async def send_update():
    try:
        users = db.get_all_users()
        tracked = []

        for user in users:
            discord_user = await bot.fetch_user(user)
            track_player = db.get_track_player(user)
            player_id = db.get_player_id(track_player)

            if track_player and player_id:
                prev_match = db.get_match_id(track_player)

                with open("headers.json", "r") as data:
                    headers = json.load(data)["headers"]

                match_data = await val.parse_stats(player_id, headers, 1)
                curr_match = list(match_data.keys())[0]
                if prev_match != curr_match:
                    tracked.append(track_player)
                    await discord_user.send(embed=await format_match(track_player))
                else:
                    pass

        for user in tracked:
            prev_match = db.get_match_id(user)
            player_id = db.get_player_id(user)
            if player_id:
                with open("headers.json", "r") as data:
                    headers = json.load(data)["headers"]

                match_data = await val.parse_stats(player_id, headers, 1)
                curr_match = list(match_data.keys())[0]
            else:
                curr_match = await trn.get_last_match(db.get_player_name(user))

            if prev_match != curr_match:
                print(f"{db.get_player_name(user)} {prev_match} {curr_match}")
                db.set_match_id(user, curr_match)
            else:
                continue

    except Exception as e:
        print(traceback.format_exc())


@bot.command()
async def link(ctx, name):
    if "#" not in name:
        await ctx.send("Missing tagline.")
        return

    db.set_player_name(ctx.author.id, name)

    await ctx.send("Riot ID has been linked.")


# Log in using RSO_AuthFlow and links discord ID with player ID
@bot.command()
async def login(ctx, username: str = "", password: str = ""):
    try:
        player_id, headers = await val.run(username, password)
        db.set_player_name(ctx.author.id, await val.get_user(player_id, headers))
        db.set_player_id(ctx.author.id, player_id)

        await ctx.send("Valorant account has been linked.")

    except Exception as e:
        print(traceback.format_exc())
        await ctx.send("Invalid Login.")


@bot.command()
async def logout(ctx):
    try:
        db.del_player_id(ctx.author.id)
        await ctx.send("Valorant player ID has been unlinked.")

    except Exception as e:
        await ctx.send("Valorant player ID was never linked.")


# Directly link player ID without entering login info
@bot.command()
async def idlink(ctx, player_id: str = None):
    if player_id is None:
        await ctx.send("Please input your Valorant player ID.")
        return

    db.set_player_id(ctx.author.id, player_id)
    await ctx.send("Valorant player ID has been linked.")


# Track a player and send updates whenever they finish a new competitive game
@bot.command()
async def track(ctx, user=None):
    if user is None:
        user = ctx.author
    elif user.isdigit():
        user = await bot.fetch_user(user)
    else:
        user = await bot.fetch_user(user.strip("<!@>"))

    db.set_track_player(ctx.author.id, user.id)
    track_player = db.get_player_name(user.id)
    await ctx.send(f"You are now tracking {track_player}.")


# Stop tracking player
@bot.command()
async def untrack(ctx):
    track_player = db.get_track_player(ctx.author.id)
    db.del_track_player(ctx.author.id)

    await ctx.send(f"You have stopped tracking {track_player}.")


@bot.command()
async def profile(ctx, user=None):
    try:
        if user is None:
            user = ctx.author
        elif user.isdigit():
            user = await bot.fetch_user(user)
        else:
            user = await bot.fetch_user(user.strip("<!@>"))

        with open("headers.json", "r") as data:
            headers = json.load(data)["headers"]

        player_id = db.get_player_id(user.id)
        player_name = db.get_player_name(user.id)
        profile = await trn.profile_stats(player_name)
        rank = profile["rank"]

        win_square = int(round(float(profile["win_pct"].rstrip("%")) / 10, 1))
        loss_square = 10 - win_square
        bar = win_square * "🟩" + loss_square * "🟥"

        description = f"{profile['wins']} W {bar} {profile['losses']} L\nWinrate: {profile['win_pct']}"
        if player_id:
            rating = await val.get_rank(player_id, headers)
            description = f"**{rating['ranked_rating']} / 100** RR\n" + description

        embed = discord.Embed(
            title=rank, description=description, timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=profile["rankIconUrl"])
        embed.set_author(name=player_name, icon_url=profile["avatarUrl"])

        embed.add_field(name="K/D Ratio", value=profile["kd_ratio"])
        embed.add_field(name="ADR", value=profile["damagePerRound"])
        embed.add_field(name="Headshots %", value=profile["hs_pct"])
        embed.add_field(name="Time Played", value=profile["time_played"], inline=False)

        footer = (
            "🟢 Player ID linked"
            if (db.get_player_id(user.id))
            else "🔴 Player ID not linked"
        )
        embed.set_footer(text=footer)
        await ctx.send(embed=embed)

    except Exception as e:
        print(traceback.format_exc())
        await ctx.send("User Riot ID not linked / Profile is private.")


@bot.command()
async def match(ctx, user=None):
    try:
        if user is None:
            user = ctx.author
        elif user.isdigit():
            user = await bot.fetch_user(user)
        else:
            user = await bot.fetch_user(user.strip("<!@>"))

        embed = await format_match(user.id)
        await ctx.send(embed=embed)

    except Exception as e:
        print(traceback.format_exc())
        await ctx.send("No recent competitive games found.")


async def format_match(user_id):
    player_id = db.get_player_id(user_id)
    player_name = db.get_player_name(user_id)
    # match_id = db.get_match_id(user_id)

    if player_id:
        with open("headers.json", "r") as data:
            headers = json.load(data)["headers"]

        match_data = await val.parse_stats(player_id, headers, 1)
        match_id = list(match_data.keys())[0]

        match, player = await val.match_data(user_id, headers, match_id)
    else:
        match_id = await trn.get_last_match(player_name)
        match, player = await trn.match_stats(match_id)

    for p in player:
        if p == player_name:
            player_team = player[p]["team"]
            player_agent = player[p]["agent_image_url"]
            break

    result = "Victory" if match[player_team]["won"] else "Defeat"
    enemy_team = "Red" if player_team == "Blue" else "Blue"
    title = f"{result} | {match[player_team]['rounds_won']} - {match[enemy_team]['rounds_won']} | {match['match_info']['map_name']}"
    team1 = "**Team 1**\n"
    team2 = "**Team 2**\n"

    sorted_players = sorted(player, key=lambda x: int(player[x]["score"]), reverse=True)

    for p in sorted_players:
        if player[p]["team"] == "Red":
            team1 += f"{res.agent_icons[player[p]['agent']]} | {res.rank_icons[player[p]['rank']]} | {p} | **{player[p]['kills']}**/**{player[p]['deaths']}**/**{player[p]['assists']}** | **{player[p]['kd_ratio']}** K/D | **{player[p]['score']}** ACS\n"
        elif player[p]["team"] == "Blue":
            team2 += f"{res.agent_icons[player[p]['agent']]} | {res.rank_icons[player[p]['rank']]} | {p} | **{player[p]['kills']}**/**{player[p]['deaths']}**/**{player[p]['assists']}** | **{player[p]['kd_ratio']}** K/D | **{player[p]['score']}** ACS\n"

    if player_id:
        recent_data = await val.parse_stats(player_id, headers, 1)
        recent = list(match_data.values())[0]

        sign = (
            f"+{recent['rating_change']} RR"
            if recent["rating_change"] > 0
            else f"{recent['rating_change']} RR"
        )
        movement_icon = res.movements[recent["movement"]]
        rating = f"{movement_icon} {sign}\n\n"

        description = f"{rating}{team1}\n{team2}"
    else:
        description = f"{team1}\n{team2}"

    color = discord.Color.green() if result == "Victory" else discord.Color.red()
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=player_agent)

    if player_id:
        start_time = datetime.fromtimestamp(
            match["match_info"]["start"] / 1000.0
        ).strftime("%m/%d • %H:%M")
    else:
        start_time = datetime.fromisoformat(match["match_info"]["start"]).strftime(
            "%m/%d • %H:%M"
        )

    embed.set_footer(text=start_time)

    return embed


# Create and send embed with rank point info
@bot.command()
async def recent(ctx, user=None):
    try:
        if user is None:
            user = ctx.author
        elif user.isdigit():
            user = await bot.fetch_user(user)
        else:
            user = await bot.fetch_user(user.strip("<!@>"))

        embed = await format_rank(user.id)
        msg = await ctx.send(embed=embed)

        await msg.add_reaction("📈")

        def check(reaction, user):
            return (
                user == ctx.message.author
                and str(reaction.emoji) == "📈"
                and reaction.message.id == msg.id
            )

        while True:
            try:
                reaction, user_ = await bot.wait_for(
                    "reaction_add", check=check, timeout=120
                )
            except asyncio.TimeoutError:
                await msg.remove_reaction("📈", bot.user)
                break
            image = await graph(user.id)
            embed.set_image(url=f"attachment://graph.png")
            await msg.delete()
            await ctx.send(file=image, embed=embed)
            break

    except Exception as e:
        print(traceback.format_exc())
        await ctx.send("User account not linked / Not enough recent competitive games.")


# Parse and process json from request
async def format_rank(discord_id, num_matches=3):

    player_id = db.get_player_id(discord_id)

    with open("headers.json", "r") as data:
        headers = json.load(data)["headers"]

    match_data = await val.parse_stats(player_id, headers, num_matches)
    matches = list(match_data.values())
    last_match = next(iter(matches))
    competitive_tier = last_match["competitive_tier"]

    rating_change = list()
    rank = res.ranks[str(competitive_tier)]
    RR = last_match["ranked_rating"]
    TRR = (competitive_tier * 100) - 300 + RR

    user = await bot.fetch_user(discord_id)
    description = f"**{RR} RR** | **{TRR} TRR**"

    embed = discord.Embed(title=rank, description=description)
    embed.set_author(name=user.display_name, icon_url=user.avatar_url)
    embed.set_thumbnail(
        url=f"https://trackercdn.com/cdn/tracker.gg/valorant/icons/tiers/{competitive_tier}.png"
    )

    for match in matches:
        stat = (
            f"+{match['rating_change']} RR"
            if match["rating_change"] > 0
            else f"{match['rating_change']} RR"
        )
        movement_icon = res.movements[match["movement"]]
        embed.add_field(
            name=f"{match['map_name']} ∙ {match['start_time']}",
            value=f"{movement_icon} {stat}",
            inline=False,
        )

    return embed


async def graph(id):
    player_id = db.get_player_id(id)

    with open("headers.json", "r") as data:
        headers = json.load(data)["headers"]

    match_data = await val.parse_stats(player_id, headers, 20)
    matches = list(match_data.values())
    ranked_rating = []
    competitive_tier = []

    for match in matches:
        ranked_rating.append(match["ranked_rating"])
        competitive_tier.append(match["competitive_tier"])

    TRR = list(
        reversed(
            [
                (tier * 100) - 300 + RR
                for RR, tier in zip(ranked_rating, competitive_tier)
            ]
        )
    )

    x = np.arange(len(TRR))
    y = np.array(TRR)

    segments_x = np.r_[x[0], x[1:-1].repeat(2), x[-1]].reshape(-1, 2)
    segments_y = np.r_[y[0], y[1:-1].repeat(2), y[-1]].reshape(-1, 2)

    # Assign colors to the line segments
    linecolors = ["green" if y_[0] < y_[1] else "red" for y_ in segments_y]

    segments = [list(zip(x_, y_)) for x_, y_ in zip(segments_x, segments_y)]
    min_ = int(math.floor(min(TRR) / 100.0)) * 100
    max_ = int(math.ceil(max(TRR) / 100.0)) * 100
    # Create figure
    plt.figure(figsize=(12, 5), dpi=150)
    plt.style.use("dark_background")
    ax = plt.axes()

    # Add a collection of lines
    ax.add_collection(LineCollection(segments, colors=linecolors))
    ax.scatter(x, y, c=[linecolors[0]] + linecolors, zorder=10)
    ax.set_xlim(0, len(x) - 1)
    ax.set_ylim(min_, max_)

    ax.xaxis.grid(linestyle="dashed")
    ax.yaxis.grid(linestyle="dashed")
    ax.spines["top"].set_linestyle("dashed")
    ax.spines["bottom"].set_capstyle("butt")
    ax.spines["right"].set_linestyle("dashed")
    ax.spines["bottom"].set_capstyle("butt")
    plt.xlabel("Past Matches")
    plt.ylabel("Rank Rating (RR)")
    plt.title("Rank Rating History")
    plt.xticks(np.arange(len(x)), labels=x[::-1])
    plt.yticks(np.arange(min_, max_, 100))
    plt.tight_layout()
    plt.savefig("graph.png", transparent=True)
    plt.close()

    with open("graph.png", "rb") as f:
        file = io.BytesIO(f.read())
    image = discord.File(file, filename="graph.png")

    return image


if __name__ == "__main__":
    bot.run(TOKEN)

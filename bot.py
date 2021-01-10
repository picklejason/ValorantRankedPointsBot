import resources as res
import RSO_AuthFlow as rs

import asyncio
import os
import sys
import re
import io
import aiohttp
import asyncio
import json
import traceback
import discord
import math
import numpy as np
import matplotlib.pyplot as plt
from discord.ext import commands, tasks
from dotenv import load_dotenv
from matplotlib.collections import LineCollection

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
USERNAME = os.getenv('USER_NAME')
PASSWORD = os.getenv('PASSWORD')
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    import database as db

bot = commands.Bot(command_prefix='-')

@bot.event
async def on_ready():
    print('Bot connected.')
    relog.start()
    send_update.start()

@tasks.loop(seconds=3600)
async def relog():
    _, headers = await rs.run(USERNAME, PASSWORD)
    with open('headers.json', 'w') as f:
        json.dump({'headers' : headers}, f, indent=4)
    print('Relogged')

@tasks.loop(seconds=60)
async def send_update():
    try:
        with open('headers.json', 'r') as data:
            headers = json.load(data)['headers']

        if DATABASE_URL:
            users = db.get_all_users()
        else:
            with open('info.json', 'r') as f:
                users = json.load(f)

        for user in users:
            discord_user = await bot.fetch_user(user)
            if DATABASE_URL:
                track_user = db.get_track_id(user)
                if track_user is not None:
                    player_id = db.get_player_id(track_user)
                    prev_match = db.get_match_id(track_user)

                    if await rs.check(player_id, headers, prev_match):
                        continue
                    else:
                        await discord_user.send(embed = await create_embed(track_user))
            else:
                if not users[user]['track_id'] == "":
                    track_user = users[user]['track_id']
                    player_id = users[track_user]['player_id']
                    prev_match = users[track_user]['match_id']

                    if await rs.check(player_id, headers, prev_match):
                        continue
                    else:
                        await discord_user.send(embed = await create_embed(track_user))
                else:
                    continue

    except Exception as e:
        print(traceback.format_exc())

# Parse and process json from request
async def process_stats(author, num_matches=3):
    if DATABASE_URL:
        player_id = db.get_player_id(author)
    else:
        with open ('info.json', 'r') as f:
            users = json.load(f)

        player_id = users[author]['player_id']

    with open('headers.json', 'r') as data:
        headers = json.load(data)['headers']

    after, diff, rank_nums, maps, arrows, start_times, prev_matches = await rs.get_stats(player_id, headers, num_matches)
    rank_num = rank_nums[0]
    stats = zip(diff, maps, arrows, start_times)
    rank = res.ranks[str(rank_num)]
    RP = after[0]
    ELO = (rank_num * 100) - 300 + RP

    if DATABASE_URL:
        db.set_match_id(author, prev_matches[0])
    else:
        users[author]['match_id'] = prev_matches[0]

        with open('info.json', 'w') as f:
            json.dump(users, f, indent=4)

    return stats, rank_num, rank, RP, ELO

# Log in using RSO_AuthFlow and links discord ID with player ID
@bot.command()
async def login(ctx, username : str = '', password : str = ''):
    author = str(ctx.author.id)
    try:
        player_id, _ = await rs.run(username, password)

        if DATABASE_URL:
            db.set_player_id(author, str(player_id))
        else:
            with open ('info.json', 'r') as f:
                users = json.load(f)

            if not author in users:
                users[author] = {}
                users[author]['player_id'] = player_id
                users[author]['track_id'] = ''
                users[author]['match_id'] = ''
                with open('info.json', 'w') as f:
                    json.dump(users, f, indent=4)

        await ctx.send('Login Successful.')

    except Exception as e:
        print(traceback.format_exc())
        await ctx.send("Invalid Login.")

# Directly link player ID without entering login info
@bot.command()
async def link(ctx, player_id : str):
    if not player_id:
        await ctx.send('Please input your Valorant player ID.')
        return
    author = str(ctx.author.id)

    if DATABASE_URL:
        db.set_player_id(author, player_id)
    else:
        if player_id:
            with open('info.json', 'r') as f:
                users = json.load(f)

            if not author in users:
                users[author] = {}
                users[author]['player_id'] = player_id
                users[author]['track_id'] = ''
                with open('info.json', 'w') as f:
                    json.dump(users, f, indent=4)

    await ctx.send('You account has been linked.')

# Track a player and send updates whenever they finish a new competitive game
@bot.command()
async def track(ctx, user = None):
    if user is None:
        user = ctx.author
    elif user.isdigit():
        user = await bot.fetch_user(user)
    else:
        user = await bot.fetch_user(user.strip('<!@>'))

    if DATABASE_URL:
        db.set_track_id(ctx.author.id, user.id)
    else:
        author = str(ctx.author.id)
        with open('info.json', 'r') as f:
            users = json.load(f)

        users[author]['track_id'] = str(user.id)
        with open('info.json', 'w') as f:
            json.dump(users, f, indent=4)

    await ctx.send(f'You are now tracking {user.name}.')

# Stop tracking player
@bot.command()
async def untrack(ctx):
    user = ctx.author
    author = str(user.id)

    if DATABASE_URL:
        db.del_track_id(user.id)
        await ctx.send('You have stopped tracking.')
    else:
        with open('info.json', 'r') as f:
            users = json.load(f)

        if author in users and users[author]['track_id']:
            users[author]['track_id'] = ""

            with open('info.json', 'w') as f:
                json.dump(users, f, indent=4)

            await ctx.send('You have stopped tracking.')

        else:
            await ctx.send('You are not tracking anyone.')

# Create and send embed with rank point info
@bot.command(aliases=['rank'])
async def profile(ctx, user = None):
    try:
        if user is None:
            user = ctx.author
        elif user.isdigit():
            user = await bot.fetch_user(user)
        else:
            user = await bot.fetch_user(user.strip('<!@>'))

        embed = await create_embed(user.id)
        msg = await ctx.send(embed=embed)

        await msg.add_reaction('📈')
        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) == '📈'

        while True:
            try:
                reaction, user_ = await bot.wait_for('reaction_add', check=check, timeout=120)
            except asyncio.TimeoutError:
                await msg.remove_reaction('📈', bot.user_)
                break
            image = await graph(user.id)
            embed.set_image(url=f'attachment://graph.png')
            await msg.delete()
            await ctx.send(file=image, embed=embed)
            break

    except Exception as e:
        print(traceback.format_exc())
        await ctx.send('User is not logged in or has not played enough recent competitive games')

async def create_embed(discord_id):
    user = await bot.fetch_user(discord_id)
    stats, rank_num, rank, RP, ELO = await process_stats(discord_id, 3)
    description = f'**{RP} RP** | **{ELO} ELO**'

    embed = discord.Embed(title=rank, description=description)
    embed.set_author(name=user.display_name, icon_url=user.avatar_url)
    embed.set_thumbnail(url=f'https://github.com/RumbleMike/ValorantStreamOverlay/blob/main/Resources/TX_CompetitiveTier_Large_{rank_num}.png?raw=true')
    for num, mmap, arrow, start_time in stats:
        stat = f'+{num} RP' if num > 0 else f'{num} RP'
        match_map = res.maps[mmap]
        movement = res.movements[arrow]
        embed.add_field(name=f'{match_map} ∙ {start_time}', value=f'{movement} {stat}', inline=False)

    return embed

async def graph(user_id):
    if DATABASE_URL:
        player_id = db.get_player_id(user_id)
    else:
        with open ('info.json', 'r') as f:
            users = json.load(f)
        player_id = users[user]['player_id']

    with open('headers.json', 'r') as data:
        headers = json.load(data)['headers']

    after, diff, rank_nums, maps, arrows, start_times, prev_matches = await rs.get_stats(player_id, headers, 20)
    ELO = list(reversed([(rank_num * 100) - 300 + RP for RP, rank_num in zip(after, rank_nums)]))

    x = np.arange(len(ELO))
    y = np.array(ELO)

    segments_x = np.r_[x[0], x[1:-1].repeat(2), x[-1]].reshape(-1, 2)
    segments_y = np.r_[y[0], y[1:-1].repeat(2), y[-1]].reshape(-1, 2)

    # Assign colors to the line segments
    linecolors = ['green' if y_[0] < y_[1] else 'red'
                  for y_ in segments_y]

    segments = [list(zip(x_, y_)) for x_, y_ in zip(segments_x, segments_y)]
    min_ = int(math.floor(min(ELO) / 100.0)) * 100
    max_ = int(math.ceil(max(ELO) / 100.0)) * 100
    # Create figure
    plt.figure(figsize=(12,5), dpi=150)
    plt.style.use('dark_background')
    ax = plt.axes()

    # Add a collection of lines
    ax.add_collection(LineCollection(segments, colors=linecolors))
    ax.scatter(x, y, c=[linecolors[0]]+linecolors, zorder=10)
    ax.set_xlim(0, len(x)-1)
    ax.set_ylim(min_, max_)

    ax.xaxis.grid(linestyle='dashed')
    ax.yaxis.grid(linestyle='dashed')
    ax.spines['top'].set_linestyle('dashed')
    ax.spines['bottom'].set_capstyle('butt')
    ax.spines['right'].set_linestyle('dashed')
    ax.spines['bottom'].set_capstyle('butt')
    plt.xlabel('Past Matches')
    plt.ylabel('ELO')
    plt.title('ELO History')
    plt.xticks(np.arange(len(x)), labels=x[::-1])
    plt.yticks(np.arange(min_, max_, 100))
    plt.tight_layout()
    plt.savefig('graph.png', transparent=True)
    plt.close()

    with open('graph.png', 'rb') as f:
        file = io.BytesIO(f.read())
    image = discord.File(file, filename='graph.png')

    return image

if __name__ == '__main__':
    bot.run(TOKEN)

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
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

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

# Parse and process json from request
async def process_stats(author, num_matches=3):

    with open ('info.json', 'r') as f:
        users = json.load(f)

    user_id = users[author]['user_id']
    with open('headers.json', 'r') as data:
        headers = json.load(data)['headers']

    after, diff, rank_nums, maps, arrows, start_times, prev_matches = await rs.get_stats(user_id, headers, num_matches)
    rank_num = rank_nums[0]
    stats = zip(diff, maps, arrows, start_times)
    rank = res.ranks[str(rank_num)]
    RP = after[0]
    ELO = (rank_num * 100) - 300 + RP
    users[author]['matches'] = prev_matches

    with open('info.json', 'w') as f:
        json.dump(users, f, indent=4)

    return stats, rank_num, rank, RP, ELO

# Log in using RSO_AuthFlow and links discord ID with player ID
@bot.command()
async def login(ctx, username : str = '', password : str = ''):

    try:
        author = str(ctx.author.id)
        with open ('info.json', 'r') as f:
            users = json.load(f)

        user_id, _ = await rs.run(username, password)
        if not author in users:
            users[author] = {}
            users[author]['user_id'] = user_id
            users[author]['track'] = ''
            with open('info.json', 'w') as f:
                json.dump(users, f, indent=4)

            await ctx.send('Login Successful.')
        else:
            await ctx.send('You are already logged in.')

    except Exception as e:
        await ctx.send("Invalid Login.")

# Remove saved profile
@bot.command(aliases=['unlink'])
async def logout(ctx):

    author = str(ctx.author.id)
    with open ('info.json', 'r') as f:
        users = json.load(f)

    if author in users:
        del users[author]
        with open('info.json', 'w') as f:
            json.dump(users, f, indent=4)

        await ctx.send('You have logged out.')
    else:
        await ctx.send('You are not logged in.')

# Directly link player ID without entering login info
@bot.command()
async def link(ctx, user_id : str):
    author = str(ctx.author.id)
    if user_id:
        with open('info.json', 'r') as f:
            users = json.load(f)

        if not author in users:
            users[author] = {}
            users[author]['user_id'] = user_id
            users[author]['track'] = ''
            with open('info.json', 'w') as f:
                json.dump(users, f, indent=4)

            await ctx.send('You account has been linked.')
        else:
            await ctx.send('Your account is already linked.')
    else:
        await ctx.send('Please input your Valorant player ID.')

# Track a player and send updates whenever they finish a new competitive game
@bot.command()
async def track(ctx, user : discord.User = ''):

    author = str(ctx.author.id)

    with open('info.json', 'r') as f:
        users = json.load(f)
    if not user:
        user = ctx.author
    uid = str(user.id)

    users[author]['track'] = uid
    with open('info.json', 'w') as f:
        json.dump(users, f, indent=4)

    await ctx.send(f'You are now tracking {user.name}.')

@tasks.loop(seconds=60)
async def send_update():
    try:
        with open('info.json', 'r') as f:
            users = json.load(f)

        for user in users:
            if not users[user]['track'] == "":
                track_user = users[user]['track']
                user_id = users[track_user]['user_id']
                prev_matches = users[track_user]['matches']
                with open('headers.json', 'r') as data:
                    headers = json.load(data)['headers']
                discord_user = await bot.fetch_user(user)

                if await rs.check(user_id, headers, prev_matches):
                    pass
                else:
                    await discord_user.send(embed = await create_embed(track_user))
            else:
                continue

    except Exception as e:
        print(traceback.format_exc())

# Stop tracking player
@bot.command()
async def untrack(ctx):
    author = str(ctx.author.id)

    with open('info.json', 'r') as f:
        users = json.load(f)

    if author in users and users[author]['track']:
        users[author]['track'] = ""

        with open('info.json', 'w') as f:
            json.dump(users, f, indent=4)

        await ctx.send('You have stopped tracking.')

    else:
        await ctx.send('You are not tracking anyone.')

# Create and send embed with rank point info
@bot.command(aliases=['rank'])
async def profile(ctx, user : discord.User = ''):
    try:
        if not user:
            user_id = str(ctx.author.id)
        else:
            user_id = str(user.id)

        embed = await create_embed(user_id)
        msg = await ctx.send(embed=embed)

        await msg.add_reaction('📈')
        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) == '📈'

        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=check, timeout=120)
            except asyncio.TimeoutError:
                await msg.remove_reaction('📈', bot.user)
                break

            image = await graph(user_id)
            # embed_ = await create_embed(user_id)
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

async def graph(user):
    num_matches = 20
    with open ('info.json', 'r') as f:
        users = json.load(f)

    user_id = users[user]['user_id']
    with open('headers.json', 'r') as data:
        headers = json.load(data)['headers']

    after, diff, rank_nums, maps, arrows, start_times, prev_matches = await rs.get_stats(user_id, headers, num_matches)
    ELO = list(reversed([(rank_num * 100) - 300 + RP for RP, rank_num in zip(after, rank_nums)]))

    x = np.arange(len(ELO))
    y = np.array(ELO)

    segments_x = np.r_[x[0], x[1:-1].repeat(2), x[-1]].reshape(-1, 2)
    segments_y = np.r_[y[0], y[1:-1].repeat(2), y[-1]].reshape(-1, 2)

    # Assign colors to the line segments
    linecolors = ['green' if y_[0] < y_[1] else 'red'
                  for y_ in segments_y]

    segments = [list(zip(x_+1, y_)) for x_, y_ in zip(segments_x, segments_y)]
    min_ = int(math.floor(min(ELO) / 10.0)) * 10
    max_ = int(math.ceil(max(ELO) / 10.0)) * 10
    # Create figure
    plt.figure(figsize=(12,5), dpi=150)
    plt.style.use('dark_background')
    ax = plt.axes()

    # Add a collection of lines
    ax.add_collection(LineCollection(segments, colors=linecolors))
    ax.scatter([x_ + 1 for x_ in x], y, c=[linecolors[0]]+linecolors, zorder=10)
    ax.set_xlim(0, len(x)+1)
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
    plt.xticks(np.arange(0, len(x)+1))
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

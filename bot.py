import resources as res
import RSO_AuthFlow as rs

import asyncio
import os
import sys
import re
import aiohttp
import asyncio
import json
import traceback
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

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
                    return
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
            user = str(ctx.author.id)
        else:
            user = str(user.id)

        await ctx.send(embed = await create_embed(user))

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

if __name__ == '__main__':
    bot.run(TOKEN)

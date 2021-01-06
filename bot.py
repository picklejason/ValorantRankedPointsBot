import resources as res
import RSO_AuthFlow as rs

import asyncio
import os
import sys
import re
import aiohttp
import asyncio
import json
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

bot = commands.Bot(command_prefix='-')

async def process_stats(author, num_matches=3):

    with open ('info.json', 'r') as f:
        users = json.load(f)

    user_id = users[author]['user_id']
    _, headers = await rs.run(USERNAME, PASSWORD)
    after, diff, rank_nums, maps, arrows, start_times = await rs.get_stats(user_id, headers, num_matches)
    rank_num = rank_nums[0]
    stats = zip(diff, maps, arrows, start_times)
    rank = res.ranks[str(rank_num)]
    RP = after[0]
    ELO = (rank_num * 100) - 300 + RP

    return stats, rank_num, rank, RP, ELO

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
            with open('info.json', 'w') as f:
                json.dump(users, f, indent=4)

            await ctx.send('Login Successful.')
        else:
            await ctx.send('You are already logged in.')

    except Exception as e:
        await ctx.send("Invalid Login.")

@bot.command()
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

@bot.command()
async def profile(ctx, user : discord.User = ''):

    if not user:
        user = ctx.author
        uid = str(ctx.author.id)
    else:
        uid = str(user.id)

    # num_matches = min if num_matches < min else max if num_matches > max else num_matches
    try:
        stats, rank_num, rank, RP, ELO = await process_stats(uid, 3)
    except:
        await ctx.send('User is not logged in or has not played enough recent competitve games')
        return

    description = f'**{RP} RP** | **{ELO} ELO**'
    embed = discord.Embed(title=rank, description=description)

    embed.set_author(name=user.display_name, icon_url=user.avatar_url)

    embed.set_thumbnail(url=f'https://github.com/RumbleMike/ValorantStreamOverlay/blob/main/Resources/TX_CompetitiveTier_Large_{rank_num}.png?raw=true')
    for num, mmap, arrow, start_time in stats:
        result = '🟢' if num > 0 else '🔴'
        stat = f'+{num} RP' if num > 0 else f'{num} RP'
        match_map = res.maps[mmap]
        movement = res.movements[arrow]
        embed.add_field(name=f'{result} {match_map} ∙ {start_time}', value=f'{movement} {stat}', inline=False)

    await ctx.send(embed=embed)

if __name__ == '__main__':
    bot.run(TOKEN)

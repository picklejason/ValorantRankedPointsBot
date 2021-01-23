import aiohttp
import asyncio
import json


async def profile_stats(user):
    username, tagline = user.split("#")

    profile_api = f"https://api.tracker.gg/api/v2/valorant/standard/profile/riot/{username}%23{tagline}"
    async with aiohttp.ClientSession() as session:
        async with session.get(profile_api, json={}) as r:
            data = (await r.json())["data"]

    user = data["platformInfo"]["platformUserIdentifier"]
    avatarUrl = data["platformInfo"]["avatarUrl"]

    stats = data["segments"][0]["stats"]
    wins = stats["matchesWon"]["displayValue"]
    losses = stats["matchesLost"]["displayValue"]
    win_pct = stats["matchesWinPct"]["displayValue"]
    hs_pct = stats["headshotsPercentage"]["displayValue"]
    kd_ratio = stats["kDRatio"]["displayValue"]
    damagePerRound = stats["damagePerRound"]["displayValue"]
    time_played = stats["timePlayed"]["displayValue"]
    rank = stats["rank"]["metadata"]["tierName"]
    rankIconUrl = stats["rank"]["metadata"]["iconUrl"]

    DATA = dict(
        user=user,
        avatarUrl=avatarUrl,
        wins=wins,
        losses=losses,
        win_pct=win_pct,
        hs_pct=hs_pct,
        kd_ratio=kd_ratio,
        damagePerRound=damagePerRound,
        time_played=time_played,
        rank=rank,
        rankIconUrl=rankIconUrl,
    )

    return DATA


async def get_last_match(user):

    username, tagline = user.split("#")
    history_api = f"https://api.tracker.gg/api/v2/valorant/rap-matches/riot/{username}%23{tagline}"
    async with aiohttp.ClientSession() as session:
        async with session.get(history_api) as r:
            data = json.loads(await r.text())

    matches = data["data"]["matches"]
    for match in matches:
        if "modeName" in match["metadata"]:
            if match["metadata"]["modeName"] == "Competitive":
                return match["attributes"]["id"]
    return None


async def match_stats(match_id):
    match_api = f"https://api.tracker.gg/api/v2/valorant/rap-matches/{match_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(match_api, json={}) as r:
            data = (await r.json())["data"]

    MATCH_DATA = {}
    PLAYER_DATA = {}

    red_team = data["segments"][0]
    blue_team = data["segments"][1]
    players = data["segments"][2:12]

    MATCH_DATA["match_info"] = {}
    MATCH_DATA["match_info"]["duration"] = data["metadata"]["duration"]
    MATCH_DATA["match_info"]["start"] = data["metadata"]["dateStarted"]
    MATCH_DATA["match_info"]["map_name"] = data["metadata"]["mapName"]
    MATCH_DATA["match_info"]["map_image_url"] = data["metadata"]["mapImageUrl"]

    MATCH_DATA["Red"] = {}
    MATCH_DATA["Red"]["rounds_won"] = red_team["stats"]["roundsWon"]["displayValue"]
    MATCH_DATA["Red"]["won"] = red_team["metadata"]["hasWon"]

    MATCH_DATA["Blue"] = {}
    MATCH_DATA["Blue"]["rounds_won"] = blue_team["stats"]["roundsWon"]["displayValue"]
    MATCH_DATA["Blue"]["won"] = blue_team["metadata"]["hasWon"]

    for player in players:
        metadata = player["metadata"]
        display_name = metadata["platformInfo"]["platformUserIdentifier"]
        team = metadata["teamId"]
        agent = metadata["agentName"]
        agentImageUrl = metadata["agentImageUrl"]

        stats = player["stats"]
        rank = stats["rank"]["displayValue"]
        score = stats["scorePerRound"]["displayValue"]
        kills = stats["kills"]["displayValue"]
        deaths = stats["deaths"]["displayValue"]
        assists = stats["assists"]["displayValue"]
        kdRatio = stats["kdRatio"]["displayValue"]
        damagePerRound = stats["damagePerRound"]["displayValue"]

        PLAYER_DATA[display_name] = {}
        PLAYER_DATA[display_name]["team"] = team
        PLAYER_DATA[display_name]["agent"] = agent
        PLAYER_DATA[display_name]["agent_image_url"] = agentImageUrl
        PLAYER_DATA[display_name]["rank"] = rank
        PLAYER_DATA[display_name]["score"] = score
        PLAYER_DATA[display_name]["kills"] = kills
        PLAYER_DATA[display_name]["deaths"] = deaths
        PLAYER_DATA[display_name]["assists"] = assists
        PLAYER_DATA[display_name]["kd_ratio"] = kdRatio

    return MATCH_DATA, PLAYER_DATA

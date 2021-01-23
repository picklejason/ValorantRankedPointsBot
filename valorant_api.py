import re
import aiohttp
import asyncio
import json
import traceback
import resources as res
from datetime import datetime


async def run(username, password):
    async with aiohttp.ClientSession() as session:
        data = {
            "client_id": "play-valorant-web-prod",
            "nonce": "1",
            "redirect_uri": "https://playvalorant.com/opt_in",
            "response_type": "token id_token",
        }
        await session.post("https://auth.riotgames.com/api/v1/authorization", json=data)

        data = {"type": "auth", "username": username, "password": password}

        async with session.put(
            "https://auth.riotgames.com/api/v1/authorization", json=data
        ) as r:
            data = await r.json()
        # print(data)
        pattern = re.compile(
            "access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)"
        )
        data = pattern.findall(data["response"]["parameters"]["uri"])[0]
        access_token = data[0]
        # print('Access Token: ' + access_token)
        id_token = data[1]
        expires_in = data[2]

        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        async with session.post(
            "https://entitlements.auth.riotgames.com/api/token/v1",
            headers=headers,
            json={},
        ) as r:
            data = await r.json()
        entitlements_token = data["entitlements_token"]
        # print('Entitlements Token: ' + entitlements_token)

        async with session.post(
            "https://auth.riotgames.com/userinfo", headers=headers, json={}
        ) as r:
            data = await r.json()
        user_id = data["sub"]
        # print('User ID: ' + user_id)
        headers["X-Riot-Entitlements-JWT"] = entitlements_token
        await session.close()

        return user_id, headers


async def parse_stats(user_id, headers, num_matches=3):
    try:
        async with aiohttp.ClientSession() as session:
            headers["X-Riot-ClientVersion"] = "release-02.01-shipping-6-511946"
            headers[
                "X-Riot-ClientPlatform"
            ] = "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9"
            async with session.get(
                f"https://pd.na.a.pvp.net/mmr/v1/players/{user_id}/competitiveupdates?startIndex=0&endIndex=20",
                headers=headers,
            ) as r:
                data = json.loads(await r.text())

            matches = data["Matches"]
            # print(matches)

            DATA = {}
            count = 0
            for match in matches:
                if match["TierAfterUpdate"] == 0:
                    continue
                else:
                    before = match["RankedRatingBeforeUpdate"]
                    after = match["RankedRatingAfterUpdate"]
                    map_id = match["MatchID"]
                    diff = match["RankedRatingEarned"]
                    DATA[map_id] = {}
                    DATA[map_id]["ranked_rating"] = after

                    if match["TierAfterUpdate"] > match["TierBeforeUpdate"]:  # Promoted
                        DATA[map_id]["movement"] = "PROMOTED"
                    elif (
                        match["TierAfterUpdate"] < match["TierBeforeUpdate"]
                    ):  # Demoted
                        DATA[map_id]["movement"] = "DEMOTED"
                    else:
                        if diff > 0:
                            DATA[map_id]["movement"] = "INCREASE"
                        elif diff < 0:
                            DATA[map_id]["movement"] = "DECREASE"
                        else:
                            DATA[map_id]["movement"] = "STABLE"
                    DATA[map_id]["rating_change"] = diff
                    count += 1
                    DATA[map_id]["competitive_tier"] = match["TierAfterUpdate"]
                    DATA[map_id]["map_name"] = res.maps[match["MapID"]]
                    start_time = match["MatchStartTime"] / 1000
                    DATA[map_id]["start_time"] = datetime.fromtimestamp(
                        start_time
                    ).strftime("%m-%d ∙ %H:%M")

                if count >= num_matches:  # [num] recent competitve matches found
                    break

            if count <= 0:
                return
            else:
                return DATA
    except:
        print(traceback.format_exc())


async def get_rank(user_id, headers):
    try:
        headers["X-Riot-ClientVersion"] = "release-02.01-shipping-6-511946"
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://pd.na.a.pvp.net/mmr/v1/players/{user_id}", headers=headers
            ) as r:
                data = json.loads(await r.text())
            # print(data)
            competitive = data["QueueSkills"]["competitive"]
            rank_tier = competitive["CompetitiveTier"]
            ranked_rating = competitive["TierProgress"]

            latest = data["LatestCompetitiveUpdate"]
            match_id = latest["MatchID"]
            map = latest["MapID"]
            start_time = latest["MatchStartTime"]
            movement = latest["CompetitiveMovement"]

            DATA = dict(
                rank_tier=rank_tier,
                ranked_rating=ranked_rating,
                match_id=match_id,
                map=map,
                start_time=start_time,
                movement=movement,
            )

            return DATA
    except:
        print(traceback.format_exc())


async def get_user(user_id, headers):

    async with aiohttp.ClientSession() as session:
        async with session.put(
            f"https://pd.na.a.pvp.net/name-service/v2/players",
            headers=headers,
            data=json.dumps([user_id]),
        ) as r:
            data = json.loads(await r.text())

        display_name = f"{data[0]['GameName']}#{data[0]['TagLine']}"

        return display_name


async def match_data(user_id, headers, match_id):
    try:
        headers["X-Riot-ClientVersion"] = "release-02.00-shipping-16-508517"
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://pd.na.a.pvp.net/match-details/v1/matches/{match_id}",
                headers=headers,
            ) as r:
                data = json.loads(await r.text())
            # print(data)
            MATCH_DATA = {}
            PLAYER_DATA = {}

            match_info = data["matchInfo"]
            MATCH_DATA["match_info"] = {}
            MATCH_DATA["match_info"]["duration"] = match_info["gameLengthMillis"]
            MATCH_DATA["match_info"]["start"] = match_info["gameStartMillis"]
            MATCH_DATA["match_info"]["map_name"] = res.maps[match_info["mapId"]]

            teams = data["teams"]
            for team in teams:
                MATCH_DATA[team["teamId"]] = {}
                MATCH_DATA[team["teamId"]]["won"] = team["won"]
                MATCH_DATA[team["teamId"]]["rounds_played"] = team["roundsPlayed"]
                MATCH_DATA[team["teamId"]]["rounds_won"] = team["roundsWon"]

            players = data["players"]
            for player in players:
                stats = player["stats"]
                display_name = f"{player['gameName']}#{player['tagLine']}"
                PLAYER_DATA[display_name] = {}
                PLAYER_DATA[display_name]["team"] = player["teamId"]

                agent_id = player["characterId"]
                agent = res.agent_map[agent_id]
                PLAYER_DATA[display_name]["agent"] = agent
                PLAYER_DATA[display_name][
                    "agent_image_url"
                ] = f"https://titles.trackercdn.com/valorant-api/agents/{agent_id}/displayicon.png"

                competitive_tier = str(player["competitiveTier"])
                PLAYER_DATA[display_name]["rank"] = res.ranks[competitive_tier]

                PLAYER_DATA[display_name]["score"] = round(
                    stats["score"] / stats["roundsPlayed"]
                )
                PLAYER_DATA[display_name]["kills"] = stats["kills"]
                PLAYER_DATA[display_name]["deaths"] = stats["deaths"]
                PLAYER_DATA[display_name]["assists"] = stats["assists"]
                PLAYER_DATA[display_name]["kd_ratio"] = round(
                    stats["kills"] / stats["deaths"], 1
                )

            return MATCH_DATA, PLAYER_DATA
    except:
        print(traceback.format_exc())


if __name__ == "__main__":

    user_id, headers = asyncio.get_event_loop().run_until_complete(run('example user name', 'my_secret_password'))
    print(asyncio.get_event_loop().run_until_complete(parse_stats(user_id, headers)))

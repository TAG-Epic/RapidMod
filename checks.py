"""
Created by Epic at 12/3/20
"""
from speedcord.ext.typing.context import MessageContext
from speedcord.ratelimiter import TimesPer
from os import environ as env
from re import compile
from aiohttp import ClientSession
from asyncio import sleep

discord_regex = compile("(?:discord.gg|discord.com|discord.net|discordapp.com|watchanimeattheoffice.com)/(\w+)")
allowed_discords = env["ALLOWED_DISCORDS"].split(" ")
max_threshold = float(env["MAX_THRESHOLD"])
ratelimited = []


async def regex_check(client, message: MessageContext):
    for regex, regex_raw in client.banned_regexes:
        if regex.match(message.content):
            return True, f"Message matched regex: {regex_raw}"
    return False, None


async def discord_invite_check(client, message: MessageContext):
    match = discord_regex.match(message.content)
    if match:
        code = match.group(0)
        if code in allowed_discords:
            return False, None
        return True, f"Discord invite found: {code}"
    return False, None


async def max_check(client, message: MessageContext):
    async with ClientSession() as session:
        r = await session.post("http://max:5000/model/predict", json={"text": [message.content]})
        data = await r.json()
        predictions = data["results"][0]["predictions"]
        for prediction_name, prediction_value in predictions.items():
            if prediction_name == "toxic":
                continue
            if prediction_value >= max_threshold:
                return True, f"Predicted {prediction_name}. {round(prediction_value * 100)}% sure"
        return False, None


async def ratelimiter_check(client, message: MessageContext):
    if message.author["id"] in ratelimited:
        return True, None
    ratelimited.append(message.author["id"])
    await sleep(1)
    ratelimited.remove(message.author["id"])
    return False, None


checks = [regex_check, discord_invite_check, max_check, ratelimiter_check]

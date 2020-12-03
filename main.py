"""
Created by Epic at 12/3/20
"""
from checks import checks

from speedcord import Client
from speedcord.http import Route
from speedcord.ext.typing.context import MessageContext
from os import environ as env
from re import compile

client = Client(512)
client.token = env["TOKEN"]

client.banned_regexes = []
client.ignored_users = env["IGNORED_USERS"].split(" ")
for regex in env["BANNED_REGEXES"].split(";"):
    if len(regex.strip()) == 0:
        continue
    client.banned_regexes.append((compile(regex), regex))


@client.listen("MESSAGE_CREATE")
async def on_message(data, shard):
    message = MessageContext(client, data)
    if message.author["id"] in client.ignored_users:
        return
    for check in checks:
        check_result, check_data = await check(client, message)
        if check_result:
            route = Route("DELETE", "/channels/{channel_id}/messages/{message_id}", channel_id=message.channel_id,
                          message_id=message.id)
            await client.http.request(route)
            # Log
            if not check_data:
                return
            route = Route("POST", "/channels/{channel_id}/messages", channel_id=env["LOG_CHANNEL_ID"])
            await client.http.request(route, json={
                "content": f"__**Check violated**__\n"
                           f"Author: <@{message.author['id']}>\n"
                           f"Message contents: {message.content}\n"
                           f"{check_data}",
                "allowed_mentions": {"parse": []}
            })
            return


client.run()

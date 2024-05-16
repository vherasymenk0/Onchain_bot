import os
import glob
import asyncio
import argparse
from itertools import cycle
from pyrogram import Client
from better_proxy import Proxy
import json
from bot.config import settings
from bot.utils import logger
from bot.core.claimer import run_claimer
from bot.core.registrator import register_sessions
from .agent_generator import generate_user_agents

start_text = """
Select an action:

    1. Create session
    2. Run clicker
"""

global tg_clients


def get_session_names() -> list[str]:
    session_names = glob.glob("sessions/*.session")
    session_names = [
        os.path.splitext(os.path.basename(file))[0] for file in session_names
    ]

    return session_names


def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file="bot/config/proxies.txt", encoding="utf-8-sig") as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []

    return proxies


def get_user_agents() -> list:
    if os.path.exists("bot/config/agents.json"):
        with open("bot/config/agents.json", "r", encoding="utf-8") as file:
            user_agents = json.load(file)
    else:
        user_agents = []

    if len(user_agents) == 0:
        raise ValueError("Not found user agents")

    return user_agents


async def get_tg_clients() -> list[Client]:
    global tg_clients

    session_names = get_session_names()
    generate_user_agents(len(session_names))

    if not session_names:
        raise FileNotFoundError("Not found session files")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [
        Client(
            name=session_name,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            workdir="sessions/",
        )
        for session_name in session_names
    ]

    return tg_clients


async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")

    logger.info(f"Detected {len(get_session_names())} sessions | {len(get_proxies())} proxies")

    action = parser.parse_args().action

    if not action:
        print(start_text)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be number")
            elif action not in ["1", "2"]:
                logger.warning("Action must be 1 or 2")
            else:
                action = int(action)
                break
    if action == 1:
        await register_sessions()
    elif action == 2:
        clients = await get_tg_clients()

        await run_tasks(tg_clients=clients)


async def run_tasks(tg_clients: list[Client]):
    proxies = get_proxies()
    agents = get_user_agents()
    proxies_cycle = cycle(proxies) if proxies else None
    agents_cycle = cycle(agents)
    tasks = [
        asyncio.create_task(
            run_claimer(
                tg_client=tg_client,
                proxy=next(proxies_cycle) if proxies_cycle else None,
                agent=next(agents_cycle),
            )
        )
        for tg_client in tg_clients
    ]

    await asyncio.gather(*tasks)

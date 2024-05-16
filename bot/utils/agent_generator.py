import json
import ua_generator
import os
from bot.utils import logger


def generate_user_agents(count: int):
    if os.path.exists("bot/config/agents.json"):
        with open("bot/config/agents.json", "r", encoding="utf-8") as file:
            user_agents = json.load(file)

        new_count = count - len(user_agents)
        if new_count <= 0:
            logger.info(f"Enough user agents available. No new user agents generated.")
            return
    else:
        user_agents = []
        new_count = count

    for _ in range(new_count):
        user_agent = ua_generator.generate(device='mobile', platform='android', browser='chrome')
        user_agents.append(user_agent.headers.get())

    with open("bot/config/agents.json", "w", encoding="utf-8") as file:
        json.dump(user_agents, file, ensure_ascii=False, indent=4)

    logger.info(f"Generated {new_count} new unique mobile user agents")

import asyncio
import aiohttp
import math
from random import randint
from aiohttp_proxy import ProxyConnector
from pyrogram import Client
from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers
from bot.config import settings
from .bot_info import bot_info
from pyrogram.raw.functions.messages import RequestWebView
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered
from urllib.parse import unquote
from better_proxy import Proxy

api_url = bot_info['api']


class Clicker:
    def __init__(self, client: Client, proxy_str: str | None, agent):
        self.client = client
        self.proxy_str = proxy_str
        self.session_name = client.name

        proxy_conn = ProxyConnector().from_url(proxy_str) if proxy_str else None
        clientHeaders = {
            **headers,
            **agent
        }
        self.http_client = aiohttp.ClientSession(headers=clientHeaders, connector=proxy_conn)

        if proxy_str:
            proxy = Proxy.from_str(proxy_str)
            self.client.proxy = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.http_client.close()

    async def check_proxy(self) -> None:
        try:
            response = await self.http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {self.proxy_str} | Error: {error}")
            return

    async def get_tg_web_data(self):
        try:
            if not self.client.is_connected:
                try:
                    await self.client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            web_view = await self.client.invoke(RequestWebView(
                peer=await self.client.resolve_peer(bot_info['username']),
                bot=await self.client.resolve_peer(bot_info['username']),
                platform='android',
                from_bot_menu=False,
                url=bot_info['origin']
            ))

            auth_url = web_view.url
            await self.client.disconnect()
            return unquote(string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

    async def login(self, tg_web_data: str):
        try:
            resp = await self.http_client.post(f"{api_url}/validate", json={"hash": tg_web_data})
            data = await resp.json()
            token = data.get("token")
            self.http_client.headers['Authorization'] = f"Bearer {token}"
        except Exception as error:
            logger.error(f"{self.session_name} | Error while login: {error}")

    async def get_info(self):
        resp = await self.http_client.get(f"{api_url}/info")
        data = await resp.json()

        if 'message' in data:
            raise Exception(data['message'])
        elif 'error' in data:
            raise Exception(data['error'])
        elif 'user' in data:
            return (await resp.json()).get("user")

    async def send_click(self, clicks: int):
        resp = await self.http_client.post(f"{api_url}/klick/myself/click", json={'clicks': clicks})
        data = await resp.json()

        if 'message' in data:
            raise Exception(data['message'])
        elif 'error' in data:
            raise Exception(data['error'])
        else:
            return math.floor(data['energy']), data['coins']

    async def apply_energy_restoration(self):
        resp = await self.http_client.post(f"{api_url}/boosts/energy", json={})
        data = await resp.json()

        if 'message' in data:
            raise Exception(data['message'])
        elif 'error' in data:
            raise Exception(data['error'])
        elif 'user' in data:
            return (await resp.json()).get("user")

    async def run(self) -> None:
        if self.proxy_str:
            await self.check_proxy()

        tg_web_data = await self.get_tg_web_data()
        await self.login(tg_web_data)

        while True:
            try:
                user_info = await self.get_info()
                energy = math.floor(user_info.get('energy'))
                has_energy_restorer = user_info.get('dailyEnergyRefill') > 0

                if settings.MIN_AVAILABLE_ENERGY < energy:
                    sleep_between_clicks = randint(a=settings.SLEEP_BETWEEN_TAP[0], b=settings.SLEEP_BETWEEN_TAP[1])
                    clicks = randint(a=settings.RANDOM_TAPS_COUNT[0], b=settings.RANDOM_TAPS_COUNT[1])
                    current_energy, balance = await self.send_click(clicks)
                    energy = current_energy

                    logger.success(
                        f"{self.session_name} | Successfully clicked +{clicks} | Energy: {energy} | Balance: {balance}")
                    logger.info(f"Sleep between clicks {sleep_between_clicks}s")

                    await asyncio.sleep(delay=sleep_between_clicks)
                    continue
                elif has_energy_restorer:
                    await self.apply_energy_restoration()
                    logger.info(f"{self.session_name} | Successfully applied energy restoration")
                    continue
                else:
                    sleep_time = settings.SLEEP_BY_MIN_ENERGY
                    logger.warning(f"{self.session_name} | Minimum energy reached, sleep {sleep_time}s | Energy: {energy}")
                    await asyncio.sleep(delay=sleep_time)
                    continue

            except Exception as error:
                if str(error) == 'Invalid token':
                    logger.error(f"{self.session_name} | Invalid or expired token")
                    logger.info(f"{self.session_name} | Relogin...")
                    await self.login(tg_web_data)
                    await asyncio.sleep(delay=20)
                    continue
                else:
                    logger.error(f"{self.session_name} | Unknown error: {error}")
                    await asyncio.sleep(delay=3)
                    continue


async def run_clicker(tg_client: Client, proxy: str | None, agent):
    try:
        async with Clicker(client=tg_client, proxy_str=proxy, agent=agent) as clicker:
            await clicker.run()
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")

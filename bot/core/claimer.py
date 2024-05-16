import asyncio
import aiohttp
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


class Claimer:
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
        try:
            resp = await self.http_client.get(f"{api_url}/info")
            user = (await resp.json()).get("user")

            return user
        except Exception as error:
            logger.error(f"{self.session_name} | Error while getting user information: {error}")

    async def run(self) -> None:
        if self.proxy_str:
            await self.check_proxy()

        tg_web_data = await self.get_tg_web_data()
        await self.login(tg_web_data)

        while True:
            try:
                logger.success(f"{self.session_name} | claimer is running!")
                await asyncio.sleep(delay=1)
                continue

            except Exception as error:
                logger.error(f"{self.session_name} | Unknown error: {error}")
                await asyncio.sleep(delay=3)


async def run_claimer(tg_client: Client, proxy: str | None, agent):
    try:
        async with Claimer(client=tg_client, proxy_str=proxy, agent=agent) as claimer:
            await claimer.run()
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")

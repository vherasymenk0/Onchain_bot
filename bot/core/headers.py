from .bot_info import bot_info

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'ru,ru-RU;q=0.9,en-US;q=0.8,en;q=0.7',
    'origin': bot_info['origin'],
    'referer': f"{bot_info['origin']}/",
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'x-requested-with': 'org.telegram.messenger',
}

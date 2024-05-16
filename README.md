| Features                            | Functionality                              |   
|-------------------------------------|--------------------------------------------|
| **Multithreading**                  | **Auto clicker**                           |
| **Binding a proxy to a session**    | **Applying free daily energy restoration** |
| **Random unique mobile user agent** |                                            |
| **Support pyrogram .session**       |                                            |
---
## Settings via .env file
| Property                  | Description                                                                  |
|---------------------------|------------------------------------------------------------------------------|
| **API_ID / API_HASH**     | Platform data from which to launch a Telegram session (stock - Android)      |
| **USE_PROXY_FROM_FILE**   | Whether to use proxy from the `bot/config/proxies.txt` file (default False)  |
| **MIN_AVAILABLE_ENERGY**  | Minimum amount of energy at which a delay occurs (default 100)               |
| **RANDOM_CLICKS_COUNT**   | Random number of clicks (default [50, 99])                                   |
| **SLEEP_BETWEEN_TAP**     | Random delay between clicks (default [4, 8])                                 |
| **SLEEP_BY_MIN_ENERGY**   | Delay when minimum energy is reached (default 200)                           |
---
## Installation 

1. Copy .env-example to .env
2. Specify your **API_ID** and **API_HASH**
3. Execute in the terminal
```shell
~bot/ >>> python -m venv venv
~bot/ >>> source venv/bin/activate
~bot/ >>> pip install -r requirements.txt
~bot/ >>> python main.py
```

#### Also for quick launch you can use arguments, for example:
```shell
~bot/ >>> python main.py --action (1/2)
# Or
~bot/ >>> python main.py -a (1/2)

#1 - Create session
#2 - Run clicker
```

# ottd-prayer

***Unless specified otherwise, this project is supported and is under active development. Please create a ticket for bug reports or features requests.***

ottd-prayer is a user-configurable AFK bot for the open-source game [OpenTTD](https://www.openttd.org/). Features of this bot include:

* Connecting to servers with direct IPs or invite codes
* Setting a custom player name to the bot
* Joining a company by name or ID
* Joining a password-protected game or company
* Toggleable automatic spectator mode when nobody is playing
* Auto-reconnecting
* ...and much more!

## Installation

### Binary Downloads

The easiest way to use the bot is to download the pre-compiled binary. To download the binary:

 1. Go to the [Build Binary actions workflow](https://github.com/wooky/ottd-prayer/actions/workflows/build.yml)
 2. Click on the latest successful build
 3. At the bottom, download the artifact corresponding to your OS
 4. Extract and run the executable

### Through pip

You will need Python 3.10+ and pip installed. You can then install the latest version of the bot with

```bash
python -m pip install https://github.com/wooky/ottd-prayer/archive/refs/heads/master.zip
```

## Running

Once you have the bot installed, you will need to make a config file. Download the [bot.sample.yaml](bot.sample.yaml) file as bot.yaml, change it as needed, then run the bot with

```bash
ottd-prayer /path/to/bot.yaml
```

If everything works correctly, your bot should be able to connect to the desired server and join your company.

## Development

You will need git, Python 3.10+ and pip installed. Afterwards, the easiest way to get started is by running these commands:

```bash
git clone https://github.com/wooky/ottd-prayer.git
cd ottd-prayer
python -m venv .venv
./.venv/scripts/activate
pip install -e .[dev]
```

(note: on Windows, the activate script is called with `.venv\Scripts\activate.bat`)

To run the script when in the virtual environment, simply call `ottd-prayer` or `python main.py`.

### Maintaining Code Quality

This project uses linting and strict type checking to maintain code quality. First, you'll need to generate types for some dependencies:

```bash
stubgen -p dataclass_wizard -p openttd_protocol
```

Run these commands often to ensure good code quality:

```bash
black src/ottd_prayer
isort src/ottd_prayer
mypy
```

## Miscellaneous

> Why was this bot created?

Company autocleaning is a feature used on a lot of servers to make room for new companies by removing stale companies. While it works well enough for removing abandoned companies, extreme care needs to be taken when setting the autoclean timeout. Unfortunately, there are servers out there that sets a ridiculously low timeout, like 1 hour. This is the purpose of this bot, to make sure that your company won't get nuked so quickly.

> Why is it called ottd-prayer?

¯\\\_(ツ)\_/¯

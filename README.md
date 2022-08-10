# ottd-prayer

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

Coming soon!

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

To run the script when in the virtual environment, simply call `ottd-prayer`.

### Maintaining Code Quality

This project uses linting and strict type checking to maintain code quality. First, you'll need to generate types for some dependencies:

```bash
stubgen -p dacite -p openttd_protocol
```

Run these commands often to ensure good code quality:

```bash
black src/ottd_prayer
isort src/ottd_prayer
mypy
```

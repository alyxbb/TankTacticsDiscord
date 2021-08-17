from discord import Intents
from discord_components import DiscordComponents
from discord.ext.commands import Bot as Client
import json
import logging
import os
import datetime

from cogs.database import c

logger = logging.getLogger("tankTactics")


def setup_logging():
    log_dir = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    current_log_dir = log_dir+"\\"+str(datetime.datetime.utcnow().strftime("%Y-%m-%d--%H-%M-%S"))
    if not os.path.exists(current_log_dir):
        os.mkdir(current_log_dir)
    discord_logger = logging.getLogger("discord")
    logger.setLevel(logging.DEBUG)
    discord_logger.setLevel(logging.DEBUG)

    handler = logging.FileHandler(filename=current_log_dir+"/tank_tactics.log", encoding="utf-8", mode="w")
    discord_handler = logging.FileHandler(filename=current_log_dir+"/discord.log", encoding="utf-8", mode="w")
    full_handler = logging.FileHandler(filename=current_log_dir+"/full_log.log", encoding="utf-8", mode="w")

    handler.setFormatter(logging.Formatter("%(asctime)s|%(levelname)s|%(name)s| %(message)s"))
    discord_handler.setFormatter(logging.Formatter("%(asctime)s|%(levelname)s|%(name)s| %(message)s"))
    full_handler.setFormatter(logging.Formatter("%(asctime)s|%(levelname)s|%(name)s| %(message)s"))

    discord_logger.addHandler(discord_handler)
    logger.addHandler(handler)
    discord_logger.addHandler(full_handler)
    logger.addHandler(full_handler)


setup_logging()
intents = Intents.default()
intents.members = True


bot = Client(command_prefix="!", intents=intents)
with open("resources/config.json") as f:
    config = json.load(f)


@bot.event
async def on_ready():

    DiscordComponents(bot)
    logger.info("We have logged in as {0.user}".format(bot))
    print("We have logged in as {0.user}".format(bot))
    for guild in bot.guilds:
        logger.info("in guild "+guild.name)
        for member in guild.members:
            logger.info("     "+member.name)
        c.execute("SELECT * FROM user_setup_process WHERE guild_id=?", (guild.id,))
        if c.fetchone() is None:
            chatManager = bot.get_cog("ChatManager")
            await chatManager.guild_join_setup(guild)
    logger.info("guild scan complete")


bot.load_extension("cogs.chatmanager")
bot.load_extension("cogs.serversetup")
bot.run(config["token"])

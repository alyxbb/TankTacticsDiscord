import discord.ext.commands as commands
from discord import VerificationLevel, NotificationLevel, ContentFilter, Embed
from discord_components import Button, ButtonStyle


from cogs.database import conn, c
import logging
logger = logging.getLogger("tankTactics.serversetup")


class ServerSetup(commands.Cog):
    def __init__(self, bot):
        logger.info("serverSetup cog loaded")
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        logger.info("joined guild"+guild.name)
        for member in guild.members:
            logger.info("     "+member.name)
        await self.guild_join_setup(guild)

    async def guild_join_setup(self, guild):
        if len(guild.text_channels) != 0:
            channel = guild.text_channels[0]
            logger.debug("using channel "+channel.name+" for setup message")
        else:
            channel = await guild.create_text_channel("general")
            logger.debug("no channel found for setup message. creating one")
        user = None
        async for member in guild.fetch_members(limit=10):
            if not member.bot:
                user = member
                logger.debug("found user: "+user.name)
        c.execute("SELECT * FROM player WHERE user_id=?", (user.id,))
        if c.fetchone() is not None:
            logger.info("setup canceled. user has already setup a server")
            await channel.send("error! you are already in a server")
            c.execute("DELETE FROM user_setup_process WHERE guild_id=?", guild.id)
            conn.commit()
            await guild.leave()
            return
        c.execute("SELECT * FROM user_setup_process WHERE user_id=?", (user.id,))
        if c.fetchone() is not None:
            logger.info("setup canceled. user has already started setting up a server")
            await channel.send("error! you have started setting up a server already")
            c.execute("DELETE FROM user_setup_process WHERE guild_id=?", (guild.id,))
            print("left", guild.name)
            conn.commit()
            await guild.leave()
            return
        components = [Button(label="setup", style=ButtonStyle.green, id="setup")]
        if guild.member_count == 2:
            setup_confirm_message = "press setup to continue. \nPLEASE NOTE!!!\nALL CHANNELS WILL BE DELETED DURING "\
                                  "THE SETUP PROCESS. IF YOU HAVE IMPORTANT DATA IN THIS SERVER PLEASE SETUP THE BOT " \
                                  "IN A DIFFERENT SERVER "
            await channel.send(setup_confirm_message, components=components)
            async for member in guild.fetch_members(limit=10):
                if not member.bot:
                    user = member
            c.execute("INSERT INTO user_setup_process VALUES (?,?,0)", (guild.id, user.id))
            conn.commit()
            logger.info("setup button sent succesfully.")
        else:
            logger.info("server contains too many users. leaving")
            c.execute("DELETE FROM user_setup_process WHERE guild_id=?", guild.id)
            await channel.send("this server contains other users")
            await guild.leave()
            return

    async def setup_server_channels(self, guild):
        important_category = None
        rules_channel = None
        instructions_channel = None
        for channel in guild.channels:
            if channel.name == "game-rules":
                rules_channel = channel
            elif channel.name == "how-to-play":
                instructions_channel = channel
            elif channel.name == "important":
                important_category = channel
        logger.debug("channels and categories found")
        user = None
        async for member in guild.fetch_members(limit=10):
            if not member.bot:
                user = member

        move_feed = await important_category.create_text_channel("move feed")
        await move_feed.send("when the game starts all moves will be sent here")
        logger.debug("move feed created")
        command_center = await important_category.create_text_channel("command center")
        command_center_components = [
            [
                Button(label="move", style=ButtonStyle.blue, id="moveMenuButton", disabled=True),
                Button(label="fire", style=ButtonStyle.blue, id="fireMenuButton", disabled=True),
                Button(label="increase range", style=ButtonStyle.blue, id="incRangeMenuButton", disabled=True),
                Button(label="give ap", style=ButtonStyle.blue, id="giveApMenuButton", disabled=True)
            ]
        ]

        await command_center.send("command center", components=command_center_components)
        logger.debug("command center created")
        chat_category = await guild.create_category("chat")
        chat_manager = await chat_category.create_text_channel("chat manager")
        chatManager = self.bot.get_cog("ChatManager")
        chat_manager_components = await chatManager.genChatManMenu()
        await chat_manager.send("CHAT MANAGER:", components=chat_manager_components)
        player_table_values = (user.id, guild.id, rules_channel.id, instructions_channel.id, move_feed.id,
                               command_center.id, chat_manager.id, chat_category.id, user.name)
        c.execute("INSERT INTO player VALUES (?,?,?,?,?,?,?,?,?,?)", player_table_values)  # TODO add nick randomizer
        conn.commit()
        logger.debug("channels setup successfully")

    async def setup_server(self, guild):
        user = None
        async for member in guild.fetch_members(limit=10):
            if not member.bot:
                user = member

        servername = "Tank Tactics Client - " + user.name
        with open("../resources/logo.png", "rb") as f:
            file = f.read()
            icon = bytearray(file)
        await guild.edit(name=servername, icon=icon, verification_level=VerificationLevel.low,
                         default_notifications=NotificationLevel.all_messages,
                         explicit_content_filter=ContentFilter.disabled, system_channel=None)
        logger.debug("guild name,icon etc setup for "+guild.name)
        old_webhooks = await guild.webhooks()
        for old_webhook in old_webhooks:
            logger.debug("deleted webhook: "+old_webhook.name)
            await old_webhook.delete()
        old_invites = await guild.invites()
        for old_invite in old_invites:
            logger.debug("deleted invite")
            await old_invite.delete()
        old_emojis = await guild.fetch_emojis()
        for old_emoji in old_emojis:
            logger.debug("deleted emoji")
            await old_emoji.delete()
        old_roles = await guild.fetch_roles()
        # todo setup role deleter
        for old_role in old_roles:
            if old_role.name != "TankTactics" and old_role.name != "@everyone":
                logger.critical("found role that needs deleting "+old_role.name)
        old_categories = guild.categories
        for old_category in old_categories:
            logger.debug("deleted category "+old_category.name)
            await old_category.delete()
        old_channels = guild.channels
        for old_channel in old_channels:
            logger.debug("deleted channel "+old_channel.name)
            await old_channel.delete()
        important_category = await guild.create_category("important")
        game_rules_channel = await important_category.create_text_channel("game rules")
        game_instructions_channel = await important_category.create_text_channel("how to play")
        game_instructions_text = "every player gets a tank placed on a random square on a grid. each tank has 3 " \
                                 "health.\n every day at 8am BST or GMT depending on what timezone britain is using, " \
                                 "each player receives 1 action token.\nan action token can be used in the following " \
                                 "ways:\n    move 1 space in any direction(including diagonals\n\t \tincrease your " \
                                 "range by 1\n    fire at 1 tank within range.\ntanks start with a range of 1 meaning "\
                                 "that they can fire at anything 1 square away(including diagonally).\n firing at a " \
                                 "tank reduces its health by 1.\n\nif you are within firing range of someone, you can "\
                                 "give action tokens to that player instead. feel free to make deals with other " \
                                 "players and plan how to kill other people, however they can betray you if they want "\
                                 "to.\n\nonce you die, you become a member of the jury, every day the jury votes on " \
                                 "players that they like. for every 3 votes a player gets on a day(rounded down) they "\
                                 "get an extra action point.\n\nall users are given an anonymous username. any " \
                                 "messages you send will appear to be sent from your anonymous username to other " \
                                 "players\n\nlast player alive wins "
        game_instructions_embed = Embed(title="--------------how to play--------------",
                                        description=game_instructions_text)
        await game_instructions_channel.send(embed=game_instructions_embed)
        game_rules_embed = await self.gen_rules_embed(game_instructions_channel)
        game_rules_buttons = [
            [
                Button(label="agree", style=ButtonStyle.green, id="gameRulesAgree"),
                Button(label="disagree", style=ButtonStyle.red, id="gameRulesDisagree")
            ]
        ]
        await game_rules_channel.send(embed=game_rules_embed, components=game_rules_buttons)
        logger.info("rules and how to play sent succsefully")

    async def gen_rules_embed(self, game_instructions_channel):
        game_rules = "\n1. do not abuse exploits in the bot. report all exploits to Doglol99.\n2.do not give out any " \
                  "information that could be used to work out which player you are while the game is running. It may " \
                  "seem like it doesnt matter at first but this game would have been made into an app by a video game "\
                  "company but it ruined friendships when they were testing it.\n3. do not add any users or bots to " \
                  "this server \n4.if you want to quit, message Doglol99 dont just not interact with the game.\n 5. " \
                  "profanity is allowed but no slurs or nsfw\n 6. dont add channels, roles, categories, " \
                  "emojis or anything else to the server.\n7. dont delete channels, roles, categories, " \
                  "emojis or anything else to the server\n8. dont edit channels,roles,categories,emojis," \
                  "server settings or anything else. "
        game_rules_text = "read how to play first in " + game_instructions_channel.mention + game_rules
        game_rules_embed = Embed(title="--------------rules--------------", description=game_rules_text)
        return game_rules_embed

    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        if interaction.custom_id == "setup":
            logger.info("setup button pressed by "+interaction.user.name)
            await interaction.respond(type=6)
            await self.setup_server(interaction.guild)
        elif interaction.custom_id == "gameRulesAgree":
            logger.info("rules agree button pressed by "+interaction.user.name)
            await interaction.respond(type=6)
            await interaction.message.edit(components=[])
            await interaction.channel.send("you agreed to the rules.")
            guild = interaction.guild
            await self.setup_server_channels(guild)
        elif interaction.custom_id == "gameRulesDisagree":
            logger.info("rules disagree button pressed by "+interaction.user.name)
            await interaction.respond(type=6)
            await interaction.channel.send("you disagreed to the rules. leaving server...")
            await interaction.guild.leave()
            logger.info("left server due to rules disagree for "+interaction.guild.name)


def setup(bot):
    bot.add_cog(ServerSetup(bot))

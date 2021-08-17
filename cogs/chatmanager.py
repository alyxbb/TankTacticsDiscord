import discord.ext.commands as commands
from discord_components import SelectOption, Button, ButtonStyle, Select

from cogs.database import c
import logging
logger = logging.getLogger("tankTactics.chatmanager")


class ChatManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("chatmanager cog loaded")

    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        if interaction.custom_id == "createChatChatButton":
            await self.create_chat_button_pressed(interaction)
        elif interaction.custom_id == "backChatButton":
            await self.back_button_pressed(interaction)

    @commands.Cog.listener()
    async def on_select_option(self, interaction):
        if interaction.custom_id == "addUserChatSelect":  # todo code here
            await interaction.respond(type=6)
            c.execute("SELECT chat_category_id FROM player WHERE guild_id=?", (interaction.guild.id,))
            chat_category_id = c.fetchone()
            chat_category = await self.bot.fetch_channel(int(chat_category_id[0]))
            print(interaction.raw_data)

    async def back_button_pressed(self, interaction):
        logger.info("back chat button pressed "+interaction.guild.name)
        await interaction.respond(type=6)
        chat_manager_components = await self.gen_chat_man_menu()
        await interaction.message.edit("CHAT MANAGER:", components=chat_manager_components)

    async def create_chat_button_pressed(self, interaction):
        logger.info("create chat button pressed in guild "+interaction.guild.name)
        await interaction.respond(type=6)
        create_chat_select_options = await self.create_chat_select_option_list(interaction.user.id)
        create_chat_components = [
            Select(placeholder="add users", options=create_chat_select_options, id="addUserChatSelect",
                   min_values=0, max_values=len(create_chat_select_options)),
            [
                Button(label="cancel", style=ButtonStyle.red, id="backChatButton"),
            ]
        ]
        await interaction.message.edit("CREATE CHAT", components=create_chat_components)
        logger.debug("create chat select sent")

    async def create_chat_select_option_list(self, userid):
        c.execute("SELECT nickname,user_id FROM player")
        users = c.fetchall()
        createChatSelectOptions = []
        logger.debug("creating chat: select list generation")
        for user in users:
            if user[1] != userid:
                sel_opt = SelectOption(label=user[0], value=user[1])
                createChatSelectOptions.append(sel_opt)
                logger.debug("    "+user[0])
        return createChatSelectOptions

    async def gen_chat_man_menu(self):
        chatManagerComponents = [[Button(label="create new chat", style=ButtonStyle.blue, id="createChatChatButton"),
                                  Button(label="leave chat", style=ButtonStyle.blue, id="leaveChatChatButton"),
                                  Button(label="add user to chat", style=ButtonStyle.blue, id="addUserChatButton")]]
        logger.debug("chat manager main menu loaded")
        return chatManagerComponents


def setup(bot):
    bot.add_cog(ChatManager(bot))

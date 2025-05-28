import discord
from discord.ext import commands
from keep_alive import keep_alive
from discord import app_commands, ui
import os
import io

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.dm_messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='p?', intents=intents)
ticket_channels = {}

GUILD_ID = 1319396490543890482  # Replace with your guild ID
CATEGORY_ID = 1371490688713228401  # Replace with the category ID where ticket channels go
MOD_ROLE_ID = 1371491095309062279  # Replace with your moderator role ID
CUSTOM_EMOJI = "<a:01charmzheart:1371440749341839432>"  # Replace with your emoji

# Define custom hex colors
LIGHT_PINK = discord.Color.from_str("#BF2018")
LIGHT_PURPLE = discord.Color.from_str("#FFFFFF")
LIGHT_RED = discord.Color.from_str("#FF4D43")
LIGHT_YELLOW = discord.Color.from_str("#952823")

class CloseButton(ui.View):
    def __init__(self, channel, user):
        super().__init__(timeout=None)
        self.channel = channel
        self.user = user

    @ui.button(label="close ang ticket na eto", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ticket closed.", ephemeral=True)
        embed = discord.Embed(
            title="<a:1_bfly1red:1371483731587502192>　　~~          ~~　　Ticket Closed.",
            color=LIGHT_RED
        )
        embed.description = "𓂃   ⸝⸝   **Your ticket has been closed <a:redpurse:1371483740043218954>**\nFeel free to dm modmail for __further assistance__\n    `  ꒰୨୧꒱  `   **Have a great day/night**   ⸝⸝   𓂃   <a:03_exclamation:1371484106399023144>"
        embed.set_footer(text="sending a new message will open a new ticket.", icon_url=self.channel.guild.icon.url)
        await self.user.send(embed=embed)
        await self.channel.delete()

bot.remove_command('help')

@bot.event
async def on_ready():
    print(f"Bot ready: {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced commands: {synced}")
    except Exception as e:
        print(f"Sync error: {e}")

    # Set custom status
    activity = discord.Activity(type=discord.ActivityType.listening, name="kung siya man ✦")
    await bot.change_presence(status=discord.Status.dnd, activity=activity)

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.guild is None and not message.author.bot:
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            print(f"Guild with ID {GUILD_ID} not found.")
            return

        category = guild.get_channel(CATEGORY_ID)
        if not category:
            print(f"Category with ID {CATEGORY_ID} not found.")
            return

        existing_channel = ticket_channels.get(message.author.id)

        if not existing_channel or not bot.get_channel(existing_channel.id):
            mod_role = guild.get_role(MOD_ROLE_ID)
            if not mod_role:
                print(f"Mod role with ID {MOD_ROLE_ID} not found.")
                return

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                mod_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }

            channel = await guild.create_text_channel(
                name=f"ticket—{message.author.name}",
                category=category,
                overwrites=overwrites
            )
            ticket_channels[message.author.id] = channel

            embed = discord.Embed(
                title="<a:white_envelope:1371482945336119389>　　~~          ~~　　Ticket Created.",
                description="**<a:01charmzheart:1371440749341839432>  Thank you for contacting modmail **\nPlease state what you __need help with__ <a:010sparkle:1371482938373443695>\n-# _ _ <:red_dot:1371489166638190595>reporting a member        <:red_dot:1371489166638190595>claiming gw\n-# _ _ <:red_dot:1371489166638190595>booster perks                     <:red_dot:1371489166638190595>ask a question\n**Our staff team will get to you shortly <a:redcheck:1371483725946163205> **",
                color=LIGHT_PINK
            )
            embed.set_footer(text="your message has been sent", icon_url=guild.icon.url)
            await message.author.send(embed=embed)

            await channel.send(embed=discord.Embed(
                description=f"new ticket by {message.author.mention} mga people!",
                color=LIGHT_YELLOW
            ), view=CloseButton(channel, message.author))
        else:
            channel = bot.get_channel(existing_channel.id)

        if channel:
            await forward_to_ticket(channel, message.author, message.content, message.author.display_avatar.url, message.attachments)
        else:
            print(f"Could not find or create a valid channel for {message.author}.")

    elif message.guild and not message.author.bot:
        if message.channel.category_id == CATEGORY_ID:
            for user_id, chan in ticket_channels.items():
                if chan.id == message.channel.id:
                    user = await bot.fetch_user(user_id)
                    embed = discord.Embed(
                        description=message.content,
                        color=LIGHT_PURPLE,
                        timestamp=discord.utils.utcnow()
                    )
                    embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
                    embed.set_footer(text=": pota staff", icon_url=message.guild.icon.url)

                    files = []
                    for attachment in message.attachments:
                        fp = await attachment.read()
                        files.append(discord.File(io.BytesIO(fp), filename=attachment.filename))

                    try:
                        await user.send(embed=embed, files=files if files else None)
                    except discord.Forbidden:
                        await message.channel.send("Could not DM the user.")
                    break

async def forward_to_ticket(channel, author, content, avatar_url, attachments):
    embed = discord.Embed(description=content, color=LIGHT_YELLOW)
    embed.set_author(name=author.name, icon_url=avatar_url)

    files = []
    for attachment in attachments:
        fp = await attachment.read()
        files.append(discord.File(io.BytesIO(fp), filename=attachment.filename))

    try:
        await channel.send(embed=embed, files=files if files else None)
    except discord.NotFound:
        print(f"Channel {channel.id} not found when trying to forward a message.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def contact(ctx, user_id: int, *, message):
    try:
        user = await bot.fetch_user(user_id)
        
        # Step 1: Introductory DM
        intro = discord.Embed(
            title="<a:white_envelope:1371482945336119389>　~~　          　~~　Ticket Created.",
            description="You’ve received a message from the staff team. You can reply to this DM to open a modmail ticket. <:003_:1371441150703042653>",
            color=LIGHT_PINK
        )
        await user.send(embed=intro)
        
        # Step 2: Staff message
        embed = discord.Embed(
            title="<:red_dot:1371489169217421392> Message from Staff:",
            description=message,
            color=LIGHT_PURPLE
        )
        embed.set_footer(text=f"sent by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await user.send(embed=embed)

        await ctx.send(embed=discord.Embed(description=f"msg sent to **{user}**.", color=discord.Color.green()))

    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(description="I can't DM this user. They may have DMs off.", color=discord.Color.red()))
    except discord.NotFound:
        await ctx.send(embed=discord.Embed(description="User not found.", color=discord.Color.red()))

keep_alive()
bot.run(TOKEN)

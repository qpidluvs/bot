from aiohttp import web
import discord
from discord.ext import commands
from discord import app_commands, ui, Embed, Interaction, ButtonStyle
from datetime import datetime
import os
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)  # No prefix commands

# ========== CONFIG ==========
WELCOME_CHANNEL_ID = 1160989454731837510
VERIFY_CHANNEL_ID = 1160989507257106536
QUEUE_CHANNEL_ID = 1161655709629419631
TICKET_CATEGORY_ID = 1160992684039741510
VERIFIED_ROLE_ID = 1161267510595825754
OWNER_ROLE_ID = 1161650985823912006
EMBED_COLOR = 0xFDFD96

# ========== EVENTS ==========
@bot.event
async def on_ready():
    await bot.tree.sync()
    bot.add_view(TicketView())  # register persistent ticket button view here
    print(f"Logged in as {bot.user} and synced commands")

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(description=(
            "<:BLANK:1258497106293952562>﹒<:yellow49:1280655357685006398>﹐**welcome to aria's comms ୨୧ *!***\n"
            "<:BLANK:1258497106293952562><:BLANK:1258497106293952562><:BLANK:1258497106293952562>⟢　 　⌅　verify [here](https://discord.com/channels/1160986425483862117/1160989507257106536) *!*　⑅　<:yellow47:1280660233756217365>\n"
            "<:BLANK:1258497106293952562><:BLANK:1258497106293952562> <:yellow48:1280655388181794826> 　♡ 　**check** out **my** services :\n"
            "<:BLANK:1258497106293952562><:BLANK:1258497106293952562>　₊　　˚　[info](https://discord.com/channels/1160986425483862117/1394729519541391491)　⌑ 　[order](https://discord.com/channels/1160986425483862117/1214937578223046686)　 ✲　 <:yellow43:1280663033588355143>"
        ), color=EMBED_COLOR)
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        embed.set_thumbnail(url="https://www.pngkey.com/png/detail/77-773093_chick-chickee-yellow-kawaii-cute-halloween-tumblr-aesth.png")
        embed.set_image(url="https://i.pinimg.com/564x/31/44/fe/3144fef2282a322cbab243d73e71653f.jpg")
        embed.set_footer(text=f"Joined on {datetime.now().strftime('%d/%m/%Y at %H:%M')}")
        await channel.send(embed=embed)

@bot.tree.command(name="cct", description="Show customer contract and terms")
async def cct_command(interaction: discord.Interaction):
    class ContractView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="accept", style=discord.ButtonStyle.success)
        async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message(
                "contract accepted, thank you ♡", ephemeral=False
            )
            self.disable_all_items()
            await interaction.message.edit(view=self)

        @discord.ui.button(label="decline", style=discord.ButtonStyle.danger)
        async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message(
                "you must accept the contract before ordering", ephemeral=True
            )

    embed = discord.Embed(
        title="customer contract & terms",
        description=(
            "before placing your order please read and agree to these terms:\n\n"
            "1. once your order is accepted it’s final, no refunds except for valid reasons\n"
            "2. delivery times can vary depending on how complex your order is and how busy i am\n"
            "3. you’re responsible for giving clear and accurate info about your order, i can’t fix mistakes caused by unclear details\n"
            "4. all communication should be respectful and honest, any disrespect may result in order cancellation\n"
            "5. you agree that i am not responsible for keeping the bot online 24/7.\n"
            "6. payments need to be done through approved methods, feel free to reach out if you have any questions before ordering\n\n"
            "by accepting these terms you confirm you understand and agree to follow the policies and guidelines"
        ),
        color=0xFDFD96
    )
    await interaction.response.send_message(embed=embed, view=ContractView())

# ========== VERIFICATION ==========
@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id == VERIFY_CHANNEL_ID and str(payload.emoji) == '<:yellow50:1280655495375622207>':
        guild = bot.get_guild(payload.guild_id)
        role = guild.get_role(VERIFIED_ROLE_ID)
        member = guild.get_member(payload.user_id)
        if role and member:
            await member.add_roles(role)

@bot.tree.command(name="sendverify")
async def sendverify(interaction: discord.Interaction):
    channel = bot.get_channel(VERIFY_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message("Verification channel not found.", ephemeral=True)
        return

    embed = discord.Embed(
        description=(
            "<:BLANK:1258497106293952562><:BLANK:1258497106293952562><:BLANK:1258497106293952562>﹒<:yellow49:1280655357685006398>﹐　verify 　୨୧　! \n"
            "<:BLANK:1258497106293952562>⟢ 　⌅　welcome to aria's services　 <:yellow47:1280660233756217365>\n"
            "<:BLANK:1258497106293952562><:yellow43:1280663033588355143> 　 ♡ 　 to verify, type : heart\n"
            "<:BLANK:1258497106293952562><:BLANK:1258497106293952562>　₊　　˚　enjoy !　⌑ 　 ✲　<:yellow48:1280655388181794826>"
        ),
        color=EMBED_COLOR
    )
    embed.set_image(url="https://64.media.tumblr.com/76b0010bc7d5e4599c7ebdfc2184808b/5e10528fe60c4a2c-40/s2048x3072/daaee3b4519dcedf4fd709024a54034af4f48402.pnj")

    message = await channel.send(embed=embed)
    await message.add_reaction("<:yellow50:1280655495375622207>")
    await interaction.response.send_message("Verification embed sent in the verification channel!", ephemeral=True)

# ========== TICKET SYSTEM ==========
class OrderModal(ui.Modal, title="new order"):
    feature = ui.TextInput(label="what commands/features?", style=discord.TextStyle.paragraph)
    payment = ui.TextInput(label="payment method", style=discord.TextStyle.short)
    description = ui.TextInput(label="describe briefly what you want", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
            guild.get_role(OWNER_ROLE_ID): discord.PermissionOverwrite(view_channel=True),
        }
        channel = await guild.create_text_channel(name=f"ticket-{interaction.user.name}", category=category, overwrites=overwrites)
        embed = discord.Embed(title="new order request", color=EMBED_COLOR)
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="what commands/features?", value=self.feature.value, inline=False)
        embed.add_field(name="payment method", value=self.payment.value, inline=False)
        embed.add_field(name="describe briefly what you want", value=self.description.value, inline=False)
        embed.set_footer(text=f"User ID: {interaction.user.id} | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        await channel.send(content=f"<@{interaction.user.id}> <@&{OWNER_ROLE_ID}>", embed=embed)
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)

class TicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # persistent view = never expires

    @ui.button(
        label="order here !",
        emoji="<:yellowbread:1283231259878883329>",
        style=discord.ButtonStyle.secondary,
        custom_id="open_ticket_button"  # required for persistent views
    )
    async def order(self, interaction: discord.Interaction, button: ui.Button):
        existing = discord.utils.get(interaction.guild.text_channels, name=f"ticket-{interaction.user.name}")
        if existing:
            await interaction.response.send_message("you already have an open ticket!", ephemeral=True)
        else:
            await interaction.response.send_modal(OrderModal())

@bot.tree.command(name="ticket", description="send the ticket embed in the designated channel")
async def ticket(interaction: discord.Interaction):
    target_channel_id = 1214937578223046686  # replace with your real channel ID
    target_channel = interaction.guild.get_channel(target_channel_id)

    if not target_channel:
        await interaction.response.send_message("Could not find the ticket channel.", ephemeral=True)
        return

    embed = discord.Embed(
        description="click the button below to open your order ticket ♡",
        color=0xFDFD96
    )

    await target_channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("ticket embed sent in the correct channel ♡", ephemeral=True)

@bot.tree.command(name="close", description="Close the current ticket channel and save transcript")
async def close(interaction: discord.Interaction):
    channel = interaction.channel
    log_channel_id = 1394831778337788006  # your transcript log channel
    log_channel = interaction.guild.get_channel(log_channel_id)

    if not channel.name.startswith("ticket-"):
        await interaction.response.send_message("this command can only be used in a ticket channel", ephemeral=True)
        return

    # Send initial response to acknowledge the command
    await interaction.response.send_message("closing ticket and saving transcript...", ephemeral=True)

    try:
        # Fetch last 300 messages in the channel
        messages = [msg async for msg in channel.history(limit=300, oldest_first=True)]

        # Build transcript text
        transcript_lines = []
        for msg in messages:
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            author = f"{msg.author.display_name}#{msg.author.discriminator}"
            content = msg.clean_content
            transcript_lines.append(f"[{timestamp}] {author}: {content}")

        transcript_text = "\n".join(transcript_lines)

        # Create a file-like object
        from io import StringIO
        transcript_file = discord.File(StringIO(transcript_text), filename=f"transcript-{channel.name}.txt")

        # Send transcript to log channel
        await log_channel.send(content=f"transcript for {channel.mention} closed by {interaction.user.mention}", file=transcript_file)

    except Exception as e:
        # If an error occurs, send a follow-up message and abort deletion
        await interaction.followup.send(f"error saving transcript: {e}", ephemeral=True)
        return

    # Delete the ticket channel last
    await channel.delete()

# ========== QUEUE SYSTEM ==========
@bot.tree.command(name="queue", description="Add a new order to the queue")
@app_commands.describe(
    user="Mention the customer",
    payment="Payment method"
)
async def queue_cmd(interaction: discord.Interaction, user: discord.Member, payment: str):
    if OWNER_ROLE_ID not in [role.id for role in interaction.user.roles]:
        await interaction.response.send_message("you don’t have permission to use this", ephemeral=True)
        return

    queue_channel = bot.get_channel(QUEUE_CHANNEL_ID)
    ticket_channel = interaction.channel.mention

    embed = discord.Embed(
        color=0xFDFD96,
        description=(
            f"**<:yellow49:1280655357685006398> order by** {interaction.user.mention}\n"
            f"**<:aayellow:1286493135580430437> ticket:** {ticket_channel}\n"
            f"**<:aayellow:1286493135580430437> user:** {user.mention}\n"
            f"**<:aayellow:1286493135580430437> payment:** {payment}\n"
            f"**<:aayellow:1286493135580430437> order status:** noted\n\n"
            f"-# thanks for your purchase <:06_dotheart:1262479031928885349>"
        )
    )
    embed.set_image(url="https://media.tenor.com/tthHOe_qi9IAAAAi/yellow-heart-pixel-divider.gif")

    await queue_channel.send(embed=embed)
    await interaction.response.send_message("queue entry posted ♡", ephemeral=True)

# ========== GUIDE LINK ============
@bot.tree.command(name="guide", description="Send guide link with bot files.")
async def guide(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)  # Prevent timeout

    attachments = interaction.attachments  # User-uploaded files

    message = (
        "Thank you for buying from aria's comms *!* <a:zumilkhug:1262475999623512154>\n"
        "Here you can find the guide to keep your bot online 24/7: "
        "https://docs.google.com/document/d/19PktPwsZNWRspD9pI_x1Elgy-DYL_A83M7dljiPC57k/edit?usp=sharing\n"
        "You can find your needed files attached to this message."
    )

    if attachments:
        files = []
        for attachment in attachments:
            data = await attachment.read()
            file = discord.File(io.BytesIO(data), filename=attachment.filename)
            files.append(file)

        await interaction.followup.send(content=message, files=files, ephemeral=False)
    else:
        await interaction.followup.send(content=message, ephemeral=False)

# ========== EMBED POSTER ==========
class EmbedModal(ui.Modal, title="Custom Embed"):
    def __init__(self):
        super().__init__()
        self.title_input = ui.TextInput(label="Title", style=discord.TextStyle.short, required=False)
        self.desc_input = ui.TextInput(label="Description", style=discord.TextStyle.paragraph, required=False)
        self.color_input = ui.TextInput(label="Hex Color (e.g. #FDFD96)", default="#FDFD96")
        self.image_input = ui.TextInput(label="Image URL", required=False)
        self.thumb_input = ui.TextInput(label="Thumbnail URL", required=False)

        self.add_item(self.title_input)
        self.add_item(self.desc_input)
        self.add_item(self.color_input)
        self.add_item(self.image_input)
        self.add_item(self.thumb_input)

    async def on_submit(self, interaction: discord.Interaction):
        if OWNER_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("You can’t use this.", ephemeral=True)
            return

        embed = discord.Embed(
            title=self.title_input.value,
            description=self.desc_input.value,
            color=int(self.color_input.value.replace("#", "0x"), 16)
        )
        if self.image_input.value:
            embed.set_image(url=self.image_input.value)
        if self.thumb_input.value:
            embed.set_thumbnail(url=self.thumb_input.value)

        await interaction.response.send_message("Where should I post the embed?", ephemeral=True, view=ChannelSelectView(embed))

class ChannelSelectView(ui.View):
    def __init__(self, embed):
        super().__init__()
        self.embed = embed

    @ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text])
    async def select_channel(self, interaction: discord.Interaction, select: ui.ChannelSelect):
        channel_id = select.values[0].id
        channel = await bot.fetch_channel(channel_id)
        await channel.send(embed=self.embed)
        await interaction.response.send_message(f"Embed posted in {channel.mention}", ephemeral=True)

@bot.tree.command(name="postembed")
async def postembed(interaction: discord.Interaction):
    await interaction.response.send_modal(EmbedModal())

@bot.tree.command(name="pp", description="Get the PayPal link")
async def pp_command(interaction: discord.Interaction):
    await interaction.response.send_message(
        "<:paypal:1396141917372416144> https://www.paypal.com/paypalme/asiatronci\n"
        "-# **send with __fnf only__**\n"
        "-# **tips are appreciated <:06_dotheart:1262479031928885349>**"
    )

# ===== Minimal web server for Render port binding =====
async def handle(request):
    return web.Response(text="Bot is running")

port = int(os.getenv("PORT", 8080))
app = web.Application()
app.add_routes([web.get('/', handle)])

async def main():
    # Start web server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server running on port {port}")

    # Start Discord bot
    await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())



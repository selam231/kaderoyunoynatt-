import os
import discord
from discord.ext import commands
from discord.ui import Button, View
import requests
import random
import string
import json
from flask import Flask
from threading import Thread

# --- MİNİ WEB SUNUCUSU ---
app = Flask('')

@app.route('/')
def home():
    return "🤖 Bot aktif ve ayakta!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# -------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ----------------- AYARLAR -----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
ROBLOX_GROUP_ID = int(os.getenv("ROBLOX_GROUP_ID", "15093066"))
ROBLOSECURITY = os.getenv("ROBLOSECURITY")

WELCOME_CHANNEL_ID = None

pending_verifications = {} 
verified_users = {}        

DATA_FILE = "roblox_users.json"
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r") as f:
            verified_users = json.load(f)
    except Exception:
        verified_users = {}

def save_users():
    with open(DATA_FILE, "w") as f:
        json.dump(verified_users, f, indent=4)
# -------------------------------------------

# ================= BUTONLU FORM SİSTEMİ =================

class FormView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📋 İcraat Formu", style=discord.ButtonStyle.secondary, custom_id="btn_icraat_form")
    async def btn_icraat(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="📋 İCRAAT FORMU", description="Aşağıdaki şablonu kopyalayıp **İcraat Kanalına** doldurarak atabilirsiniz:", color=discord.Color.dark_gray())
        embed.add_field(name="📝 Kopyalanabilir Şablon:", value="```\nİcraati yapan:\nİcraati yapanın rütbesi:\nİcraati:\nKanıtlar:\n```", inline=False)
        embed.set_footer(text="⚓ Su Altı Taarruz Resmi Botu")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📁 Dosya Formu", style=discord.ButtonStyle.secondary, custom_id="btn_dosya_form")
    async def btn_dosya(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="📁 DOSYA FORMU", description="Aşağıdaki şablonu kopyalayıp **Dosya Kanalına** doldurarak atabilirsiniz:", color=discord.Color.dark_gray())
        embed.add_field(name="📝 Kopyalanabilir Şablon:", value="```\nDosyayla ilgilenen:\nDosyayla İlgilenin Rütbesi:\nDosyalananın İsmi:\nDosyalananın Discord İsmi:\nDosyalanma Sebebi:\nDosya Delilleri:\n```", inline=False)
        embed.set_footer(text="⚓ Su Altı Taarruz Resmi Botu")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⚖️ Ceza Formu", style=discord.ButtonStyle.secondary, custom_id="btn_ceza_form")
    async def btn_ceza(self, interaction: discord.Interaction, button: discord.Button):
        embed = discord.Embed(title="⚖️ CEZA FORMU", description="Aşağıdaki şablonu kopyalayıp **Ceza Kanalına** doldurarak atabilirsiniz:", color=discord.Color.dark_gray())
        embed.add_field(name="📝 Kopyalanabilir Şablon:", value="```\nCeza neden:\nCeza veren:\nCeza alan:\nCeza alanın rütbesi:\nCeza verinin rütbesi:\nCeza:\nKanıt:\n```", inline=False)
        embed.set_footer(text="⚓ Su Altı Taarruz Resmi Botu")
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ================= BUTONLU KAYIT SİSTEMİ =================

class KayitModal(discord.ui.Modal, title="🔗 Roblox Hesap Bağlama"):
    roblox_username = discord.ui.TextInput(label="Roblox Kullanıcı Adınız", placeholder="Örn: Ahmet123", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        username = self.roblox_username.value.strip()
        
        req = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]})
        if req.status_code != 200 or not req.json().get("data"):
            await interaction.response.send_message(f"❌ **{username}** adında bir Roblox kullanıcısı bulunamadı!", ephemeral=True)
            return

        user_data = req.json()["data"][0]
        roblox_id = user_data["id"]

        code = "SAT-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        pending_verifications[str(interaction.user.id)] = {"roblox_name": user_data["name"], "roblox_id": roblox_id, "code": code}

        embed_dm = discord.Embed(
            title="🔒 Gizli Roblox Doğrulama Kodu", 
            description=f"Merhaba **{interaction.user.name}**! 🪖\nRoblox hesabını doğrulamak için özel kodun aşağıdadır:\n\n🔑 **Doğrulama Kodun:** **`{code}`**\n\n📌 **Adımlar:**\n1️⃣ Roblox profilindeki **Bio / Hakkımda** kısmına bu kodu yapıştır.\n2️⃣ Profilini kaydettikten sonra sunucudaki **`✅ Hesabı Doğrula`** butonuna bas!", 
            color=discord.Color.dark_gray()
        )
        embed_dm.set_footer(text="⚓ Su Altı Taarruz - Özel Mesaj")

        try:
            await interaction.user.send(embed=embed_dm)
            await interaction.response.send_message("📩 **Doğrulama kodun DM (Özel Mesaj) kutuna gönderildi!** Lütfen kontrol et.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("⚠️ **DM kutun kapalı!** Lütfen gizlilik ayarlarından DM mesajlarını açıp tekrar dene.", ephemeral=True)

class KayitView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔗 Roblox Hesabını Bağla", style=discord.ButtonStyle.primary, custom_id="btn_kaydol")
    async def btn_kaydol_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(KayitModal())

    @discord.ui.button(label="✅ Hesabı Doğrula", style=discord.ButtonStyle.success, custom_id="btn_dogrula")
    async def btn_dogrula_callback(self, interaction: discord.Interaction, button: Button):
        user_id_str = str(interaction.user.id)
        if user_id_str not in pending_verifications:
            await interaction.response.send_message("❌ Önce **`🔗 Roblox Hesabını Bağla`** butonuna basmalısın!", ephemeral=True)
            return

        pending = pending_verifications[user_id_str]
        roblox_id = pending["roblox_id"]
        roblox_name = pending["roblox_name"]
        expected_code = pending["code"]

        res = requests.get(f"https://users.roblox.com/v1/users/{roblox_id}")
        if res.status_code != 200:
            await interaction.response.send_message("❌ Roblox profili çekilemedi.", ephemeral=True)
            return

        bio = res.json().get("description", "")

        if expected_code in bio:
            group_check_url = f"https://groups.roblox.com/v1/users/{roblox_id}/groups/roles"
            group_res = requests.get(group_check_url)
            
            in_group = False
            if group_res.status_code == 200:
                groups_data = group_res.json().get("data", [])
                for g in groups_data:
                    if g.get("group", {}).get("id") == ROBLOX_GROUP_ID:
                        in_group = True
                        break

            guild = interaction.guild
            restricted_role = discord.utils.get(guild.roles, name="Kısıtlı")
            verified_role = discord.utils.get(guild.roles, name="Doğrulandı")

            if not verified_role:
                verified_role = await guild.create_role(name="Doğrulandı", color=discord.Color.green())
            if not restricted_role:
                restricted_role = await guild.create_role(name="Kısıtlı", color=discord.Color.red())

            if not in_group:
                try:
                    await interaction.user.add_roles(restricted_role)
                    if verified_role in interaction.user.roles:
                        await interaction.user.remove_roles(verified_role)
                except Exception:
                    pass
                await interaction.response.send_message("❌ Kodun onaylandı ancak grupta bulunamadın!", ephemeral=True)
                return

            verified_users[user_id_str] = {"roblox_id": roblox_id, "roblox_name": roblox_name}
            save_users()
            del pending_verifications[user_id_str]

            try:
                if restricted_role and restricted_role in interaction.user.roles:
                    await interaction.user.remove_roles(restricted_role)
                if verified_role:
                    await interaction.user.add_roles(verified_role)
            except Exception as e:
                print(f"Rol hatası: {e}")

            try:
                await interaction.user.edit(nick=roblox_name)
            except Exception as e:
                print(f"İsim değiştirme hatası: {e}")

            await interaction.response.send_message(f"🎉 **Tebrikler!** Hesabın başarıyla doğrulandı ve rollerin verildi!", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Kod profil bio'nuzda bulunamadı!", ephemeral=True)

# ================= BOT EVENTS & KOMUTLAR =================

@bot.event
async def on_ready():
    bot.add_view(KayitView())
    bot.add_view(FormView())
    print(f'🤖 Bot {bot.user} olarak giriş yaptı ve göreve hazır!')

@bot.event
async def on_member_join(member):
    global WELCOME_CHANNEL_ID
    
    restricted_role = discord.utils.get(member.guild.roles, name="Kısıtlı")
    if not restricted_role:
        try:
            restricted_role = await member.guild.create_role(name="Kısıtlı", color=discord.Color.red())
        except Exception:
            pass

    if restricted_role:
        try:
            await member.add_roles(restricted_role)
        except Exception:
            pass

    channel = None
    if WELCOME_CHANNEL_ID:
        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    
    if channel is None:
        for ch in member.guild.text_channels:
            if "hoşgeldin" in ch.name.lower() or "welcome" in ch.name.lower() or "giriş" in ch.name.lower():
                channel = ch
                break
                
    if channel is None and member.guild.text_channels:
        channel = member.guild.text_channels[0]

    if channel:
        embed = discord.Embed(title="🎉 Yeni Komandot Katıldı!", description=f"Aramıza hoş geldin {member.mention}! 🪖", color=discord.Color.dark_gray())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="⚓ Su Altı Taarruz Resmi Botu")
        await channel.send(content=f"👋 Hoş geldin {member.mention}!", embed=embed)

@bot.command()
async def form(ctx):
    embed = discord.Embed(title="📑 Su Altı Taarruz - Form Paneli", description="Lütfen almak istediğiniz form butonuna tıklayın. 📋", color=discord.Color.dark_gray())
    embed.set_footer(text="⚓ Su Altı Taarruz Resmi Botu")
    await ctx.send(embed=embed, view=FormView())

@bot.command()
async def şikayet(ctx):
    embed = discord.Embed(title="🚨 Ticket & Şikayet Formları", description="Aşağıdaki şablonları kullanabilirsiniz:", color=discord.Color.dark_gray())
    embed.add_field(name="🎫 DESTEK TICKET", value="```\nİsim:\nSorun:\nSS:\n```", inline=False)
    embed.add_field(name="⚖️ SİKAYET TICKET", value="```\nİsim:\nŞikayet Edilen:\nSS:\n```", inline=False)
    embed.set_footer(text="⚓ Su Altı Taarruz Resmi Botu")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def xmesaj(ctx, *, mesaj: str = None):
    try:
        await ctx.message.delete()
    except Exception:
        pass
    if not mesaj:
        return
    embed = discord.Embed(title="📢 Su Altı Taarruz Duyurusu", description=mesaj, color=discord.Color.dark_gray())
    embed.set_footer(text=f"👮 Yetkili: {ctx.author.name}")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def sil(ctx, amount: int = None):
    if amount is None or amount <= 0:
        return
    await ctx.channel.purge(limit=amount + 1)

@bot.command()
@commands.has_permissions(administrator=True)
async def xxdm(ctx, target_name: str = None, *, mesaj: str = None):
    try:
        await ctx.message.delete()
    except Exception:
        pass
    if not target_name or not mesaj:
        return
    member = discord.utils.find(lambda m: target_name.lower() in m.name.lower(), ctx.guild.members)
    if member:
        await member.send(f"🔒 **Özel Bilgilendirme:** {mesaj}")

@bot.command()
@commands.has_permissions(administrator=True)
async def telsiz(ctx, *, mesaj: str = None):
    try:
        await ctx.message.delete()
    except Exception:
        pass
    if not mesaj:
        return
    embed = discord.Embed(title="🔴 ─── TELSİZ ANONS ───", description=f"📡 **Yayın:** `{ctx.author.name}`\n```{mesaj}```", color=discord.Color.dark_red())
    embed.set_footer(text="⚡ Askeri Haberleşme Sistemi")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def ban(ctx, target_name: str = None, *, sebep: str = "Belirtilmedi"):
    try:
        await ctx.message.delete()
    except Exception:
        pass
    if not target_name:
        return
    member = discord.utils.find(lambda m: target_name.lower() in m.name.lower(), ctx.guild.members)
    if member:
        await member.ban(reason=sebep)
        await ctx.send(f"🔨 **{member.name}** başarıyla uzaklaştırıldı! Sebep: `{sebep}`")

@bot.command()
async def sesgir(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Önce bir ses kanalına girmelisin!", delete_after=5)
        return
    channel = ctx.author.voice.channel
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()
    await ctx.send(f"🔊 Başarıyla **{channel.name}** kanalına giriş yapıldı ve nöbet başlatıldı!", delete_after=5)

@bot.command()
async def xxx222(ctx):
    await ctx.send("⭐ Bot aktif! Yapımcı: **ddontshot_**")

@bot.command(name="help")
async def help_command(ctx, *args):
    await yardım(ctx)

@bot.command()
async def yardım(ctx, *args):
    embed = discord.Embed(title="📖 Su Altı Taarruz - Yardım Menüsü", description="Tüm komutlar aşağıdadır:", color=discord.Color.dark_gray())
    embed.add_field(name="⚙️ Komutlar", value="`!form`, `!şikayet`, `!sesgir`, `!telsiz`, `!sil`, `!ban`, `!xmesaj`", inline=False)
    embed.set_footer(text="⚓ Su Altı Taarruz Resmi Botu")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def kaydolkurulum(ctx, target_channel: discord.TextChannel = None):
    if target_channel is None:
        return
    guild = ctx.guild
    bilgi_msj = await ctx.send("⏳ Kurulum yapılıyor...")

    restricted_role = discord.utils.get(guild.roles, name="Kısıtlı")
    if not restricted_role:
        restricted_role = await guild.create_role(name="Kısıtlı", color=discord.Color.red())

    verified_role = discord.utils.get(guild.roles, name="Doğrulandı")
    if not verified_role:
        verified_role = await guild.create_role(name="Doğrulandı", color=discord.Color.green())

    for m in guild.members:
        if not m.bot and verified_role not in m.roles:
            try:
                await m.add_roles(restricted_role)
            except Exception:
                pass

    for channel in guild.channels:
        if channel.id == target_channel.id:
            await channel.set_permissions(guild.default_role, read_messages=True, send_messages=False)
        else:
            await channel.set_permissions(guild.default_role, read_messages=False)
            await channel.set_permissions(verified_role, read_messages=True)

    try:
        await target_channel.purge(limit=1000)
    except Exception:
        pass

    embed = discord.Embed(title="🛡️ Su Altı Taarruz - Roblox Doğrulama Paneli", description="Hesabınızı bağlamak ve rütbenizi senkronize etmek için aşağıdaki butonları kullanın.", color=discord.Color.dark_gray())
    embed.set_footer(text="⚓ Su Altı Taarruz Resmi Bot Entegrasyonu")
    
    await target_channel.send(embed=embed, view=KayitView())
    await bilgi_msj.edit(content="✅ Kurulum tamamlandı!")

@bot.command()
@commands.has_permissions(administrator=True)
async def kurulum(ctx, target_channel: discord.TextChannel = None):
    global WELCOME_CHANNEL_ID
    if target_channel is None:
        return
    WELCOME_CHANNEL_ID = target_channel.id
    await target_channel.purge(limit=1000)
    await target_channel.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = discord.Embed(title="🎉 Hoşgeldin Kanalı Kuruldu", color=discord.Color.dark_gray())
    await target_channel.send(embed=embed)
    await ctx.send("✅ Kurulum başarılı!")

if __name__ == "__main__":
    keep_alive()
    bot.run(BOT_TOKEN)

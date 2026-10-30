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

# --- MİNİ WEB SUNUCUSU (Render Uyku Modunu Önlemek İçin) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot aktif ve ayakta!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ---------------------------------------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ----------------- GÜVENLİ AYARLAR (Render & GitHub Uyumlu) -----------------
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
# ---------------------------------------------------------------------------

# ================= BUTONLU FORM SİSTEMİ =================

class FormView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📋 İcraat Formu", style=discord.ButtonStyle.secondary, custom_id="btn_icraat_form")
    async def btn_icraat(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="📋 İCRAAT FORMU", description="Aşağıdaki şablonu kopyalayıp **İcraat Kanalına** doldurarak atabilirsiniz:", color=discord.Color.dark_gray())
        embed.add_field(name="📝 Kopyalanabilir Şablon:", value="```\nİcraati yapan:\nİcraati yapanın rütbesi:\nİcraati:\nKanıtlar:\n```", inline=False)
        embed.set_footer(text="Su Altı Taarruz Resmi Botu")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📁 Dosya Formu", style=discord.ButtonStyle.secondary, custom_id="btn_dosya_form")
    async def btn_dosya(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="📁 DOSYA FORMU", description="Aşağıdaki şablonu kopyalayıp **Dosya Kanalına** doldurarak atabilirsiniz:", color=discord.Color.dark_gray())
        embed.add_field(name="📝 Kopyalanabilir Şablon:", value="```\nDosyayla ilgilenen:\nDosyayla İlgilenin Rütbesi:\nDosyalananın İsmi:\nDosyalananın Discord İsmi:\nDosyalanma Sebebi:\nDosya Delilleri:\n```", inline=False)
        embed.set_footer(text="Su Altı Taarruz Resmi Botu")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⚖️ Ceza Formu", style=discord.ButtonStyle.secondary, custom_id="btn_ceza_form")
    async def btn_ceza(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="⚖️ CEZA FORMU", description="Aşağıdaki şablonu kopyalayıp **Ceza Kanalına** doldurarak atabilirsiniz:", color=discord.Color.dark_gray())
        embed.add_field(name="📝 Kopyalanabilir Şablon:", value="```\nCeza neden:\nCeza veren:\nCeza alan:\nCeza alanın rütbesi:\nCeza verinin rütbesi:\nCeza:\nKanıt:\n```", inline=False)
        embed.add_field(name="📌 Not:", value="Not", inline=False)
        embed.set_footer(text="Su Altı Taarruz Resmi Botu")
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

        code = "BTF-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        pending_verifications[str(interaction.user.id)] = {"roblox_name": user_data["name"], "roblox_id": roblox_id, "code": code}

        embed_dm = discord.Embed(
            title="🔒 Gizli Roblox Doğrulama Kodu", 
            description=f"Merhaba **{interaction.user.name}**!\nRoblox hesabını (`{user_data['name']}`) doğrulamak için özel kodun aşağıdadır:\n\n🔑 **Doğrulama Kodun:** **`{code}`**\n\n**Adımlar:**\n1️⃣ Roblox profilindeki **Bio / Hakkımda** kısmına bu kodu yapıştır.\n2️⃣ Profilini kaydettikten sonra kanaldaki **`✅ Hesabı Doğrula`** butonuna bas!", 
            color=discord.Color.dark_gray()
        )
        embed_dm.set_footer(text="Su Altı Taarruz - Özel Mesaj")

        try:
            await interaction.user.send(embed=embed_dm)
            await interaction.response.send_message("📩 **Doğrulama kodun DM (Özel Mesaj) kutuna gönderildi!**\nLütfen DM kutunu kontrol edip kodu Roblox profil bio'na ekledikten sonra **`✅ Hesabı Doğrula`** butonuna bas.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("⚠️ **DM (Özel Mesaj) kutunuz kapalı!** Kodu gönderebilmem için lütfen sunucu gizlilik ayarlarından DM mesajlarını açıp tekrar butona basın.", ephemeral=True)

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
            await interaction.response.send_message("❌ Önce **`🔗 Roblox Hesabını Bağla`** butonuna basarak DM'den kod almalısın!", ephemeral=True)
            return

        pending = pending_verifications[user_id_str]
        roblox_id = pending["roblox_id"]
        roblox_name = pending["roblox_name"]
        expected_code = pending["code"]

        res = requests.get(f"https://users.roblox.com/v1/users/{roblox_id}")
        if res.status_code != 200:
            await interaction.response.send_message("❌ Roblox profili çekilemedi, lütfen tekrar deneyin.", ephemeral=True)
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
            verified_role = discord.utils.get(guild.roles, name="Doğrulandi")

            if not verified_role:
                verified_role = await guild.create_role(name="Doğrulandi", color=discord.Color.green())
            if not restricted_role:
                restricted_role = await guild.create_role(name="Kısıtlı", color=discord.Color.red())

            if not in_group:
                try:
                    await interaction.user.add_roles(restricted_role)
                    if verified_role in interaction.user.roles:
                        await interaction.user.remove_roles(verified_role)
                except Exception:
                    pass
                await interaction.response.send_message(f"❌ Doğrulama kodun onaylandı ancak **BTF - Kara Kuvvetleri İnfaz Timi** grubunda bulunamadın!\nLütfen gruba katıldıktan sonra tekrar dene.", ephemeral=True)
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
                name_status = f" İsminiz sunucuda zorla **{roblox_name}** olarak güncellendi ve tüm kanallar açıldı!"
            except Exception as e:
                print(f"İsim değiştirme hatası: {e}")
                name_status = " (Rollerin verildi ama botun rolü sunucu sahibinin veya yetkili birinin üstünde olmadığı için ismi değiştiremedi)."

            await interaction.response.send_message(f"✅ **Tebrikler!** Discord hesabın **{roblox_name}** Roblox hesabıyla ve grup üyeliğin onaylanarak başarıyla doğrulandı!{name_status}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ DM'den gönderilen kod Roblox profil bio'nuzda bulunamadı!\nBeklenen Kod: **`{expected_code}`**\nLütfen profilinizi güncelleyip tekrar butona basın.", ephemeral=True)

# ================= BOT EVENTS & KOMUTLAR =================

@bot.event
async def on_ready():
    bot.add_view(KayitView())
    bot.add_view(FormView())
    print(f'Bot {bot.user} olarak giriş yaptı ve göreve hazır!')

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
        for ch

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
        for ch in member.guild.text_channels:
            if "hoşgeldin" in ch.name.lower() or "welcome" in ch.name.lower() or "giriş" in ch.name.lower():
                channel = ch
                break
                
    if channel is None and member.guild.text_channels:
        channel = member.guild.text_channels[0]

    if channel:
        embed = discord.Embed(title="🎉 Yeni Üye Katıldı!", description=f"Aramıza hoş geldin {member.mention}!\n\n👤 **Kullanıcı Adı:** `{member.name}`\n🆔 **Discord ID:** `{member.id}`", color=discord.Color.dark_gray())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Su Altı Taarruz Resmi Botu")
        await channel.send(content=f"👋 Hoş geldin {member.mention}!", embed=embed)

@bot.command()
async def form(ctx):
    embed = discord.Embed(title="📑 Su Altı Taarruz - Form Paneli", description="Lütfen almak istediğiniz form butonuna tıklayın. Form şablonu **sadece sizin görebileceğiniz şekilde** açılacaktır.", color=discord.Color.dark_gray())
    embed.set_footer(text="Su Altı Taarruz Resmi Botu")
    await ctx.send(embed=embed, view=FormView())

@bot.command()
async def şikayet(ctx):
    rol_enstitu = discord.utils.get(ctx.guild.roles, name="Güvenlik Enstitüsü")
    rol_baskan = discord.utils.get(ctx.guild.roles, name="Güvenlik Enstitüsü Başkanı")
    
    tag_metin = f"{rol_enstitu.mention if rol_enstitu else '@Güvenlik Enstitüsü'} {rol_baskan.mention if rol_baskan else '@Güvenlik Enstitüsü Başkanı'}"

    embed = discord.Embed(title="🚨 Ticket & Şikayet Formları", description="Aşağıdaki şablonları kopyalarak ilgili kanala iletebilirsiniz:", color=discord.Color.dark_gray())
    
    embed.add_field(name="🎫 DESTEK TİCKETİ", value="```\nİsim:\nSorun:\nSS:\n```", inline=False)
    embed.add_field(name="⚖️ ŞİKAYET TİCKETİ", value="```\nİsim:\nKit Rütbe:\nŞikayet Edilenin İsim:\nKit Rütbesi:\nSS:\n```", inline=False)
    
    embed.add_field(name="📌 Yetkili Etiketleri", value=tag_metin, inline=False)
    embed.set_footer(text="Su Altı Taarruz Resmi Botu")
    
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def xmesaj(ctx, *, mesaj: str = None):
    try:
        await ctx.message.delete()
    except Exception:
        pass

    if not mesaj:
        await ctx.send("❌ Lütfen duyuru metnini yazın! Örnek: `!xmesaj Buraya yazılacak şey`", delete_after=5)
        return

    embed = discord.Embed(title="📢 Su Altı Taarruz Duyurusu", description=mesaj, color=discord.Color.dark_gray())
    embed.set_footer(text=f"Yetkili: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def sil(ctx, amount: int = None):
    if amount is None or amount <= 0:
        await ctx.send("❌ Lütfen silinecek mesaj sayısını girin! Örnek: `!sil 10`", delete_after=5)
        return

    deleted = await ctx.channel.purge(limit=amount + 1)
    confirm_msg = await ctx.send(f"🗑️ **{len(deleted)-1}** adet mesaj başarıyla silindi!")
    await confirm_msg.delete(delay=3)

# ================= GİZLİ DM GÖNDERME KOMUTU (!xxdm) =================

@bot.command()
@commands.has_permissions(administrator=True)
async def xxdm(ctx, target_name: str = None, *, mesaj: str = None):
    try:
        await ctx.message.delete()
    except Exception:
        pass

    if not target_name or not mesaj:
        await ctx.send("❌ Eksik kullanım! Örnek: `!xxdm ahmet123 Merhaba bu gizli bir mesajdır.`", delete_after=5)
        return

    member = discord.utils.find(lambda m: target_name.lower() in m.name.lower() or (m.nick and target_name.lower() in m.nick.lower()), ctx.guild.members)

    if not member:
        await ctx.send(f"❌ **{target_name}** adında bir kullanıcı bu sunucuda bulunamadı!", delete_after=5)
        return

    try:
        embed = discord.Embed(title="🔒 Su Altı Taarruz - Özel Bilgilendirme", description=mesaj, color=discord.Color.dark_gray())
        embed.set_footer(text="Bu mesaj yetkili tarafından gizli olarak gönderilmiştir.")
        await member.send(embed=embed)
    except discord.Forbidden:
        await ctx.send(f"⚠️ **{member.name}** adlı kullanıcının DM (Özel Mesaj) kutusu kapalı, mesaj iletilemedi!", delete_after=6)
    except Exception as e:
        print(f"xxdm hatası: {e}")

# ================= TELSİZ ANONS KOMUTU (!telsiz) =================

@bot.command()
@commands.has_permissions(administrator=True)
async def telsiz(ctx, *, mesaj: str = None):
    try:
        await ctx.message.delete()
    except Exception:
        pass

    if not mesaj:
        temp = await ctx.send("❌ Lütfen telsiz mesajını yazın! Örnek: `!telsiz Bölge güvenli, herkes yerini alsın.`", delete_after=5)
        return

    embed = discord.Embed(
        title="🔴 ─── TELSİZ ANONS - KANAL 1 ───", 
        description=f"📡 **Yayın Yapan Yetkili:** `{ctx.author.name}`\n\n💬 **Mesaj:**\n```{mesaj}```", 
        color=discord.Color.dark_red()
    )
    embed.set_footer(text="Su Altı Taarruz - Askeri Haberleşme Sistemi")
    
    await ctx.send(embed=embed)

# ================= YETKİLİ BAN KOMUTU (!ban) =================

@bot.command()
@commands.has_permissions(administrator=True)
async def ban(ctx, target_name: str = None, *, sebep: str = "Belirtilmedi"):
    try:
        await ctx.message.delete()
    except Exception:
        pass

    if not target_name:
        await ctx.send("❌ Eksik kullanım! Örnek: `!ban ahmet123 Kurallara uymamak`", delete_after=5)
        return

    member = discord.utils.find(lambda m: target_name.lower() in m.name.lower() or (m.nick and target_name.lower() in m.nick.lower()), ctx.guild.members)

    if not member:
        await ctx.send(f"❌ **{target_name}** adında bir kullanıcı bu sunucuda bulunamadı!", delete_after=5)
        return

    try:
        embed_dm = discord.Embed(
            title="🔨 Su Altı Taarruz - Uzaklaştırma (Ban)",
            description=f"Sunucumuzdan kalıcı olarak uzaklaştırıldınız.\n\n🛡️ **Sunucu:** `{ctx.guild.name}`\n📌 **Sebep:** `{sebep}`\n👮 **Yetkili:** `{ctx.author.name}`",
            color=discord.Color.dark_red()
        )
        await member.send(embed_dm)
    except Exception:
        pass

    try:
        await member.ban(reason=sebep)
        embed_log = discord.Embed(
            title="🔨 Askeri İnfaz / Ban İşlemi",
            description=f"👤 **Uzaklaştırılan Üye:** `{member.name}`\n📌 **Sebep:** `{sebep}`\n👮 **İşlemi Yapan Yetkili:** `{ctx.author.name}`",
            color=discord.Color.dark_red()
        )
        embed_log.set_footer(text="Su Altı Taarruz - Disiplin Sistemi")
        await ctx.send(embed=embed_log)
    except Exception as e:
        await ctx.send(f"❌ Ban atılırken bir hata oluştu: {e}", delete_after=6)

# ================= SES KANALINA GİRME KOMUTU (!sesgir) =================

@bot.command()
async def sesgir(ctx):
    if ctx.author.voice and ctx.author.voice.channel:
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(f"🔊 Başarıyla **{channel.name}** ses kanalına giriş yapıldı.", delete_after=5)
    else:
        await ctx.send("❌ Önce bir ses kanalına girmelisin!", delete_after=5)

# ================= SECRET COMMAND (!xxx222) =================

@bot.command()
async def xxx222(ctx):
    await ctx.send("Merhaba botumuz aktiftir ve yürürlülüğe geçmiştir bu botun yapımcısı ddontshot_ dur (SniperX_Shhot) bot hakkında bilgi edinmek için !yardım komutunu kullanabilirsiniz bugları sorunları veya eklemem istediğiniz şeyleri yukarda bıraktığım dc isminden bana ulaşıp iletebilirsiniz Hayırlı Olsun!")

# ================= YARDIM KOMUTLARI (!yardım ve !help) =================

@bot.command(name="help")
async def help_command(ctx, *args):
    await yardım(ctx)

@bot.command()
async def yardım(ctx, *args):
    embed = discord.Embed(title="📖 Su Altı Taarruz - Yardım Menüsü", description="Tüm bot komutları ve ne işe yaradıkları aşağıdadır:", color=discord.Color.dark_gray())
    embed.add_field(name="📑 Form Paneli", value="`!form` - İcraat, Dosya ve Ceza formlarını butonlu özel panel olarak açar.", inline=False)
    embed.add_field(name="🛡️ Yönetim & Kanal Komutları", value="`!sil <miktar>` - Belirtilen sayıda mesajı kanaldan temizler.\n`!kurulum #kanal` - Kanalı kilitler ve otomatik karşılama kanalını ayarlar.\n`!kaydolkurulum #kanal` - 'Kısıtlı' ve 'Doğrulandi' rollerini oluşturur, TÜM kanalları kilitler ve butonlu paneli kurar.\n`!telsiz <mesaj>` - Askeri telsiz frekansından şık telsiz anonsu geçer.\n`!ban <kullanıcı_adı> <sebep>` - Belirtilen kullanıcıyı sebep belirterek banlar.\n`!sesgir` - Bulunduğunuz ses kanalına katılır.", inline=False)
    embed.add_field(name="🚨 Şikayet & Destek", value="`!şikayet` - Destek ve şikayet şablonlarını yetkili etiketleriyle gönderir.", inline=False)
    embed.set_footer(text="Su Altı Taarruz Resmi Botu")
    await ctx.send(embed=embed)

# ====================================================================================

@bot.command()
@commands.has_permissions(administrator=True)
async def kaydolkurulum(ctx, target_channel: discord.TextChannel = None):
    if target_channel is None:
        await ctx.send("❌ Lütfen bir kanal etiketleyin! Örnek: `!kaydolkurulum #kayıt-ol`")
        return

    guild = ctx.guild
    bilgi_msj = await ctx.send(f"⏳ **{target_channel.mention}** ayarlanıyor, roller oluşturuluyor ve sunucu kanalları kilitleniyor...")

    restricted_role = discord.utils.get(guild.roles, name="Kısıtlı")
    if not restricted_role:
        restricted_role = await guild.create_role(name="Kısıtlı", color=discord.Color.red())

    verified_role = discord.utils.get(guild.roles, name="Doğrulandi")
    if not verified_role:
        verified_role = await guild.create_role(name="Doğrulandi", color=discord.Color.green())

    for m in guild.members:
        if not m.bot and verified_role not in m.roles:
            try:
                await m.add_roles(restricted_role)
            except Exception:
                pass

    for channel in guild.channels:
        if channel.id == target_channel.id:
            await channel.set_permissions(guild.default_role, read_messages=True, send_messages=False)
            await channel.set_permissions(restricted_role, read_messages=True, send_messages=False)
            await channel.set_permissions(verified_role, read_messages=True, send_messages=False)
        else:
            await channel.set_permissions(guild.default_role, read_messages=False)
            await channel.set_permissions(restricted_role, read_messages=False)
            await channel.set_permissions(verified_role, read_messages=True)

    try:
        await target_channel.purge(limit=1000)
    except Exception as e:
        print(f"Purge hatası: {e}")

    embed = discord.Embed(title="🛡️ Su Altı Taarruz - Roblox Doğrulama Paneli", description="Aramıza hoş geldiniz! Sunucuya erişim sağlamak ve Roblox gruptaki rütbenizi senkronize etmek için hesabınızı bağlamanız gerekmektedir.\n\n**Adımlar:**\n1️⃣ Aşağıdaki **`🔗 Roblox Hesabını Bağla`** butonuna basın ve Roblox kullanıcı adınızı girin.\n2️⃣ Botun size **Özel Mesaj (DM)** üzerinden gönderdiği kodu Roblox profilinizin **Bio / Hakkımda** kısmına ekleyin.\n3️⃣ Profilinizi kaydettikten sonra **`✅ Hesabı Doğrula`** butonuna basarak işleminizi tamamlayın!", color=discord.Color.dark_gray())
    embed.set_footer(text="Su Altı Taarruz Resmi Bot Entegrasyonu")

    await target_channel.send(embed=embed, view=KayitView())
    await bilgi_msj.edit(content=f"✅ **{target_channel.mention}** kuruldu! Kayıt kanalı dışındaki **tüm sunucu kanalları kilitlendi** ve doğrulama sonrası erişilebilir hale getirildi!")

@bot.command()
@commands.has_permissions(administrator=True)
async def kurulum(ctx, target_channel: discord.TextChannel = None):
    global WELCOME_CHANNEL_ID
    if target_channel is None:
        await ctx.send("❌ Lütfen bir kanal etiketleyin! Örnek: `!kurulum #hoşgeldin`")
        return

    WELCOME_CHANNEL_ID = target_channel.id
    bilgi_msj = await ctx.send(f"⏳ **{target_channel.mention}** kanalı temizleniyor ve kilitleniyor...")

    try:
        await target_channel.purge(limit=1000)
    except Exception as e:
        print(f"Mesaj silme hatası: {e}")

    await target_channel.set_permissions(ctx.guild.default_role, send_messages=False)

    members = [m for m in ctx.guild.members if not m.bot]
    user_info_list = "\n".join([f"👤 **{m.name}** (`{m.id}`)" for m in members[:25]])

    embed = discord.Embed(title="🎉 Hoşgeldin!", description=f"Sunucumuza hoş geldiniz! Bu kanal kilitlenmiştir.\n\n**Mevcut Üye Listesi:**\n{user_info_list}", color=discord.Color.dark_gray())
    embed.set_footer(text="Su Altı Taarruz Resmi Botu")
    await target_channel.send(embed=embed)
    await bilgi_msj.edit(content=f"✅ **{target_channel.mention}** kanalı kuruldu ve otomatik karşılama aktif edildi!")

# Botu ve web sunucusunu aynı anda çalıştırıyoruz
if __name__ == "__main__":
    keep_alive()
    bot.run(BOT_TOKEN)

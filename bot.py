import asyncio
import os
import json
from datetime import datetime
from aiohttp import web
from highrise import BaseBot, __main__, User, Position
from highrise.__main__ import BotDefinition

# ==========================================
# 1. AYARLAR HR 10 BOT 
# ==========================================
ODA_ID = "6a6aef24bab5b4c876afeefe"
SAHIP_KULLANICI_ADI = "llzeyrox"  # Küçük harfle kendi Highrise kullanıcı adın
PANEL_SIFRESI = "1234"                # Web paneline giriş şifren

# 10 Botun Token Listesi (1. sıradaki bot Ana Şef ve Kayıt Botu olur)
BOT_TOKENLERI = [
"TRB_CHAT_61=4bc4174223619abecb334249042e5da59c853c265e68ab5a0777e037ad78a588"

"TRB_GAME_61=dd4870a763600157c7be80227f615ec01e249166eb506f28d05277d45b855544"

"TRB_BRAIN_61=163d5489bb0197af180e655f7e84dcc24d26b3d16f86c4f589d254b85fd0de33"

"TRB_EMOTE_61=c3e8be5ceada5a49c98af88bad1b299dbbde7bf3a95c235be3789b2054413d3e"

"TRB_MUSIC_61=11ad74d4fd757f2616a88e8959f0c743eaaa44a259a873f9d578185e1067387c"

"TRB_EVENT_61=9d4847b5a94a9eda60027f4cbc211e70de5965302721d6355ed04802673b634d"

"TRB_SOCIAL_61=de67e07ab3c673e547885c3b0376819b25504ca8223b29ebc98d611ae4a59a1f"

"TRB_ECONOMY_61=ea6d1f79b6b7d1227b3fe3b1fb70ce3967065c325695496f410e23cf977cd37b"

"TRB_61_AFK=8610da686bbfc7da7460d58db007a0d0e74a82319451dc8346211c4096c54304"

"ADMINHARD_61 38ab255e76effff5e995369da425a56bac4658da24ac6a3b833a563e4f0ce37f"
]

# Yasaklı Kelimeler Listesi (İstediğin kelimeleri virgülle ekleyebilirsin)
KOTU_SOZLER = [
    "amk", "aq", "oç", "piç", "siktir", "orospu", "yavşak", "göt", "mal", "salak"
]

# ==========================================
# 2. KAYIT VE KARALİSTE HAFIZASI
# ==========================================
GUNLUK_SOHBET = []   # Odadaki konuşmalar ve giriş-çıkışlar
KARALISTE = {}       # Küfür edenler ve yasaklılar

def saat_al():
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")

def sohbet_ekle(metin):
    GUNLUK_SOHBET.append(f"[{saat_al()}] {metin}")
    if len(GUNLUK_SOHBET) > 500:  # Son 500 kaydı hafızada tutar
        GUNLUK_SOHBET.pop(0)

# ==========================================
# 3. HIGHRISE BOT SINIFI
# ==========================================
class KapsamliBot(BaseBot):
    def __init__(self, bot_no: int):
        super().__init__()
        self.bot_no = bot_no
        self.ana_bot_mu = (bot_no == 1)  # Sadece 1. bot kayıt tutar

    async def on_start(self, session_metadata) -> None:
        print(f"✅ Bot #{self.bot_no} odaya başarıyla bağlandı!")
        if self.ana_bot_mu:
            sohbet_ekle("🟢 SİSTEM BAŞLATILDI: 10 Botluk ekip odaya giriş yaptı.")
        # Botların odada üst üste binmemesi için hafif yan yana dizilme
        try:
            await self.highrise.walk_to(Position(x=float(self.bot_no), y=0.0, z=float(self.bot_no % 3)))
        except Exception:
            pass

    async def on_user_join(self, user: User, position: Position) -> None:
        if not self.ana_bot_mu:
            return
        sohbet_ekle(f"➡️ GİRİŞ: @{user.username} odaya katıldı.")
        
        # Karaliste Kontrolü
        if user.username.lower() in KARALISTE:
            bilgi = KARALISTE[user.username.lower()]
            sohbet_ekle(f"🚨 ALARM: Karalistedeki @{user.username} odaya girdi! (Sebep: {bilgi['sebep']})")
            try:
                await self.highrise.chat(f"⚠️ Uyarı: @{user.username} karalistede bulunuyor!")
            except Exception:
                pass

    async def on_user_leave(self, user: User) -> None:
        if self.ana_bot_mu:
            sohbet_ekle(f"⬅️ ÇIKIŞ: @{user.username} odadan ayrıldı.")

    async def on_chat(self, user: User, message: str) -> None:
        mesaj_kucuk = message.lower().strip()

        # Sadece 1. Bot (Ana Şef) sohbeti kaydeder ve kötü söz kontrolü yapar
        if self.ana_bot_mu:
            sohbet_ekle(f"💬 @{user.username}: {message}")

            # Kötü söz taraması
            bulunan_kufur = next((kelime for kelime in KOTU_SOZLER if kelime in mesaj_kucuk), None)
            if bulunan_kufur and user.username.lower() != SAHIP_KULLANICI_ADI.lower():
                KARALISTE[user.username.lower()] = {
                    "nick": user.username,
                    "id": user.id,
                    "sebep": f"Yasaklı kelime ({bulunan_kufur}) - Cümle: '{message}'",
                    "tarih": saat_al()
                }
                sohbet_ekle(f"⛔ KARALİSTE: @{user.username} kötü söz nedeniyle karalisteye alındı!")
                try:
                    await self.highrise.chat(f"🚫 @{user.username} uygunsuz dil nedeniyle karalisteye eklendi!")
                except Exception:
                    pass

        # Yönetici Komutları (Sadece sen yazdığında çalışır)
        if user.username.lower() == SAHIP_KULLANICI_ADI.lower():
            if mesaj_kucuk == "!dans":
                try:
                    await self.highrise.send_emote("emote-dance-macarena")
                except Exception:
                    pass
            elif mesaj_kucuk == "!karaliste" and self.ana_bot_mu:
                if not KARALISTE:
                    await self.highrise.chat("✅ Karaliste şu an tamamen temiz.")
                else:
                    isimler = ", ".join([v["nick"] for v in KARALISTE.values()])
                    await self.highrise.chat(f"⛔ Karalistedekiler ({len(KARALISTE)}): {isimler}")
            elif mesaj_kucuk.startswith("!temizle ") and self.ana_bot_mu:
                hedef = mesaj_kucuk.replace("!temizle ", "").replace("@", "").strip()
                if hedef in KARALISTE:
                    del KARALISTE[hedef]
                    sohbet_ekle(f"♻️ @{hedef} yönetici tarafından karalisteden çıkarıldı.")
                    await self.highrise.chat(f"✅ @{hedef} karalisteden silindi.")

# ==========================================
# 4. CANLI WEB PANELİ (RENDER 7/24 KORUMASI)
# ==========================================
async def web_ana_sayfa(request):
    sifre = request.query.get("sifre", "")
    if sifre != PANEL_SIFRESI:
        html_giris = """
        <html><body style="font-family:sans-serif;background:#111;color:#fff;text-align:center;padding-top:80px;">
        <h2>🔒 Highrise 10 Bot Canlı Takip Paneli</h2>
        <form method="get">
            <input type="password" name="sifre" placeholder="Panel Şifresi" style="padding:10px;border-radius:5px;">
            <button type="submit" style="padding:10px 20px;background:#28a745;color:white;border:none;border-radius:5px;">Giriş Yap</button>
        </form></body></html>
        """
        return web.Response(text=html_giris, content_type="text/html")

    sohbet_html = "<br>".join(reversed(GUNLUK_SOHBET)) if GUNLUK_SOHBET else "Henüz kayıt yok..."
    karaliste_html = ""
    for k, v in KARALISTE.items():
        karaliste_html += f"<div style='background:#3a1515;padding:10px;margin:5px 0;border-left:4px solid red;'><b>@{v['nick']}</b> ({v['tarih']})<br><small>{v['sebep']}</small></div>"
    if not karaliste_html:
        karaliste_html = "<p style='color:#4caf50;'>Karalistede kimse yok.</p>"

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="10">
        <title>Highrise Canlı Panel</title>
    </head>
    <body style="font-family:sans-serif;background:#121212;color:#eee;padding:20px;max-width:900px;margin:auto;">
        <h2>🤖 Highrise 10 Bot Canlı Kontrol & Günlük Paneli</h2>
        <p style="color:#aaa;">Sayfa her 10 saniyede bir otomatik yenilenir. | Oda ID: <b>{ODA_ID}</b></p>
        
        <h3 style="color:#ff5252;">⛔ Karaliste ({len(KARALISTE)} Kişi)</h3>
        {karaliste_html}
        
        <h3 style="color:#4fc3f7;margin-top:30px;">📜 Canlı Oda Sohbeti ve Giriş-Çıkış Günlüğü</h3>
        <div style="background:#1e1e1e;padding:15px;border-radius:8px;height:400px;overflow-y:scroll;line-height:1.6;">
            {sohbet_html}
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")

async def web_sunucusunu_baslat():
    app = web.Application()
    app.router.add_get("/", web_ana_sayfa)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Canlı Web Paneli aktif! Port: {port}")

# ==========================================
# 5. ANA ÇALIŞTIRICI (KADEMELİ & ÖLÜMSÜZ MOTOR)
# ==========================================
async def tek_bot_calistir(bot_no: int, token: str, gecikme: int):
    await asyncio.sleep(gecikme)  # IP engeli yememek için 3'er saniye arayla giriş
    while True:
        try:
            bot_instance = KapsamliBot(bot_no=bot_no)
            tanim = [BotDefinition(bot_instance, ODA_ID, token)]
            await __main__.main(tanim)
        except Exception as hata:
            print(f"⚠️ Bot #{bot_no} bağlantısı koptu ({hata}). 10 saniye sonra tekrar bağlanıyor...")
            await asyncio.sleep(10)

async def main():
    await web_sunucusunu_baslat()
    
    gorevler = []
    for index, token in enumerate(BOT_TOKENLERI, start=1):
        if token and not token.startswith("BURAYA_"):
            # Her bot 3 saniye arayla sıraya girer (0s, 3s, 6s...)
            gorevler.append(asyncio.create_task(tek_bot_calistir(index, token, (index - 1) * 3)))
    
    if not gorevler:
        print("⚠️ HATA: Lütfen BOT_TOKENLERI listesine en az 1 geçerli token ekleyin!")
        while True:
            await asyncio.sleep(60)
    else:
        print(f"🚀 Toplam {len(gorevler)} bot kademeli olarak başlatılıyor...")
        await asyncio.gather(*gorevler)

if __name__ == "__main__":
    asyncio.run(main())

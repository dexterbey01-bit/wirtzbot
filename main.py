from flask import Flask from threading import Thread import requests import time import logging from telegram import Bot import os

--- BOT AYARLARI ---

BOT_TOKEN = os.environ.get("BOT_TOKEN") CHAT_IDS = ["1400011317", "-1002740055071"]

--- API AYARLARI ---

API_KEY = os.environ.get("API_KEY") API_HOST = "api-football-v1.p.rapidapi.com"

bot = Bot(token=BOT_TOKEN) app = Flask('')

@app.route('/') def home(): return "Bot çalışıyor!"

def run(): app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

gönderilen_maclar = set() takip_edilen_maclar = {} logging.basicConfig(level=logging.INFO)

def api_football_canli_maclar(): url = "https://api-football-v1.p.rapidapi.com/v3/fixtures?live=all" headers = { "X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": API_HOST } try: res = requests.get(url, headers=headers, timeout=15) res.raise_for_status() return res.json().get("response", []) except Exception as e: logging.error(f"API-Football verisi alınamadı: {e}") return []

def istatistik_getir(match_id): url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/statistics?fixture={match_id}" headers = { "X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": API_HOST } try: res = requests.get(url, headers=headers, timeout=10) res.raise_for_status() return res.json().get("response", []) except Exception as e: logging.error(f"İstatistik verisi alınamadı (match_id={match_id}): {e}") return []

def bahis_sonucu_gonder(ev_sahibi, misafir, dakika, skor, bahis, bahis_sonucu): mesaj = f"{'🎉' if bahis_sonucu == 'Tuttu' else '❌'} Bahis Sonucu:\n\n" 
f"🏆 Maç: {ev_sahibi} vs {misafir}\n" 
f"⏱️ Dakika: {dakika}\n" 
f"⚽ Skor: {skor}\n\n" 
f"💥 Bahis: {bahis}\n" 
f"{'✅ Bahis Tuttu! Tebrikler!' if bahis_sonucu == 'Tuttu' else '❌ Bahis Yattı.'}" for chat_id in CHAT_IDS: try: bot.send_message(chat_id=chat_id, text=mesaj, parse_mode='Markdown') except Exception as e: logging.error(f"Telegram mesaj gönderme hatası: {e}")

def maclari_sec_ve_gonder(): maclar = api_football_canli_maclar() logging.info(f"Toplam {len(maclar)} canlı maç bulundu.") adaylar = [] for mac in maclar: match_id = mac['fixture']['id'] dakika = mac['fixture']['status']['elapsed'] or 0 if match_id in gönderilen_maclar or not (5 <= dakika <= 25): continue ev = mac['teams']['home']['name'] dep = mac['teams']['away']['name'] ev_skor = mac['goals']['home'] dep_skor = mac['goals']['away'] skor = f"{ev_skor} - {dep_skor}" stats_data = istatistik_getir(match_id) toplam_sut = 0 isabetli_sut = 0 toplam_korner = 0 for team in stats_data: for stat in team.get("statistics", []): if stat['type'] == 'Shots on Goal' and stat['value']: isabetli_sut += int(stat['value']) if stat['type'] == 'Total Shots' and stat['value']: toplam_sut += int(stat['value']) if stat['type'] == 'Corner Kicks' and stat['value']: toplam_korner += int(stat['value']) logging.info(f"{ev} vs {dep} | Dakika: {dakika} | Skor: {skor} | Şut: {toplam_sut} | İsabetli: {isabetli_sut} | Korner: {toplam_korner}") if toplam_sut >= 3 and isabetli_sut >= 1: adaylar.append((dakika, match_id, mac)) adaylar.sort(key=lambda x: x[0]) secilenler = adaylar[:3] for dakika, match_id, mac in secilenler: ev = mac['teams']['home']['name'] dep = mac['teams']['away']['name'] ev_skor = mac['goals']['home'] dep_skor = mac['goals']['away'] skor = f"{ev_skor} - {dep_skor}" bahis = "İlk Yarı 0.5 Üst" bahis_sonucu = "Tuttu" bahis_sonucu_gonder(ev, dep, dakika, skor, bahis, bahis_sonucu) gönderilen_maclar.add(match_id) takip_edilen_maclar[match_id] = {'gol': False}

def gol_takip_et(): maclar = api_football_canli_maclar() for mac in maclar: match_id = mac['fixture']['id'] if match_id not in takip_edilen_maclar: continue ev_skor = mac['goals']['home'] dep_skor = mac['goals']['away'] dakika = mac['fixture']['status']['elapsed'] or 0 ev = mac['teams']['home']['name'] dep = mac['teams']['away']['name'] if (ev_skor > 0 or dep_skor > 0) and not takip_edilen_maclar[match_id]['gol']: mesaj = f"✅ GOL GELDİ!\n{ev} vs {dep}\n⚽ Skor: {ev_skor}-{dep_skor} ⏱️ {dakika}.dk" for chat_id in CHAT_IDS: bot.send_message(chat_id=chat_id, text=mesaj, parse_mode='Markdown') takip_edilen_maclar[match_id]['gol'] = True if dakika >= 45 and not takip_edilen_maclar[match_id]['gol']: mesaj = f"❌ İlk Yarı Gol Gelmedi\n{ev} vs {dep}\n⏱️ {dakika}.dk - Skor: {ev_skor}-{dep_skor}" for chat_id in CHAT_IDS: bot.send_message(chat_id=chat_id, text=mesaj, parse_mode='Markdown') takip_edilen_maclar[match_id]['gol'] = True

if name == "main": while True: try: logging.info("Bot döngüsü başladı.") maclari_sec_ve_gonder() gol_takip_et() except Exception as e: logging.error(f"Hata: {e}") time.sleep(300)
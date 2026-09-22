import os
import json
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# --- 1. Render 호스팅 유지용 웹 서버 (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "포인트 목표 봇이 정상 작동 중입니다!"

def run():
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ---------------------------------------------

# --- 2. 데이터 저장 및 로드 설정 (JSON) ---
DATA_DIR = '/data' if os.environ.get('RENDER') else './data'
FILE_PATH = os.path.join(DATA_DIR, 'points.json')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

data = {
    "goal_title": "기본 목표",
    "goal_point": 0,
    "current_point": 0
}

def load_data():
    global data
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "goal_title" not in data:
                    data["goal_title"] = "기본 목표"
                print("💾 데이터를 성공적으로 불러왔습니다:", data)
        except Exception as e:
            print(f"❌ 데이터 로드 오류: {e}")
    else:
        save_data()

def save_data():
    try:
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            print("💾 데이터가 안전하게 저장되었습니다.")
    except Exception as e:
        print(f"❌ 데이터 저장 오류: {e}")
# ---------------------------------------------

# --- 3. 디스코드 봇 설정 ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} 봇이 준비되었습니다!')
    load_data()

# 1. 목표 설정 명령어 (!목표설정 [숫자] [목표 제목])
@bot.command(name='목표설정')
async def set_goal(ctx, target: int = None, *, title: str = None):
    if target is None or target <= 0:
        await ctx.reply('❌ 올바른 목표 포인트를 숫자로 입력해주세요. (예: !목표설정 1000 서버 활성화)')
        return
        
    if title is None:
        title = "현재 진행 중인 목표"
        
    data["goal_point"] = target
    data["goal_title"] = title
    save_data()
    await ctx.reply(f'🎯 목표 **[{title}]**의 목표 포인트가 **{target:,}**으로 설정되었습니다!')

# 2. 포인트 명령어 (!포인트 또는 !포인트 [숫자])
@bot.command(name='포인트')
async def manage_points(ctx, amount: int = None):
    if data["goal_point"] == 0:
        await ctx.reply('📢 먼저 `!목표설정 [숫자] [제목]` 명령어로 목표를 설정해주세요!')
        return

    if amount is None:
        await ctx.reply(f'📋 **목표: {data["goal_title"]}**\n📌 현재 포인트는 **{data["current_point"]:,} / {data["goal_point"]:,}** 입니다.')
        return

    if amount <= 0:
        await ctx.reply('❌ 추가할 포인트는 1점 이상이어야 합니다.')
        return

    data["current_point"] += amount
    save_data()

    response = f'✨ **{amount:,} 포인트**가 적립되었습니다!\n📋 **목표: {data["goal_title"]}** ({data["current_point"]:,} / {data["goal_point"]:,})'
    
    if data["current_point"] >= data["goal_point"]:
        response += f'\n\n🎉 **축하합니다! 설정한 목표 [{data["goal_title"]}] ({data["goal_point"]:,})를 달성했습니다!** 🥳'

    await ctx.reply(response)

# --- 4. 실행 ---
keep_alive()
bot.run(os.environ.get('DISCORD_TOKEN'))
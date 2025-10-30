# streamlit_war_game_ultimate.py
import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random

st.set_page_config(page_title="Ultimate Soldier War Game", layout="wide")

TILE_SIZE = 40
VIEW_RANGE = 3  # player visible range
FONT = ImageFont.load_default()

# -------------------- Generate Tile Images --------------------
def create_tile(color, pattern=None):
    img = Image.new("RGBA", (TILE_SIZE, TILE_SIZE), color)
    draw = ImageDraw.Draw(img)
    if pattern == "trench":
        for i in range(0, TILE_SIZE, 4):
            draw.line([(0,i),(TILE_SIZE,i)], fill=(80,80,80))
    if pattern == "hill":
        draw.ellipse([5,5,TILE_SIZE-5,TILE_SIZE-5], fill=(0,100,0))
    return img

tiles = {
    'ground': create_tile((139,69,19,255)),
    'trench': create_tile((105,105,105,255), pattern='trench'),
    'hill': create_tile((34,139,34,255), pattern='hill'),
    'player': create_tile((0,0,255,255)),
    'enemy': create_tile((255,0,0,255))
}

# -------------------- Initialize Game State --------------------
MAP_WIDTH, MAP_HEIGHT = 15, 12
TERRAIN_TYPES = ['ground', 'trench', 'hill']

if 'map' not in st.session_state:
    st.session_state['map'] = np.random.choice(TERRAIN_TYPES, (MAP_HEIGHT, MAP_WIDTH))

if 'player_pos' not in st.session_state:
    st.session_state['player_pos'] = (1,1)

if 'player_hp' not in st.session_state:
    st.session_state['player_hp'] = 20
    st.session_state['player_max_hp'] = 20
    st.session_state['player_atk'] = 5

if 'enemies' not in st.session_state:
    st.session_state['enemies'] = [
        {'pos': (MAP_HEIGHT-2, MAP_WIDTH-2), 'hp': 12, 'atk': 4, 'alive': True},
        {'pos': (MAP_HEIGHT-3, MAP_WIDTH-5), 'hp': 10, 'atk': 3, 'alive': True},
        {'pos': (2, MAP_WIDTH-3), 'hp': 8, 'atk': 2, 'alive': True}
    ]

if 'quests' not in st.session_state:
    st.session_state['quests'] = [
        {'pos': (3,3), 'desc': 'Recover supply crate', 'reward': 'hp+5', 'completed': False},
        {'pos': (7,6), 'desc': 'Rescue ally', 'reward': 'atk+1', 'completed': False}
    ]

if 'log' not in st.session_state:
    st.session_state['log'] = ["Ultimate Soldier War Game started!"]

# -------------------- Functions --------------------
def draw_map():
    full_map = Image.new('RGBA', (MAP_WIDTH*TILE_SIZE, MAP_HEIGHT*TILE_SIZE))
    px, py = st.session_state['player_pos']

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            # field-of-view
            if abs(x-px) > VIEW_RANGE or abs(y-py) > VIEW_RANGE:
                tile_img = create_tile((0,0,0,255))  # unseen
            else:
                terrain = st.session_state['map'][y,x]
                tile_img = tiles[terrain]
            full_map.paste(tile_img, (x*TILE_SIZE, y*TILE_SIZE))

    # draw quests
    for q in st.session_state['quests']:
        qx,qy = q['pos']
        if not q['completed'] and abs(qx-px)<=VIEW_RANGE and abs(qy-py)<=VIEW_RANGE:
            quest_img = create_tile((255,255,0,255))
            full_map.paste(quest_img, (qx*TILE_SIZE, qy*TILE_SIZE))

    # draw enemies with health bars
    for e in st.session_state['enemies']:
        if e['alive']:
            ex,ey = e['pos'][1], e['pos'][0]
            if abs(ex-px)<=VIEW_RANGE and abs(ey-py)<=VIEW_RANGE:
                full_map.paste(tiles['enemy'], (ex*TILE_SIZE, ey*TILE_SIZE), tiles['enemy'])
                draw = ImageDraw.Draw(full_map)
                hp_ratio = e['hp']/10
                draw.rectangle([ex*TILE_SIZE, ey*TILE_SIZE-5, ex*TILE_SIZE+int(TILE_SIZE*hp_ratio), ey*TILE_SIZE-2], fill=(255,0,0))

    # draw player with health bar
    full_map.paste(tiles['player'], (px*TILE_SIZE, py*TILE_SIZE), tiles['player'])
    draw = ImageDraw.Draw(full_map)
    hp_ratio = st.session_state['player_hp']/st.session_state['player_max_hp']
    draw.rectangle([px*TILE_SIZE, py*TILE_SIZE-5, px*TILE_SIZE+int(TILE_SIZE*hp_ratio), py*TILE_SIZE-2], fill=(0,0,255))

    st.image(full_map)

def move_player(dy, dx):
    py, px = st.session_state['player_pos']
    ny, nx = py + dy, px + dx
    if 0<=ny<MAP_HEIGHT and 0<=nx<MAP_WIDTH:
        # check enemy blocking
        if any(e['alive'] and e['pos']==(ny,nx) for e in st.session_state['enemies']):
            st.session_state['log'].append("Enemy blocks your path!")
        else:
            st.session_state['player_pos'] = (ny,nx)
            check_quests()

def check_quests():
    py, px = st.session_state['player_pos']
    for q in st.session_state['quests']:
        if not q['completed'] and q['pos']==(px,py):
            q['completed']=True
            st.session_state['log'].append(f"Quest completed: {q['desc']} Reward: {q['reward']}")
            apply_reward(q['reward'])

def apply_reward(reward):
    if 'hp' in reward:
        st.session_state['player_hp'] = min(st.session_state['player_max_hp'], st.session_state['player_hp']+5)
    if 'atk' in reward:
        st.session_state['player_atk'] += 1

def attack():
    px, py = st.session_state['player_pos']
    for e in st.session_state['enemies']:
        ey, ex = e['pos']
        if e['alive'] and abs(px-ex)+abs(py-ey)<=1:
            bonus = 1
            terrain = st.session_state['map'][ey,ex]
            if terrain=='hill':
                bonus=2  # extra attack from hill
            damage = st.session_state['player_atk'] + bonus
            if terrain=='trench':
                damage = max(damage-1,1)  # trench reduces damage
            e['hp'] -= damage
            if e['hp']<=0:
                e['alive']=False
                st.session_state['log'].append("Enemy killed!")
            else:
                st.session_state['log'].append(f"Hit enemy! Enemy HP: {e['hp']}")
            return
    st.session_state['log'].append("No enemy in range!")

def enemy_turn():
    px, py = st.session_state['player_pos']
    for e in st.session_state['enemies']:
        if e['alive']:
            ey, ex = e['pos']
            if abs(px-ex)+abs(py-ey)<=1:
                # enemy attack
                terrain = st.session_state['map'][py,px]
                bonus = 0
                if terrain=='trench':
                    bonus=-1  # player protected
                st.session_state['player_hp'] -= max(e['atk']+bonus,1)
                st.session_state['log'].append(f"Enemy hits you! Your HP: {st.session_state['player_hp']}")
            else:
                dx = 1 if px>ex else -1 if px<ex else 0
                dy = 1 if py>ey else -1 if py<ey else 0
                new_pos=(ey+dy,ex+dx)
                if 0<=new_pos[0]<MAP_HEIGHT and 0<=new_pos[1]<MAP_WIDTH:
                    if not any(oe['alive'] and oe['pos']==new_pos for oe in st.session_state['enemies']):
                        e['pos']=new_pos

def check_game_over():
    if st.session_state['player_hp']<=0:
        st.error("You died! Game over.")
        return True
    elif all(not e['alive'] for e in st.session_state['enemies']):
        st.success("All enemies defeated! Victory!")
        return True
    return False

# -------------------- UI --------------------
st.title("🪖 Ultimate Soldier War Game")

draw_map()
st.subheader(f"Player HP: {st.session_state['player_hp']}  ATK: {st.session_state['player_atk']}")

st.subheader("Controls: WASD to move, Space to attack")
key = st.text_input("Enter keys:")

if key:
    key = key.lower()
    if 'w' in key: move_player(-1,0)
    if 's' in key: move_player(1,0)
    if 'a' in key: move_player(0,-1)
    if 'd' in key: move_player(0,1)
    if ' ' in key: attack()
    enemy_turn()
    st.experimental_rerun()

st.subheader("Quests")
for q in st.session_state['quests']:
    status = '✅' if q['completed'] else '📍'
    st.write(f"{q['desc']} {status}")

st.subheader("Battle Log")
for l in st.session_state['log'][-10:]:
    st.write(l)

check_game_over()


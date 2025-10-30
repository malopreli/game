# streamlit_war_game_full.py
import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
import random

st.set_page_config(page_title="Soldier War Game", layout="wide")

TILE_SIZE = 32
VIEW_RANGE = 3  # visibility around player

# -------------------- Generate Tile Images --------------------
def create_tile(color):
    img = Image.new("RGBA", (TILE_SIZE, TILE_SIZE), color)
    draw = ImageDraw.Draw(img)
    return img

tiles = {
    'ground': create_tile((139,69,19,255)),      # brown dirt
    'trench': create_tile((105,105,105,255)),    # grey trench
    'hill': create_tile((34,139,34,255)),        # green hill
    'player': create_tile((0,0,255,255)),        # blue soldier
    'enemy': create_tile((255,0,0,255))          # red enemy
}

# -------------------- Initialize Game State --------------------
MAP_WIDTH, MAP_HEIGHT = 15, 10
TERRAIN_TYPES = ['ground', 'trench', 'hill']

if 'map' not in st.session_state:
    st.session_state['map'] = np.random.choice(TERRAIN_TYPES, (MAP_HEIGHT, MAP_WIDTH))

if 'player_pos' not in st.session_state:
    st.session_state['player_pos'] = (1, 1)

if 'player_hp' not in st.session_state:
    st.session_state['player_hp'] = 20
    st.session_state['player_max_hp'] = 20
    st.session_state['player_atk'] = 5

if 'enemies' not in st.session_state:
    st.session_state['enemies'] = [
        {'pos': (MAP_HEIGHT-2, MAP_WIDTH-2), 'hp': 10, 'atk': 3, 'alive': True},
        {'pos': (MAP_HEIGHT-3, MAP_WIDTH-5), 'hp': 12, 'atk': 4, 'alive': True}
    ]

if 'quests' not in st.session_state:
    st.session_state['quests'] = [
        {'pos': (3,3), 'desc': 'Recover supply crate', 'reward': 'hp+5', 'completed': False},
        {'pos': (7,6), 'desc': 'Rescue ally', 'reward': 'atk+1', 'completed': False}
    ]

if 'log' not in st.session_state:
    st.session_state['log'] = ["Game started!"]

# -------------------- Functions --------------------
def draw_map():
    full_map = Image.new('RGBA', (MAP_WIDTH*TILE_SIZE, MAP_HEIGHT*TILE_SIZE))
    px, py = st.session_state['player_pos']
    
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            # apply field-of-view
            if abs(x-px) > VIEW_RANGE or abs(y-py) > VIEW_RANGE:
                tile_img = create_tile((0,0,0,255))  # unseen area black
            else:
                tile_img = tiles[st.session_state['map'][y, x]]
            
            full_map.paste(tile_img, (x*TILE_SIZE, y*TILE_SIZE))
    
    # draw quests
    for q in st.session_state['quests']:
        qx, qy = q['pos']
        if not q['completed'] and abs(qx-px) <= VIEW_RANGE and abs(qy-py) <= VIEW_RANGE:
            full_map.paste(create_tile((255,255,0,255)), (qx*TILE_SIZE, qy*TILE_SIZE))
    
    # draw enemies
    for e in st.session_state['enemies']:
        if e['alive']:
            ex, ey = e['pos'][1], e['pos'][0]
            if abs(ex-px) <= VIEW_RANGE and abs(ey-py) <= VIEW_RANGE:
                full_map.paste(tiles['enemy'], (ex*TILE_SIZE, ey*TILE_SIZE), tiles['enemy'])
    
    # draw player
    full_map.paste(tiles['player'], (px*TILE_SIZE, py*TILE_SIZE), tiles['player'])
    
    st.image(full_map)

def move_player(dy, dx):
    py, px = st.session_state['player_pos']
    ny, nx = py + dy, px + dx
    if 0 <= ny < MAP_HEIGHT and 0 <= nx < MAP_WIDTH:
        # check if enemy blocks the way
        if any(e['alive'] and e['pos'] == (ny,nx) for e in st.session_state['enemies']):
            st.session_state['log'].append("Enemy in the way!")
        else:
            st.session_state['player_pos'] = (ny, nx)
            check_quests()

def check_quests():
    py, px = st.session_state['player_pos']
    for q in st.session_state['quests']:
        if not q['completed'] and q['pos'] == (px, py):
            q['completed'] = True
            st.session_state['log'].append(f"Quest completed: {q['desc']} Reward: {q['reward']}")
            apply_reward(q['reward'])

def apply_reward(reward):
    if 'hp' in reward:
        st.session_state['player_hp'] = min(st.session_state['player_max_hp'], st.session_state['player_hp'] + 5)
    if 'atk' in reward:
        st.session_state['player_atk'] += 1

def attack():
    px, py = st.session_state['player_pos']
    for e in st.session_state['enemies']:
        ey, ex = e['pos']
        if e['alive'] and abs(px-ex)+abs(py-ey) <= 1:  # attack range
            e['hp'] -= st.session_state['player_atk']
            if e['hp'] <= 0:
                e['alive'] = False
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
            # if in range, attack player
            if abs(px-ex)+abs(py-ey) <= 1:
                st.session_state['player_hp'] -= e['atk']
                st.session_state['log'].append(f"Enemy hits you! Your HP: {st.session_state['player_hp']}")
            else:
                # simple AI move toward player
                dx = 1 if px > ex else -1 if px < ex else 0
                dy = 1 if py > ey else -1 if py < ey else 0
                new_pos = (ey+dy, ex+dx)
                if 0 <= new_pos[0] < MAP_HEIGHT and 0 <= new_pos[1] < MAP_WIDTH:
                    if not any(oe['alive'] and oe['pos'] == new_pos for oe in st.session_state['enemies']):
                        e['pos'] = new_pos

def check_game_over():
    if st.session_state['player_hp'] <= 0:
        st.error("You died! Game over.")
        return True
    elif all(not e['alive'] for e in st.session_state['enemies']):
        st.success("All enemies defeated! Victory!")
        return True
    return False

# -------------------- UI --------------------
st.title("🪖 Soldier War Game — Full Version")

draw_map()

st.subheader(f"Player HP: {st.session_state['player_hp']}  ATK: {st.session_state['player_atk']}")

st.subheader("Controls: WASD to move, Space to attack")
key = st.text_input("Enter keys:")

if key:
    key = key.lower()
    if 'w' in key: move_player(-1, 0)
    if 's' in key: move_player(1, 0)
    if 'a' in key: move_player(0, -1)
    if 'd' in key: move_player(0, 1)
    if ' ' in key: attack()
    enemy_turn()
    st.experimental_rerun()

st.subheader("Quests")
for q in st.session_state['quests']:
    status = '✅' if q['completed'] else '📍'
    st.write(f"{q['desc']} {status}")

st.subheader("Log")
for l in st.session_state['log'][-10:]:
    st.write(l)

check_game_over()

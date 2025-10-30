# streamlit_war_game_first_person.py
import streamlit as st
import numpy as np
from PIL import Image, ImageDraw

st.set_page_config(page_title="First-Person Soldier Game", layout="wide")

TILE_SIZE = 80  # base tile size for perspective
VIEW_DEPTH = 5  # how many tiles ahead we can see

DIRECTIONS = ['N','E','S','W']  # facing
if 'facing' not in st.session_state:
    st.session_state['facing'] = 'N'

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

# -------------------- Generate simple tile images --------------------
def create_tile(color):
    img = Image.new("RGBA", (TILE_SIZE, TILE_SIZE), color)
    return img

tiles = {
    'ground': create_tile((139,69,19,255)),
    'trench': create_tile((105,105,105,255)),
    'hill': create_tile((34,139,34,255)),
    'enemy': create_tile((255,0,0,255))
}

# -------------------- First-Person Rendering --------------------
def draw_first_person():
    px, py = st.session_state['player_pos']
    facing = st.session_state['facing']
    fp_img = Image.new('RGBA', (TILE_SIZE*VIEW_DEPTH, TILE_SIZE*VIEW_DEPTH))
    
    # Simple perspective: draw tiles ahead, smaller as they are further
    for depth in range(1, VIEW_DEPTH+1):
        scale = int(TILE_SIZE*(1 - depth*0.1))
        for offset in [-1,0,1]:  # left, center, right
            dx, dy = 0,0
            if facing=='N':
                dx, dy = offset, -depth
            elif facing=='S':
                dx, dy = offset, depth
            elif facing=='E':
                dx, dy = depth, offset
            elif facing=='W':
                dx, dy = -depth, offset
            tx, ty = px+dx, py+dy
            if 0<=ty<MAP_HEIGHT and 0<=tx<MAP_WIDTH:
                terrain = st.session_state['map'][ty,tx]
                t_img = tiles[terrain].resize((scale,scale))
                pos_x = int((VIEW_DEPTH+offset)*TILE_SIZE/2)
                pos_y = int((depth-1)*TILE_SIZE*0.9)
                fp_img.paste(t_img, (pos_x,pos_y))
    
    # draw enemies if in view
    for e in st.session_state['enemies']:
        if e['alive']:
            ex, ey = e['pos']
            rel_x, rel_y = ex-px, ey-py
            visible = False
            if facing=='N' and rel_y<0 and abs(rel_x)<=1: visible=True
            if facing=='S' and rel_y>0 and abs(rel_x)<=1: visible=True
            if facing=='E' and rel_x>0 and abs(rel_y)<=1: visible=True
            if facing=='W' and rel_x<0 and abs(rel_y)<=1: visible=True
            if visible:
                dist = max(abs(rel_x), abs(rel_y))
                scale = int(TILE_SIZE*(1 - dist*0.1))
                t_img = tiles['enemy'].resize((scale,scale))
                pos_x = int(TILE_SIZE*VIEW_DEPTH/2)
                pos_y = int((dist)*TILE_SIZE*0.9)
                fp_img.paste(t_img, (pos_x,pos_y), t_img)
    
    st.image(fp_img)

# -------------------- Player Movement --------------------
def move_forward():
    px, py = st.session_state['player_pos']
    facing = st.session_state['facing']
    nx, ny = px, py
    if facing=='N': ny-=1
    elif facing=='S': ny+=1
    elif facing=='E': nx+=1
    elif facing=='W': nx-=1
    if 0<=nx<MAP_WIDTH and 0<=ny<MAP_HEIGHT:
        st.session_state['player_pos']=(nx,ny)

def move_backward():
    px, py = st.session_state['player_pos']
    facing = st.session_state['facing']
    nx, ny = px, py
    if facing=='N': ny+=1
    elif facing=='S': ny-=1
    elif facing=='E': nx-=1
    elif facing=='W': nx+=1
    if 0<=nx<MAP_WIDTH and 0<=ny<MAP_HEIGHT:
        st.session_state['player_pos']=(nx,ny)

def turn_left():
    idx = DIRECTIONS.index(st.session_state['facing'])
    st.session_state['facing'] = DIRECTIONS[(idx-1)%4]

def turn_right():
    idx = DIRECTIONS.index(st.session_state['facing'])
    st.session_state['facing'] = DIRECTIONS[(idx+1)%4]

# -------------------- UI --------------------
st.title("🔫 First-Person Soldier War Game")

draw_first_person()
st.write(f"HP: {st.session_state['player_hp']}  ATK: {st.session_state['player_atk']}")
st.subheader("Controls: W/S Forward/Back, A/D Turn Left/Right, Space to attack")
key = st.text_input("Enter keys:")

if key:
    key = key.lower()
    for k in key:
        if k=='w': move_forward()
        if k=='s': move_backward()
        if k=='a': turn_left()
        if k=='d': turn_right()
    st.experimental_rerun()


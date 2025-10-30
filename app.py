import streamlit as st
import numpy as np
from PIL import Image, ImageDraw

st.set_page_config(page_title="First-Person Soldier Game", layout="wide")

TILE_SIZE = 80
VIEW_DEPTH = 5
DIRECTIONS = ['N','E','S','W']

# -------------------- Game State --------------------
MAP_WIDTH, MAP_HEIGHT = 15, 12
TERRAIN_TYPES = ['ground', 'trench', 'hill']

if 'map' not in st.session_state:
    st.session_state['map'] = np.random.choice(TERRAIN_TYPES, (MAP_HEIGHT, MAP_WIDTH))

if 'player_pos' not in st.session_state:
    st.session_state['player_pos'] = (1,1)
if 'facing' not in st.session_state:
    st.session_state['facing'] = 'N'
if 'player_hp' not in st.session_state:
    st.session_state['player_hp'] = 20
    st.session_state['player_atk'] = 5

if 'enemies' not in st.session_state:
    st.session_state['enemies'] = [
        {'pos': (MAP_HEIGHT-2, MAP_WIDTH-2), 'hp': 12, 'alive': True},
        {'pos': (MAP_HEIGHT-3, MAP_WIDTH-5), 'hp': 10, 'alive': True}
    ]

# -------------------- Tiles --------------------
def create_tile(color, pattern=None):
    img = Image.new("RGBA", (TILE_SIZE, TILE_SIZE), color)
    draw = ImageDraw.Draw(img)
    if pattern=='trench':
        for i in range(0,TILE_SIZE,4):
            draw.line([(0,i),(TILE_SIZE,i)], fill=(80,80,80))
    if pattern=='hill':
        draw.ellipse([5,5,TILE_SIZE-5,TILE_SIZE-5], fill=(0,100,0))
    return img

tiles = {
    'ground': create_tile((139,69,19,255)),
    'trench': create_tile((105,105,105,255),'trench'),
    'hill': create_tile((34,139,34,255),'hill'),
    'enemy': create_tile((255,0,0,255))
}

# -------------------- First-Person Rendering --------------------
def draw_first_person():
    px, py = st.session_state['player_pos']
    facing = st.session_state['facing']
    fp_img = Image.new('RGBA', (TILE_SIZE*VIEW_DEPTH, TILE_SIZE*VIEW_DEPTH))
    
    for depth in range(1, VIEW_DEPTH+1):
        scale = int(TILE_SIZE*(1 - depth*0.1))
        for offset in [-1,0,1]:
            dx, dy = 0,0
            if facing=='N': dx, dy = offset, -depth
            elif facing=='S': dx, dy = offset, depth
            elif facing=='E': dx, dy = depth, offset
            elif facing=='W': dx, dy = -depth, offset
            tx, ty = px+dx, py+dy
            if 0<=ty<MAP_HEIGHT and 0<=tx<MAP_WIDTH:
                terrain = st.session_state['map'][ty,tx]
                t_img = tiles[terrain].resize((scale,scale))
                pos_x = int((VIEW_DEPTH+offset)*TILE_SIZE/2)
                pos_y = int((depth-1)*TILE_SIZE*0.9)
                fp_img.paste(t_img,(pos_x,pos_y))
    
    # Draw enemies
    for e in st.session_state['enemies']:
        if e['alive']:
            ex, ey = e['pos']
            rel_x, rel_y = ex-px, ey-py
            visible=False
            if facing=='N' and rel_y<0 and abs(rel_x)<=1: visible=True
            if facing=='S' and rel_y>0 and abs(rel_x)<=1: visible=True
            if facing=='E' and rel_x>0 and abs(rel_y)<=1: visible=True
            if facing=='W' and rel_x<0 and abs(rel_y)<=1: visible=True
            if visible:
                dist = max(abs(rel_x), abs(rel_y))
                scale=int(TILE_SIZE*(1-dist*0.1))
                t_img = tiles['enemy'].resize((scale,scale))
                pos_x=int(TILE_SIZE*VIEW_DEPTH/2)
                pos_y=int(dist*TILE_SIZE*0.9)
                fp_img.paste(t_img,(pos_x,pos_y),t_img)
    
    st.image(fp_img)

# -------------------- Movement --------------------
def move_forward():
    px, py = st.session_state['player_pos']
    f = st.session_state['facing']
    nx, ny = px, py
    if f=='N': ny-=1
    elif f=='S': ny+=1
    elif f=='E': nx+=1
    elif f=='W': nx-=1
    if 0<=nx<MAP_WIDTH and 0<=ny<MAP_HEIGHT:
        st.session_state['player_pos']=(nx,ny)

def move_backward():
    px, py = st.session_state['player_pos']
    f = st.session_state['facing']
    nx, ny = px, py
    if f=='N': ny+=1
    elif f=='S': ny-=1
    elif f=='E': nx-=1
    elif f=='W': nx+=1
    if 0<=nx<MAP_WIDTH and 0<=ny<MAP_HEIGHT:
        st.session_state['player_pos']=(nx,ny)

def turn_left():
    idx = DIRECTIONS.index(st.session_state['facing'])
    st.session_state['facing']=DIRECTIONS[(idx-1)%4]

def turn_right():
    idx = DIRECTIONS.index(st.session_state['facing'])
    st.session_state['facing']=DIRECTIONS[(idx+1)%4]

# -------------------- UI --------------------
st.title("⚔️ First-Person Battlefield")

draw_first_person()
st.write(f"HP: {st.session_state['player_hp']}  ATK: {st.session_state['player_atk']}")

st.subheader("Controls: W/S Forward/Back, A/D Turn Left/Right")
key = st.text_input("Enter keys:")

if key:
    key = key.lower()
    for k in key:
        if k=='w': move_forward()
        if k=='s': move_backward()
        if k=='a': turn_left()
        if k=='d': turn_right()
    st.experimental_rerun()


# streamlit_war_game_tiles.py
import streamlit as st
import numpy as np
from PIL import Image

st.set_page_config(page_title="Soldier Map War Game", layout="wide")

# -------------------- Load Tiles --------------------
TILE_SIZE = 32  # pixels
tiles = {
    'ground': Image.open("tiles/ground.png"),
    'trench': Image.open("tiles/trench.png"),
    'hill': Image.open("tiles/hill.png"),
    'player': Image.open("tiles/player.png"),
    'enemy': Image.open("tiles/enemy.png")
}

# -------------------- Map & Units --------------------
MAP_WIDTH, MAP_HEIGHT = 15, 10
TERRAIN_TYPES = ['ground', 'trench', 'hill']

if 'map' not in st.session_state:
    # Random terrain map
    st.session_state['map'] = np.random.choice(TERRAIN_TYPES, (MAP_HEIGHT, MAP_WIDTH))

if 'player_pos' not in st.session_state:
    st.session_state['player_pos'] = (1, 1)

if 'enemies' not in st.session_state:
    st.session_state['enemies'] = [(MAP_HEIGHT-2, MAP_WIDTH-2), (MAP_HEIGHT-3, MAP_WIDTH-5)]

# -------------------- Functions --------------------
def draw_map():
    height, width = st.session_state['map'].shape
    full_map = Image.new('RGBA', (width*TILE_SIZE, height*TILE_SIZE))
    
    # Draw terrain
    for y in range(height):
        for x in range(width):
            tile_type = st.session_state['map'][y, x]
            full_map.paste(tiles[tile_type], (x*TILE_SIZE, y*TILE_SIZE))
    
    # Draw enemies
    for ey, ex in st.session_state['enemies']:
        full_map.paste(tiles['enemy'], (ex*TILE_SIZE, ey*TILE_SIZE), tiles['enemy'])
    
    # Draw player
    py, px = st.session_state['player_pos']
    full_map.paste(tiles['player'], (px*TILE_SIZE, py*TILE_SIZE), tiles['player'])
    
    st.image(full_map)

def move_player(dy, dx):
    py, px = st.session_state['player_pos']
    ny, nx = py + dy, px + dx
    if 0 <= ny < MAP_HEIGHT and 0 <= nx < MAP_WIDTH:
        st.session_state['player_pos'] = (ny, nx)

# -------------------- UI --------------------
st.title("🪖 Soldier Map War Game (Realistic Tiles)")

draw_map()

st.subheader("Controls")
key = st.text_input("Enter WASD to move:", "")

if key:
    key = key.lower()
    if 'w' in key: move_player(-1, 0)
    if 's' in key: move_player(1, 0)
    if 'a' in key: move_player(0, -1)
    if 'd' in key: move_player(0, 1)
    st.experimental_rerun()

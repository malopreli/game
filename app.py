# streamlit_fps_soldier_game.py
import streamlit as st
import numpy as np
from PIL import Image, ImageDraw

st.set_page_config(page_title="FPS Soldier Game", layout="wide")

TILE_SIZE = 80
VIEW_DEPTH = 5
DIRECTIONS = ['N','E','S','W']

# -------------------- Initialize Game State --------------------
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
    st.session_state['log'] = ["FPS Soldier Game started!"]

# -------------------- Tile Images --------------------
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
        scale = int(TILE_SIZE*(1-depth*0.1))
        for offset in [-1,0,1]:
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
                fp_img.paste(t_img,(pos_x,pos_y))
    
    # Enemies in view
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

# -------------------- Movement & Rotation --------------------
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
        check_quests()

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
        check_quests()

def turn_left():
    idx = DIRECTIONS.index(st.session_state['facing'])
    st.session_state['facing'] = DIRECTIONS[(idx-1)%4]

def turn_right():
    idx = DIRECTIONS.index(st.session_state['facing'])
    st.session_state['facing'] = DIRECTIONS[(idx+1)%4]

# -------------------- Combat & Quests --------------------
def attack():
    px, py = st.session_state['player_pos']
    facing = st.session_state['facing']
    for e in st.session_state['enemies']:
        ex, ey = e['pos']
        # enemy in front
        if facing=='N' and ey<py and ex==px and py-ey<=1: hit=True
        elif facing=='S' and ey>py and ex==px and ey-py<=1: hit=True
        elif facing=='E' and ex>px and ey==py and ex-px<=1: hit=True
        elif facing=='W' and ex<px and ey==py and px-ex<=1: hit=True
        else: hit=False
        if hit and e['alive']:
            terrain=st.session_state['map'][ey,ex]
            damage=st.session_state['player_atk']
            if terrain=='hill': damage+=2
            if terrain=='trench': damage=max(damage-1,1)
            e['hp']-=damage
            if e['hp']<=0: e['alive']=False; st.session_state['log'].append("Enemy killed!")
            else: st.session_state['log'].append(f"Hit enemy! HP: {e['hp']}")
            return
    st.session_state['log'].append("No enemy in range!")

def enemy_turn():
    px, py = st.session_state['player_pos']
    for e in st.session_state['enemies']:
        if e['alive']:
            ex, ey = e['pos']
            # attack if adjacent
            if abs(px-ex)+abs(py-ey)<=1:
                terrain=st.session_state['map'][py,px]
                dmg=e['atk']
                if terrain=='trench': dmg=max(dmg-1,1)
                st.session_state['player_hp']-=dmg
                st.session_state['log'].append(f"Enemy hits! HP: {st.session_state['player_hp']}")
            else:
                # simple AI move toward player
                dx=1 if px>ex else -1 if px<ex else 0
                dy=1 if py>ey else -1 if py<ey else 0
                new_pos=(ex+dx,ey+dy)
                if 0<=new_pos[0]<MAP_WIDTH and 0<=new_pos[1]<MAP_HEIGHT:
                    if not any(o['alive'] and o['pos']==(new_pos[0],new_pos[1]) for o in st.session_state['enemies']):
                        e['pos']=(new_pos[0],new_pos[1])

def check_quests():
    px, py = st.session_state['player_pos']
    for q in st.session_state['quests']:
        if not q['completed'] and q['pos']==(px,py):
            q['completed']=True
            st.session_state['log'].append(f"Quest done: {q['desc']} Reward: {q['reward']}")
            apply_reward(q['reward'])

def apply_reward(reward):
    if 'hp' in reward:
        st.session_state['player_hp']=min(st.session_state['player_max_hp'],st.session_state['player_hp']+5)
    if 'atk' in reward:
        st.session_state['player_atk']+=1

def check_game_over():
    if st.session_state['player_hp']<=0:
        st.error("You died! Game over.")
        return True
    elif all(not e['alive'] for e in st.session_state['enemies']):
        st.success("All enemies defeated! Victory!")
        return True
    return False

# -------------------- UI --------------------
st.title("🔫 FPS Soldier Game")

draw_first_person()
st.write(f"HP: {st.session_state['player_hp']}  ATK: {st.session_state['player_atk']}")

st.subheader("Controls: W/S Forward/Back, A/D Turn Left/Right, Space Attack")
key = st.text_input("Enter keys:")

if key:
    key=key.lower()
    for k in key:
        if k=='w': move_forward()
        if k=='s': move_backward()
        if k=='a': turn_left()
        if k=='d': turn_right()
        if k==' ': attack()
    enemy_turn()
    st.experimental_rerun()

st.subheader("Quests")
for q in st.session_state['quests']:
    status='✅' if q['completed'] else '📍'
    st.write(f"{q['desc']} {status}")

st.subheader("Battle Log")
for l in st.session_state['log'][-10:]:
    st.write(l)

check_game_over()



# streamlit_war_game.py with Side Quests
# Turn-based war game in Streamlit with levels and optional side quests.

import streamlit as st
import numpy as np
import matplotlib
# Use a non-interactive backend so Streamlit servers without a display won't crash.
# If matplotlib is not installed, the import will fail — see the error guidance below.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import random
from dataclasses import dataclass, field
from typing import Tuple, List, Dict

st.set_page_config(page_title="Streamlit War Game", layout="wide")

# ------------------------- Data Structures -------------------------

@dataclass
class Unit:
    id: int
    name: str
    team: str  # 'player' or 'enemy'
    hp: int
    max_hp: int
    atk: int
    move: int
    range: int
    pos: Tuple[int,int]
    alive: bool = True

    def is_in_range(self, other: 'Unit') -> bool:
        return manhattan(self.pos, other.pos) <= self.range

@dataclass
class SideQuest:
    description: str
    location: Tuple[int,int]
    reward: str
    completed: bool = False

@dataclass
class Level:
    name: str
    width: int
    height: int
    num_enemies: int
    player_units: List[Dict]
    terrain: np.ndarray = field(default_factory=lambda: np.zeros((0,0), dtype=int))
    side_quests: List[SideQuest] = field(default_factory=list)

# ------------------------- Utility Functions -------------------------

def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def in_bounds(pos, width, height):
    x,y = pos
    return 0 <= x < width and 0 <= y < height

def neighbors(pos, width, height):
    x,y = pos
    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx,ny = x+dx, y+dy
        if in_bounds((nx,ny), width, height):
            yield (nx,ny)

# ------------------------- Level Setup -------------------------

LEVELS = [
    Level(
        name="Skirmish",
        width=8,
        height=6,
        num_enemies=2,
        player_units=[{"name":"Rifleman","hp":10,"atk":4,"move":3,"range":1}],
        side_quests=[SideQuest("Recover a lost supply crate", (3,3), "+5 HP to all units")]
    ),
    Level(
        name="Outpost",
        width=10,
        height=8,
        num_enemies=4,
        player_units=[{"name":"Rifleman","hp":10,"atk":4,"move":3,"range":1},{"name":"Sniper","hp":6,"atk":7,"move":2,"range":4}],
        side_quests=[SideQuest("Rescue the trapped ally", (5,4), "+1 Attack to all units")]
    )
]

for lvl in LEVELS:
    w,h = lvl.width, lvl.height
    terrain = np.zeros((w,h), dtype=int)
    for _ in range((w*h)//8):
        x,y = random.randrange(w), random.randrange(h)
        terrain[x,y] = 1 if random.random() < 0.6 else 2
    lvl.terrain = terrain

# ------------------------- Game State -------------------------

def reset_level(level_idx):
    lvl = LEVELS[level_idx]
    st.session_state['level_idx'] = level_idx
    st.session_state['width'] = lvl.width
    st.session_state['height'] = lvl.height
    st.session_state['terrain'] = lvl.terrain.copy()
    st.session_state['units'] = {}
    st.session_state['turn'] = 'player'
    st.session_state['selected_unit'] = None
    st.session_state['quests'] = [q for q in lvl.side_quests]
    st.session_state['message'] = f"Level '{lvl.name}' started."

    uid = 1
    for spec in lvl.player_units:
        pos = (0, random.randrange(lvl.height))
        st.session_state['units'][uid] = Unit(uid, spec['name'], 'player', spec['hp'], spec['hp'], spec['atk'], spec['move'], spec['range'], pos)
        uid += 1
    for i in range(lvl.num_enemies):
        pos = (lvl.width-1, random.randrange(lvl.height))
        st.session_state['units'][uid] = Unit(uid, "Enemy", 'enemy', 8, 8, 3, 3, 1, pos)
        uid += 1

    st.session_state['log'] = [st.session_state['message']]

def get_units():
    return list(st.session_state['units'].values())

# ------------------------- Map Rendering -------------------------

def draw_map():
    w = st.session_state['width']
    h = st.session_state['height']
    terrain = st.session_state['terrain']
    fig, ax = plt.subplots(figsize=(w/2, h/2))
    ax.set_xlim(-0.5, w-0.5)
    ax.set_ylim(-0.5, h-0.5)
    ax.invert_yaxis()
    ax.set_aspect('equal')

    for x in range(w):
        for y in range(h):
            face = (0.9,0.9,0.9) if terrain[x,y]==0 else ((0.8,0.7,0.6) if terrain[x,y]==1 else (0.6,0.8,0.6))
            ax.add_patch(plt.Rectangle((x-0.5,y-0.5),1,1,facecolor=face,edgecolor='black'))

    for q in st.session_state['quests']:
        if not q.completed:
            x,y = q.location
            ax.text(x, y, "Q", color='gold', ha='center', va='center', fontsize=12, fontweight='bold')

    for u in get_units():
        if not u.alive: continue
        x,y = u.pos
        color = 'blue' if u.team=='player' else 'red'
        ax.text(x, y, f"{u.name[0]}{u.id}", color=color, ha='center', va='center', fontsize=8, fontweight='bold')
        ax.plot([x-0.4, x-0.4 + 0.8*(u.hp/u.max_hp)], [y+0.35]*2, linewidth=4, color=color)

    st.pyplot(fig)

# ------------------------- Actions -------------------------

def move_unit(unit, dest):
    dist = manhattan(unit.pos, dest)
    if dist > unit.move:
        st.session_state['message'] = "Move too far."
        return False
    if any(u.pos==dest and u.alive for u in get_units() if u.id!=unit.id):
        st.session_state['message'] = "Destination occupied."
        return False
    unit.pos = dest
    for q in st.session_state['quests']:
        if not q.completed and q.location == dest:
            q.completed = True
            st.session_state['message'] = f"Quest completed: {q.description}! Reward: {q.reward}"
            apply_reward(q.reward)
    st.session_state['log'].append(st.session_state['message'])
    return True

def apply_reward(reward):
    if '+5 HP' in reward:
        for u in get_units():
            if u.team=='player':
                u.hp = min(u.max_hp+5, u.hp+5)
    elif '+1 Attack' in reward:
        for u in get_units():
            if u.team=='player':
                u.atk += 1

def attack(attacker, defender):
    if not attacker.is_in_range(defender):
        st.session_state['message'] = "Out of range."
        return False
    dmg = attacker.atk - (1 if st.session_state['terrain'][defender.pos]==2 else 0)
    defender.hp -= dmg
    if defender.hp <= 0:
        defender.alive = False
        st.session_state['message'] = f"{attacker.name} killed {defender.name}."
    else:
        st.session_state['message'] = f"{attacker.name} hit {defender.name} for {dmg}."
    st.session_state['log'].append(st.session_state['message'])
    return True

def enemy_ai_turn():
    enemies = [u for u in get_units() if u.team=='enemy' and u.alive]
    players = [u for u in get_units() if u.team=='player' and u.alive]
    for e in enemies:
        if not players: break
        target = min(players, key=lambda p: manhattan(p.pos, e.pos))
        if e.is_in_range(target):
            attack(e,target)
        else:
            ex,ey = e.pos
            tx,ty = target.pos
            step = (ex+(1 if tx>ex else -1 if tx<ex else 0), ey+(1 if ty>ey else -1 if ty<ey else 0))
            if in_bounds(step, st.session_state['width'], st.session_state['height']) and not any(u.pos==step and u.alive for u in get_units()):
                e.pos = step
    st.session_state['turn'] = 'player'

# ------------------------- Streamlit UI -------------------------

st.title("⚔️ Streamlit War Game with Side Quests")

if 'level_idx' not in st.session_state:
    reset_level(0)

col1, col2 = st.columns([3,1])
with col1:
    draw_map()
    st.subheader("Action Log")
    for line in st.session_state['log'][-10:]:
        st.write(line)

with col2:
    lvl_choice = st.selectbox("Choose level", options=list(range(len(LEVELS))), format_func=lambda i: LEVELS[i].name, index=st.session_state['level_idx'])
    if st.button("Restart Level"):
        reset_level(lvl_choice)

    st.write(f"Turn: {st.session_state['turn']}")
    st.write(st.session_state['message'])

    st.subheader("Quests")
    for q in st.session_state['quests']:
        status = "✅ Completed" if q.completed else f"📍 Location: {q.location}"
        st.write(f"**{q.description}** — {status}")

    st.subheader("Units")
    for u in get_units():
        if u.team=='player':
            if st.button(f"Select {u.name} {u.id} ({u.hp} HP)"):
                st.session_state['selected_unit'] = u.id

    if st.session_state.get('selected_unit'):
        u = st.session_state['units'][st.session_state['selected_unit']]
        st.write(f"Selected {u.name} at {u.pos}")
        mx = st.number_input("Move X", 0, st.session_state['width']-1, u.pos[0])
        my = st.number_input("Move Y", 0, st.session_state['height']-1, u.pos[1])
        if st.button("Move"):
            if move_unit(u,(mx,my)):
                st.session_state['turn']='enemy'
                enemy_ai_turn()
        enemy_ids = [x.id for x in get_units() if x.team=='enemy' and x.alive]
        if enemy_ids:
            target = st.selectbox("Attack target", enemy_ids)
            if st.button("Attack"):
                attack(u, st.session_state['units'][target])
                st.session_state['turn']='enemy'
                enemy_ai_turn()

    if st.button("End Turn"):
        st.session_state['turn']='enemy'
        enemy_ai_turn()

    players_alive = [u for u in get_units() if u.team=='player' and u.alive]
    enemies_alive = [u for u in get_units() if u.team=='enemy' and u.alive]
    if not enemies_alive:
        st.success("Victory! All enemies defeated.")
    elif not players_alive:
        st.error("Defeat! All units lost.")

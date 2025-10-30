# streamlit_war_game_no_matplotlib.py
# Turn-based war game in Streamlit (no matplotlib)

import streamlit as st
import numpy as np
import random
from dataclasses import dataclass, field
from typing import Tuple, List, Dict

st.set_page_config(page_title="Streamlit War Game", layout="wide")

@dataclass
class Unit:
    id: int
    name: str
    team: str
    hp: int
    max_hp: int
    atk: int
    move: int
    range: int
    pos: Tuple[int,int]
    alive: bool = True

    def is_in_range(self, other: 'Unit') -> bool:
        return abs(self.pos[0]-other.pos[0]) + abs(self.pos[1]-other.pos[1]) <= self.range

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
    side_quests: List[SideQuest] = field(default_factory=list)

# -------------------- Setup --------------------

LEVELS = [
    Level(
        name="Skirmish",
        width=8,
        height=6,
        num_enemies=2,
        player_units=[{"name":"Rifleman","hp":10,"atk":4,"move":3,"range":1}],
        side_quests=[SideQuest("Recover supply crate", (3,3), "+5 HP")]
    ),
    Level(
        name="Outpost",
        width=10,
        height=8,
        num_enemies=4,
        player_units=[{"name":"Rifleman","hp":10,"atk":4,"move":3,"range":1},{"name":"Sniper","hp":6,"atk":7,"move":2,"range":4}],
        side_quests=[SideQuest("Rescue ally", (5,4), "+1 ATK")]
    )
]

# -------------------- State --------------------

def reset_level(idx):
    lvl = LEVELS[idx]
    st.session_state['level_idx'] = idx
    st.session_state['width'] = lvl.width
    st.session_state['height'] = lvl.height
    st.session_state['units'] = {}
    st.session_state['quests'] = [q for q in lvl.side_quests]
    st.session_state['turn'] = 'player'
    st.session_state['selected_unit'] = None
    st.session_state['log'] = [f"Starting {lvl.name}"]

    uid = 1
    for spec in lvl.player_units:
        pos = (0, random.randrange(lvl.height))
        st.session_state['units'][uid] = Unit(uid, spec['name'], 'player', spec['hp'], spec['hp'], spec['atk'], spec['move'], spec['range'], pos)
        uid += 1
    for i in range(lvl.num_enemies):
        pos = (lvl.width-1, random.randrange(lvl.height))
        st.session_state['units'][uid] = Unit(uid, "Enemy", 'enemy', 8, 8, 3, 3, 1, pos)
        uid += 1

def get_units():
    return list(st.session_state['units'].values())

# -------------------- Rendering --------------------

def draw_map():
    w = st.session_state['width']
    h = st.session_state['height']
    grid = []
    for y in range(h):
        row = []
        for x in range(w):
            symbol = '⬜'
            for q in st.session_state['quests']:
                if not q.completed and q.location == (x,y):
                    symbol = '🟨'
            for u in get_units():
                if u.alive and u.pos == (x,y):
                    symbol = '🔵' if u.team=='player' else '🔴'
            row.append(symbol)
        grid.append(''.join(row))
    st.markdown('<br>'.join(grid), unsafe_allow_html=True)

# -------------------- Actions --------------------

def move_unit(unit, dest):
    if abs(unit.pos[0]-dest[0]) + abs(unit.pos[1]-dest[1]) > unit.move:
        st.session_state['log'].append("Too far.")
        return
    if any(u.pos==dest and u.alive for u in get_units() if u.id!=unit.id):
        st.session_state['log'].append("Tile occupied.")
        return
    unit.pos = dest
    for q in st.session_state['quests']:
        if not q.completed and q.location == dest:
            q.completed = True
            st.session_state['log'].append(f"Quest done: {q.description}! Reward {q.reward}.")
            apply_reward(q.reward)

def apply_reward(reward):
    for u in get_units():
        if u.team=='player':
            if 'HP' in reward:
                u.hp = min(u.max_hp+5, u.hp+5)
            if 'ATK' in reward:
                u.atk += 1

def attack(attacker, defender):
    if abs(attacker.pos[0]-defender.pos[0]) + abs(attacker.pos[1]-defender.pos[1]) > attacker.range:
        st.session_state['log'].append("Out of range.")
        return
    defender.hp -= attacker.atk
    if defender.hp <= 0:
        defender.alive = False
        st.session_state['log'].append(f"{attacker.name} killed {defender.name}!")
    else:
        st.session_state['log'].append(f"{attacker.name} hit {defender.name} ({defender.hp} HP left)")

def enemy_ai_turn():
    enemies = [u for u in get_units() if u.team=='enemy' and u.alive]
    players = [u for u in get_units() if u.team=='player' and u.alive]
    if not players:
        return
    for e in enemies:
        target = min(players, key=lambda p: abs(p.pos[0]-e.pos[0])+abs(p.pos[1]-e.pos[1]))
        if abs(e.pos[0]-target.pos[0])+abs(e.pos[1]-target.pos[1]) <= e.range:
            attack(e,target)
        else:
            dx = 1 if target.pos[0]>e.pos[0] else -1 if target.pos[0]<e.pos[0] else 0
            dy = 1 if target.pos[1]>e.pos[1] else -1 if target.pos[1]<e.pos[1] else 0
            new_pos = (e.pos[0]+dx, e.pos[1]+dy)
            if not any(u.pos==new_pos and u.alive for u in get_units()):
                e.pos = new_pos
    st.session_state['turn']='player'

# -------------------- UI --------------------

st.title("⚔️ Streamlit War Game — No Matplotlib")

if 'level_idx' not in st.session_state:
    reset_level(0)

col1, col2 = st.columns([3,1])
with col1:
    draw_map()
    st.write('---')
    for log in st.session_state['log'][-10:]:
        st.write(log)

with col2:
    lvl = st.selectbox("Level", list(range(len(LEVELS))), format_func=lambda i: LEVELS[i].name, index=st.session_state['level_idx'])
    if st.button("Restart"):
        reset_level(lvl)

    st.write(f"Turn: {st.session_state['turn']}")

    st.subheader("Quests")
    for q in st.session_state['quests']:
        status = '✅' if q.completed else f"📍 {q.location}"
        st.write(f"{q.description} — {status}")

    st.subheader("Units")
    for u in get_units():
        if u.team=='player':
            if st.button(f"Select {u.name} ({u.hp} HP)"):
                st.session_state['selected_unit']=u.id

    if st.session_state.get('selected_unit'):
        u = st.session_state['units'][st.session_state['selected_unit']]
        st.write(f"Selected {u.name} at {u.pos}")
        mx = st.number_input('X',0,st.session_state['width']-1,u.pos[0])
        my = st.number_input('Y',0,st.session_state['height']-1,u.pos[1])
        if st.button('Move'):
            move_unit(u,(mx,my))
            st.session_state['turn']='enemy'
            enemy_ai_turn()
        enemies = [e for e in get_units() if e.team=='enemy' and e.alive]
        if enemies:
            tid = st.selectbox('Attack target',[e.id for e in enemies])
            if st.button('Attack'):
                attack(u, st.session_state['units'][tid])
                st.session_state['turn']='enemy'
                enemy_ai_turn()

    if st.button('End Turn'):
        st.session_state['turn']='enemy'
        enemy_ai_turn()

    if not any(u.alive and u.team=='enemy' for u in get_units()):
        st.success('Victory!')
    elif not any(u.alive and u.team=='player' for u in get_units()):
        st.error('Defeat!')

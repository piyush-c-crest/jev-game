# 🎮 Jev Plays the Game — Web & CLI Edition

A dark fantasy dungeon RPG featuring **TypeSafe AI's Jev (System One) model**. Playable in **both a rich browser Web UI** and a terminal CLI!

---

## 🌟 Game Modes

1. **🎮 Manual Player Mode ("You Play")**:
   - Take direct control of the adventurer with tactile action buttons and keyboard shortcuts (`1`, `2`, `3`, `4`).
   - In combat: Strike foes, raise your shield, quaff healing potions, or tactically retreat.
   - In chambers: Open treasure vaults, pray at celestial healing shrines, disarm spiked traps, or pick crossroads corridors.
   - **🧠 Consult Jev Oracle (`[A]`)**: Query Jev in real-time to see what the System One model recommends and inspect its decision probabilities!

2. **🤖 Autonomous Agent Mode ("Jev Plays")**:
   - Jev is the active player! The AI analyzes the dungeon state each turn using System One and answers multi-question decisions in parallel.
   - Full playback controls: Play/Pause (`Space`), Step 1 Turn, and Speed Slider (Slow, Normal, Fast, Turbo).
   - Seamlessly toggle between Manual and Agent mode at any moment during a run.

3. **💻 Terminal CLI Mode**:
   - The classic rich terminal interface with ASCII art, health bars, and live logs.

---

## 🚀 Quick Start

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Launch the Web RPG (Recommended)
```powershell
python server.py
```
This automatically opens your browser to `http://127.0.0.1:8000`.

### 3. Or Run the Terminal CLI
```powershell
python main.py
```

---

## 🎨 Web Features

- **Visual Battler Arena**: Animated cards for the Adventurer and dungeon monsters (Goblin, Orc Warrior, Dark Mage, Troll, Dragon Boss).
- **Procedural Sound Effects**: Pure Web Audio API retro synth sound effects (sword slashes, critical strikes, shield blocks, potion chugs, gold drops, victory fanfare) with persistent mute toggle.
- **Floating Combat Numbers & Screen Shake**: Dynamic floating damage numbers and screen tremors on impactful blows.
- **Dungeon Progression Bar**: Floor minimap track showing cleared rooms, active location, and boss chamber.
- **Jev Brain Telemetry**: Live visualization of Jev's System One confidence, probability distributions, threat meter, and proactive Noul probabilities.

---

## 📁 Project Structure

```
jev-game/
├── .env                  # TYPESAFE_API_KEY
├── README.md             # Documentation
├── requirements.txt      # Python dependencies
├── server.py             # FastAPI Web Server (serves Web RPG)
├── game_session.py       # Session manager (player, dungeon, turns, serialization)
├── action_resolver.py    # Game mechanics resolver (human & agent actions)
├── jev_engine.py         # TypeSafe AI Jev System One integration
├── state_builder.py      # Natural language state serializer
├── world.py              # Dungeon generation, entities, rooms
├── game_loop.py          # Terminal CLI turn orchestrator
├── main.py               # Terminal CLI entry point
├── ui.py                 # Terminal Rich UI
├── test_web_api.py       # Automated verification test suite
└── web/                  # Browser Frontend (Vanilla ES6, HTML5, CSS3)
    ├── index.html        # Web RPG application layout
    └── static/
        ├── css/game.css  # Dark fantasy styling & animations
        └── js/
            ├── audio.js  # Web Audio API sound synthesizer
            └── game.js   # Game client controller & dual-play engine
```

---

## 🔑 API Key

Store your Jev API key in `.env`:
```env
TYPESAFE_API_KEY=your-typesafe-api-key
```
*(If no API key is present or in case of network timeouts, built-in heuristic fallbacks ensure uninterrupted gameplay!)*

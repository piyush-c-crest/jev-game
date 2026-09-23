/**
 * game.js - Core Web RPG Client Controller for Jev Plays the Game.
 * Coordinates UI rendering, REST API sync, Dual-Play Modes, Web Audio & FX.
 */

class WebGameApp {
  constructor() {
    this.state = null;
    this.mode = 'manual'; // 'manual' or 'agent'
    this.isAgentRunning = false;
    this.agentTimer = null;
    this.agentSpeedMs = 1100;
    this.activeLogFilter = 'all';
    this.isRequestInProgress = false;

    // Entity visual portraits & icons
    this.portraits = {
      'Goblin': '👺',
      'Orc Warrior': '🧌',
      'Dark Mage': '🧙‍♂️',
      'Troll': '👹',
      'Dragon Boss': '🐉',
      'treasure': '💎',
      'shrine': '✨',
      'trap': '⚙️',
      'fork': '🧭',
      'empty': '🕸️',
    };

    this.initElements();
    this.bindEvents();
    this.loadInitialState();
  }

  initElements() {
    // Nav & Mode
    this.modeManualBtn = document.getElementById('modeManualBtn');
    this.modeAgentBtn = document.getElementById('modeAgentBtn');
    this.agentControls = document.getElementById('agentControls');
    this.agentPlayPauseBtn = document.getElementById('agentPlayPauseBtn');
    this.playPauseIcon = document.getElementById('playPauseIcon');
    this.playPauseText = document.getElementById('playPauseText');
    this.agentStepBtn = document.getElementById('agentStepBtn');
    this.agentSpeedSelect = document.getElementById('agentSpeedSelect');
    this.soundToggleBtn = document.getElementById('soundToggleBtn');
    this.newGameBtn = document.getElementById('newGameBtn');

    // Minimap & Header
    this.floorBadgeText = document.getElementById('floorBadgeText');
    this.turnCounterText = document.getElementById('turnCounterText');
    this.roomProgressTrack = document.getElementById('roomProgressTrack');

    // Stage & Battlers
    this.mainStage = document.getElementById('mainStage');
    this.roomName = document.getElementById('roomName');
    this.roomDesc = document.getElementById('roomDesc');
    this.encounterPhasePill = document.getElementById('encounterPhasePill');
    this.combatantsStage = document.getElementById('combatantsStage');
    this.floatingTextContainer = document.getElementById('floatingTextContainer');

    // Hero HUD
    this.heroHpText = document.getElementById('heroHpText');
    this.heroHpFill = document.getElementById('heroHpFill');
    this.heroAtk = document.getElementById('heroAtk');
    this.heroDef = document.getElementById('heroDef');
    this.heroPotions = document.getElementById('heroPotions');
    this.heroGold = document.getElementById('heroGold');

    // Enemy / Chamber HUD
    this.vsBadge = document.getElementById('vsBadge');
    this.enemyCard = document.getElementById('enemyCard');
    this.enemyPortrait = document.getElementById('enemyPortrait');
    this.enemyName = document.getElementById('enemyName');
    this.enemyHpText = document.getElementById('enemyHpText');
    this.enemyHpFill = document.getElementById('enemyHpFill');
    this.enemyAtk = document.getElementById('enemyAtk');
    this.enemyDef = document.getElementById('enemyDef');
    this.enemyGold = document.getElementById('enemyGold');
    this.chamberStage = document.getElementById('chamberStage');
    this.chamberIcon = document.getElementById('chamberIcon');
    this.chamberDescription = document.getElementById('chamberDescription');

    // Action Deck
    this.deckModeNotice = document.getElementById('deckModeNotice');
    this.actionButtonsContainer = document.getElementById('actionButtonsContainer');
    this.advisorBar = document.getElementById('advisorBar');
    this.askAdvisorBtn = document.getElementById('askAdvisorBtn');
    this.advisorBanner = document.getElementById('advisorBanner');
    this.advisorRecText = document.getElementById('advisorRecText');
    this.executeAdvisorMoveBtn = document.getElementById('executeAdvisorMoveBtn');

    // Jev Brain Telemetry
    this.latencyTicker = document.getElementById('latencyTicker');
    this.brainActionText = document.getElementById('brainActionText');
    this.brainConfidenceText = document.getElementById('brainConfidenceText');
    this.probBarsContainer = document.getElementById('probBarsContainer');
    this.meterLabel = document.getElementById('meterLabel');
    this.meterValText = document.getElementById('meterValText');
    this.meterFill = document.getElementById('meterFill');
    this.noulPotionProb = document.getElementById('noulPotionProb');
    this.noulFleeProb = document.getElementById('noulFleeProb');

    // Chronicle Log
    this.logScrollArea = document.getElementById('logScrollArea');
    this.filterButtons = document.querySelectorAll('.filter-btn');

    // Modals
    this.victoryModal = document.getElementById('victoryModal');
    this.vTurns = document.getElementById('vTurns');
    this.vGold = document.getElementById('vGold');
    this.vKills = document.getElementById('vKills');
    this.vRooms = document.getElementById('vRooms');
    this.vRestartBtn = document.getElementById('vRestartBtn');

    this.gameOverModal = document.getElementById('gameOverModal');
    this.gameOverCauseText = document.getElementById('gameOverCauseText');
    this.dTurns = document.getElementById('dTurns');
    this.dFloor = document.getElementById('dFloor');
    this.dGold = document.getElementById('dGold');
    this.dKills = document.getElementById('dKills');
    this.dRestartBtn = document.getElementById('dRestartBtn');
  }

  bindEvents() {
    // Mode toggling
    this.modeManualBtn.addEventListener('click', () => this.switchMode('manual'));
    this.modeAgentBtn.addEventListener('click', () => this.switchMode('agent'));

    // Agent Controls
    this.agentPlayPauseBtn.addEventListener('click', () => this.toggleAgentPlay());
    this.agentStepBtn.addEventListener('click', () => this.stepAgent());
    this.agentSpeedSelect.addEventListener('change', (e) => {
      this.agentSpeedMs = parseInt(e.target.value, 10);
    });

    // Sound toggle
    this.soundToggleBtn.addEventListener('click', () => {
      const isMuted = window.soundFX.toggleMute();
      this.soundToggleBtn.innerHTML = isMuted ? '🔇 Muted' : '🔊 Sound';
    });
    this.soundToggleBtn.innerHTML = window.soundFX.isMuted() ? '🔇 Muted' : '🔊 Sound';

    // New Game & Restarts
    this.newGameBtn.addEventListener('click', () => this.startNewGame());
    this.vRestartBtn.addEventListener('click', () => {
      this.victoryModal.classList.remove('active');
      this.startNewGame();
    });
    this.dRestartBtn.addEventListener('click', () => {
      this.gameOverModal.classList.remove('active');
      this.startNewGame();
    });

    // Advisor
    this.askAdvisorBtn.addEventListener('click', () => this.fetchAdvisorAdvice());
    this.executeAdvisorMoveBtn.addEventListener('click', () => this.executeRecommendedAdvisorMove());

    // Log filters
    this.filterButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        this.filterButtons.forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        this.activeLogFilter = e.target.dataset.filter;
        this.renderLogs();
      });
    });

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => this.handleKeyboardInput(e));
  }

  handleKeyboardInput(e) {
    // Ignore when typing in input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;

    if (e.key === 'm' || e.key === 'M') {
      this.soundToggleBtn.click();
      return;
    }

    if (this.mode === 'agent') {
      if (e.code === 'Space') {
        e.preventDefault();
        this.toggleAgentPlay();
      }
      return;
    }

    // Manual mode hotkeys
    if (e.key === 'a' || e.key === 'A') {
      e.preventDefault();
      this.fetchAdvisorAdvice();
      return;
    }

    const keyNum = parseInt(e.key, 10);
    if (keyNum >= 1 && keyNum <= 5) {
      const buttons = this.actionButtonsContainer.querySelectorAll('.action-btn');
      const targetBtn = buttons[keyNum - 1];
      if (targetBtn && !targetBtn.disabled) {
        e.preventDefault();
        targetBtn.click();
      }
    }
  }

  switchMode(targetMode) {
    this.mode = targetMode;
    if (targetMode === 'manual') {
      this.modeManualBtn.classList.add('active');
      this.modeAgentBtn.classList.remove('active');
      this.agentControls.style.display = 'none';
      this.deckModeNotice.textContent = '🎮 Your Turn — Select an Action:';
      this.advisorBar.style.display = 'flex';
      this.stopAgentLoop();
    } else {
      this.modeAgentBtn.classList.add('active');
      this.modeManualBtn.classList.remove('active');
      this.agentControls.style.display = 'flex';
      this.deckModeNotice.textContent = '🤖 Jev System One Autonomous Mode:';
      this.advisorBar.style.display = 'none';
    }

    // Inform server of mode change
    fetch('/api/game/mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: targetMode }),
    }).catch(err => console.error(err));

    this.renderActionButtons();
  }

  async loadInitialState() {
    try {
      const res = await fetch('/api/game/state');
      if (res.ok) {
        const data = await res.json();
        this.updateGameState(data, false);
      }
    } catch (err) {
      console.error('Failed to load initial state:', err);
    }
  }

  async startNewGame() {
    this.stopAgentLoop();
    this.victoryModal.classList.remove('active');
    this.gameOverModal.classList.remove('active');
    try {
      const res = await fetch('/api/game/new', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ floors: 5, mode: this.mode }),
      });
      if (res.ok) {
        const data = await res.json();
        this.updateGameState(data, true);
        window.soundFX.playStep();
      }
    } catch (err) {
      console.error('Failed to start new game:', err);
    }
  }

  async executePlayerAction(action) {
    if (this.isRequestInProgress || this.state?.status !== 'PLAYING') return;
    this.isRequestInProgress = true;
    this.advisorBanner.style.display = 'none';

    try {
      const res = await fetch('/api/game/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action }),
      });
      if (res.ok) {
        const data = await res.json();
        this.updateGameState(data, true);
      }
    } catch (err) {
      console.error('Action failed:', err);
    } finally {
      this.isRequestInProgress = false;
    }
  }

  async stepAgent() {
    if (this.isRequestInProgress || this.state?.status !== 'PLAYING') return;
    this.isRequestInProgress = true;

    try {
      const res = await fetch('/api/game/agent-step', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        this.updateGameState(data, true);
      }
    } catch (err) {
      console.error('Agent step failed:', err);
    } finally {
      this.isRequestInProgress = false;
    }
  }

  toggleAgentPlay() {
    if (this.isAgentRunning) {
      this.stopAgentLoop();
    } else {
      this.startAgentLoop();
    }
  }

  startAgentLoop() {
    if (this.state?.status !== 'PLAYING') return;
    this.isAgentRunning = true;
    this.playPauseIcon.textContent = '⏸';
    this.playPauseText.textContent = 'Pause';
    this.runAgentCycle();
  }

  stopAgentLoop() {
    this.isAgentRunning = false;
    if (this.agentTimer) {
      clearTimeout(this.agentTimer);
      this.agentTimer = null;
    }
    this.playPauseIcon.textContent = '▶';
    this.playPauseText.textContent = 'Play';
  }

  async runAgentCycle() {
    if (!this.isAgentRunning || this.state?.status !== 'PLAYING') {
      this.stopAgentLoop();
      return;
    }

    await this.stepAgent();

    if (this.isAgentRunning && this.state?.status === 'PLAYING') {
      this.agentTimer = setTimeout(() => this.runAgentCycle(), this.agentSpeedMs);
    } else {
      this.stopAgentLoop();
    }
  }

  async fetchAdvisorAdvice() {
    if (this.state?.status !== 'PLAYING') return;
    this.askAdvisorBtn.disabled = true;
    this.askAdvisorBtn.textContent = '🧠 Analyzing...';

    try {
      const res = await fetch('/api/game/advisor');
      if (res.ok) {
        const advice = await res.json();
        this.renderAdvisorAdvice(advice);
      }
    } catch (err) {
      console.error('Advisor query failed:', err);
    } finally {
      this.askAdvisorBtn.disabled = false;
      this.askAdvisorBtn.innerHTML = '<span>🧠 Consult Jev</span><span class="key-badge">[A]</span>';
    }
  }

  renderAdvisorAdvice(advice) {
    if (!advice || advice.error) return;

    this.advisorBanner.style.display = 'block';
    const confPct = Math.round((advice.confidence || 0.8) * 100);
    this.advisorRecText.textContent = `${advice.action} (${confPct}% confidence)`;
    this.executeAdvisorMoveBtn.dataset.action = advice.action;

    // Update telemetry gauges with advice data
    this.updateTelemetryFromDecision(advice);
    window.soundFX.playTone(740, 'sine', 0.15, 0.2);
  }

  executeRecommendedAdvisorMove() {
    const action = this.executeAdvisorMoveBtn.dataset.action;
    if (action) {
      this.executePlayerAction(action);
    }
  }

  // --------------------------------------------------------------------------
  // UI Rendering & State Sync
  // --------------------------------------------------------------------------
  updateGameState(newState, triggerFX = false) {
    const prevState = this.state;
    this.state = newState;

    // Trigger visual/audio feedback based on state transitions
    if (triggerFX && newState.last_outcome) {
      this.handleCombatFX(newState.last_outcome, prevState);
    }

    // Sync Mode
    if (newState.mode && newState.mode !== this.mode) {
      this.switchMode(newState.mode);
    }

    // Render Components
    this.renderHeaderAndMinimap();
    this.renderStage();
    this.renderActionButtons();
    this.renderTelemetry();
    this.renderLogs();

    // Check Victory / Game Over
    if (newState.status === 'VICTORY') {
      this.showVictoryModal();
    } else if (newState.status === 'GAME_OVER') {
      this.showGameOverModal();
    }
  }

  handleCombatFX(outcome, prevState) {
    // Floating damage numbers
    if (outcome.damage_dealt > 0) {
      const isCrit = outcome.details?.some(d => d.includes('CRITICAL'));
      this.spawnFloatingText(
        isCrit ? `CRIT! -${outcome.damage_dealt}` : `-${outcome.damage_dealt}`,
        isCrit ? 'crit' : 'damage-dealt',
        'enemy'
      );
      if (isCrit) {
        window.soundFX.playCrit();
      } else {
        window.soundFX.playAttack();
      }
      this.shakeElement(this.enemyCard);
    }

    if (outcome.damage_taken > 0) {
      this.spawnFloatingText(`-${outcome.damage_taken}`, 'damage-taken', 'hero');
      if (outcome.details?.some(d => d.includes('Iron Guard'))) {
        window.soundFX.playBlock();
      } else {
        window.soundFX.playTone(180, 'sawtooth', 0.2, 0.25);
      }
      this.shakeElement(this.mainStage);
    }

    if (outcome.healing_done > 0) {
      this.spawnFloatingText(`+${outcome.healing_done} HP`, 'heal', 'hero');
      window.soundFX.playPotion();
    }

    if (outcome.gold_gained > 0) {
      this.spawnFloatingText(`+${outcome.gold_gained} Gold`, 'gold', 'hero');
      window.soundFX.playGold();
    }
  }

  spawnFloatingText(text, typeClass, target) {
    const el = document.createElement('div');
    el.className = `floating-damage ${typeClass}`;
    el.textContent = text;

    if (target === 'hero') {
      el.style.left = '22%';
    } else {
      el.style.left = '68%';
    }

    this.floatingTextContainer.appendChild(el);
    setTimeout(() => {
      if (el.parentNode) el.parentNode.removeChild(el);
    }, 1200);
  }

  shakeElement(el) {
    if (!el) return;
    el.classList.remove('shake-screen');
    void el.offsetWidth; // Trigger reflow
    el.classList.add('shake-screen');
    setTimeout(() => el.classList.remove('shake-screen'), 450);
  }

  renderHeaderAndMinimap() {
    const dungeon = this.state.dungeon;
    const player = this.state.player;

    this.floorBadgeText.textContent = `Floor ${dungeon.current_floor} of ${dungeon.total_floors}`;
    this.turnCounterText.textContent = `Turn ${player.total_turns}`;

    // Render floor progress nodes
    this.roomProgressTrack.innerHTML = '';
    dungeon.floor_progress.forEach((node, idx) => {
      const nodeEl = document.createElement('div');
      nodeEl.className = `room-node ${node.status} ${node.is_boss ? 'boss' : ''}`;
      if (node.is_boss) {
        nodeEl.textContent = '💀';
      } else if (node.type === 'treasure') {
        nodeEl.textContent = '💎';
      } else if (node.type === 'shrine') {
        nodeEl.textContent = '✨';
      } else {
        nodeEl.textContent = idx + 1;
      }
      this.roomProgressTrack.appendChild(nodeEl);
    });
  }

  renderStage() {
    const room = this.state.current_room;
    const player = this.state.player;
    const phase = this.state.encounter_phase;

    if (!room) return;

    this.roomName.textContent = `🚪 ${room.name}`;
    this.roomDesc.textContent = room.description;

    // Phase Pill
    this.encounterPhasePill.textContent = phase.toUpperCase();
    this.encounterPhasePill.className = `phase-pill ${phase}`;

    // Hero HUD
    this.heroHpText.textContent = `${player.health} / ${player.max_health}`;
    const heroHpRatio = Math.max(0, Math.min(100, (player.health / player.max_health) * 100));
    this.heroHpFill.style.width = `${heroHpRatio}%`;
    this.heroHpFill.className = `hp-fill ${heroHpRatio < 30 ? 'danger' : heroHpRatio < 60 ? 'warning' : ''}`;

    this.heroAtk.textContent = player.attack;
    this.heroDef.textContent = player.defense;
    this.heroPotions.textContent = player.potions;
    this.heroGold.textContent = player.gold;

    // Enemy vs Chamber Display
    if (phase === 'combat' && room.enemy) {
      this.chamberStage.style.display = 'none';
      this.enemyCard.style.display = 'flex';
      this.vsBadge.style.display = 'flex';

      const enemy = room.enemy;
      this.enemyName.textContent = enemy.name;
      this.enemyPortrait.textContent = this.portraits[enemy.name] || '👹';
      this.enemyHpText.textContent = `${enemy.health} / ${enemy.max_health}`;

      const enemyHpRatio = Math.max(0, Math.min(100, (enemy.health / enemy.max_health) * 100));
      this.enemyHpFill.style.width = `${enemyHpRatio}%`;

      this.enemyAtk.textContent = enemy.attack;
      this.enemyDef.textContent = enemy.defense;
      this.enemyGold.textContent = `${enemy.reward_gold}g`;
    } else {
      // Non-combat chamber
      this.enemyCard.style.display = 'none';
      this.vsBadge.style.display = 'none';
      this.chamberStage.style.display = 'flex';

      this.chamberIcon.textContent = this.portraits[room.type] || '🚪';
      this.chamberDescription.textContent = room.description;
    }
  }

  renderActionButtons() {
    this.actionButtonsContainer.innerHTML = '';
    const actions = this.state.available_actions || [];

    if (this.state.status !== 'PLAYING') {
      const notice = document.createElement('div');
      notice.style.gridColumn = '1 / -1';
      notice.style.textAlign = 'center';
      notice.style.color = 'var(--text-dim)';
      notice.textContent = 'Run completed. Press New Run to play again.';
      this.actionButtonsContainer.appendChild(notice);
      return;
    }

    const actionIcons = {
      'ATTACK': { icon: '⚔️ Attack', class: 'attack' },
      'DEFEND': { icon: '🛡️ Defend', class: 'defend' },
      'USE_POTION': { icon: '🧪 Potion', class: 'potion' },
      'FLEE': { icon: '🏃 Flee', class: '' },
      'TAKE_TREASURE': { icon: '💎 Claim Loot', class: 'loot' },
      'USE_SHRINE': { icon: '✨ Rest & Heal', class: 'potion' },
      'DISARM_TRAP': { icon: '🔧 Disarm Trap', class: 'attack' },
      'SEARCH_MORE': { icon: '🔍 Search Chamber', class: 'loot' },
      'IGNORE': { icon: '🚶 Bypass Room', class: '' },
      'LEFT': { icon: '⬅️ Left Path', class: 'defend' },
      'RIGHT': { icon: '➡️ Right Path', class: 'defend' },
      'BACK': { icon: '↩️ Backtrack', class: '' },
    };

    actions.forEach((act, idx) => {
      const btn = document.createElement('button');
      const info = actionIcons[act] || { icon: act, class: '' };
      btn.className = `action-btn ${info.class}`;
      btn.dataset.action = act;

      // Disable potion if 0 potions available
      if (act === 'USE_POTION' && this.state.player.potions <= 0) {
        btn.disabled = true;
      }

      btn.innerHTML = `
        <span>${info.icon}</span>
        <span class="key-badge">[${idx + 1}]</span>
      `;

      btn.addEventListener('click', () => {
        if (this.mode === 'manual') {
          this.executePlayerAction(act);
        }
      });

      this.actionButtonsContainer.appendChild(btn);
    });
  }

  renderTelemetry() {
    const decision = this.state.last_decision;
    if (decision) {
      this.updateTelemetryFromDecision(decision);
    }
  }

  updateTelemetryFromDecision(d) {
    if (!d) return;

    this.latencyTicker.textContent = `⚡ ${d.latency_ms || 120} ms`;
    this.brainActionText.textContent = d.action || 'READY';
    const confPct = Math.round((d.confidence || 0.8) * 100);
    this.brainConfidenceText.textContent = `${confPct}%`;

    // Probability Bars
    this.probBarsContainer.innerHTML = '';
    const probs = d.probabilities || {};
    const probEntries = Object.entries(probs);

    if (probEntries.length > 0) {
      probEntries.forEach(([choice, pVal]) => {
        const pct = Math.round(pVal * 100);
        const row = document.createElement('div');
        row.className = 'prob-row';
        row.innerHTML = `
          <div class="prob-labels">
            <span>${choice}</span>
            <span>${pct}%</span>
          </div>
          <div class="prob-track">
            <div class="prob-bar ${choice.toLowerCase()}" style="width: ${pct}%;"></div>
          </div>
        `;
        this.probBarsContainer.appendChild(row);
      });
    }

    // Threat / Value / Risk Meter
    let meterVal = 5.0;
    let label = 'Threat Level';
    if (d.threat_level !== undefined) {
      meterVal = d.threat_level;
      label = 'Threat Level';
    } else if (d.value_score !== undefined) {
      meterVal = d.value_score;
      label = 'Room Value';
    } else if (d.risk_score !== undefined) {
      meterVal = d.risk_score;
      label = 'Route Risk';
    }

    this.meterLabel.textContent = label;
    this.meterValText.textContent = `${meterVal.toFixed(1)} / 10`;
    this.meterFill.style.width = `${Math.min(100, meterVal * 10)}%`;

    // Noul Probabilities
    if (d.use_potion_first_prob !== undefined) {
      this.noulPotionProb.textContent = `${Math.round(d.use_potion_first_prob * 100)}%`;
    }
    if (d.flee_worth_it_prob !== undefined) {
      this.noulFleeProb.textContent = `${Math.round(d.flee_worth_it_prob * 100)}%`;
    }
  }

  renderLogs() {
    this.logScrollArea.innerHTML = '';
    const logs = this.state.logs || [];

    const filtered = logs.filter(log => {
      if (this.activeLogFilter === 'all') return true;
      return log.type === this.activeLogFilter;
    });

    filtered.forEach(log => {
      const entry = document.createElement('div');
      entry.className = `log-entry ${log.type}`;
      entry.innerHTML = `
        <span class="log-turn">[T${log.turn}]</span>
        <span>${log.text}</span>
      `;
      this.logScrollArea.appendChild(entry);
    });

    // Auto scroll to bottom
    this.logScrollArea.scrollTop = this.logScrollArea.scrollHeight;
  }

  showVictoryModal() {
    this.stopAgentLoop();
    window.soundFX.playVictory();
    const p = this.state.player;
    this.vTurns.textContent = p.total_turns;
    this.vGold.textContent = p.gold;
    this.vKills.textContent = p.kills;
    this.vRooms.textContent = p.rooms_cleared;
    this.victoryModal.classList.add('active');
  }

  showGameOverModal() {
    this.stopAgentLoop();
    window.soundFX.playDefeat();
    const p = this.state.player;
    this.dTurns.textContent = p.total_turns;
    this.dFloor.textContent = p.floor;
    this.dGold.textContent = p.gold;
    this.dKills.textContent = p.kills;
    this.gameOverModal.classList.add('active');
  }
}

// Boot application when DOM is ready
window.addEventListener('DOMContentLoaded', () => {
  window.gameApp = new WebGameApp();
});

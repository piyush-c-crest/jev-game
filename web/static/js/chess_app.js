/**
 * chess_app.js - Core Web Controller for JEV vs JEV Autonomous Chess Arena.
 * Coordinates chess.js client rules, REST API sync, Web Audio, SVG rendering,
 * and live System One telemetry dashboards.
 */

class ChessApp {
  constructor() {
    this.chess = new (window.Chess || Chess)();
    this.orientation = 'white'; // 'white' or 'black'
    this.isAutoPlaying = false;
    this.autoPlayTimer = null;
    this.speedMs = 1200;
    this.isRequestInProgress = false;
    this.lastMove = null; // { from: 'e2', to: 'e4' }
    this.selectedSquare = null;
    this.serverState = null;

    this.initElements();
    this.bindEvents();
    this.renderBoard();
    this.loadInitialState();
  }

  initElements() {
    // Top Nav
    this.soundToggleBtn = document.getElementById('soundToggleBtn');
    this.resetBtn = document.getElementById('resetBtn');

    // Match Header Info
    this.matchStatusText = document.getElementById('matchStatusText');
    this.matchTurnText = document.getElementById('matchTurnText');

    // Evaluation Bar
    this.evalScoreBadge = document.getElementById('evalScoreBadge');
    this.evalFillWhite = document.getElementById('evalFillWhite');

    // Player Cards
    this.whiteCard = document.getElementById('whiteCard');
    this.blackCard = document.getElementById('blackCard');
    this.whiteStatusPill = document.getElementById('whiteStatusPill');
    this.blackStatusPill = document.getElementById('blackStatusPill');
    this.whiteCapturedRack = document.getElementById('whiteCapturedRack');
    this.blackCapturedRack = document.getElementById('blackCapturedRack');
    this.whiteMaterialDiff = document.getElementById('whiteMaterialDiff');
    this.blackMaterialDiff = document.getElementById('blackMaterialDiff');

    // Board
    this.boardFrame = document.getElementById('boardFrame');

    // Playback Controls
    this.playPauseBtn = document.getElementById('playPauseBtn');
    this.playPauseIcon = document.getElementById('playPauseIcon');
    this.playPauseText = document.getElementById('playPauseText');
    this.stepBtn = document.getElementById('stepBtn');
    this.speedSelect = document.getElementById('speedSelect');
    this.flipBtn = document.getElementById('flipBtn');

    // Telemetry Panel
    this.latencyTicker = document.getElementById('latencyTicker');
    this.telemetryAgentBadge = document.getElementById('telemetryAgentBadge');
    this.telemetryMoveText = document.getElementById('telemetryMoveText');
    this.telemetryConfidenceText = document.getElementById('telemetryConfidenceText');
    this.telemetryProbContainer = document.getElementById('telemetryProbContainer');
    this.sharpnessValText = document.getElementById('sharpnessValText');
    this.sharpnessFill = document.getElementById('sharpnessFill');

    // Chronicle
    this.chronicleTableBody = document.getElementById('chronicleTableBody');
    this.chronicleScrollArea = document.getElementById('chronicleScrollArea');

    // Modal
    this.resultModal = document.getElementById('resultModal');
    this.modalTitle = document.getElementById('modalTitle');
    this.modalMessage = document.getElementById('modalMessage');
    this.modalStatsTurns = document.getElementById('modalStatsTurns');
    this.modalStatsWinner = document.getElementById('modalStatsWinner');
    this.modalRestartBtn = document.getElementById('modalRestartBtn');
  }

  bindEvents() {
    this.playPauseBtn.addEventListener('click', () => this.toggleAutoPlay());
    this.stepBtn.addEventListener('click', () => this.stepTurn());
    this.speedSelect.addEventListener('change', (e) => {
      this.speedMs = parseInt(e.target.value, 10);
    });

    this.flipBtn.addEventListener('click', () => {
      this.orientation = this.orientation === 'white' ? 'black' : 'white';
      this.renderBoard();
    });

    this.resetBtn.addEventListener('click', () => this.resetGame());
    this.modalRestartBtn.addEventListener('click', () => {
      this.resultModal.classList.remove('active');
      this.resetGame();
    });

    // Sound toggle
    this.soundToggleBtn.addEventListener('click', () => {
      const isMuted = window.chessAudio.toggleMute();
      this.soundToggleBtn.innerHTML = isMuted ? '🔇 Muted' : '🔊 Sound';
    });
    this.soundToggleBtn.innerHTML = window.chessAudio.isMuted() ? '🔇 Muted' : '🔊 Sound';

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;

      if (e.code === 'Space') {
        e.preventDefault();
        this.toggleAutoPlay();
      } else if (e.key === 's' || e.key === 'S' || e.key === 'ArrowRight') {
        e.preventDefault();
        this.stepTurn();
      } else if (e.key === 'f' || e.key === 'F') {
        this.flipBtn.click();
      } else if (e.key === 'r' || e.key === 'R') {
        this.resetGame();
      } else if (e.key === 'm' || e.key === 'M') {
        this.soundToggleBtn.click();
      }
    });
  }

  async loadInitialState() {
    try {
      const res = await fetch('/api/chess/state');
      if (res.ok) {
        const data = await res.json();
        this.serverState = data;
        if (data.fen && data.fen !== this.chess.fen()) {
          this.chess.load(data.fen);
        }
        this.updateUI();
      }
    } catch (err) {
      console.warn('Initial chess state load:', err);
    }
  }

  renderBoard() {
    this.boardFrame.innerHTML = '';
    const isFlipped = this.orientation === 'black';

    const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
    const ranks = ['8', '7', '6', '5', '4', '3', '2', '1'];

    const displayRanks = isFlipped ? [...ranks].reverse() : ranks;
    const displayFiles = isFlipped ? [...files].reverse() : files;

    const inCheck = this.chess.in_check();
    const turnColor = this.chess.turn(); // 'w' or 'b'

    displayRanks.forEach((rank, rIdx) => {
      displayFiles.forEach((file, fIdx) => {
        const squareKey = `${file}${rank}`;
        const fileNum = file.charCodeAt(0) - 97;
        const rankNum = parseInt(rank, 10);
        const isLight = (fileNum + rankNum) % 2 !== 0;

        const sqDiv = document.createElement('div');
        sqDiv.className = `square ${isLight ? 'light' : 'dark'}`;
        sqDiv.dataset.square = squareKey;

        // Coordinate Labels on edges
        if (fIdx === 0) {
          const rankLabel = document.createElement('span');
          rankLabel.className = 'coord-rank';
          rankLabel.textContent = rank;
          sqDiv.appendChild(rankLabel);
        }
        if (rIdx === 7) {
          const fileLabel = document.createElement('span');
          fileLabel.className = 'coord-file';
          fileLabel.textContent = file;
          sqDiv.appendChild(fileLabel);
        }

        // Highlight Last Move
        if (this.lastMove) {
          if (this.lastMove.from === squareKey) sqDiv.classList.add('highlight-from');
          if (this.lastMove.to === squareKey) sqDiv.classList.add('highlight-to');
        }

        // Check Highlight on active King
        const piece = this.chess.get(squareKey);
        if (inCheck && piece && piece.type === 'k' && piece.color === turnColor) {
          sqDiv.classList.add('highlight-check');
        }

        // Render Piece SVG
        if (piece) {
          const pieceKey = `${piece.color}${piece.type.toUpperCase()}`;
          const svgMarkup = window.CHESS_PIECES ? window.CHESS_PIECES[pieceKey] : null;
          if (svgMarkup) {
            const pieceContainer = document.createElement('div');
            pieceContainer.className = 'piece-svg-container';
            pieceContainer.innerHTML = svgMarkup;
            sqDiv.appendChild(pieceContainer);
          }
        }

        // Click to preview legal moves
        sqDiv.addEventListener('click', () => this.handleSquareClick(squareKey));

        this.boardFrame.appendChild(sqDiv);
      });
    });

    // Render preview legal move dots if square is selected
    if (this.selectedSquare) {
      this.renderLegalMoveDots(this.selectedSquare);
    }
  }

  handleSquareClick(sqKey) {
    if (this.selectedSquare === sqKey) {
      this.selectedSquare = null;
      this.renderBoard();
      return;
    }
    const piece = this.chess.get(sqKey);
    if (piece && piece.color === this.chess.turn()) {
      this.selectedSquare = sqKey;
      this.renderBoard();
    } else {
      this.selectedSquare = null;
      this.renderBoard();
    }
  }

  renderLegalMoveDots(sqKey) {
    const legalMoves = this.chess.moves({ square: sqKey, verbose: true });
    legalMoves.forEach((m) => {
      const targetSq = this.boardFrame.querySelector(`[data-square="${m.to}"]`);
      if (targetSq) {
        if (m.captured) {
          const ring = document.createElement('div');
          ring.className = 'legal-capture-ring';
          targetSq.appendChild(ring);
        } else {
          const dot = document.createElement('div');
          dot.className = 'legal-dot';
          targetSq.appendChild(dot);
        }
      }
    });
  }

  toggleAutoPlay() {
    if (this.isAutoPlaying) {
      this.stopAutoPlay();
    } else {
      this.startAutoPlay();
    }
  }

  startAutoPlay() {
    if (this.chess.game_over()) return;
    this.isAutoPlaying = true;
    this.playPauseIcon.textContent = '⏸';
    this.playPauseText.textContent = 'Pause';
    this.runAutoPlayCycle();
  }

  stopAutoPlay() {
    this.isAutoPlaying = false;
    if (this.autoPlayTimer) {
      clearTimeout(this.autoPlayTimer);
      this.autoPlayTimer = null;
    }
    this.playPauseIcon.textContent = '▶';
    this.playPauseText.textContent = 'Auto-Play';
  }

  async runAutoPlayCycle() {
    if (!this.isAutoPlaying || this.chess.game_over()) {
      this.stopAutoPlay();
      return;
    }

    await this.stepTurn();

    if (this.isAutoPlaying && !this.chess.game_over()) {
      this.autoPlayTimer = setTimeout(() => this.runAutoPlayCycle(), this.speedMs);
    } else {
      this.stopAutoPlay();
    }
  }

  async stepTurn() {
    if (this.isRequestInProgress || this.chess.game_over()) {
      if (this.chess.game_over()) this.checkTerminalState();
      return;
    }

    this.isRequestInProgress = true;
    this.selectedSquare = null;

    const activeColor = this.chess.turn() === 'w' ? 'white' : 'black';
    this.setAgentThinking(activeColor, true);

    const legalMoves = this.chess.moves({ verbose: true });
    const inCheck = this.chess.in_check();

    try {
      const res = await fetch('/api/chess/step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fen: this.chess.fen(),
          legal_moves: legalMoves,
          in_check: inCheck,
          history: this.chess.history(),
          is_game_over: this.chess.game_over(),
        }),
      });

      if (res.ok) {
        const state = await res.json();
        this.serverState = state;

        const decision = activeColor === 'white' ? state.last_white_decision : state.last_black_decision;
        if (decision && decision.move) {
          const moveResult = this.chess.move(decision.move);
          if (moveResult) {
            this.lastMove = { from: moveResult.from, to: moveResult.to };

            // Trigger Sound Effects
            if (this.chess.in_checkmate()) {
              window.chessAudio.playVictory();
            } else if (this.chess.in_check()) {
              window.chessAudio.playCheck();
            } else if (moveResult.flags.includes('k') || moveResult.flags.includes('q')) {
              window.chessAudio.playCastle();
            } else if (moveResult.captured) {
              window.chessAudio.playCapture();
            } else {
              window.chessAudio.playMove();
            }

            this.updateTelemetry(decision, activeColor);
          } else {
            console.warn('Move not accepted by client chess.js (strict):', decision.move);
            const fallbackResult = this.chess.move(decision.move, { sloppy: true });
            if (fallbackResult) {
              this.lastMove = { from: fallbackResult.from, to: fallbackResult.to };
              window.chessAudio.playMove();
              this.updateTelemetry(decision, activeColor);
            }
          }
        }

        this.updateUI();
        this.renderBoard();
        this.checkTerminalState();
      }
    } catch (err) {
      console.error('Failed to advance chess turn:', err);
    } finally {
      this.setAgentThinking(activeColor, false);
      this.isRequestInProgress = false;
    }
  }

  setAgentThinking(color, isThinking) {
    if (color === 'white') {
      this.whiteStatusPill.className = `player-status-pill ${isThinking ? 'thinking' : 'active'}`;
      this.whiteStatusPill.innerHTML = isThinking ? '<span class="spinner"></span> Thinking...' : 'Ready';
    } else {
      this.blackStatusPill.className = `player-status-pill ${isThinking ? 'thinking' : 'active'}`;
      this.blackStatusPill.innerHTML = isThinking ? '<span class="spinner"></span> Thinking...' : 'Ready';
    }
  }

  updateUI() {
    const isWhiteTurn = this.chess.turn() === 'w';

    // Highlight active card
    if (isWhiteTurn) {
      this.whiteCard.classList.add('active-turn');
      this.blackCard.classList.remove('active-turn');
    } else {
      this.blackCard.classList.add('active-turn');
      this.whiteCard.classList.remove('active-turn');
    }

    // Match Header Text
    const fullMoves = Math.floor(this.chess.history().length / 2) + 1;
    this.matchTurnText.textContent = `Turn ${fullMoves} • ${isWhiteTurn ? 'White' : 'Black'} to Move`;

    if (this.chess.in_checkmate()) {
      this.matchStatusText.textContent = `👑 Checkmate! ${isWhiteTurn ? 'Black' : 'White'} Wins!`;
    } else if (this.chess.in_check()) {
      this.matchStatusText.textContent = `⚠️ Check! King is threatened!`;
    } else if (this.chess.in_draw()) {
      this.matchStatusText.textContent = `🤝 Game Drawn`;
    } else {
      this.matchStatusText.textContent = `⚔️ In Progress`;
    }

    // Captured pieces tally & material difference
    this.renderCapturedPieces();

    // PGN Chronicle Table
    this.renderChronicle();
  }

  renderCapturedPieces() {
    const board = this.chess.board();
    const initialCounts = { p: 8, n: 2, b: 2, r: 2, q: 1 };

    const currentWhite = { p: 0, n: 0, b: 0, r: 0, q: 0 };
    const currentBlack = { p: 0, n: 0, b: 0, r: 0, q: 0 };

    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const piece = board[r][c];
        if (piece && piece.type !== 'k') {
          if (piece.color === 'w') currentWhite[piece.type]++;
          else currentBlack[piece.type]++;
        }
      }
    }

    // White captured = missing Black pieces
    this.whiteCapturedRack.innerHTML = '';
    let whiteDiffScore = 0;
    const pieceValues = { p: 1, n: 3, b: 3, r: 5, q: 9 };

    for (const [type, init] of Object.entries(initialCounts)) {
      const missingBlack = Math.max(0, init - currentBlack[type]);
      for (let i = 0; i < missingBlack; i++) {
        const el = document.createElement('span');
        el.className = 'captured-piece-mini';
        el.innerHTML = window.CHESS_PIECES ? window.CHESS_PIECES[`b${type.toUpperCase()}`] || '' : type;
        this.whiteCapturedRack.appendChild(el);
      }
    }

    // Black captured = missing White pieces
    this.blackCapturedRack.innerHTML = '';
    for (const [type, init] of Object.entries(initialCounts)) {
      const missingWhite = Math.max(0, init - currentWhite[type]);
      for (let i = 0; i < missingWhite; i++) {
        const el = document.createElement('span');
        el.className = 'captured-piece-mini';
        el.innerHTML = window.CHESS_PIECES ? window.CHESS_PIECES[`w${type.toUpperCase()}`] || '' : type;
        this.blackCapturedRack.appendChild(el);
      }
    }

    // Total material score difference
    let wMat = 0, bMat = 0;
    for (const [t, val] of Object.entries(pieceValues)) {
      wMat += currentWhite[t] * val;
      bMat += currentBlack[t] * val;
    }
    const diff = wMat - bMat;
    this.whiteMaterialDiff.textContent = diff > 0 ? `+${diff}` : '';
    this.blackMaterialDiff.textContent = diff < 0 ? `+${Math.abs(diff)}` : '';
  }

  updateTelemetry(d, color) {
    if (!d) return;

    this.latencyTicker.textContent = `⚡ ${d.latency_ms || 240} ms`;
    this.telemetryAgentBadge.textContent = color.toUpperCase();
    this.telemetryAgentBadge.style.color = color === 'white' ? '#f1f5f9' : 'var(--accent-gold)';

    this.telemetryMoveText.textContent = d.move || '--';
    const confPct = Math.round((d.confidence || 0.8) * 100);
    this.telemetryConfidenceText.textContent = `${confPct}%`;

    // Probability Bars
    this.telemetryProbContainer.innerHTML = '';
    const probs = d.probabilities || {};
    const entries = Object.entries(probs).slice(0, 4);

    if (entries.length > 0) {
      entries.forEach(([moveKey, pVal]) => {
        const pct = Math.round(pVal * 100);
        const row = document.createElement('div');
        row.className = 'prob-row';
        row.innerHTML = `
          <div class="prob-labels">
            <span>${moveKey}</span>
            <span>${pct}%</span>
          </div>
          <div class="prob-track">
            <div class="prob-bar" style="width: ${pct}%; background: var(--accent-gold);"></div>
          </div>
        `;
        this.telemetryProbContainer.appendChild(row);
      });
    }

    // Tactical Sharpness
    const sharpness = Math.round((d.tactical_sharpness || 0.25) * 100);
    this.sharpnessValText.textContent = `${sharpness}%`;
    this.sharpnessFill.style.width = `${sharpness}%`;

    // Evaluation Bar update
    if (d.eval_score !== undefined) {
      // Scale 0.0 to 10.0 -> eval ratio
      const score = d.eval_score;
      const whitePct = Math.min(95, Math.max(5, score * 10));
      this.evalFillWhite.style.height = `${whitePct}%`;

      const numAdvantage = ((score - 5.0) * 1.5).toFixed(1);
      this.evalScoreBadge.textContent = numAdvantage > 0 ? `+${numAdvantage}` : numAdvantage;
    }
  }

  renderChronicle() {
    this.chronicleTableBody.innerHTML = '';
    const history = this.chess.history({ verbose: true });
    const rows = [];

    for (let i = 0; i < history.length; i += 2) {
      const turnNum = Math.floor(i / 2) + 1;
      const wMove = history[i] ? history[i].san : '';
      const bMove = history[i + 1] ? history[i + 1].san : '';
      rows.push({ turn: turnNum, w: wMove, b: bMove });
    }

    rows.forEach((r, idx) => {
      const isLatest = idx === rows.length - 1;
      const tr = document.createElement('tr');
      if (isLatest) tr.className = 'latest-turn';

      const isWhiteLatest = isLatest && !r.b;
      const isBlackLatest = isLatest && Boolean(r.b);

      tr.innerHTML = `
        <td style="color: var(--text-dim);">${r.turn}.</td>
        <td class="${isWhiteLatest ? 'active-move' : ''}">${r.w}</td>
        <td class="${isBlackLatest ? 'active-move' : ''}">${r.b}</td>
      `;
      this.chronicleTableBody.appendChild(tr);
    });

    this.chronicleScrollArea.scrollTop = this.chronicleScrollArea.scrollHeight;
  }

  checkTerminalState() {
    if (!this.chess.game_over()) return;

    this.stopAutoPlay();
    let title = "Game Finished";
    let message = "";
    let winner = "Draw";

    if (this.chess.in_checkmate()) {
      const winnerColor = this.chess.turn() === 'w' ? 'Black (Kronos)' : 'White (Apollo)';
      title = "👑 Checkmate!";
      message = `${winnerColor} delivers checkmate and conquers the board!`;
      winner = winnerColor;
      window.chessAudio.playVictory();
    } else if (this.chess.in_stalemate()) {
      title = "🤝 Stalemate!";
      message = "No legal moves remain and the King is not in check. The game is a draw.";
      window.chessAudio.playDraw();
    } else if (this.chess.in_threefold_repetition()) {
      title = "⚖️ Threefold Repetition!";
      message = "The same position was repeated three times. Game drawn by FIDE rules.";
      window.chessAudio.playDraw();
    } else if (this.chess.insufficient_material()) {
      title = "⚖️ Insufficient Material!";
      message = "Neither player has enough pieces to force checkmate. Game drawn.";
      window.chessAudio.playDraw();
    } else {
      title = "🤝 Draw!";
      message = "The match concluded in an honorable draw.";
      window.chessAudio.playDraw();
    }

    this.modalTitle.textContent = title;
    this.modalMessage.textContent = message;
    this.modalStatsTurns.textContent = Math.floor(this.chess.history().length / 2) + 1;
    this.modalStatsWinner.textContent = winner;
    this.resultModal.classList.add('active');
  }

  async resetGame() {
    this.stopAutoPlay();
    this.selectedSquare = null;
    this.lastMove = null;
    this.chess.reset();
    this.resultModal.classList.remove('active');

    try {
      await fetch('/api/chess/reset', { method: 'POST' });
    } catch (e) {
      console.warn(e);
    }

    this.renderBoard();
    this.updateUI();
    window.chessAudio.playMove();
  }
}

// Boot application when DOM is ready
window.addEventListener('DOMContentLoaded', () => {
  window.chessApp = new ChessApp();
});

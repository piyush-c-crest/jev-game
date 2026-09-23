/**
 * mario_engine.js - Complete Super Mario Bros Engine & Procedural NES Renderer.
 * High-performance 60 FPS HTML5 Canvas engine with sub-pixel physics,
 * continuous AABB tilemap collisions, enemy states, power-ups, and dual-play interface.
 */

class MarioEngine {
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.ctx.imageSmoothingEnabled = false;

        // Virtual NES internal resolution (256x240)
        this.viewWidth = 256;
        this.viewHeight = 240;
        this.tileSize = 16;

        // Game State
        this.mode = options.mode || 'manual'; // 'manual' or 'agent'
        this.state = 'START'; // 'START', 'PLAYING', 'DYING', 'FLAGPOLE', 'CLEARED', 'GAMEOVER'
        this.score = 0;
        this.coins = 0;
        this.world = '1-1';
        this.time = 400;
        this.lives = 3;
        this.timerAccumulator = 0;

        // Camera
        this.cameraX = 0;

        // Level Data
        this.level = null;
        this.grid = [];
        this.gridRows = 15;
        this.gridCols = 212;

        // Entities
        this.mario = null;
        this.enemies = [];
        this.items = []; // Mushrooms, bouncing coins
        this.particles = []; // Shattered bricks, score popups
        this.scenery = [];
        this.floatingCoins = [];

        // Animation counters
        this.globalFrame = 0;

        // Input state
        this.keys = {
            left: false,
            right: false,
            jump: false,
            sprint: false,
            down: false
        };

        // Telemetry & Vision
        this.showVision = false;
        this.agent = null; // Injected MarioAgent instance
        this.telemetryCallback = options.onTelemetry || null;

        // Procedural Sprite Sheet
        this.sprites = {};
        this.initSprites();

        // Bind animation loop
        this.lastTime = 0;
        this.running = false;
        this.loop = this.loop.bind(this);
    }

    /* -------------------------------------------------------------
       PROCEDURAL NES SPRITE GENERATOR (Pixel-Art in Memory)
       ------------------------------------------------------------- */
    initSprites() {
        const createPixelCanvas = (w, h, drawFn) => {
            const c = document.createElement('canvas');
            c.width = w;
            c.height = h;
            const ctx = c.getContext('2d');
            ctx.imageSmoothingEnabled = false;
            drawFn(ctx);
            return c;
        };

        // NES Palette
        const P = {
            RED: '#d82800',
            BROWN: '#8c5200',
            GOLD: '#fc9838',
            BEIGE: '#fce4a0',
            WHITE: '#ffffff',
            BLACK: '#000000',
            BLUE: '#0058f8',
            GREEN: '#00a800',
            DARK_GREEN: '#006800',
            LIGHT_GREEN: '#58d854',
            BRICK_BROWN: '#b84418',
            BRICK_DARK: '#442800',
            PIPE_GREEN_LIGHT: '#84e850',
            PIPE_GREEN_MID: '#00a800',
            PIPE_GREEN_DARK: '#005800',
            SKY_BLUE: '#6888fc',
            QUESTION_YELLOW: '#fc9838',
            QUESTION_BROWN: '#8c5200',
            METAL_GRAY: '#b8b8b8',
            METAL_DARK: '#505050'
        };

        // Helper: draw pixel matrix [rows of strings or numbers]
        const drawMatrix = (ctx, matrix, colorMap, scale = 1, offsetX = 0, offsetY = 0) => {
            for (let r = 0; r < matrix.length; r++) {
                const row = matrix[r];
                for (let c = 0; c < row.length; c++) {
                    const char = row[c];
                    if (char !== ' ' && char !== '.' && colorMap[char]) {
                        ctx.fillStyle = colorMap[char];
                        ctx.fillRect(offsetX + c * scale, offsetY + r * scale, scale, scale);
                    }
                }
            }
        };

        // 1. SMALL MARIO SPRITES (16x16)
        // Mario Colors: R = Red, B = Brown, G = Gold/Skin
        const mColors = { 'R': P.RED, 'B': P.BROWN, 'G': P.GOLD };

        // Idle
        const mIdle = [
            "....RRRRR.......",
            "...RRRRRRRRR....",
            "...BBBGG.G......",
            "..BGBGGG.GGG....",
            "..BGBBGGG.GGG...",
            "..BBGGGGGGGG....",
            "....GGGGGGG.....",
            "...RRBRRR.......",
            "..RRRBRRBRRR....",
            ".RRRRBBBBBRRR...",
            ".GG.RBRBBR.GG...",
            ".GGG.BBBBB.GGG..",
            ".GG.BBBBBBB.GG..",
            "....BBB.BBB.....",
            "...BBB...BBB....",
            "..BBBB...BBBB..."
        ];
        this.sprites.mario_idle = createPixelCanvas(16, 16, ctx => drawMatrix(ctx, mIdle, mColors));

        // Run Frame 1
        const mRun1 = [
            "....RRRRR.......",
            "...RRRRRRRRR....",
            "...BBBGG.G......",
            "..BGBGGG.GGG....",
            "..BGBBGGG.GGG...",
            "..BBGGGGGGGG....",
            "....GGGGGGG.....",
            "...RRBRRR.......",
            "..RRRBRRBRRR....",
            ".RRRRBBBBBRRR...",
            ".GG.RBRBBR.GG...",
            ".GGG.BBBBB.GGG..",
            ".GG.BBBBBBB.GG..",
            "...BBBB.BBB.....",
            "..BBBB...BBB....",
            "..BBB..........."]
        this.sprites.mario_run1 = createPixelCanvas(16, 16, ctx => drawMatrix(ctx, mRun1, mColors));

        // Run Frame 2
        const mRun2 = [
            "....RRRRR.......",
            "...RRRRRRRRR....",
            "...BBBGG.G......",
            "..BGBGGG.GGG....",
            "..BGBBGGG.GGG...",
            "..BBGGGGGGGG....",
            "....GGGGGGG.....",
            "....RRBRR.......",
            "...RRRBRRBRRR...",
            "..RRRRBBBBBRRR..",
            ".GG.RRBRBBR.GG..",
            ".GGG.BBBBBB.GGG.",
            ".GG.BBBBBBB.GG..",
            "....BBBB.BB.....",
            "...BBBB...BB....",
            "..........BBB..."]
        this.sprites.mario_run2 = createPixelCanvas(16, 16, ctx => drawMatrix(ctx, mRun2, mColors));

        // Run Frame 3
        const mRun3 = [
            "....RRRRR.......",
            "...RRRRRRRRR....",
            "...BBBGG.G......",
            "..BGBGGG.GGG....",
            "..BGBBGGG.GGG...",
            "..BBGGGGGGGG....",
            "....GGGGGGG.....",
            "...RRBRRR.......",
            "..RRRBRRBRRR....",
            ".RRRRBBBBBRRR...",
            ".GG.RBRBBR.GG...",
            ".GGG.BBBBB.GGG..",
            ".GG.BBBBBBB.GG..",
            "....BBB.BBBB....",
            "...BBB...BBBB...",
            "...........BBB.."]
        this.sprites.mario_run3 = createPixelCanvas(16, 16, ctx => drawMatrix(ctx, mRun3, mColors));

        // Jump Frame
        const mJump = [
            ".........RRRRR..",
            "........RRRRRRRR",
            "........BBBGG.G.",
            ".......BGBGGG.GG",
            ".......BGBBGGG.G",
            ".......BBGGGGGGG",
            ".........GGGGGGG",
            "..GG...RRBRRR...",
            ".GGG.RRRRBRRBRRR",
            ".GG.RRRRRBBBBBRR",
            "....GG.RBRBBR.GG",
            ".......BBBBBB...",
            "......BBBBBBBB..",
            ".....BBBB.BBBB..",
            "....BBBB...BBBB.",
            "....BBB.....BBB."]
        this.sprites.mario_jump = createPixelCanvas(16, 16, ctx => drawMatrix(ctx, mJump, mColors));

        // Skid Frame
        const mSkid = [
            "....RRRRR.......",
            "...RRRRRRRRR....",
            "...BBBGG.G......",
            "..BGBGGG.GGG....",
            "..BGBBGGG.GGG...",
            "..BBGGGGGGGG....",
            "....GGGGGGG.....",
            "...RRBRRR.......",
            "..RRRBRRBRRR....",
            ".RRRRBBBBBRRR...",
            ".GG.RBRBBR.GG...",
            ".GGG.BBBBB.GGG..",
            ".GG.BBBBBBB.GG..",
            "...BBBBBBBB.....",
            "...BBBB.BBBB....",
            "...BBB...BBB...."]
        this.sprites.mario_skid = createPixelCanvas(16, 16, ctx => drawMatrix(ctx, mSkid, mColors));

        // Death Frame
        const mDie = [
            "....RRRRR.......",
            "...RRRRRRRRR....",
            "...BBBGG.G......",
            "..BGBGGG.GGG....",
            "..BGBBGGG.GGG...",
            "..BBGGGGGGGG....",
            "....GGGGGGG.....",
            "....RRBRRR......",
            "..RRRBRRBRRR....",
            ".RRRRBBBBBRRR...",
            ".GG.RBRBBR.GG...",
            ".GGG.BBBBB.GGG..",
            ".GG.BBBBBBB.GG..",
            "...BBBB.BBBB....",
            "..BBBB...BBBB...",
            ".BBBB.....BBBB.."]
        this.sprites.mario_die = createPixelCanvas(16, 16, ctx => drawMatrix(ctx, mDie, mColors));

        // 2. SUPER MARIO (16x32)
        const sIdle = [
            "....RRRRR.......",
            "...RRRRRRRRR....",
            "...BBBGG.G......",
            "..BGBGGG.GGG....",
            "..BGBBGGG.GGG...",
            "..BBGGGGGGGG....",
            "....GGGGGGG.....",
            "...RRBRRR.......",
            "..RRRBRRBRRR....",
            ".RRRRBRRBRRRR...",
            ".RRRRBBBBBRRR...",
            ".RR.RBRBBR.RR...",
            ".GG.BBBBBB.GG...",
            ".GGG.BBBB.GGG...",
            ".GG..BBBB..GG...",
            "....RRRRRR......",
            "...RRRRRRRR.....",
            "..RRRRRRRRRR....",
            ".RR.RRRRRR.RR...",
            ".GG.RRRRRR.GG...",
            "....BBBBBB......",
            "...BBBBBBBB.....",
            "..BBBBBBBBBB....",
            "..BBBBBBBBBB....",
            "..BBBB..BBBB....",
            "..BBBB..BBBB....",
            "..BBB....BBB....",
            "..BBB....BBB....",
            "..BBB....BBB....",
            ".BBBB....BBBB...",
            ".BBBB....BBBB...",
            ".BBBB....BBBB..."
        ];
        this.sprites.super_idle = createPixelCanvas(16, 32, ctx => drawMatrix(ctx, sIdle, mColors));
        this.sprites.super_run1 = this.sprites.super_idle; // Scaled animations
        this.sprites.super_jump = createPixelCanvas(16, 32, ctx => {
            ctx.drawImage(this.sprites.super_idle, 0, 0);
            ctx.fillStyle = P.GOLD;
            ctx.fillRect(1, 4, 3, 3);
            ctx.fillRect(12, 4, 3, 3);
        });

        // 3. GOOMBA SPRITES (16x16)
        const gColors = { 'B': P.BROWN, 'G': P.GOLD, 'K': P.BLACK, 'W': P.WHITE };
        const gWalk1 = [
            "......BBBB......",
            "....BBBBBBBB....",
            "...BBBBBBBBBB...",
            "..BBBBBBBBBBBB..",
            ".BBBBBBBBBBBBBB.",
            ".BBBKWBBBWKBBBB.",
            ".BBBKWBBBWKBBBB.",
            ".BBBKWBBBWKBBBB.",
            "BBBBKWBBBWKBBBBB",
            "BBBBBBKKBBBBBBBB",
            "BBBBGGGGGGGGBBBB",
            "..GGGGGGGGGGGG..",
            "...GGGGGGGGGG...",
            "..KKKK....KKKK..",
            ".KKKKKK..KKKKKK.",
            ".KKKKKK..KKKKKK."]
        this.sprites.goomba_walk1 = createPixelCanvas(16, 16, ctx => drawMatrix(ctx, gWalk1, gColors));

        const gWalk2 = [
            "......BBBB......",
            "....BBBBBBBB....",
            "...BBBBBBBBBB...",
            "..BBBBBBBBBBBB..",
            ".BBBBBBBBBBBBBB.",
            ".BBBKWBBBWKBBBB.",
            ".BBBKWBBBWKBBBB.",
            ".BBBKWBBBWKBBBB.",
            "BBBBKWBBBWKBBBBB",
            "BBBBBBKKBBBBBBBB",
            "BBBBGGGGGGGGBBBB",
            "..GGGGGGGGGGGG..",
            "...GGGGGGGGGG...",
            "....KKKKKK......",
            "....KKKKKK......",
            ".....KKKK......."]
        this.sprites.goomba_walk2 = createPixelCanvas(16, 16, ctx => drawMatrix(ctx, gWalk2, gColors));

        const gFlat = [
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "......BBBB......",
            "..BBBBBBBBBBBB..",
            ".BBBBKWBBBWKBBBB",
            "BBBBGGGGGGGGBBBB",
            ".KKKKKKKKKKKKKK.",
            "..KKKKKKKKKKKK.."]
        this.sprites.goomba_flat = createPixelCanvas(16, 16, ctx => drawMatrix(ctx, gFlat, gColors));

        // 4. KOOPA TROOPA (16x24 & Shell 16x16)
        const kColors = { 'G': P.GREEN, 'L': P.LIGHT_GREEN, 'W': P.WHITE, 'K': P.BLACK, 'O': P.GOLD, 'R': P.RED };
        const kWalk1 = [
            "......GGGG......",
            "....GGGGGGGG....",
            "....GGGWKG......",
            "...GGGGWKKGG....",
            "...GGGGOGGGG....",
            "....GGGOOO......",
            ".....LLLL.......",
            "...LLGGGGLL.....",
            "..LLGGGGGGLL....",
            ".LLGGWWWWGGLL...",
            ".LLGWWWWWWGLL...",
            ".LLGWWWWWWGLL...",
            ".LLGGWWWWGGLL...",
            "..LLGGGGGGLL....",
            "...LLGGGGLL.....",
            "....OOOOOO......",
            "...OOOOOOOO.....",
            "...OO....OO.....",
            "..OOOO..OOOO....",
            "..OOOO..OOOO....",
            "..OO......OO....",
            "..OO......OO....",
            ".OOOO....OOOO...",
            ".OOOO....OOOO..."]
        this.sprites.koopa_walk1 = createPixelCanvas(16, 24, ctx => drawMatrix(ctx, kWalk1, kColors));

        const kShell = [
            "......GGGG......",
            "....GGGGGGGG....",
            "...GGGGGGGGGG...",
            "..GGGGWWWWGGGG..",
            ".GGGGWWWWWWGGGG.",
            ".GGGGWWWWWWGGGG.",
            "GGGGWWWWWWWWGGGG",
            "GGGGWWWWWWWWGGGG",
            "GGGGWWWWWWWWGGGG",
            "GGGGWWWWWWWWGGGG",
            ".GGGGWWWWWWGGGG.",
            ".GGGGWWWWWWGGGG.",
            "..GGGGWWWWGGGG..",
            "...GGGGGGGGGG...",
            "....GGGGGGGG....",
            "......GGGG......"]
        this.sprites.koopa_shell = createPixelCanvas(16, 16, ctx => drawMatrix(ctx, kShell, kColors));

        // 5. BLOCKS
        // Ground block
        this.sprites.ground = createPixelCanvas(16, 16, ctx => {
            ctx.fillStyle = P.GOLD;
            ctx.fillRect(0, 0, 16, 16);
            ctx.fillStyle = P.BROWN;
            ctx.fillRect(0, 0, 16, 2);
            ctx.fillRect(0, 0, 2, 16);
            ctx.fillRect(14, 0, 2, 16);
            ctx.fillRect(0, 14, 16, 2);
            ctx.fillStyle = P.BLACK;
            ctx.fillRect(4, 4, 8, 8);
            ctx.fillStyle = P.GOLD;
            ctx.fillRect(5, 5, 6, 6);
        });

        // Brick block
        this.sprites.brick = createPixelCanvas(16, 16, ctx => {
            ctx.fillStyle = P.BRICK_BROWN;
            ctx.fillRect(0, 0, 16, 16);
            ctx.fillStyle = P.BRICK_DARK;
            // Mortar horizontal lines
            ctx.fillRect(0, 0, 16, 1);
            ctx.fillRect(0, 4, 16, 1);
            ctx.fillRect(0, 8, 16, 1);
            ctx.fillRect(0, 12, 16, 1);
            // Mortar vertical lines
            ctx.fillRect(8, 0, 1, 4);
            ctx.fillRect(4, 4, 1, 4);
            ctx.fillRect(12, 4, 1, 4);
            ctx.fillRect(8, 8, 1, 4);
            ctx.fillRect(4, 12, 1, 4);
            ctx.fillRect(12, 12, 1, 4);
        });

        // Step Stone Block (stairs)
        this.sprites.step = createPixelCanvas(16, 16, ctx => {
            ctx.fillStyle = P.BRICK_BROWN;
            ctx.fillRect(0, 0, 16, 16);
            ctx.fillStyle = P.BLACK;
            ctx.fillRect(0, 0, 16, 1);
            ctx.fillRect(0, 0, 1, 16);
            ctx.fillStyle = P.GOLD;
            ctx.fillRect(1, 1, 14, 1);
            ctx.fillRect(1, 1, 1, 14);
        });

        // Mystery Block [?] (Frames 0-3 shimmer)
        const qColors = { 'Y': P.QUESTION_YELLOW, 'B': P.QUESTION_BROWN, 'W': P.WHITE, 'K': P.BLACK };
        const qMatrix = [
            "BBBBBBBBBBBBBBBB",
            "BYYYYYYYYYYYYYYB",
            "BYYWWWWWWWWYYYKB",
            "BYYWYYYYYYWWYYKB",
            "BYYWWYYYYYYWYYKB",
            "BYYYYYYYYYWWYYKB",
            "BYYYYYYYYWWYYYKB",
            "BYYYYYYYWWYYYYKB",
            "BYYYYYYYWWYYYYKB",
            "BYYYYYYYYYYYYYKB",
            "BYYYYYYYWWYYYYKB",
            "BYYYYYYYWWYYYYKB",
            "BYYYYYYYYYYYYYKB",
            "BKKKKKKKKKKKKKKB",
            "BBBBBBBBBBBBBBBB",
            "................"
        ];
        this.sprites.mystery0 = createPixelCanvas(16, 16, ctx => drawMatrix(ctx, qMatrix, qColors));
        this.sprites.mystery1 = createPixelCanvas(16, 16, ctx => {
            drawMatrix(ctx, qMatrix, { ...qColors, 'Y': '#e08020' });
        });
        this.sprites.mystery2 = createPixelCanvas(16, 16, ctx => {
            drawMatrix(ctx, qMatrix, { ...qColors, 'Y': '#b06010' });
        });

        // Empty Solid Hit Block
        this.sprites.empty_block = createPixelCanvas(16, 16, ctx => {
            ctx.fillStyle = P.BRICK_BROWN;
            ctx.fillRect(0, 0, 16, 16);
            ctx.fillStyle = P.BLACK;
            ctx.fillRect(0, 0, 16, 1);
            ctx.fillRect(0, 0, 1, 16);
            ctx.fillRect(15, 0, 1, 16);
            ctx.fillRect(0, 15, 16, 1);
            // 4 corner bolts
            ctx.fillRect(2, 2, 2, 2);
            ctx.fillRect(12, 2, 2, 2);
            ctx.fillRect(2, 12, 2, 2);
            ctx.fillRect(12, 12, 2, 2);
        });

        // 6. PIPES
        // Pipe Top-Left (6)
        this.sprites.pipe_tl = createPixelCanvas(16, 16, ctx => {
            ctx.fillStyle = P.PIPE_GREEN_MID;
            ctx.fillRect(0, 0, 16, 16);
            ctx.fillStyle = P.PIPE_GREEN_LIGHT;
            ctx.fillRect(2, 0, 3, 16);
            ctx.fillStyle = P.BLACK;
            ctx.fillRect(0, 0, 16, 2); // Rim top
            ctx.fillRect(0, 0, 2, 16); // Rim left
            ctx.fillRect(0, 14, 16, 2); // Lip
        });

        // Pipe Top-Right (7)
        this.sprites.pipe_tr = createPixelCanvas(16, 16, ctx => {
            ctx.fillStyle = P.PIPE_GREEN_MID;
            ctx.fillRect(0, 0, 16, 16);
            ctx.fillStyle = P.PIPE_GREEN_DARK;
            ctx.fillRect(8, 0, 6, 16);
            ctx.fillStyle = P.BLACK;
            ctx.fillRect(0, 0, 16, 2); // Rim top
            ctx.fillRect(14, 0, 2, 16); // Rim right
            ctx.fillRect(0, 14, 16, 2); // Lip
        });

        // Pipe Shaft-Left (8)
        this.sprites.pipe_sl = createPixelCanvas(16, 16, ctx => {
            ctx.fillStyle = P.PIPE_GREEN_MID;
            ctx.fillRect(2, 0, 14, 16);
            ctx.fillStyle = P.PIPE_GREEN_LIGHT;
            ctx.fillRect(4, 0, 3, 16);
            ctx.fillStyle = P.BLACK;
            ctx.fillRect(2, 0, 2, 16);
        });

        // Pipe Shaft-Right (9)
        this.sprites.pipe_sr = createPixelCanvas(16, 16, ctx => {
            ctx.fillStyle = P.PIPE_GREEN_MID;
            ctx.fillRect(0, 0, 14, 16);
            ctx.fillStyle = P.PIPE_GREEN_DARK;
            ctx.fillRect(6, 0, 6, 16);
            ctx.fillStyle = P.BLACK;
            ctx.fillRect(12, 0, 2, 16);
        });

        // 7. POWER-UPS & ITEMS
        // Super Mushroom (16x16)
        const shroomColors = { 'R': P.RED, 'W': P.WHITE, 'B': P.BEIGE, 'K': P.BLACK };
        const shroomMatrix = [
            "......RRRR......",
            "....RRRRRRRR....",
            "...RRRRWWWRRR...",
            "..RRRWWWWWWRRR..",
            ".RRRWWWWWWWWRRR.",
            ".RRRWWWWWWWWRRR.",
            ".RRWWWWWWWWWWRR.",
            "RRRWWWWWWWWWWRRR",
            "RRRRRRWWWWWRRRRR",
            "..KKKKBBBBKKKK..",
            "..KBBKBKKBKBBK..",
            "..KBBKBKKBKBBK..",
            "..KBBBBBBBBBBK..",
            "...KBBBBBBBBK...",
            "....KKKKKKKK....",
            "................"
        ];
        this.sprites.mushroom = createPixelCanvas(16, 16, ctx => drawMatrix(ctx, shroomMatrix, shroomColors));

        // Spinning Coin (16x16, 4 frames)
        this.sprites.coin0 = createPixelCanvas(16, 16, ctx => {
            ctx.fillStyle = P.GOLD;
            ctx.fillRect(4, 2, 8, 12);
            ctx.fillStyle = P.WHITE;
            ctx.fillRect(6, 4, 4, 8);
            ctx.fillStyle = P.QUESTION_BROWN;
            ctx.fillRect(7, 5, 2, 6);
        });
        this.sprites.coin1 = createPixelCanvas(16, 16, ctx => {
            ctx.fillStyle = P.GOLD;
            ctx.fillRect(6, 2, 4, 12);
            ctx.fillStyle = P.WHITE;
            ctx.fillRect(7, 4, 2, 8);
        });
        this.sprites.coin2 = createPixelCanvas(16, 16, ctx => {
            ctx.fillStyle = P.GOLD;
            ctx.fillRect(7, 2, 2, 12);
        });
        this.sprites.coin3 = this.sprites.coin1;

        // Flagpole & Castle
        this.sprites.flag_top = createPixelCanvas(16, 16, ctx => {
            ctx.fillStyle = P.LIGHT_GREEN;
            ctx.beginPath();
            ctx.arc(8, 8, 6, 0, Math.PI * 2);
            ctx.fill();
        });
        this.sprites.flag_pole = createPixelCanvas(16, 16, ctx => {
            ctx.fillStyle = P.DARK_GREEN;
            ctx.fillRect(7, 0, 2, 16);
        });
        this.sprites.flag_base = createPixelCanvas(16, 16, ctx => {
            ctx.fillStyle = P.DARK_GREEN;
            ctx.fillRect(7, 0, 2, 8);
            ctx.fillStyle = P.BRICK_BROWN;
            ctx.fillRect(0, 8, 16, 8);
        });
        this.sprites.castle_brick = createPixelCanvas(16, 16, ctx => {
            ctx.fillStyle = '#b84418';
            ctx.fillRect(0, 0, 16, 16);
            ctx.fillStyle = '#442800';
            ctx.fillRect(0, 0, 16, 1);
            ctx.fillRect(0, 8, 16, 1);
            ctx.fillRect(8, 0, 1, 8);
            ctx.fillRect(4, 8, 1, 8);
        });
        this.sprites.castle_door = createPixelCanvas(16, 16, ctx => {
            ctx.fillStyle = P.BLACK;
            ctx.fillRect(0, 0, 16, 16);
        });
    }

    /* -------------------------------------------------------------
       LEVEL LOADING & INITIALIZATION
       ------------------------------------------------------------- */
    async loadLevel(difficulty = 'extreme') {
        this.difficulty = difficulty;
        try {
            const resp = await fetch(`/api/mario/level?difficulty=${difficulty}`);
            if (resp.ok) {
                const data = await resp.json();
                this.initLevelData(data);
                return;
            }
        } catch (e) {
            console.warn("Could not fetch level from server, using fallback local generator:", e);
        }
        // Fallback level initialization
        this.initLevelData(this.getFallbackLevel());
    }

    initLevelData(levelData) {
        this.level = levelData;
        this.grid = levelData.grid.map(row => [...row]);
        this.gridRows = levelData.rows;
        this.gridCols = levelData.cols;
        this.scenery = levelData.scenery || [];

        // Reset Mario
        this.mario = {
            x: levelData.spawn ? levelData.spawn.x : 48,
            y: levelData.spawn ? levelData.spawn.y : 192,
            vx: 0,
            vy: 0,
            isSuper: false,
            width: 14,
            height: 16, // 16 for small, 30 for super
            grounded: false,
            facing: 'right', // 'right' or 'left'
            jumpHeld: false,
            jumpFrames: 0,
            maxJumpFrames: 14,
            skidding: false,
            invulnerableTimer: 0, // In frames (~120 for 2s)
            state: 'IDLE', // 'IDLE', 'RUN', 'JUMP', 'SKID', 'DIE', 'FLAGPOLE'
            flagpoleStep: 0,
            deathVy: 0,
            deathY: 0
        };

        // Reset Camera
        this.cameraX = 0;

        // Reset Enemies with extreme speed scaling
        const isExtreme = this.difficulty === 'extreme' || levelData.difficulty === 'extreme';
        const enemyBaseSpeed = isExtreme ? -1.1 : -0.75;

        this.enemies = (levelData.enemies || []).map(e => ({
            type: e.type, // 'goomba' or 'koopa'
            x: e.x,
            y: e.y,
            vx: enemyBaseSpeed,
            vy: 0,
            width: 14,
            height: e.type === 'koopa' ? 24 : 16,
            grounded: false,
            state: 'WALK', // 'WALK', 'FLAT', 'SHELL_IDLE', 'SHELL_SLIDING'
            stateTimer: 0,
            dead: false
        }));

        // Reset Items & Particles
        this.items = [];
        this.particles = [];
        this.floatingCoins = (levelData.coins || []).map(c => ({ ...c, collected: false }));

        this.world = levelData.world || (isExtreme ? '8-4 (EXTREME)' : '1-1');
        this.time = levelData.time || (isExtreme ? 200 : 400);
        this.state = 'PLAYING';

        if (window.marioAudio) {
            window.marioAudio.startBGM();
        }
    }

    getFallbackLevel() {
        // Minimal fallback layout in case of offline testing
        const rows = 15;
        const cols = 212;
        const grid = Array.from({ length: rows }, () => Array(cols).fill(0));
        for (let c = 0; c < cols; c++) {
            if (c !== 69 && c !== 70 && c !== 86 && c !== 87 && c !== 88) {
                grid[13][c] = 1;
                grid[14][c] = 1;
            }
        }
        grid[9][16] = 3; // Mystery
        grid[9][21] = 4; // Shroom
        return {
            world: "1-1",
            rows,
            cols,
            tile_size: 16,
            grid,
            coins: [],
            enemies: [{ type: "goomba", x: 22 * 16, y: 12 * 16 }],
            scenery: [],
            spawn: { x: 48, y: 192 }
        };
    }

    /* -------------------------------------------------------------
       INPUT CONTROLS
       ------------------------------------------------------------- */
    setKey(name, isDown) {
        if (this.keys[name] !== undefined) {
            this.keys[name] = isDown;
        }
    }

    setMode(mode) {
        this.mode = mode;
        // Reset keys when switching modes
        this.keys.left = false;
        this.keys.right = false;
        this.keys.jump = false;
        this.keys.sprint = false;
        this.keys.down = false;
    }

    toggleMode() {
        this.setMode(this.mode === 'manual' ? 'agent' : 'manual');
        return this.mode;
    }

    toggleVision() {
        this.showVision = !this.showVision;
        return this.showVision;
    }

    /* -------------------------------------------------------------
       PHYSICS & UPDATE LOOP (60 FPS)
       ------------------------------------------------------------- */
    start() {
        if (!this.running) {
            this.running = true;
            this.lastTime = performance.now();
            requestAnimationFrame(this.loop);
        }
    }

    stop() {
        this.running = false;
        if (window.marioAudio) {
            window.marioAudio.stopBGM();
        }
    }

    loop(time) {
        if (!this.running) return;
        const dt = Math.min((time - this.lastTime) / 1000, 0.1);
        this.lastTime = time;

        this.update(dt);
        this.render();

        requestAnimationFrame(this.loop);
    }

    update(dt) {
        this.globalFrame++;

        // Timer countdown
        if (this.state === 'PLAYING') {
            this.timerAccumulator += dt;
            if (this.timerAccumulator >= 0.4) { // Classic Mario clock ticks fast
                this.time = Math.max(0, this.time - 1);
                this.timerAccumulator = 0;
                if (this.time === 0) {
                    this.killMario();
                }
            }
        }

        // Autonomous Agent Tick
        if (this.mode === 'agent' && this.agent && this.state === 'PLAYING') {
            const botControls = this.agent.update(this);
            this.keys.left = !!botControls.left;
            this.keys.right = !!botControls.right;
            this.keys.jump = !!botControls.jump;
            this.keys.sprint = !!botControls.sprint;
            this.keys.down = !!botControls.down;
        }

        // Mario State Machine
        if (this.state === 'PLAYING') {
            this.updateMarioPhysics();
            this.updateEnemies();
            this.updateItems();
            this.updateFloatingCoins();
            this.updateParticles();
            this.updateCamera();
        } else if (this.state === 'DYING') {
            this.updateMarioDeath();
            this.updateParticles();
        } else if (this.state === 'FLAGPOLE') {
            this.updateFlagpoleSequence();
            this.updateParticles();
        }

        // Telemetry update callback
        if (this.telemetryCallback) {
            this.telemetryCallback(this.getTelemetryData());
        }
    }

    /* -------------------------------------------------------------
       MARIO PHYSICS & COLLISION
       ------------------------------------------------------------- */
    updateMarioPhysics() {
        const m = this.mario;
        m.height = m.isSuper ? 30 : 16;
        m.width = 14;

        if (m.invulnerableTimer > 0) {
            m.invulnerableTimer--;
        }

        // Horizontal Movement & Acceleration
        const maxSpeed = this.keys.sprint ? 3.6 : 2.2;
        const accel = 0.14;
        const friction = 0.09;
        const skidFriction = 0.35;

        if (this.keys.right) {
            m.facing = 'right';
            if (m.vx < 0) {
                // Skidding
                m.skidding = true;
                m.vx += skidFriction;
            } else {
                m.skidding = false;
                m.vx = Math.min(m.vx + accel, maxSpeed);
            }
        } else if (this.keys.left) {
            m.facing = 'left';
            if (m.vx > 0) {
                // Skidding
                m.skidding = true;
                m.vx -= skidFriction;
            } else {
                m.skidding = false;
                m.vx = Math.max(m.vx - accel, -maxSpeed);
            }
        } else {
            m.skidding = false;
            // Friction deceleration
            if (m.vx > 0) {
                m.vx = Math.max(0, m.vx - friction);
            } else if (m.vx < 0) {
                m.vx = Math.min(0, m.vx + friction);
            }
        }

        // Variable Jump Physics
        const gravity = 0.36;
        const maxFallSpeed = 7.0;

        if (this.keys.jump) {
            if (m.grounded && !m.jumpHeld) {
                // Initiate Jump
                m.grounded = false;
                m.jumpHeld = true;
                m.jumpFrames = 0;
                m.vy = -5.6 - Math.abs(m.vx) * 0.15; // Sprint boost on jump
                if (window.marioAudio) {
                    window.marioAudio.playJump(m.isSuper);
                }
            } else if (m.jumpHeld && m.jumpFrames < m.maxJumpFrames) {
                // Continue holding jump for higher arc
                m.jumpFrames++;
                m.vy -= 0.18; // Sustained upward boost
            }
        } else {
            // Releasing jump cuts upward velocity for short hop
            m.jumpHeld = false;
            if (m.vy < -2.0) {
                m.vy = -2.0;
            }
        }

        // Apply Gravity
        m.vy = Math.min(m.vy + gravity, maxFallSpeed);

        // Update Animation State
        if (!m.grounded) {
            m.state = 'JUMP';
        } else if (m.skidding) {
            m.state = 'SKID';
        } else if (Math.abs(m.vx) > 0.1) {
            m.state = 'RUN';
        } else {
            m.state = 'IDLE';
        }

        // SUB-PIXEL COLLISION RESOLUTION
        // Horizontal Movement & Wall Collisions
        m.x += m.vx;

        // Prevent Mario from moving past left camera boundary (authentic NES camera lock)
        if (m.x < this.cameraX) {
            m.x = this.cameraX;
            m.vx = 0;
        }

        this.resolveTileCollisionX(m);

        // Vertical Movement & Ground/Ceiling Collisions
        m.grounded = false;
        m.y += m.vy;
        this.resolveTileCollisionY(m);

        // Pit detection (Mario falls off bottom of screen)
        if (m.y > this.viewHeight + 16) {
            this.killMario();
        }
    }

    // Horizontal Tile Collision Sweep
    resolveTileCollisionX(entity) {
        const leftTile = Math.floor(entity.x / this.tileSize);
        const rightTile = Math.floor((entity.x + entity.width - 1) / this.tileSize);
        const topTile = Math.floor(entity.y / this.tileSize);
        const bottomTile = Math.floor((entity.y + entity.height - 1) / this.tileSize);

        for (let r = topTile; r <= bottomTile; r++) {
            for (let c = leftTile; c <= rightTile; c++) {
                if (this.isSolidTile(r, c)) {
                    if (entity.vx > 0) {
                        entity.x = c * this.tileSize - entity.width;
                        entity.vx = 0;
                    } else if (entity.vx < 0) {
                        entity.x = (c + 1) * this.tileSize;
                        entity.vx = 0;
                    }
                    return;
                }
            }
        }
    }

    // Vertical Tile Collision Sweep (Ground & Head Bumps)
    resolveTileCollisionY(entity) {
        const leftTile = Math.floor(entity.x / this.tileSize);
        const rightTile = Math.floor((entity.x + entity.width - 1) / this.tileSize);
        const topTile = Math.floor(entity.y / this.tileSize);
        const bottomTile = Math.floor((entity.y + entity.height - 1) / this.tileSize);

        for (let r = topTile; r <= bottomTile; r++) {
            for (let c = leftTile; c <= rightTile; c++) {
                if (this.isSolidTile(r, c)) {
                    if (entity.vy > 0) {
                        // Landing on top of tile
                        entity.y = r * this.tileSize - entity.height;
                        entity.vy = 0;
                        entity.grounded = true;
                        return;
                    } else if (entity.vy < 0) {
                        // Head bump into block from below
                        entity.y = (r + 1) * this.tileSize;
                        entity.vy = 0;
                        if (entity === this.mario) {
                            this.onBlockHit(r, c);
                        }
                        return;
                    }
                }
            }
        }
    }

    isSolidTile(r, c) {
        if (r < 0 || r >= this.gridRows || c < 0 || c >= this.gridCols) {
            return false;
        }
        const t = this.grid[r][c];
        // Solid tiles: 1 (Ground), 2 (Brick), 3 (? Coin), 4 (? Shroom), 5 (Hit/Metal), 6-9 (Pipes), 13 (Castle Brick), 16 (Step)
        return (t === 1 || t === 2 || t === 3 || t === 4 || t === 5 || (t >= 6 && t <= 9) || t === 13 || t === 16);
    }

    /* -------------------------------------------------------------
       BLOCK HITTING & ITEM SPAWNING
       ------------------------------------------------------------- */
    onBlockHit(row, col) {
        const tile = this.grid[row][col];

        // 1. Mystery Block [?] with Coin (3)
        if (tile === 3) {
            this.grid[row][col] = 5; // Turns to empty/metal block
            this.score += 200;
            this.coins += 1;
            this.spawnBouncingCoin(col * this.tileSize, (row - 1) * this.tileSize);
            this.spawnScorePopup(col * this.tileSize + 4, row * this.tileSize - 8, 200);
            if (window.marioAudio) {
                window.marioAudio.playCoin();
            }
        }
        // 2. Mystery Block [?] with Super Mushroom (4)
        else if (tile === 4) {
            this.grid[row][col] = 5; // Turns to empty/metal block
            this.spawnMushroom(col * this.tileSize, (row - 1) * this.tileSize);
            if (window.marioAudio) {
                window.marioAudio.playPowerupAppear();
            }
        }
        // 3. Breakable Brick (2)
        else if (tile === 2) {
            if (this.mario.isSuper) {
                // Super Mario shatters brick!
                this.grid[row][col] = 0; // Empty
                this.score += 50;
                this.spawnShatteredBricks(col * this.tileSize, row * this.tileSize);
                if (window.marioAudio) {
                    window.marioAudio.playBrickBreak();
                }
            } else {
                // Small Mario bumps brick without breaking
                if (window.marioAudio) {
                    window.marioAudio.playBlockBump();
                }
            }
        }
        // 4. Already hit or solid metal block
        else {
            if (window.marioAudio) {
                window.marioAudio.playBlockBump();
            }
        }
    }

    spawnBouncingCoin(x, y) {
        this.items.push({
            type: 'bouncing_coin',
            x: x + 4,
            y: y,
            vy: -4.5,
            frame: 0,
            timer: 30
        });
    }

    spawnMushroom(x, y) {
        this.items.push({
            type: 'mushroom',
            x: x,
            y: y,
            vx: 1.2,
            vy: 0,
            width: 16,
            height: 16,
            grounded: false
        });
    }

    spawnShatteredBricks(x, y) {
        // 4 debris fragments spinning outward
        const frags = [
            { vx: -1.8, vy: -4.5 },
            { vx: 1.8, vy: -4.5 },
            { vx: -1.2, vy: -3.0 },
            { vx: 1.2, vy: -3.0 }
        ];
        frags.forEach(f => {
            this.particles.push({
                type: 'brick_shard',
                x: x + 4,
                y: y + 4,
                vx: f.vx,
                vy: f.vy,
                angle: 0,
                timer: 45
            });
        });
    }

    spawnScorePopup(x, y, text) {
        this.particles.push({
            type: 'score_text',
            text: text.toString(),
            x: x,
            y: y,
            vy: -0.8,
            timer: 40
        });
    }

    /* -------------------------------------------------------------
       ENEMIES & INTERACTIONS
       ------------------------------------------------------------- */
    updateEnemies() {
        const m = this.mario;

        for (let i = 0; i < this.enemies.length; i++) {
            const e = this.enemies[i];
            if (e.dead) continue;

            // Only update enemies active near camera viewport
            if (e.x < this.cameraX - 64 || e.x > this.cameraX + this.viewWidth + 64) {
                continue;
            }

            // Squashed flat state
            if (e.state === 'FLAT') {
                e.stateTimer--;
                if (e.stateTimer <= 0) {
                    e.dead = true;
                }
                continue;
            }

            // Gravity
            e.vy = Math.min(e.vy + 0.35, 6.0);

            // Horizontal Patrol
            e.x += e.vx;
            // Wall collisions
            const leftTile = Math.floor(e.x / this.tileSize);
            const rightTile = Math.floor((e.x + e.width - 1) / this.tileSize);
            const topTile = Math.floor(e.y / this.tileSize);
            const bottomTile = Math.floor((e.y + e.height - 1) / this.tileSize);

            for (let r = topTile; r <= bottomTile; r++) {
                if (e.vx > 0 && this.isSolidTile(r, rightTile)) {
                    e.x = rightTile * this.tileSize - e.width;
                    e.vx = -Math.abs(e.vx);
                    break;
                } else if (e.vx < 0 && this.isSolidTile(r, leftTile)) {
                    e.x = (leftTile + 1) * this.tileSize;
                    e.vx = Math.abs(e.vx);
                    break;
                }
            }

            // Vertical movement
            e.grounded = false;
            e.y += e.vy;
            const newBottomTile = Math.floor((e.y + e.height - 1) / this.tileSize);
            const eMidXTile = Math.floor((e.x + e.width / 2) / this.tileSize);
            if (this.isSolidTile(newBottomTile, eMidXTile)) {
                e.y = newBottomTile * this.tileSize - e.height;
                e.vy = 0;
                e.grounded = true;
            }

            // Sliding shell destroys other enemies!
            if (e.state === 'SHELL_SLIDING') {
                for (let j = 0; j < this.enemies.length; j++) {
                    if (i === j) continue;
                    const other = this.enemies[j];
                    if (!other.dead && this.checkAABB(e, other)) {
                        other.dead = true;
                        this.score += 500;
                        this.spawnScorePopup(other.x, other.y, 500);
                        if (window.marioAudio) {
                            window.marioAudio.playKickShell();
                        }
                    }
                }
            }

            // MARIO VS ENEMY COLLISION
            if (this.checkAABB(m, e)) {
                // Check if Mario stomped enemy from above
                const isFalling = m.vy > 0;
                const marioFeet = m.y + m.height;
                const enemyCenterY = e.y + e.height / 2;

                if (isFalling && marioFeet <= enemyCenterY + 6) {
                    // STOMP HIT!
                    if (e.type === 'goomba') {
                        e.state = 'FLAT';
                        e.stateTimer = 25; // 0.4s
                        this.score += 100;
                        this.spawnScorePopup(e.x + 2, e.y, 100);
                        if (window.marioAudio) {
                            window.marioAudio.playStomp();
                        }
                    } else if (e.type === 'koopa') {
                        if (e.state === 'WALK') {
                            e.state = 'SHELL_IDLE';
                            e.vx = 0;
                            e.height = 16;
                            e.y += 8;
                            this.score += 100;
                            this.spawnScorePopup(e.x + 2, e.y, 100);
                            if (window.marioAudio) {
                                window.marioAudio.playStomp();
                            }
                        } else if (e.state === 'SHELL_SLIDING') {
                            // Stop sliding shell
                            e.state = 'SHELL_IDLE';
                            e.vx = 0;
                            if (window.marioAudio) {
                                window.marioAudio.playStomp();
                            }
                        }
                    }

                    // Mario bounces upward
                    m.vy = this.keys.jump ? -7.2 : -5.0;
                    m.y = e.y - m.height;
                } else {
                    // HORIZONTAL TOUCH
                    if (e.type === 'koopa' && e.state === 'SHELL_IDLE') {
                        // Kick the shell!
                        const kickDir = (m.x + m.width / 2 < e.x + e.width / 2) ? 1 : -1;
                        e.state = 'SHELL_SLIDING';
                        e.vx = kickDir * 5.5;
                        this.score += 200;
                        this.spawnScorePopup(e.x + 2, e.y, 200);
                        if (window.marioAudio) {
                            window.marioAudio.playKickShell();
                        }
                    } else {
                        // Hurt Mario!
                        if (m.invulnerableTimer === 0) {
                            this.damageMario();
                        }
                    }
                }
            }
        }
    }

    /* -------------------------------------------------------------
       ITEMS (MUSHROOM & BOUNCING COIN)
       ------------------------------------------------------------- */
    updateItems() {
        const m = this.mario;

        for (let i = this.items.length - 1; i >= 0; i--) {
            const item = this.items[i];

            if (item.type === 'bouncing_coin') {
                item.vy += 0.35;
                item.y += item.vy;
                item.timer--;
                if (item.timer <= 0) {
                    this.items.splice(i, 1);
                }
            } else if (item.type === 'mushroom') {
                // Mushroom gravity & sliding
                item.vy = Math.min(item.vy + 0.35, 6.0);
                item.x += item.vx;
                this.resolveTileCollisionX(item);

                item.grounded = false;
                item.y += item.vy;
                this.resolveTileCollisionY(item);

                // Mario touches mushroom!
                if (this.checkAABB(m, item)) {
                    this.score += 1000;
                    this.spawnScorePopup(item.x, item.y, 1000);
                    this.mario.isSuper = true;
                    this.items.splice(i, 1);
                    if (window.marioAudio) {
                        window.marioAudio.playPowerup();
                    }
                }
            }
        }
    }

    updateFloatingCoins() {
        const m = this.mario;
        for (const coin of this.floatingCoins) {
            if (coin.collected) continue;
            // Distance check to Mario
            const dx = (coin.x) - (m.x + m.width / 2);
            const dy = (coin.y) - (m.y + m.height / 2);
            if (Math.hypot(dx, dy) < 14) {
                coin.collected = true;
                this.coins++;
                this.score += 200;
                this.spawnScorePopup(coin.x, coin.y, 200);
                if (window.marioAudio) {
                    window.marioAudio.playCoin();
                }
            }
        }
    }

    updateParticles() {
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            p.timer--;
            if (p.timer <= 0) {
                this.particles.splice(i, 1);
                continue;
            }

            if (p.type === 'brick_shard') {
                p.vy += 0.35;
                p.x += p.vx;
                p.y += p.vy;
                p.angle += 0.2;
            } else if (p.type === 'score_text') {
                p.y += p.vy;
            }
        }
    }

    checkAABB(a, b) {
        return (
            a.x < b.x + b.width &&
            a.x + a.width > b.x &&
            a.y < b.y + b.height &&
            a.y + a.height > b.y
        );
    }

    /* -------------------------------------------------------------
       CAMERA & LEVEL COMPLETION
       ------------------------------------------------------------- */
    updateCamera() {
        const m = this.mario;
        // Scroll forward only (authentic NES lock)
        const targetX = m.x - 90;
        if (targetX > this.cameraX) {
            this.cameraX = targetX;
        }

        // Check Flagpole Collision (World 1-1 completion)
        const flagpoleCol = this.level.flagpole ? this.level.flagpole.col : 198;
        const poleX = flagpoleCol * this.tileSize + 6;
        if (m.x >= poleX - 4 && m.x <= poleX + 10 && this.state === 'PLAYING') {
            this.startFlagpoleSequence(poleX);
        }
    }

    startFlagpoleSequence(poleX) {
        this.state = 'FLAGPOLE';
        this.mario.state = 'FLAGPOLE';
        this.mario.x = poleX - 4;
        this.mario.vx = 0;
        this.mario.vy = 2.0; // Slide down pole
        this.score += Math.max(500, Math.floor((200 - this.mario.y) * 20));
        if (window.marioAudio) {
            window.marioAudio.playStageClear();
        }
    }

    updateFlagpoleSequence() {
        const m = this.mario;
        const groundY = 12 * this.tileSize;

        if (m.y < groundY) {
            // Slide down pole
            m.y = Math.min(m.y + 2.0, groundY);
        } else {
            // Hop off pole and walk right into castle
            m.x += 1.2;
            m.facing = 'right';
            m.state = 'RUN';

            // Reached castle door
            const castleDoorX = this.level.castle ? this.level.castle.door_x : (204 * 16 + 8);
            if (m.x >= castleDoorX) {
                this.state = 'CLEARED';
                this.submitScore('cleared');
            }
        }
    }

    /* -------------------------------------------------------------
       DAMAGE & DEATH
       ------------------------------------------------------------- */
    damageMario() {
        const m = this.mario;
        if (m.isSuper) {
            m.isSuper = false;
            m.invulnerableTimer = 120; // 2 seconds flashing
            if (window.marioAudio) {
                window.marioAudio.playPowerdown();
            }
        } else {
            this.killMario();
        }
    }

    killMario() {
        if (this.state === 'DYING') return;
        this.state = 'DYING';
        this.mario.state = 'DIE';
        this.mario.vx = 0;
        this.mario.deathVy = -6.5;
        this.mario.deathY = this.mario.y;
        this.lives--;

        if (window.marioAudio) {
            window.marioAudio.playDie();
        }

        setTimeout(() => {
            if (this.lives > 0) {
                this.initLevelData(this.level);
            } else {
                this.state = 'GAMEOVER';
                this.submitScore('game_over');
            }
        }, 3200);
    }

    updateMarioDeath() {
        const m = this.mario;
        m.deathVy += 0.3;
        m.y += m.deathVy;
    }

    async submitScore(status) {
        try {
            await fetch('/api/mario/scores', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    player_name: this.mode === 'agent' ? 'MarioBot-AI' : 'Player',
                    score: this.score,
                    coins: this.coins,
                    time_left: this.time,
                    mode: this.mode,
                    status: status
                })
            });
        } catch (e) {
            console.error("Score submit error:", e);
        }
    }

    /* -------------------------------------------------------------
       RENDERING PIPELINE (60 FPS Pixel Art)
       ------------------------------------------------------------- */
    render() {
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Determine uniform scale to fit canvas
        const scaleX = this.canvas.width / this.viewWidth;
        const scaleY = this.canvas.height / this.viewHeight;

        ctx.save();
        ctx.scale(scaleX, scaleY);

        // 1. Sky Background
        ctx.fillStyle = '#6888fc';
        ctx.fillRect(0, 0, this.viewWidth, this.viewHeight);

        // 2. Scenery (Hills, Bushes, Clouds)
        this.renderScenery(ctx);

        // 3. Tilemap
        this.renderTiles(ctx);

        // 4. Floating Coins
        this.renderFloatingCoins(ctx);

        // 5. Items (Mushrooms, Bouncing Coins)
        this.renderItems(ctx);

        // 6. Enemies
        this.renderEnemies(ctx);

        // 7. Mario
        this.renderMario(ctx);

        // 8. Particles (Debris & Score Popups)
        this.renderParticles(ctx);

        // 9. Vision Telemetry Overlay (when active)
        if (this.showVision && this.state === 'PLAYING') {
            this.renderVisionOverlay(ctx);
        }

        ctx.restore();
    }

    renderScenery(ctx) {
        for (const item of this.scenery) {
            const rx = item.x - this.cameraX;
            if (rx < -64 || rx > this.viewWidth + 64) continue;

            if (item.type === 'cloud') {
                ctx.fillStyle = '#ffffff';
                ctx.beginPath();
                ctx.arc(rx + 16, item.y + 12, 12, 0, Math.PI * 2);
                ctx.arc(rx + 28, item.y + 8, 14, 0, Math.PI * 2);
                ctx.arc(rx + 42, item.y + 12, 12, 0, Math.PI * 2);
                ctx.fill();
            } else if (item.type === 'hill') {
                ctx.fillStyle = '#00a800';
                ctx.beginPath();
                ctx.moveTo(rx, item.y + 32);
                ctx.lineTo(rx + 24, item.y);
                ctx.lineTo(rx + 48, item.y + 32);
                ctx.fill();
                ctx.fillStyle = '#005800';
                ctx.fillRect(rx + 20, item.y + 6, 8, 8);
            } else if (item.type === 'bush') {
                ctx.fillStyle = '#00a800';
                ctx.beginPath();
                ctx.arc(rx + 10, item.y + 12, 8, 0, Math.PI * 2);
                ctx.arc(rx + 22, item.y + 10, 10, 0, Math.PI * 2);
                ctx.arc(rx + 34, item.y + 12, 8, 0, Math.PI * 2);
                ctx.fill();
            }
        }
    }

    renderTiles(ctx) {
        const startCol = Math.max(0, Math.floor(this.cameraX / this.tileSize));
        const endCol = Math.min(this.gridCols - 1, Math.ceil((this.cameraX + this.viewWidth) / this.tileSize));

        const shimmerFrame = Math.floor(this.globalFrame / 10) % 3;

        for (let r = 0; r < this.gridRows; r++) {
            for (let c = startCol; c <= endCol; c++) {
                const tile = this.grid[r][c];
                if (tile === 0) continue;

                const screenX = c * this.tileSize - this.cameraX;
                const screenY = r * this.tileSize;

                let sprite = null;
                switch (tile) {
                    case 1: sprite = this.sprites.ground; break;
                    case 2: sprite = this.sprites.brick; break;
                    case 3:
                    case 4:
                        sprite = shimmerFrame === 0 ? this.sprites.mystery0 :
                                 shimmerFrame === 1 ? this.sprites.mystery1 : this.sprites.mystery2;
                        break;
                    case 5: sprite = this.sprites.empty_block; break;
                    case 6: sprite = this.sprites.pipe_tl; break;
                    case 7: sprite = this.sprites.pipe_tr; break;
                    case 8: sprite = this.sprites.pipe_sl; break;
                    case 9: sprite = this.sprites.pipe_sr; break;
                    case 10: sprite = this.sprites.flag_top; break;
                    case 11: sprite = this.sprites.flag_pole; break;
                    case 12: sprite = this.sprites.flag_base; break;
                    case 13: sprite = this.sprites.castle_brick; break;
                    case 14: sprite = this.sprites.castle_door; break;
                    case 15: sprite = this.sprites.castle_brick; break;
                    case 16: sprite = this.sprites.step; break;
                }

                if (sprite) {
                    ctx.drawImage(sprite, Math.floor(screenX), Math.floor(screenY));
                }
            }
        }
    }

    renderFloatingCoins(ctx) {
        const coinFrame = Math.floor(this.globalFrame / 8) % 4;
        const sprite = this.sprites[`coin${coinFrame}`];

        for (const coin of this.floatingCoins) {
            if (coin.collected) continue;
            const rx = coin.x - this.cameraX;
            if (rx >= -16 && rx <= this.viewWidth) {
                ctx.drawImage(sprite, Math.floor(rx - 8), Math.floor(coin.y - 8));
            }
        }
    }

    renderItems(ctx) {
        for (const item of this.items) {
            const rx = item.x - this.cameraX;
            if (rx < -16 || rx > this.viewWidth) continue;

            if (item.type === 'bouncing_coin') {
                const coinFrame = Math.floor(this.globalFrame / 6) % 4;
                ctx.drawImage(this.sprites[`coin${coinFrame}`], Math.floor(rx), Math.floor(item.y));
            } else if (item.type === 'mushroom') {
                ctx.drawImage(this.sprites.mushroom, Math.floor(rx), Math.floor(item.y));
            }
        }
    }

    renderEnemies(ctx) {
        const walkFrame = Math.floor(this.globalFrame / 10) % 2;

        for (const e of this.enemies) {
            if (e.dead) continue;
            const rx = e.x - this.cameraX;
            if (rx < -32 || rx > this.viewWidth + 32) continue;

            let sprite = null;
            if (e.type === 'goomba') {
                if (e.state === 'FLAT') {
                    sprite = this.sprites.goomba_flat;
                } else {
                    sprite = walkFrame === 0 ? this.sprites.goomba_walk1 : this.sprites.goomba_walk2;
                }
            } else if (e.type === 'koopa') {
                if (e.state === 'SHELL_IDLE' || e.state === 'SHELL_SLIDING') {
                    sprite = this.sprites.koopa_shell;
                } else {
                    sprite = this.sprites.koopa_walk1;
                }
            }

            if (sprite) {
                ctx.drawImage(sprite, Math.floor(rx), Math.floor(e.y));
            }
        }
    }

    renderMario(ctx) {
        const m = this.mario;
        const rx = m.x - this.cameraX;

        // Invulnerability flicker
        if (m.invulnerableTimer > 0 && (Math.floor(m.invulnerableTimer / 4) % 2 === 0)) {
            return;
        }

        let sprite = null;
        if (m.state === 'DIE') {
            sprite = this.sprites.mario_die;
        } else if (m.isSuper) {
            if (m.state === 'JUMP') sprite = this.sprites.super_jump;
            else if (m.state === 'RUN') sprite = this.sprites.super_run1;
            else sprite = this.sprites.super_idle;
        } else {
            if (m.state === 'JUMP') sprite = this.sprites.mario_jump;
            else if (m.state === 'SKID') sprite = this.sprites.mario_skid;
            else if (m.state === 'RUN') {
                const runCycle = Math.floor(this.globalFrame / 6) % 3;
                sprite = runCycle === 0 ? this.sprites.mario_run1 :
                         runCycle === 1 ? this.sprites.mario_run2 : this.sprites.mario_run3;
            } else {
                sprite = this.sprites.mario_idle;
            }
        }

        if (sprite) {
            ctx.save();
            if (m.facing === 'left') {
                ctx.translate(Math.floor(rx + 16), Math.floor(m.y));
                ctx.scale(-1, 1);
                ctx.drawImage(sprite, 0, 0);
            } else {
                ctx.drawImage(sprite, Math.floor(rx), Math.floor(m.y));
            }
            ctx.restore();
        }
    }

    renderParticles(ctx) {
        for (const p of this.particles) {
            const rx = p.x - this.cameraX;
            if (p.type === 'brick_shard') {
                ctx.save();
                ctx.translate(rx, p.y);
                ctx.rotate(p.angle);
                ctx.fillStyle = '#b84418';
                ctx.fillRect(-3, -3, 6, 6);
                ctx.restore();
            } else if (p.type === 'score_text') {
                ctx.font = '8px "Press Start 2P", monospace';
                ctx.fillStyle = '#ffffff';
                ctx.fillText(p.text, rx, p.y);
            }
        }
    }

    /* -------------------------------------------------------------
       AGENT VISION & TELEMETRY OVERLAY
       ------------------------------------------------------------- */
    renderVisionOverlay(ctx) {
        const m = this.mario;
        const marioCenter = { x: m.x - this.cameraX + 8, y: m.y + m.height / 2 };

        // 1. Sensory Lookahead Cones & Rays
        ctx.strokeStyle = 'rgba(0, 255, 128, 0.4)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(marioCenter.x, marioCenter.y);
        ctx.lineTo(marioCenter.x + 160, marioCenter.y - 30);
        ctx.moveTo(marioCenter.x, marioCenter.y);
        ctx.lineTo(marioCenter.x + 180, marioCenter.y);
        ctx.moveTo(marioCenter.x, marioCenter.y);
        ctx.lineTo(marioCenter.x + 160, marioCenter.y + 40);
        ctx.stroke();

        // 2. Parabolic Jump Trajectory Arc
        ctx.strokeStyle = 'rgba(255, 235, 59, 0.85)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        let simX = m.x;
        let simY = m.y;
        let simVx = (this.keys.sprint ? 3.6 : 2.2) * (m.facing === 'left' ? -1 : 1);
        let simVy = -6.2;
        ctx.moveTo(simX - this.cameraX + 8, simY + 8);
        for (let step = 0; step < 26; step++) {
            simX += simVx;
            simVy += 0.36;
            simY += simVy;
            ctx.lineTo(simX - this.cameraX + 8, simY + 8);
        }
        ctx.stroke();
        ctx.setLineDash([]);

        // 3. Enemy Danger Bounding Boxes
        for (const e of this.enemies) {
            if (e.dead) continue;
            const rx = e.x - this.cameraX;
            if (rx >= -20 && rx <= this.viewWidth + 20) {
                ctx.strokeStyle = '#ff3d00';
                ctx.lineWidth = 1;
                ctx.strokeRect(rx - 1, e.y - 1, e.width + 2, e.height + 2);

                // Label tag
                ctx.fillStyle = '#ff3d00';
                ctx.font = '6px monospace';
                ctx.fillText(e.type.toUpperCase(), rx, e.y - 3);
            }
        }

        // 4. Mystery Block Targets
        const startCol = Math.max(0, Math.floor(this.cameraX / this.tileSize));
        const endCol = Math.min(this.gridCols - 1, Math.ceil((this.cameraX + this.viewWidth) / this.tileSize));
        for (let r = 0; r < this.gridRows; r++) {
            for (let c = startCol; c <= endCol; c++) {
                const t = this.grid[r][c];
                if (t === 3 || t === 4) {
                    const bx = c * this.tileSize - this.cameraX;
                    ctx.strokeStyle = '#00e5ff';
                    ctx.strokeRect(bx, r * this.tileSize, 16, 16);
                }
            }
        }
    }

    getTelemetryData() {
        return {
            mode: this.mode,
            state: this.state,
            score: this.score,
            coins: this.coins,
            world: this.world,
            time: this.time,
            lives: this.lives,
            marioX: this.mario ? Math.floor(this.mario.x) : 0,
            marioY: this.mario ? Math.floor(this.mario.y) : 0,
            marioVx: this.mario ? this.mario.vx.toFixed(2) : 0,
            marioVy: this.mario ? this.mario.vy.toFixed(2) : 0,
            isSuper: this.mario ? this.mario.isSuper : false,
            keys: { ...this.keys },
            activeEnemies: this.enemies.filter(e => !e.dead).length,
            agentObjective: (this.agent && this.agent.currentObjective) ? this.agent.currentObjective : 'IDLE',
            hazardDist: (this.agent && this.agent.nearestHazardDist) ? this.agent.nearestHazardDist : 999
        };
    }
}

window.MarioEngine = MarioEngine;

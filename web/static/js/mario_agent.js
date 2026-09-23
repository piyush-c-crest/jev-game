/**
 * mario_agent.js - Autonomous AI Agent ("Mario Bot") for Super Mario Bros.
 * Uses real-time 60 FPS sensory grid analysis, hazard prediction,
 * gap jump solver, stomp trajectory alignment, and power-up opportunism.
 */

class MarioAgent {
    constructor() {
        this.currentObjective = 'SURVEY_PATH';
        this.nearestHazardDist = 999;
        this.stuckCounter = 0;
        this.lastX = 0;
        this.jumpHoldTimer = 0;
        this.jumpTargetFrames = 0;

        // Visual telemetry details
        this.visionScan = {
            detectedPit: false,
            detectedObstacle: false,
            detectedEnemy: null,
            targetBlock: null
        };
    }

    /**
     * Main update tick called by MarioEngine at 60 FPS when in 'agent' mode.
     * Returns virtual controller key states: { left, right, jump, sprint, down }
     */
    update(engine) {
        const m = engine.mario;
        if (!m || engine.state !== 'PLAYING') {
            return { left: false, right: false, jump: false, sprint: false, down: false };
        }

        // Check if Mario is stuck
        if (Math.abs(m.x - this.lastX) < 0.1 && m.grounded) {
            this.stuckCounter++;
        } else {
            this.stuckCounter = 0;
        }
        this.lastX = m.x;

        // 1. Sensory Scan Ahead
        const sensor = this.scanEnvironment(engine);
        this.nearestHazardDist = sensor.nearestHazardDist;

        // Default inputs
        let right = true;
        let left = false;
        let jump = false;
        let sprint = false;
        let down = false;
        let objective = 'SURVEY_PATH';

        // Manage active jump hold duration (for variable jump height)
        if (this.jumpHoldTimer > 0) {
            jump = true;
            sprint = true;
            this.jumpHoldTimer--;
        }

        // DECISION HIERARCHY

        // 1. PIT / GAP CLEARANCE (Highest survival priority)
        if (sensor.pitAhead && sensor.pitDist < 85) {
            objective = 'SPRINT_JUMP_GAP';
            sprint = true;
            right = true;

            // Trigger jump right at the precipice of the pit (within 16-24px of edge)
            if (sensor.pitDist <= 24 && m.grounded) {
                jump = true;
                // Hold jump for maximum distance across the gap, capped if low ceiling
                this.jumpHoldTimer = sensor.lowCeiling ? 6 : 14;
            }
        }

        // 2. INCOMING SLIDING SHELL (Instant threat)
        else if (sensor.slidingShellAhead && sensor.slidingShellDist < 90) {
            objective = 'LEAP_SLIDING_SHELL';
            sprint = true;
            if (sensor.slidingShellDist < 60 && m.grounded) {
                jump = true;
                this.jumpHoldTimer = sensor.lowCeiling ? 5 : 12;
            }
        }

        // 3. ENEMY AHEAD (Goomba / Koopa)
        else if (sensor.enemyAhead && sensor.enemyDist < 100) {
            const e = sensor.enemyAhead;

            if (e.state === 'SHELL_IDLE') {
                // Stationary Koopa shell: kick it forward!
                objective = 'KICK_SHELL';
                right = true;
            } else {
                objective = 'STOMP_ATTACK';
                sprint = true;

                if (m.grounded) {
                    // Time jump to launch stomp trajectory
                    if (sensor.enemyDist <= 50) {
                        jump = true;
                        this.jumpHoldTimer = sensor.lowCeiling ? 5 : 10;
                    }
                } else {
                    // In mid-air: steer toward enemy to guarantee stomp landing
                    if (m.x + m.width / 2 < e.x + e.width / 2 - 2) {
                        right = true;
                        left = false;
                    } else if (m.x + m.width / 2 > e.x + e.width / 2 + 2) {
                        left = true;
                        right = false;
                    }
                }
            }
        }

        // 4. PIPE OR WALL OBSTACLE
        else if (sensor.obstacleAhead && sensor.obstacleDist < 36) {
            objective = 'CLEAR_PIPE';
            sprint = true;
            right = true;

            if (m.grounded && sensor.obstacleDist <= 28) {
                jump = true;
                // Higher hold time for taller pipes (height 3-4 tiles)
                this.jumpHoldTimer = sensor.obstacleHeight > 2 ? 14 : 9;
            }
        }

        // 5. STUCK RECOVERY
        else if (this.stuckCounter > 12 && m.grounded) {
            objective = 'UNSTUCK_JUMP';
            jump = true;
            sprint = true;
            right = true;
            this.jumpHoldTimer = 12;
            this.stuckCounter = 0;
        }

        // 6. MUSHROOM PURSUIT
        else if (sensor.mushroomAhead) {
            objective = 'HUNT_MUSHROOM';
            sprint = true;
            if (sensor.mushroomAhead.x > m.x) {
                right = true;
                left = false;
            } else {
                left = true;
                right = false;
            }
            if (m.grounded && sensor.mushroomAhead.y < m.y - 12) {
                jump = true;
            }
        }

        // 7. MYSTERY BLOCK LOOTING
        else if (sensor.mysteryBlockAhead && sensor.mysteryDist < 30) {
            objective = 'LOOT_MYSTERY_BLOCK';
            right = true;
            if (m.grounded && Math.abs(sensor.mysteryBlockAhead.x - (m.x + 8)) < 12) {
                jump = true;
                this.jumpHoldTimer = 8;
            }
        }

        // 8. CRUISE FORWARD
        else {
            objective = 'SURVEY_PATH';
            right = true;
            // Sprint if the way ahead is completely clear
            if (sensor.nearestHazardDist > 120 && !sensor.obstacleAhead) {
                sprint = true;
            }
        }

        this.currentObjective = objective;

        return {
            left,
            right,
            jump,
            sprint,
            down
        };
    }

    /**
     * Senses tiles, pits, pipes, enemies, and items ahead of Mario
     */
    scanEnvironment(engine) {
        const m = engine.mario;
        const currentTileCol = Math.floor(m.x / engine.tileSize);
        const currentTileRow = Math.floor((m.y + m.height - 1) / engine.tileSize);

        let pitAhead = false;
        let pitDist = 999;
        let pitStartCol = -1;

        let obstacleAhead = false;
        let obstacleDist = 999;
        let obstacleHeight = 0;

        let enemyAhead = null;
        let enemyDist = 999;

        let slidingShellAhead = false;
        let slidingShellDist = 999;

        let mushroomAhead = null;
        let mysteryBlockAhead = null;
        let mysteryDist = 999;

        // Check for low ceiling right above Mario (restricts jump height)
        let lowCeiling = false;
        const marioCol = Math.floor(m.x / engine.tileSize);
        for (let r = Math.max(0, currentTileRow - 4); r <= currentTileRow - 1; r++) {
            if (engine.isSolidTile(r, marioCol) || engine.isSolidTile(r, marioCol + 1)) {
                lowCeiling = true;
                break;
            }
        }

        // 1. Scan Ground for Pits (next 12 columns)
        // A column is safe if ANY tile between rows 5 and 14 is solid (including floating stepping stones)
        for (let c = currentTileCol; c <= currentTileCol + 12 && c < engine.gridCols; c++) {
            let hasPlatform = false;
            for (let r = 5; r <= 14; r++) {
                if (engine.isSolidTile(r, c)) {
                    hasPlatform = true;
                    break;
                }
            }
            if (!hasPlatform) {
                pitAhead = true;
                pitStartCol = c;
                pitDist = Math.max(0, c * engine.tileSize - (m.x + m.width));
                break;
            }
        }

        // 2. Scan for Solid Obstacles (Pipes, Steps, Walls)
        for (let c = currentTileCol + 1; c <= currentTileCol + 5 && c < engine.gridCols; c++) {
            // Check rows from 9 to 12
            for (let r = 12; r >= 8; r--) {
                const tile = engine.grid[r][c];
                // Pipe or step or brick at walking height
                if (engine.isSolidTile(r, c) && r < 13) {
                    const dist = c * engine.tileSize - (m.x + m.width);
                    if (dist >= 0 && dist < obstacleDist) {
                        obstacleAhead = true;
                        obstacleDist = dist;
                        obstacleHeight = 13 - r; // Height in tiles
                    }
                }
            }
            if (obstacleAhead) break;
        }

        // 3. Scan for Nearby Enemies
        for (const e of engine.enemies) {
            if (e.dead || e.state === 'FLAT') continue;
            const dist = e.x - (m.x + m.width);

            // Enemy is in front of Mario and within 180px
            if (dist > -12 && dist < 180) {
                if (e.state === 'SHELL_SLIDING' && e.vx < 0) {
                    slidingShellAhead = true;
                    if (dist < slidingShellDist) {
                        slidingShellDist = dist;
                    }
                }

                if (dist < enemyDist) {
                    enemyDist = dist;
                    enemyAhead = e;
                }
            }
        }

        // 4. Scan for Moving Mushrooms
        for (const item of engine.items) {
            if (item.type === 'mushroom') {
                const dist = Math.abs(item.x - m.x);
                if (dist < 160) {
                    mushroomAhead = item;
                }
            }
        }

        // 5. Scan for Mystery Blocks [?]
        for (let c = currentTileCol; c <= currentTileCol + 4 && c < engine.gridCols; c++) {
            for (let r = 8; r <= 10; r++) {
                const t = engine.grid[r][c];
                if (t === 3 || t === 4) {
                    const dist = Math.abs(c * engine.tileSize + 8 - (m.x + 8));
                    if (dist < mysteryDist) {
                        mysteryDist = dist;
                        mysteryBlockAhead = { x: c * engine.tileSize + 8, y: r * engine.tileSize, col: c, row: r };
                    }
                }
            }
        }

        // Calculate overall nearest hazard distance
        const nearestHazardDist = Math.min(
            pitAhead ? pitDist : 999,
            enemyAhead ? enemyDist : 999,
            slidingShellAhead ? slidingShellDist : 999
        );

        return {
            pitAhead,
            pitDist,
            obstacleAhead,
            obstacleDist,
            obstacleHeight,
            enemyAhead,
            enemyDist,
            slidingShellAhead,
            slidingShellDist,
            mushroomAhead,
            mysteryBlockAhead,
            mysteryDist,
            nearestHazardDist,
            lowCeiling
        };
    }
}

window.MarioAgent = MarioAgent;

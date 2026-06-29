import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="3D Police Chase Simulator",
    page_icon="🚓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🚓 3D Police Chase Open World")
st.write("Klicke in das Spielfeld! Überlebe **5 Minuten** vor der Polizei. Tasten: WASD / Pfeiltasten | Reset: R")

game_html = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; overflow: hidden; background-color: #bae6fd; font-family: sans-serif; }
        #canvas-container { width: 100vw; height: 75vh; position: relative; border-radius: 12px; overflow: hidden; box-shadow: 0 15px 35px rgba(0,0,0,0.4); }
        #ui-layer {
            position: absolute; bottom: 25px; left: 25px; color: #0f172a;
            background: rgba(255, 255, 255, 0.95); padding: 15px 25px; border-radius: 12px;
            font-size: 22px; font-weight: bold; border: 2px solid #cbd5e1; pointer-events: none;
        }
        #ui-layer span { color: #dc2626; }
        #timer-layer {
            position: absolute; top: 25px; right: 25px; color: #ffffff;
            background: rgba(15, 23, 42, 0.9); padding: 12px 25px; border-radius: 12px;
            font-size: 28px; font-weight: bold; border: 2px solid #3b82f6; pointer-events: none;
        }
        #game-status {
            position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%);
            color: #ffffff; background: rgba(0,0,0,0.85); padding: 30px 50px; border-radius: 15px;
            font-size: 36px; font-weight: bold; text-align: center; display: none; z-index: 100;
            border: 3px solid #dc2626;
        }
        #reset-btn {
            position: absolute; top: 25px; left: 25px; color: #ffffff;
            background: #2563eb; padding: 10px 20px; border-radius: 8px;
            font-size: 14px; font-weight: bold; border: none; cursor: pointer; z-index: 10;
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>

    <div id="canvas-container" onclick="window.focus();">
        <button id="reset-btn" onclick="resetGame(); event.stopPropagation();">🔄 Neustart (R)</button>
        <div id="game-status"><span id="status-text">GAME OVER</span><br><span style="font-size:18px; color:#aaa;">Klicke 'Neustart' oder drücke R</span></div>
        <div id="ui-layer"><span id="speed-val">0</span> KM/H</div>
        <div id="timer-layer">⏱️ <span id="time-val">05:00</span></div>
    </div>

    <script>
        // --- 1. SETUP ---
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xa5f3fc);
        scene.fog = new THREE.FogExp2(0xa5f3fc, 0.004);

        const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 1500);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        // LIGHTS
        scene.add(new THREE.AmbientLight(0xffffff, 0.7));
        const sun = new THREE.DirectionalLight(0xfffbeb, 1.2);
        sun.position.set(200, 400, 150);
        scene.add(sun);

        // --- 2. CONFIG & ARRAYS ---
        const mapSize = 1000;
        const blockSize = 80;
        const roadWidth = 22;
        const sidewalkW = 3.5;

        let gameActive = true;
        let timeLeft = 300; // 5 Minuten in Sekunden

        const collisionObstacles = [];
        const npcTraffic = [];
        const npcPedestrians = [];

        const boxGeo = new THREE.BoxGeometry(1, 1, 1);
        const planeGeo = new THREE.PlaneGeometry(1, 1);
        const cylGeo = new THREE.CylinderGeometry(1, 1, 1, 16);

        // GROUND
        const ground = new THREE.Mesh(new THREE.PlaneGeometry(mapSize, mapSize), new THREE.MeshStandardMaterial({ color: 0x16a34a, roughness: 0.9 }));
        ground.rotation.x = -Math.PI / 2;
        scene.add(ground);

        // --- 3. CITY GENERATION ---
        for (let x = -mapSize/2; x < mapSize/2; x += blockSize) {
            for (let z = -mapSize/2; z < mapSize/2; z += blockSize) {
                createRoads(x, z, blockSize);
                if (Math.abs(x) < blockSize && Math.abs(z) < blockSize) continue;
                
                // Gehwege
                const innerW = blockSize - roadWidth;
                const sw = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0xa1a1aa }));
                sw.scale.set(innerW, 0.2, innerW);
                sw.position.set(x + roadWidth/2 + innerW/2, 0.1, z + roadWidth/2 + innerW/2);
                scene.add(sw);

                if (Math.random() > 0.2) {
                    createBuilding(x, z, innerW);
                }
            }
        }

        function createRoads(x, z, size) {
            const road = new THREE.Mesh(planeGeo, new THREE.MeshStandardMaterial({ color: 0x27272a, roughness: 0.8 }));
            road.scale.set(size, size, 1);
            road.rotation.x = -Math.PI / 2;
            road.position.set(x + size/2, 0.02, z + size/2);
            scene.add(road);
        }

        function createBuilding(x, z, innerW) {
            const h = 30 + Math.random() * 60;
            const body = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0x4b5563, roughness: 0.5 }));
            body.scale.set(innerW - sidewalkW*2, h, innerW - sidewalkW*2);
            body.position.set(x + blockSize/2, h/2, z + blockSize/2);
            scene.add(body);
            collisionObstacles.push({ box: new THREE.Box3().setFromObject(body) });
        }

        // --- 4. VEHICLES ---
        // Player
        const playerCar = new THREE.Group();
        const pBody = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0xe11d48 }));
        pBody.scale.set(2.2, 0.7, 4.5); pBody.position.y = 0.5;
        playerCar.add(pBody);
        playerCar.position.set(6, 0.1, 6);
        scene.add(playerCar);
        const playerBox = new THREE.Box3();

        // Police
        const policeCar = new THREE.Group();
        const polBody = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0x1e3a8a }));
        polBody.scale.set(2.2, 0.7, 4.5); polBody.position.y = 0.5;
        policeCar.add(polBody);
        
        // Blaulicht
        const siren = new THREE.Mesh(boxGeo, new THREE.MeshBasicMaterial({ color: 0x3b82f6 }));
        siren.scale.set(0.6, 0.2, 0.6); siren.position.set(0, 1.3, 0);
        policeCar.add(siren);
        
        policeCar.position.set(-60, 0.1, -60);
        scene.add(policeCar);
        const policeBox = new THREE.Box3();

        // NPC Traffic (Realistischerer Look)
        const trafficArray = [];
        const trafficColors = [0x16a34a, 0xd97706, 0x4f46e5, 0x059669];
        
        function spawnTraffic(x, z, isXAxis) {
            const tCar = new THREE.Group();
            const tBody = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: trafficColors[Math.floor(Math.random()*4)] }));
            tBody.scale.set(2.2, 0.7, 4.5); tBody.position.y = 0.5;
            tCar.add(tBody);
            tCar.position.set(x, 0.1, z);
            if (!isXAxis) tCar.rotation.y = Math.PI / 2;
            scene.add(tCar);
            trafficArray.push({ group: tCar, mesh: tBody, box: new THREE.Box3(), isX: isXAxis, speed: 0.3, dir: 1 });
        }

        for(let i = -300; i < 300; i += 100) {
            spawnTraffic(i, -12, true);
            spawnTraffic(12, i, false);
        }

        // --- 5. LOGIC & CONTROLS ---
        let speed = 0, maxSpeed = 2.4, accel = 0.05, friction = 0.02, angle = 0, turnSpeed = 0.05;
        const keys = { w: false, a: false, s: false, d: false, ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false };

        window.addEventListener('keydown', (e) => { 
            if (e.key in keys) { keys[e.key] = true; e.preventDefault(); }
            if (e.key.toLowerCase() === 'r') resetGame();
        });
        window.addEventListener('keyup', (e) => { if (e.key in keys) keys[e.key] = false; });

        // Timer Interval
        setInterval(() => {
            if (!gameActive) return;
            timeLeft--;
            let mins = Math.floor(timeLeft / 60);
            let secs = timeLeft % 60;
            document.getElementById('time-val').innerText = (mins < 10 ? "0" : "") + mins + ":" + (secs < 10 ? "0" : "") + secs;
            
            if (timeLeft <= 0) {
                gameActive = false;
                document.getElementById('status-text').innerText = "🏆 GEWONNEN!";
                document.getElementById('status-text').style.color = "#10b981";
                document.getElementById('game-status').style.display = "block";
            }
        }, 1000);

        function resetGame() {
            playerCar.position.set(6, 0.1, 6);
            policeCar.position.set(-60, 0.1, -60);
            speed = 0; angle = 0; timeLeft = 300;
            gameActive = true;
            document.getElementById('game-status').style.display = "none";
        }

        // --- 6. ENGINE LOOP ---
        function animate() {
            requestAnimationFrame(animate);
            if (!gameActive) return;

            // Player Bewegung
            if (keys.w || keys.ArrowUp) { if (speed < maxSpeed) speed += accel; }
            else if (keys.s || keys.ArrowDown) { if (speed > -maxSpeed/2) speed -= accel; }
            else {
                if (speed > 0) speed -= friction;
                else if (speed < 0) speed += friction;
                if (Math.abs(speed) < friction) speed = 0;
            }

            if (Math.abs(speed) > 0.05) {
                const modifier = speed > 0 ? 1 : -1;
                if (keys.a || keys.ArrowLeft) angle += turnSpeed * modifier;
                if (keys.d || keys.ArrowRight) angle -= turnSpeed * modifier;
            }

            playerCar.rotation.y = angle;
            const oldX = playerCar.position.x;
            const oldZ = playerCar.position.z;

            playerCar.position.x += Math.sin(angle) * speed;
            playerCar.position.z += Math.cos(angle) * speed;
            playerBox.setFromObject(pBody);

            // Kollision Gebäude
            for (let i = 0; i < collisionObstacles.length; i++) {
                if (playerBox.intersectsBox(collisionObstacles[i].box)) {
                    playerCar.position.set(oldX, 0.1, oldZ);
                    speed = -speed * 0.3;
                    break;
                }
            }

            // --- KI POLIZEI LOGIK ---
            const dx = playerCar.position.x - policeCar.position.x;
            const dz = playerCar.position.z - policeCar.position.z;
            const pAngle = Math.atan2(dx, dz);
            policeCar.rotation.y = pAngle;
            
            const polSpeed = 1.3; 
            policeCar.position.x += Math.sin(pAngle) * polSpeed;
            policeCar.position.z += Math.cos(pAngle) * polSpeed;
            policeBox.setFromObject(polBody);

            // BLAULICHT BLINKEN
            siren.material.color.setHex(Math.floor(Date.now() / 150) % 2 === 0 ? 0x3b82f6 : 0xdc2626);

            // Polizei erwischt Spieler
            if (playerBox.intersectsBox(policeBox)) {
                gameActive = false;
                document.getElementById('status-text').innerText = "💥 GAME OVER";
                document.getElementById('status-text').style.color = "#dc2626";
                document.getElementById('game-status').style.display = "block";
            }

            // --- NPC VERKEHR LOGIK (Fahren geordnet, blockieren sich) ---
            trafficArray.forEach((npc, index) => {
                const nOldX = npc.group.position.x;
                const nOldZ = npc.group.position.z;

                if (npc.isX) npc.group.position.x += npc.speed * npc.dir;
                else npc.group.position.z += npc.speed * npc.dir;

                npc.box.setFromObject(npc.mesh);

                // Check ob NPC ein Gebäude oder ein anderes Auto rammen würde
                let blockiert = false;
                
                // Gegen andere NPCs prüfen
                for (let j = 0; j < trafficArray.length; j++) {
                    if (index !== j && npc.box.intersectsBox(trafficArray[j].box)) { blockiert = true; break; }
                }

                if (blockiert || Math.abs(npc.group.position.x) > mapSize/2 || Math.abs(npc.group.position.z) > mapSize/2) {
                    npc.group.position.set(nOldX, 0.1, nOldZ);
                    npc.dir *= -1; // Richtung umkehren statt durchzufahren
                }

                // Spieler rammt NPC
                if (playerBox.intersectsBox(npc.box)) {
                    playerCar.position.set(oldX, 0.1, oldZ);
                    speed = -speed * 0.4;
                }
            });

            // UI
            document.getElementById('speed-val').innerText = Math.round(Math.abs(speed) * 110);

            // Kamera
            camera.position.x += (playerCar.position.x - Math.sin(angle) * 15 - camera.position.x) * 0.1;
            camera.position.y += (playerCar.position.y + 6.0 - camera.position.y) * 0.1;
            camera.position.z += (playerCar.position.z - Math.cos(angle) * 15 - camera.position.z) * 0.1;
            camera.lookAt(playerCar.position);

            renderer.render(scene, camera);
        }

        animate();
    </script>
</body>
</html>
"""

components.html(game_html, height=650, scrolling=False)

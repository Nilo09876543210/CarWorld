import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Ultimate 3D Escape",
    page_icon="🚓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🏙️ 3D City Escape (Engine V3 - Anti-Stuck Fix)")
st.write("👉 **WICHTIG:** Klicke einmal mit der Maus in das Spiel! Nutze **WASD** oder **Pfeiltasten**. Drücke **R** für Reset.")

game_html = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; overflow: hidden; background-color: #0f172a; font-family: sans-serif; user-select: none; }
        #canvas-container { width: 100vw; height: 75vh; position: relative; cursor: pointer; }
        #ui-layer {
            position: absolute; bottom: 25px; left: 25px; color: #ffffff;
            background: rgba(15, 23, 42, 0.85); padding: 15px 25px; border-radius: 8px;
            font-size: 24px; font-weight: bold; border: 2px solid #475569; pointer-events: none;
        }
        #ui-layer span { color: #f43f5e; }
        #timer-layer {
            position: absolute; top: 25px; right: 25px; color: #ffffff;
            background: rgba(15, 23, 42, 0.9); padding: 12px 25px; border-radius: 8px;
            font-size: 28px; font-weight: bold; border: 2px solid #3b82f6; pointer-events: none;
        }
        #game-status {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            color: #ffffff; background: rgba(15, 23, 42, 0.95); padding: 40px 60px; border-radius: 12px;
            font-size: 42px; font-weight: bold; text-align: center; display: none; z-index: 100;
            border: 3px solid #f43f5e;
        }
        #focus-prompt {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: #eab308; color: #0f172a; padding: 20px 40px; border-radius: 8px;
            font-size: 22px; font-weight: bold; border: 3px solid #ca8a04; text-align: center;
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>

    <div id="canvas-container">
        <div id="focus-prompt">🕹️ KLICKE HIER REIN ZUM STARTEN & FAHREN!</div>
        <div id="game-status"><span id="status-text">GAME OVER</span><br><span style="font-size:16px; color:#94a3b8;">Drücke R zum Neustarten</span></div>
        <div id="ui-layer"><span id="speed-val">0</span> KM/H</div>
        <div id="timer-layer">⏱️ <span id="time-val">05:00</span></div>
    </div>

    <script>
        // --- 1. CORE ENGINE ---
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0f172a); // Stylische Nacht/Abend-Atmosphäre
        scene.fog = new THREE.FogExp2(0x0f172a, 0.004);

        const camera = new THREE.PerspectiveCamera(65, container.clientWidth / container.clientHeight, 0.1, 1500);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        // LIGHTS
        scene.add(new THREE.AmbientLight(0xffffff, 0.6));
        const sun = new THREE.DirectionalLight(0x38bdf8, 1.2);
        sun.position.set(200, 400, 100);
        scene.add(sun);

        const mapSize = 1000;
        const blockSize = 100;
        const roadW = 26;

        let gameActive = true;
        let timeLeft = 300;

        const collisionObstacles = [];
        const npcTraffic = [];

        const boxGeo = new THREE.BoxGeometry(1, 1, 1);

        // Boden (Asphalt-Optik)
        const ground = new THREE.Mesh(new THREE.PlaneGeometry(mapSize, mapSize), new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.8 }));
        ground.rotation.x = -Math.PI / 2;
        scene.add(ground);

        // --- 2. STADTBAU (KLARER & KONTRASTREICHER) ---
        for (let x = -mapSize/2; x < mapSize/2; x += blockSize) {
            for (let z = -mapSize/2; z < mapSize/2; z += blockSize) {
                // Straßen-Asphalt-Platten
                const rd = new THREE.Mesh(new THREE.PlaneGeometry(blockSize, blockSize), new THREE.MeshStandardMaterial({ color: 0x0f172a }));
                rd.rotation.x = -Math.PI / 2;
                rd.position.set(x + blockSize/2, 0.01, z + blockSize/2);
                scene.add(rd);

                if (Math.abs(x) < blockSize && Math.abs(z) < blockSize) continue;

                // Gehwege / Gebäudeblöcke
                const buildW = blockSize - roadW;
                const h = 40 + Math.random() * 70;
                
                const bMesh = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.4 }));
                bMesh.scale.set(buildW, h, buildW);
                bMesh.position.set(x + blockSize/2, h/2 + 0.1, z + blockSize/2);
                scene.add(bMesh);

                collisionObstacles.push({ box: new THREE.Box3().setFromObject(bMesh) });
            }
        }

        // --- 3. VEHICLES CONFIG ---
        // Spieler (Neon Rot)
        const playerCar = new THREE.Group();
        const pBody = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0xf43f5e, metalness: 0.5 }));
        pBody.scale.set(2.4, 0.8, 4.8); pBody.position.y = 0.4;
        playerCar.add(pBody);
        playerCar.position.set(10, 0.1, 10);
        scene.add(playerCar);
        const playerBox = new THREE.Box3();

        // Polizei (Blau)
        const policeCar = new THREE.Group();
        const polBody = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0x2563eb }));
        polBody.scale.set(2.4, 0.8, 4.8); polBody.position.y = 0.4;
        policeCar.add(polBody);
        const siren = new THREE.Mesh(boxGeo, new THREE.MeshBasicMaterial({ color: 0x0000ff }));
        siren.scale.set(0.8, 0.2, 0.4); siren.position.set(0, 1.3, 0);
        policeCar.add(siren);
        policeCar.position.set(-80, 0.1, -80);
        scene.add(policeCar);
        const policeBox = new THREE.Box3();

        // NPCs (Zivile Autos mit Abstandsregelung)
        const colors = [0x10b981, 0xf59e0b, 0x8b5cf6, 0x64748b];
        function spawnAI(startX, startZ, isX) {
            const ai = new THREE.Group();
            const aiBody = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: colors[Math.floor(Math.random()*4)] }));
            aiBody.scale.set(2.4, 0.8, 4.8); aiBody.position.y = 0.4;
            ai.add(aiBody);
            ai.position.set(startX, 0.1, startZ);
            if (!isX) ai.rotation.y = Math.PI / 2;
            scene.add(ai);
            npcTraffic.push({ group: ai, mesh: aiBody, box: new THREE.Box3(), isX: isX, speed: 0.4, dir: 1 });
        }

        // Verkehr sicher platzieren
        for (let i = -300; i < 300; i += 120) {
            spawnAI(i, -12, true);
            spawnAI(12, i, false);
        }

        // --- 4. ENGINE CONTROLS ---
        let speed = 0, maxSpeed = 2.6, accel = 0.06, friction = 0.03, angle = 0, turnSpeed = 0.052;
        const keys = { w: false, a: false, s: false, d: false };

        container.addEventListener('click', () => {
            window.focus();
            document.getElementById('focus-prompt').style.display = 'none';
        });

        document.addEventListener('keydown', (e) => {
            const k = e.key.toLowerCase();
            if (k === 'w' || e.key === 'ArrowUp') keys.w = true;
            if (k === 's' || e.key === 'ArrowDown') keys.s = true;
            if (k === 'a' || e.key === 'ArrowLeft') keys.a = true;
            if (k === 'd' || e.key === 'ArrowRight') keys.d = true;
            if (k === 'r') resetGame();
        });

        document.addEventListener('keyup', (e) => {
            const k = e.key.toLowerCase();
            if (k === 'w' || e.key === 'ArrowUp') keys.w = false;
            if (k === 's' || e.key === 'ArrowDown') keys.s = false;
            if (k === 'a' || e.key === 'ArrowLeft') keys.a = false;
            if (k === 'd' || e.key === 'ArrowRight') keys.d = false;
        });

        // COUNTDOWN
        setInterval(() => {
            if (!gameActive) return;
            timeLeft--;
            let m = Math.floor(timeLeft / 60), s = timeLeft % 60;
            document.getElementById('time-val').innerText = (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
            if (timeLeft <= 0) {
                gameActive = false;
                document.getElementById('status-text').innerText = "🏆 GEWONNEN!";
                document.getElementById('status-text').style.color = "#10b981";
                document.getElementById('game-status').style.display = "block";
            }
        }, 1000);

        function resetGame() {
            playerCar.position.set(10, 0.1, 10);
            policeCar.position.set(-80, 0.1, -80);
            speed = 0; angle = 0; timeLeft = 300; gameActive = true;
            document.getElementById('game-status').style.display = "none";
            window.focus();
        }

        // --- 5. LOGIC RECHNER ---
        function animate() {
            requestAnimationFrame(animate);
            if (!gameActive) return;

            // Physik Beschleunigung
            if (keys.w) { if (speed < maxSpeed) speed += accel; } 
            else if (keys.s) { if (speed > -maxSpeed/2) speed -= accel; } 
            else {
                if (speed > 0) speed -= friction;
                else if (speed < 0) speed += friction;
                if (Math.abs(speed) < friction) speed = 0;
            }

            if (Math.abs(speed) > 0.05) {
                const dir = speed > 0 ? 1 : -1;
                if (keys.a) angle += turnSpeed * dir;
                if (keys.d) angle -= turnSpeed * dir;
            }

            playerCar.rotation.y = angle;
            const oX = playerCar.position.x, oZ = playerCar.position.z;

            // Sichere Kollision X
            playerCar.position.x += Math.sin(angle) * speed;
            playerBox.setFromObject(pBody);
            let hitX = false;
            for(let i=0; i<collisionObstacles.length; i++) { if(playerBox.intersectsBox(collisionObstacles[i].box)) { hitX = true; break; } }
            if(hitX) { playerCar.position.x = oX; speed *= -0.2; }

            // Sichere Kollision Z
            playerCar.position.z += Math.cos(angle) * speed;
            playerBox.setFromObject(pBody);
            let hitZ = false;
            for(let i=0; i<collisionObstacles.length; i++) { if(playerBox.intersectsBox(collisionObstacles[i].box)) { hitZ = true; break; } }
            if(hitZ) { playerCar.position.z = oZ; speed *= -0.2; }

            // POLIZEI KI (Verfolgung)
            const dx = playerCar.position.x - policeCar.position.x, dz = playerCar.position.z - policeCar.position.z;
            const pAngle = Math.atan2(dx, dz); policeCar.rotation.y = pAngle;
            policeCar.position.x += Math.sin(pAngle) * 1.4; policeCar.position.z += Math.cos(pAngle) * 1.4;
            policeBox.setFromObject(polBody);

            siren.material.color.setHex(Math.floor(Date.now() / 100) % 2 === 0 ? 0x0000ff : 0xff0000);

            if (playerBox.intersectsBox(policeBox)) {
                gameActive = false;
                document.getElementById('status-text').innerText = "💥 GAME OVER";
                document.getElementById('status-text').style.color = "#f43f5e";
                document.getElementById('game-status').style.display = "block";
            }

            // ANTI-STUCK KI FÜR ZIVILISTEN
            npcTraffic.forEach((npc) => {
                const nX = npc.group.position.x, nZ = npc.group.position.z;
                
                // NPCs fahren nur vorwärts, wenn kein Auto oder Spieler direkt vor ihnen steht
                npc.box.setFromObject(npc.mesh);
                let pathBlocked = playerBox.intersectsBox(npc.box);

                if (!pathBlocked) {
                    if (npc.isX) npc.group.position.x += npc.speed * npc.dir;
                    else npc.group.position.z += npc.speed * npc.dir;
                }

                let hitBuilding = false;
                for(let i=0; i<collisionObstacles.length; i++) { if(npc.box.intersectsBox(collisionObstacles[i].box)) { hitBuilding = true; break; } }
                
                // Wenn Grenze erreicht oder Haus gerammt -> Umkehren
                if (hitBuilding || Math.abs(npc.group.position.x) > mapSize/2 || Math.abs(npc.group.position.z) > mapSize/2) {
                    npc.group.position.set(nX, 0.1, nZ); npc.dir *= -1;
                }

                // Spieler rammt NPC von hinten/der Seite -> Wegdrücken verhindern
                if (playerBox.intersectsBox(npc.box)) {
                    playerCar.position.set(oX, 0.1, oZ); speed *= -0.3;
                }
            });

            // UI & CAM VERFOLGUNG
            document.getElementById('speed-val').innerText = Math.round(Math.abs(speed) * 110);
            camera.position.x += (playerCar.position.x - Math.sin(angle) * 18 - camera.position.x) * 0.08;
            camera.position.y += (playerCar.position.y + 7.5 - camera.position.y) * 0.08;
            camera.position.z += (playerCar.position.z - Math.cos(angle) * 18 - camera.position.z) * 0.08;
            camera.lookAt(playerCar.position);

            renderer.render(scene, camera);
        }

        animate();
    </script>
</body>
</html>
"""

components.html(game_html, height=660, scrolling=False)

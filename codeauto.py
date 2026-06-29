import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="3D City Escape Pro",
    page_icon="🚓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🏙️ 3D City Escape Simulator (Fixed Engine)")
st.write("Klicke in das Spielfeld. Steuerung mit **WASD / Pfeiltasten**. Überlebe 5 Minuten vor der Polizei! Drücke **R** für einen manuellen Reset.")

# Das komplette, überarbeitete Spiel-Skript
game_html = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>3D City Escape Pro</title>
    <style>
        body { margin: 0; overflow: hidden; background-color: #bae6fd; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; user-select: none; }
        #canvas-container { width: 100vw; height: 75vh; position: relative; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.4); background-color: #a5f3fc; }
        #ui-layer {
            position: absolute; bottom: 25px; left: 25px; color: #0f172a;
            background: rgba(255, 255, 255, 0.95); padding: 15px 25px; border-radius: 12px;
            font-size: 24px; font-weight: bold; border: 2px solid #cbd5e1; pointer-events: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        #ui-layer span { color: #dc2626; }
        #timer-layer {
            position: absolute; top: 25px; right: 25px; color: #ffffff;
            background: rgba(15, 23, 42, 0.95); padding: 12px 25px; border-radius: 12px;
            font-size: 28px; font-weight: bold; border: 2px solid #3b82f6; pointer-events: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        #game-status {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            color: #ffffff; background: rgba(15, 23, 42, 0.95); padding: 40px 60px; border-radius: 16px;
            font-size: 42px; font-weight: bold; text-align: center; display: none; z-index: 100;
            border: 3px solid #dc2626; box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        }
        #reset-btn {
            position: absolute; top: 25px; left: 25px; color: #ffffff;
            background: #2563eb; padding: 12px 24px; border-radius: 8px;
            font-size: 15px; font-weight: bold; border: none; cursor: pointer; z-index: 10;
            box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3); transition: background 0.2s;
        }
        #reset-btn:hover { background: #1d4ed8; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>

    <div id="canvas-container" onclick="window.focus();">
        <button id="reset-btn" onclick="resetGame(); event.stopPropagation();">🔄 Spiel Neustarten (R)</button>
        <div id="game-status">
            <span id="status-text">GAME OVER</span><br>
            <span style="font-size:18px; color:#94a3b8; font-weight:normal; display:block; margin-top:10px;">Klicke den Button oben oder drücke R zum Wiederholen</span>
        </div>
        <div id="ui-layer"><span id="speed-val">0</span> KM/H</div>
        <div id="timer-layer">⏱️ <span id="time-val">05:00</span></div>
    </div>

    <script>
        // ==========================================
        // 1. ENGINE CONFIG & CORE SETUP
        // ==========================================
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xa5f3fc);
        scene.fog = new THREE.FogExp2(0xa5f3fc, 0.0035);

        const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 2000);
        const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(renderer.domElement);

        // BELEUCHTUNG
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.75);
        scene.add(ambientLight);

        const sun = new THREE.DirectionalLight(0xfffbeb, 1.3);
        sun.position.set(300, 500, 200);
        sun.castShadow = true;
        sun.shadow.mapSize.width = 2048;
        sun.shadow.mapSize.height = 2048;
        sun.shadow.camera.near = 0.5;
        sun.shadow.camera.far = 1500;
        const d = 300;
        sun.shadow.camera.left = -d; sun.shadow.camera.right = d;
        sun.shadow.camera.top = d; sun.shadow.camera.bottom = -d;
        scene.add(sun);

        // ==========================================
        // 2. SPIELVARIABLEN & GLOBALE ARRAYS
        // ==========================================
        const mapSize = 1200;
        const blockSize = 90;
        const roadWidth = 24;
        const sidewalkW = 4;

        let gameActive = true;
        let timeLeft = 300; 

        const collisionObstacles = [];
        const npcTraffic = [];
        const npcPedestrians = [];

        // Geometrie & Material-Pools
        const boxGeo = new THREE.BoxGeometry(1, 1, 1);
        const planeGeo = new THREE.PlaneGeometry(1, 1);
        const cylGeo = new THREE.CylinderGeometry(1, 1, 1, 16);

        // ==========================================
        // 3. PROZEDURALER STADTGENERATOR (GRAFIK UPDATE)
        // ==========================================
        const groundMat = new THREE.MeshStandardMaterial({ color: 0x15803d, roughness: 0.9 });
        const ground = new THREE.Mesh(new THREE.PlaneGeometry(mapSize, mapSize), groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        scene.add(ground);

        for (let x = -mapSize/2; x < mapSize/2; x += blockSize) {
            for (let z = -mapSize/2; z < mapSize/2; z += blockSize) {
                // Straßenbahn-Asphalt erstellen
                createAdvancedRoads(x, z, blockSize);
                
                // Startzone schützen
                if (Math.abs(x) < blockSize && Math.abs(z) < blockSize) {
                    createDecorativeTrees(x, z);
                    continue;
                }

                // Gehweg-System (Erhöhter Beton)
                const innerW = blockSize - roadWidth;
                const swMat = new THREE.MeshStandardMaterial({ color: 0x71717a, roughness: 0.7 });
                const sw = new THREE.Mesh(boxGeo, swMat);
                sw.scale.set(innerW, 0.4, innerW);
                sw.position.set(x + roadWidth/2 + innerW/2, 0.2, z + roadWidth/2 + innerW/2);
                sw.receiveShadow = true;
                scene.add(sw);

                // Detailliertes Gebäude platzieren
                if (Math.random() > 0.15) {
                    createProBuilding(x, z, innerW);
                } else {
                    createDecorativeTrees(x, z);
                }
            }
        }

        function createAdvancedRoads(x, z, size) {
            const rMat = new THREE.MeshStandardMaterial({ color: 0x1e1b4b, roughness: 0.85 });
            const road = new THREE.Mesh(planeGeo, rMat);
            road.scale.set(size, size, 1);
            road.rotation.x = -Math.PI / 2;
            road.position.set(x + size/2, 0.02, z + size/2);
            road.receiveShadow = true;
            scene.add(road);

            // Weiße Fahrbahnbegrenzungen (Mittelstreifen)
            const lineMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
            const mLine = new THREE.Mesh(planeGeo, lineMat);
            mLine.scale.set(0.2, size, 1); mLine.rotation.x = -Math.PI / 2;
            mLine.position.set(x + size/2, 0.03, z + size/2);
            scene.add(mLine);
        }

        function createProBuilding(x, z, innerW) {
            const h = 40 + Math.random() * 80;
            const buildW = innerW - sidewalkW * 2;
            
            const buildingColors = [0x3f3f46, 0x52525b, 0x18181b, 0x27272a, 0x5b5151];
            const chosenColor = buildingColors[Math.floor(Math.random() * buildingColors.length)];

            const bGroup = new THREE.Group();
            
            // Fassade
            const body = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: chosenColor, roughness: 0.4, metalness: 0.1 }));
            body.scale.set(buildW, h, buildW);
            body.position.y = h / 2;
            body.castShadow = true;
            body.receiveShadow = true;
            bGroup.add(body);

            // Dachkante/Struktur
            const roof = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0x09090b }));
            roof.scale.set(buildW + 1, 1.5, buildW + 1);
            roof.position.y = h + 0.75;
            bGroup.add(roof);

            // Fensterstrukturen simulieren
            const winGeo = new THREE.PlaneGeometry(1.4, 2);
            const winMat = new THREE.MeshBasicMaterial({ color: 0xfef08a });

            for (let yHeight = 6; yHeight < h - 6; yHeight += 7) {
                for (let xPos = -buildW/2 + 3; xPos < buildW/2 - 3; xPos += 5) {
                    const wFace1 = new THREE.Mesh(winGeo, winMat);
                    wFace1.position.set(xPos, yHeight, buildW/2 + 0.05);
                    bGroup.add(wFace1);

                    const wFace2 = new THREE.Mesh(winGeo, winMat);
                    wFace2.position.set(xPos, yHeight, -buildW/2 - 0.05);
                    wFace2.rotation.y = Math.PI;
                    bGroup.add(wFace2);
                }
            }

            bGroup.position.set(x + blockSize/2, 0.4, z + blockSize/2);
            scene.add(bGroup);

            // Exakte Kollisionsbox generieren
            const staticBox = new THREE.Box3().setFromObject(body);
            collisionObstacles.push({ box: staticBox, mesh: body });
        }

        function createDecorativeTrees(x, z) {
            for (let i = 0; i < 3; i++) {
                const tx = x + roadWidth + Math.random() * 20;
                const tz = z + roadWidth + Math.random() * 20;
                
                const tree = new THREE.Group();
                const trunk = new THREE.Mesh(cylGeo, new THREE.MeshStandardMaterial({ color: 0x451a03 }));
                trunk.scale.set(0.5, 5, 0.5); trunk.position.y = 2.5; trunk.castShadow = true;
                tree.add(trunk);

                const crown = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0x065f46, roughness: 0.6 }));
                crown.scale.set(3, 4, 3); crown.position.y = 5.5; crown.castShadow = true;
                tree.add(crown);

                tree.position.set(tx, 0.4, tz);
                scene.add(tree);
                
                collisionObstacles.push({ box: new THREE.Box3().setFromObject(trunk), mesh: trunk });
            }
        }

        // ==========================================
        // 4. ENTITIES: SPIELER, POLIZEI & TRAFFIC
        // ==========================================
        
        // SPIELER (Sportwagen)
        const playerCar = new THREE.Group();
        const pBody = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0xdc2626, metalness: 0.8, roughness: 0.1 }));
        pBody.scale.set(2.4, 0.65, 4.6); pBody.position.y = 0.5; pBody.castShadow = true;
        playerCar.add(pBody);
        
        const pCab = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0x0f172a }));
        pCab.scale.set(1.8, 0.55, 2.2); pCab.position.set(0, 1.05, -0.2);
        playerCar.add(pCab);

        playerCar.position.set(8, 0.2, 8);
        scene.add(playerCar);
        const playerBox = new THREE.Box3();

        // POLIZEI (Verfolger)
        const policeCar = new THREE.Group();
        const polBody = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0x1d4ed8, metalness: 0.5, roughness: 0.2 }));
        polBody.scale.set(2.4, 0.7, 4.6); polBody.position.y = 0.5; polBody.castShadow = true;
        policeCar.add(polBody);

        const polCab = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0xf8fafc }));
        polCab.scale.set(1.8, 0.55, 2.2); polCab.position.set(0, 1.1, -0.1);
        policeCar.add(polCab);

        const blaulicht = new THREE.Mesh(boxGeo, new THREE.MeshBasicMaterial({ color: 0x0000ff }));
        blaulicht.scale.set(0.8, 0.2, 0.4); blaulicht.position.set(0, 1.45, 0);
        policeCar.add(blaulicht);

        policeCar.position.set(-80, 0.2, -80);
        scene.add(policeCar);
        const policeBox = new THREE.Box3();

        // ZIVIL-VERKEHR (Geordnetes Fahren ohne Ineinander-Clashing)
        const trafficColors = [0x059669, 0xd97706, 0x6d28d9, 0x4b5563, 0x0891b2];
        
        function generateTraffic(startX, startZ, moveOnX) {
            const aiCar = new THREE.Group();
            const aiBody = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: trafficColors[Math.floor(Math.random() * trafficColors.length)], roughness: 0.3 }));
            aiBody.scale.set(2.3, 0.7, 4.6); aiBody.position.y = 0.5; aiBody.castShadow = true;
            aiCar.add(aiBody);

            aiCar.position.set(startX, 0.2, startZ);
            if (!moveOnX) aiCar.rotation.y = Math.PI / 2;
            scene.add(aiCar);

            npcTraffic.push({
                group: aiCar, mesh: aiBody, box: new THREE.Box3(), isX: moveOnX, speed: 0.35, dir: Math.random() > 0.5 ? 1 : -1
            });
        }

        // Spawne Verkehrs-Teilnehmer auf den Hauptstraßen-Achsen
        for (let i = -400; i < 400; i += 90) {
            generateTraffic(i, -14, true);
            generateTraffic(14, i, false);
            generateTraffic(i + 30, 14, true);
        }

        // ==========================================
        // 5. PHYSIK, PHYSIK-ENGINE (AXIS-SEPARATED COLLISION) & INPUT
        // ==========================================
        let speed = 0, maxSpeed = 2.5, accel = 0.055, friction = 0.025, angle = 0, turnSpeed = 0.048;
        const keys = { w: false, a: false, s: false, d: false, ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false };

        window.addEventListener('keydown', (e) => {
            if (e.key in keys) { keys[e.key] = true; e.preventDefault(); }
            if (e.key.toLowerCase() === 'r') resetGame();
        });
        window.addEventListener('keyup', (e) => { if (e.key in keys) keys[e.key] = false; });

        // COUNTDOWN TIMER INTERVALL
        const timerInterval = setInterval(() => {
            if (!gameActive) return;
            timeLeft--;
            
            let minutes = Math.floor(timeLeft / 60);
            let seconds = timeLeft % 60;
            document.getElementById('time-val').innerText = (minutes < 10 ? "0" : "") + minutes + ":" + (seconds < 10 ? "0" : "") + seconds;

            if (timeLeft <= 0) {
                gameActive = false;
                document.getElementById('status-text').innerText = "🏆 GEWONNEN!";
                document.getElementById('status-text').style.color = "#10b981";
                document.getElementById('game-status').style.display = "block";
            }
        }, 1000);

        function resetGame() {
            playerCar.position.set(8, 0.2, 8);
            policeCar.position.set(-80, 0.2, -80);
            speed = 0; angle = 0; timeLeft = 300;
            gameActive = true;
            document.getElementById('game-status').style.display = "none";
        }

        // ==========================================
        // 6. ENGINE CORE LOOP (ANIMATE)
        // ==========================================
        function animate() {
            requestAnimationFrame(animate);
            if (!gameActive) return;

            // --- PHYSIK RECHNER PLAYER ---
            if (keys.w || keys.ArrowUp) { if (speed < maxSpeed) speed += accel; }
            else if (keys.s || keys.ArrowDown) { if (speed > -maxSpeed/2) speed -= accel; }
            else {
                if (speed > 0) speed -= friction;
                else if (speed < 0) speed += friction;
                if (Math.abs(speed) < friction) speed = 0;
            }

            if (Math.abs(speed) > 0.05) {
                const dirMod = speed > 0 ? 1 : -1;
                if (keys.a || keys.ArrowLeft) angle += turnSpeed * dirMod;
                if (keys.d || keys.ArrowRight) angle -= turnSpeed * dirMod;
            }

            playerCar.rotation.y = angle;

            // --- ACHSENGETRENNTE KOLLISION (Verhindert das Feststecken komplett) ---
            const origX = playerCar.position.x;
            const origZ = playerCar.position.z;

            // 1. Bewege nur X-Achse
            playerCar.position.x += Math.sin(angle) * speed;
            playerBox.setFromObject(pBody);
            let collidedX = false;
            for (let i = 0; i < collisionObstacles.length; i++) {
                if (playerBox.intersectsBox(collisionObstacles[i].box)) { collidedX = true; break; }
            }
            if (collidedX) { playerCar.position.x = origX; speed *= -0.25; } // Prallt ab, gleitet aber weiter

            // 2. Bewege nur Z-Achse
            playerCar.position.z += Math.cos(angle) * speed;
            playerBox.setFromObject(pBody);
            let collidedZ = false;
            for (let i = 0; i < collisionObstacles.length; i++) {
                if (playerBox.intersectsBox(collisionObstacles[i].box)) { collidedZ = true; break; }
            }
            if (collidedZ) { playerCar.position.z = origZ; speed *= -0.25; }

            // --- POLIZEI VERFOLGUNGS-KI ---
            const deltaX = playerCar.position.x - policeCar.position.x;
            const deltaZ = playerCar.position.z - policeCar.position.z;
            const polAngle = Math.atan2(deltaX, deltaZ);
            policeCar.rotation.y = polAngle;

            const currentPoliceSpeed = 1.35; 
            policeCar.position.x += Math.sin(polAngle) * currentPoliceSpeed;
            policeCar.position.z += Math.cos(polAngle) * currentPoliceSpeed;
            policeBox.setFromObject(polBody);

            // Blaulicht Effekt
            blaulicht.material.color.setHex(Math.floor(Date.now() / 120) % 2 === 0 ? 0x0000ff : 0xff0000);

            // Busted-Bedingung
            if (playerBox.intersectsBox(policeBox)) {
                gameActive = false;
                document.getElementById('status-text').innerText = "💥 BUSTED / GAME OVER";
                document.getElementById('status-text').style.color = "#dc2626";
                document.getElementById('game-status').style.display = "block";
            }

            // --- NPC VERKEHRS-MANAGEMENT (Fahren koordiniert ohne Durchdringen) ---
            npcTraffic.forEach((npc, idx) => {
                const npcOrigX = npc.group.position.x;
                const npcOrigZ = npc.group.position.z;

                if (npc.isX) npc.group.position.x += npc.speed * npc.dir;
                else npc.group.position.z += npc.speed * npc.dir;

                npc.box.setFromObject(npc.mesh);

                let isBlocked = false;

                // Prüfe Kollision gegen alle anderen Zivil-Autos
                for (let j = 0; j < npcTraffic.length; j++) {
                    if (idx !== j && npc.box.intersectsBox(npcTraffic[j].box)) { isBlocked = true; break; }
                }
                
                // Prüfe Kollision gegen Gebäude
                for (let k = 0; k < collisionObstacles.length; k++) {
                    if (npc.box.intersectsBox(collisionObstacles[k].box)) { isBlocked = true; break; }
                }

                // Spielfeldrand-Check oder Blockade -> Umkehren
                if (isBlocked || Math.abs(npc.group.position.x) > mapSize/2 || Math.abs(npc.group.position.z) > mapSize/2) {
                    npc.group.position.set(npcOrigX, 0.2, npcOrigZ);
                    npc.dir *= -1; 
                }

                // Wenn Spieler den NPC rammt
                if (playerBox.intersectsBox(npc.box)) {
                    playerCar.position.set(origX, 0.2, origZ);
                    speed = -speed * 0.35;
                }
            });

            // --- UI UPDATE & INTERPOLIERTE KAMERA ---
            document.getElementById('speed-val').innerText = Math.round(Math.abs(speed) * 115);

            // Kamera-Federung hinter dem Spieler hergezogen
            const wishCamX = playerCar.position.x - Math.sin(angle) * 16;
            const wishCamZ = playerCar.position.z - Math.cos(angle) * 16;
            const wishCamY = playerCar.position.y + 6.5;

            camera.position.x += (wishCamX - camera.position.x) * 0.09;
            camera.position.y += (wishCamY - camera.position.y) * 0.09;
            camera.position.z += (wishCamZ - camera.position.z) * 0.09;
            camera.lookAt(playerCar.position.x + Math.sin(angle) * 3, playerCar.position.y + 0.5, playerCar.position.z + Math.cos(angle) * 3);

            renderer.render(scene, camera);
        }

        // Window Resize Handler
        window.addEventListener('resize', () => {
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        });

        animate();
    </script>
</body>
</html>
"""

components.html(game_html, height=660, scrolling=False)

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="3D City Escape Pro",
    page_icon="🚓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🏙️ 3D City Escape Simulator (Steuerung Fix)")
st.write("👉 **HINWEIS:** Klicke einmal mitten in das Spiel, um loszufahren. Tasten: **WASD** oder **Pfeiltasten**.")

game_html = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>3D City Escape Pro</title>
    <style>
        body { margin: 0; overflow: hidden; background-color: #bae6fd; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; user-select: none; }
        #canvas-container { width: 100vw; height: 75vh; position: relative; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.4); background-color: #a5f3fc; cursor: pointer; }
        #ui-layer {
            position: absolute; bottom: 25px; left: 25px; color: #0f172a;
            background: rgba(255, 255, 255, 0.95); padding: 15px 25px; border-radius: 12px;
            font-size: 24px; font-weight: bold; border: 2px solid #cbd5e1; pointer-events: none;
        }
        #ui-layer span { color: #dc2626; }
        #timer-layer {
            position: absolute; top: 25px; right: 25px; color: #ffffff;
            background: rgba(15, 23, 42, 0.95); padding: 12px 25px; border-radius: 12px;
            font-size: 28px; font-weight: bold; border: 2px solid #3b82f6; pointer-events: none;
        }
        #game-status {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            color: #ffffff; background: rgba(15, 23, 42, 0.95); padding: 40px 60px; border-radius: 16px;
            font-size: 42px; font-weight: bold; text-align: center; display: none; z-index: 100;
            border: 3px solid #dc2626;
        }
        #reset-btn {
            position: absolute; top: 25px; left: 25px; color: #ffffff;
            background: #2563eb; padding: 12px 24px; border-radius: 8px;
            font-size: 15px; font-weight: bold; border: none; cursor: pointer; z-index: 10;
        }
        #focus-warning {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: rgba(234, 179, 8, 0.95); color: #0f172a; padding: 20px 40px;
            border-radius: 12px; font-weight: bold; font-size: 20px; border: 2px solid #ca8a04;
            text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>

    <div id="canvas-container">
        <button id="reset-btn" onclick="resetGame(); event.stopPropagation();">🔄 Spiel Neustarten (R)</button>
        <div id="focus-warning">⚠️ BITTE HIER REINKLICKEN ZUM FAHREN!</div>
        <div id="game-status">
            <span id="status-text">GAME OVER</span><br>
            <span style="font-size:18px; color:#94a3b8; font-weight:normal; display:block; margin-top:10px;">Drücke R zum Wiederholen</span>
        </div>
        <div id="ui-layer"><span id="speed-val">0</span> KM/H</div>
        <div id="timer-layer">⏱️ <span id="time-val">05:00</span></div>
    </div>

    <script>
        // ==========================================
        // 1. ENGINE SETUP
        // ==========================================
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xa5f3fc);
        scene.fog = new THREE.FogExp2(0xa5f3fc, 0.0035);

        const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 2000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        scene.add(new THREE.AmbientLight(0xffffff, 0.75));
        const sun = new THREE.DirectionalLight(0xfffbeb, 1.3);
        sun.position.set(300, 500, 200);
        sun.castShadow = true;
        scene.add(sun);

        // VARIABLEN
        const mapSize = 1200;
        const blockSize = 90;
        const roadWidth = 24;
        const sidewalkW = 4;

        let gameActive = true;
        let timeLeft = 300; 

        const collisionObstacles = [];
        const npcTraffic = [];

        const boxGeo = new THREE.BoxGeometry(1, 1, 1);
        const planeGeo = new THREE.PlaneGeometry(1, 1);
        const cylGeo = new THREE.CylinderGeometry(1, 1, 1, 16);

        // GROUND
        const ground = new THREE.Mesh(new THREE.PlaneGeometry(mapSize, mapSize), new THREE.MeshStandardMaterial({ color: 0x15803d, roughness: 0.9 }));
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        scene.add(ground);

        // STADT GENERIEREN
        for (let x = -mapSize/2; x < mapSize/2; x += blockSize) {
            for (let z = -mapSize/2; z < mapSize/2; z += blockSize) {
                createRoads(x, z, blockSize);
                
                if (Math.abs(x) < blockSize && Math.abs(z) < blockSize) continue;

                const innerW = blockSize - roadWidth;
                const sw = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0x71717a }));
                sw.scale.set(innerW, 0.4, innerW);
                sw.position.set(x + roadWidth/2 + innerW/2, 0.2, z + roadWidth/2 + innerW/2);
                scene.add(sw);

                if (Math.random() > 0.15) {
                    createBuilding(x, z, innerW);
                }
            }
        }

        function createRoads(x, z, size) {
            const road = new THREE.Mesh(planeGeo, new THREE.MeshStandardMaterial({ color: 0x1e1b4b, roughness: 0.85 }));
            road.scale.set(size, size, 1); road.rotation.x = -Math.PI / 2;
            road.position.set(x + size/2, 0.02, z + size/2);
            scene.add(road);

            const mLine = new THREE.Mesh(planeGeo, new THREE.MeshBasicMaterial({ color: 0xffffff }));
            mLine.scale.set(0.2, size, 1); mLine.rotation.x = -Math.PI / 2;
            mLine.position.set(x + size/2, 0.03, z + size/2);
            scene.add(mLine);
        }

        function createBuilding(x, z, innerW) {
            const h = 40 + Math.random() * 80;
            const buildW = innerW - sidewalkW * 2;
            const body = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0x3f3f46, roughness: 0.5 }));
            body.scale.set(buildW, h, buildW); body.position.set(x + blockSize/2, h/2 + 0.2, z + blockSize/2);
            body.castShadow = true; scene.add(body);
            collisionObstacles.push({ box: new THREE.Box3().setFromObject(body) });
        }

        // FAHRZEUGE
        const playerCar = new THREE.Group();
        const pBody = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0xdc2626, metalness: 0.6 }));
        pBody.scale.set(2.4, 0.7, 4.6); pBody.position.y = 0.5; playerCar.add(pBody);
        playerCar.position.set(8, 0.2, 8); scene.add(playerCar);
        const playerBox = new THREE.Box3();

        const policeCar = new THREE.Group();
        const polBody = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0x1d4ed8 }));
        polBody.scale.set(2.4, 0.7, 4.6); polBody.position.y = 0.5; policeCar.add(polBody);
        const blaulicht = new THREE.Mesh(boxGeo, new THREE.MeshBasicMaterial({ color: 0x0000ff }));
        blaulicht.scale.set(0.8, 0.2, 0.4); blaulicht.position.set(0, 1.3, 0); policeCar.add(blaulicht);
        policeCar.position.set(-60, 0.2, -60); scene.add(policeCar);
        const policeBox = new THREE.Box3();

        // TRAFFIC
        const trafficColors = [0x059669, 0xd97706, 0x6d28d9, 0x4b5563];
        function generateTraffic(startX, startZ, moveOnX) {
            const aiCar = new THREE.Group();
            const aiBody = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: trafficColors[Math.floor(Math.random()*4)] }));
            aiBody.scale.set(2.3, 0.7, 4.6); aiBody.position.y = 0.5; aiCar.add(aiBody);
            aiCar.position.set(startX, 0.2, startZ);
            if (!moveOnX) aiCar.rotation.y = Math.PI / 2;
            scene.add(aiCar);
            npcTraffic.push({ group: aiCar, mesh: aiBody, box: new THREE.Box3(), isX: moveOnX, speed: 0.35, dir: 1 });
        }
        for (let i = -300; i < 300; i += 90) {
            generateTraffic(i, -14, true);
            generateTraffic(14, i, false);
        }

        // ==========================================
        // STEUERUNGS CORE (ABSOLUT SEPARIERT FÜR FOKUS)
        // ==========================================
        let speed = 0, maxSpeed = 2.5, accel = 0.06, friction = 0.025, angle = 0, turnSpeed = 0.05;
        const keys = { w: false, a: false, s: false, d: false };

        // Aktiviert Steuerung per Klick
        container.addEventListener('click', (e) => {
            window.focus();
            document.getElementById('focus-warning').style.display = 'none';
        });

        // Event-Listener direkt an das Dokument binden
        document.addEventListener('keydown', (e) => {
            const k = e.key.toLowerCase();
            if (k === 'w' || e.key === 'ArrowUp') { keys.w = true; e.preventDefault(); }
            if (k === 's' || e.key === 'ArrowDown') { keys.s = true; e.preventDefault(); }
            if (k === 'a' || e.key === 'ArrowLeft') { keys.a = true; e.preventDefault(); }
            if (k === 'd' || e.key === 'ArrowRight') { keys.d = true; e.preventDefault(); }
            if (k === 'r') resetGame();
        });

        document.addEventListener('keyup', (e) => {
            const k = e.key.toLowerCase();
            if (k === 'w' || e.key === 'ArrowUp') keys.w = false;
            if (k === 's' || e.key === 'ArrowDown') keys.s = false;
            if (k === 'a' || e.key === 'ArrowLeft') keys.a = false;
            if (k === 'd' || e.key === 'ArrowRight') keys.d = false;
        });

        // TIMER
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
            playerCar.position.set(8, 0.2, 8); policeCar.position.set(-60, 0.2, -60);
            speed = 0; angle = 0; timeLeft = 300; gameActive = true;
            document.getElementById('game-status').style.display = "none";
            window.focus();
        }

        // GAME LOOP
        function animate() {
            requestAnimationFrame(animate);
            if (!gameActive) return;

            // Beschleunigung berechnen
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

            // X-Achse bewegen & prüfen
            playerCar.position.x += Math.sin(angle) * speed;
            playerBox.setFromObject(pBody);
            let hitX = false;
            for(let i=0; i<collisionObstacles.length; i++) { if(playerBox.intersectsBox(collisionObstacles[i].box)) { hitX = true; break; } }
            if(hitX) { playerCar.position.x = oX; speed *= -0.2; }

            // Z-Achse bewegen & prüfen
            playerCar.position.z += Math.cos(angle) * speed;
            playerBox.setFromObject(pBody);
            let hitZ = false;
            for(let i=0; i<collisionObstacles.length; i++) { if(playerBox.intersectsBox(collisionObstacles[i].box)) { hitZ = true; break; } }
            if(hitZ) { playerCar.position.z = oZ; speed *= -0.2; }

            // POLIZEI KI
            const dx = playerCar.position.x - policeCar.position.x, dz = playerCar.position.z - policeCar.position.z;
            const pAngle = Math.atan2(dx, dz); policeCar.rotation.y = pAngle;
            policeCar.position.x += Math.sin(pAngle) * 1.35; policeCar.position.z += Math.cos(pAngle) * 1.35;
            policeBox.setFromObject(polBody);

            blaulicht.material.color.setHex(Math.floor(Date.now() / 120) % 2 === 0 ? 0x0000ff : 0xff0000);

            if (playerBox.intersectsBox(policeBox)) {
                gameActive = false;
                document.getElementById('status-text').innerText = "💥 GAME OVER";
                document.getElementById('status-text').style.color = "#dc2626";
                document.getElementById('game-status').style.display = "block";
            }

            // TRAFFIC KI
            npcTraffic.forEach((npc) => {
                const nX = npc.group.position.x, nZ = npc.group.position.z;
                if (npc.isX) npc.group.position.x += npc.speed * npc.dir;
                else npc.group.position.z += npc.speed * npc.dir;
                npc.box.setFromObject(npc.mesh);

                let blocked = false;
                for(let i=0; i<collisionObstacles.length; i++) { if(npc.box.intersectsBox(collisionObstacles[i].box)) { blocked = true; break; } }
                if (blocked || Math.abs(npc.group.position.x) > mapSize/2 || Math.abs(npc.group.position.z) > mapSize/2) {
                    npc.group.position.set(nX, 0.2, nZ); npc.dir *= -1;
                }
                if (playerBox.intersectsBox(npc.box)) { playerCar.position.set(oX, 0.2, oZ); speed *= -0.3; }
            });

            // UI & CAM
            document.getElementById('speed-val').innerText = Math.round(Math.abs(speed) * 115);
            camera.position.x += (playerCar.position.x - Math.sin(angle) * 16 - camera.position.x) * 0.09;
            camera.position.y += (playerCar.position.y + 6.5 - camera.position.y) * 0.09;
            camera.position.z += (playerCar.position.z - Math.cos(angle) * 16 - camera.position.z) * 0.09;
            camera.lookAt(playerCar.position);

            renderer.render(scene, camera);
        }

        // Direktfokus beim Laden erzwingen versuchen
        window.onload = () => { window.focus(); };
        animate();
    </script>
</body>
</html>
"""

components.html(game_html, height=660, scrolling=False)

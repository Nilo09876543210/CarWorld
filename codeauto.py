import streamlit as st
import streamlit.components.v1 as components

# Seiten-Konfiguration für maximale Breite
st.set_page_config(
    page_title="3D Open World City Driver Pro",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🏙️ 3D Open World City Simulator")
st.write("Klicke einmal in das Spielfeld, um die Steuerung zu aktivieren. Nutze WASD oder die Pfeiltasten!")

# Der komplette, optimierte HTML5 / Three.js Code
game_html = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; overflow: hidden; background-color: #a5f3fc; font-family: sans-serif; }
        #canvas-container { width: 100vw; height: 75vh; position: relative; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        #ui-layer {
            position: absolute; bottom: 20px; left: 20px; color: #1e293b;
            background: rgba(255, 255, 255, 0.9); padding: 12px 20px; border-radius: 8px;
            font-size: 22px; font-weight: bold; border: 2px solid #cbd5e1; pointer-events: none;
        }
        #ui-layer span { color: #2563eb; }
        #controls-hint {
            position: absolute; top: 20px; right: 20px; color: #334155;
            background: rgba(255, 255, 255, 0.9); padding: 10px 15px; border-radius: 8px;
            font-size: 13px; border: 1px solid #cbd5e1; pointer-events: none;
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>

    <div id="canvas-container" onclick="window.focus();">
        <div id="ui-layer"><span id="speed-val">0</span> KM/H</div>
        <div id="controls-hint">🕹️ <b>Hier klicken zum Aktivieren</b><br>Steuerung: WASD / Pfeiltasten</div>
    </div>

    <script>
        // --- 1. SETUP & ATMOSPHÄRE ---
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xa5f3fc); // Heller Sommerhimmel
        scene.fog = new THREE.FogExp2(0xa5f3fc, 0.005);

        const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(renderer.domElement);

        // --- 2. TAGESLICHT (Sonne) ---
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const sunLight = new THREE.DirectionalLight(0xfffbeb, 1.2);
        sunLight.position.set(150, 250, 100);
        sunLight.castShadow = true;
        sunLight.shadow.mapSize.width = 2048;
        sunLight.shadow.mapSize.height = 2048;
        scene.add(sunLight);

        // --- 3. WELT-GENERIERUNG (Straßen & Häuser im Raster) ---
        const mapSize = 800;
        const blockSize = 60;   
        const roadWidth = 16;   
        const sidewalkW = 2;    

        // Wiese als Untergrund
        const lawn = new THREE.Mesh(
            new THREE.PlaneGeometry(mapSize, mapSize),
            new THREE.MeshStandardMaterial({ color: 0x15803d, roughness: 0.9 })
        );
        lawn.rotation.x = -Math.PI / 2;
        lawn.receiveShadow = true;
        scene.add(lawn);

        const buildingBoxen = []; 

        for (let x = -mapSize/2; x < mapSize/2; x += blockSize) {
            for (let z = -mapSize/2; z < mapSize/2; z += blockSize) {
                
                // Asphaltierten Straßenabschnitt bauen
                createRoad(x, z, blockSize);

                // Startzone im Zentrum (0,0) frei lassen
                if (Math.abs(x) < blockSize && Math.abs(z) < blockSize) continue;

                // Erhöhte Gehwege bauen
                createSidewalk(x, z, blockSize);

                // Häuserblöcke platzieren
                if (Math.random() > 0.25) {
                    const hHeight = 25 + Math.random() * 65;
                    const hWidth = blockSize - roadWidth - (sidewalkW * 2);
                    const hDepth = blockSize - roadWidth - (sidewalkW * 2);

                    const houseColors = [0x94a3b8, 0xcbd5e1, 0xe2e8f0, 0x78716c, 0xf5f5f4];
                    const randomColor = houseColors[Math.floor(Math.random() * houseColors.length)];

                    const bGeo = new THREE.BoxGeometry(hWidth, hHeight, hDepth);
                    const bMat = new THREE.MeshStandardMaterial({ color: randomColor, roughness: 0.5 });
                    const building = new THREE.Mesh(bGeo, bMat);
                    
                    const posX = x + roadWidth/2 + sidewalkW + hWidth/2;
                    const posZ = z + roadWidth/2 + sidewalkW + hDepth/2;
                    building.position.set(posX, hHeight/2, posZ);
                    building.castShadow = true;
                    building.receiveShadow = true;
                    scene.add(building);

                    // Fenster auf das Haus zeichnen
                    addWindows(building, hWidth, hHeight, hDepth);

                    // Kollisionsbox registrieren
                    const box = new THREE.Box3().setFromObject(building);
                    buildingBoxen.push(box);
                }
            }
        }

        function createRoad(x, z, size) {
            const rGeo = new THREE.PlaneGeometry(size, size);
            const rMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.8 });
            const road = new THREE.Mesh(rGeo, rMat);
            road.rotation.x = -Math.PI / 2;
            road.position.set(x + size/2, 0.02, z + size/2);
            road.receiveShadow = true;
            scene.add(road);

            // Mittelstreifen
            const lineMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
            const lineGeo = new THREE.PlaneGeometry(0.2, size);
            const marker = new THREE.Mesh(lineGeo, lineMat);
            marker.rotation.x = -Math.PI / 2;
            marker.position.set(x + size/2, 0.03, z + size/2);
            scene.add(marker);
        }

        function createSidewalk(x, z, size) {
            const swWidth = size - roadWidth;
            const swGeo = new THREE.BoxGeometry(swWidth, 0.2, swWidth);
            const swMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.6 });
            const sw = new THREE.Mesh(swGeo, swMat);
            sw.position.set(x + roadWidth/2 + swWidth/2, 0.1, z + roadWidth/2 + swWidth/2);
            sw.receiveShadow = true;
            scene.add(sw);
        }

        function addWindows(building, w, h, d) {
            const winGeo = new THREE.PlaneGeometry(0.8, 1.2);
            const winMat = new THREE.MeshBasicMaterial({ color: 0xbae6fd });
            for (let yHeight = 4; yHeight < h - 4; yHeight += 5) {
                for (let xPos = -w/2 + 3; xPos < w/2 - 3; xPos += 4) {
                    const win = new THREE.Mesh(winGeo, winMat);
                    win.position.set(xPos, yHeight - h/2, d/2 + 0.05);
                    building.add(win);
                }
            }
        }

        // --- 4. DAS 3D-AUTO ---
        const car = new THREE.Group();
        const carBody = new THREE.Mesh(
            new THREE.BoxGeometry(2.2, 0.6, 4.4), 
            new THREE.MeshStandardMaterial({ color: 0xdc2626, metalness: 0.7, roughness: 0.2 })
        );
        carBody.position.y = 0.5;
        carBody.castShadow = true;
        car.add(carBody);

        const cab = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.5, 2.0), new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.2 }));
        cab.position.set(0, 0.9, -0.2);
        car.add(cab);

        // Räder
        const wheelGeo = new THREE.CylinderGeometry(0.5, 0.5, 0.4, 32);
        const wheelMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.8 });
        wheelGeo.rotateZ(Math.PI / 2);

        const wheelPos = [[-1.15, 0.5, 1.4], [1.15, 0.5, 1.4], [-1.15, 0.5, -1.4], [1.15, 0.5, -1.4]];
        const wheels = [];
        wheelPos.forEach(pos => {
            const w = new THREE.Mesh(wheelGeo, wheelMat);
            w.position.set(pos[0], pos[1], pos[2]);
            w.castShadow = true;
            car.add(w);
            wheels.push(w);
        });

        car.position.set(8, 0, 8); // Startplatz auf der Straße
        scene.add(car);

        const carBox = new THREE.Box3();

        // --- 5. PHYSIK-VARIABLEN ---
        let speed = 0, maxSpeed = 1.8, accel = 0.04, friction = 0.02, brakePower = 0.07, angle = 0, turnSpeed = 0.045;
        const keys = { w: false, a: false, s: false, d: false, ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false };
        
        window.addEventListener('keydown', (e) => { if (e.key in keys) { keys[e.key] = true; e.preventDefault(); } });
        window.addEventListener('keyup', (e) => { if (e.key in keys) keys[e.key] = false; });

        // --- 6. GAME LOOP (mit Schramm-Kollision) ---
        function animate() {
            requestAnimationFrame(animate);

            if (keys.w || keys.ArrowUp) { if (speed < maxSpeed) speed += accel; }
            else if (keys.s || keys.ArrowDown) {
                if (speed > 0) speed -= brakePower;
                else if (speed > -maxSpeed/2) speed -= accel;
            } else {
                if (speed > 0) speed -= friction;
                else if (speed < 0) speed += friction;
                if (Math.abs(speed) < friction) speed = 0;
            }

            if (Math.abs(speed) > 0.05) {
                const dir = speed > 0 ? 1 : -1;
                if (keys.a || keys.ArrowLeft) { angle += turnSpeed * dir; wheels[0].rotation.y = 0.35; wheels[1].rotation.y = 0.35; }
                else if (keys.d || keys.ArrowRight) { angle -= turnSpeed * dir; wheels[0].rotation.y = -0.35; wheels[1].rotation.y = -0.35; }
                else { wheels[0].rotation.y = 0; wheels[1].rotation.y = 0; }
            }

            wheels.forEach(w => w.rotation.x += speed * 0.4);
            car.rotation.y = angle;

            // --- ERWEITERTE SCHRAMM-KOLLISION (Achsen-getrennt) ---
            const oldX = car.position.x;
            const oldZ = car.position.z;

            // 1. Bewegung auf X-Achse testen
            car.position.x += Math.sin(angle) * speed;
            carBox.setFromObject(carBody);
            let hitX = false;
            for (let i = 0; i < buildingBoxen.length; i++) {
                if (carBox.intersectsBox(buildingBoxen[i])) { hitX = true; break; }
            }
            if (hitX) { car.position.x = oldX; speed *= 0.7; } // X zurücksetzen bei Treffer

            // 2. Bewegung auf Z-Achse testen
            car.position.z += Math.cos(angle) * speed;
            carBox.setFromObject(carBody);
            let hitZ = false;
            for (let i = 0; i < buildingBoxen.length; i++) {
                if (carBox.intersectsBox(buildingBoxen[i])) { hitZ = true; break; }
            }
            if (hitZ) { car.position.z = oldZ; speed *= 0.7; } // Z zurücksetzen bei Treffer

            document.getElementById('speed-val').innerText = Math.round(Math.abs(speed) * 110);

            // Kamera-Verfolgung
            camera.position.x += (car.position.x - Math.sin(angle) * 14 - camera.position.x) * 0.1;
            camera.position.y += (car.position.y + 5.0 - camera.position.y) * 0.1;
            camera.position.z += (car.position.z - Math.cos(angle) * 14 - camera.position.z) * 0.1;
            camera.lookAt(car.position.x + Math.sin(angle)*2, car.position.y + 0.8, car.position.z + Math.cos(angle)*2);

            renderer.render(scene, camera);
        }

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

components.html(game_html, height=640, scrolling=False)

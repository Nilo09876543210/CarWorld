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
st.write("Klicke einmal in das Spielfeld, um zu steuern. Nutze WASD oder die Pfeiltasten. Erkunde die Straßen und weiche den Gebäuden aus!")

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
        // --- 1. SETUP & ATHMOSPHÄRE (TAGMODUS) ---
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xa5f3fc); // Schöner, heller Sommerhimmel
        scene.fog = new THREE.FogExp2(0xa5f3fc, 0.005); // Sanfter Horizont-Dunst

        const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(renderer.domElement);

        // --- 2. BELEUCHTUNG (Realistischer Sonnenstand) ---
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const sunLight = new THREE.DirectionalLight(0xfffbeb, 1.2);
        sunLight.position.set(150, 250, 100);
        sunLight.castShadow = true;
        sunLight.shadow.mapSize.width = 2048;
        sunLight.shadow.mapSize.height = 2048;
        sunLight.shadow.camera.near = 0.5;
        sunLight.shadow.camera.far = 500;
        const d = 100;
        sunLight.shadow.camera.left = -d;
        sunLight.shadow.camera.right = d;
        sunLight.shadow.camera.top = d;
        sunLight.shadow.camera.bottom = -d;
        scene.add(sunLight);

        // --- 3. DIE STADTPLANUNG (Straßen, Gehwege, Häuser) ---
        const mapSize = 800;
        const blockSize = 60;   // Größe eines Häuserblocks
        const roadWidth = 16;   // Breite der Hauptstraßen
        const sidewalkW = 2;    // Breite des Gehwegs neben den Häusern

        // Grüner Grundboden (Wiesen zwischen/unter der Stadt)
        const lawnGeo = new THREE.PlaneGeometry(mapSize, mapSize);
        const lawnMat = new THREE.MeshStandardMaterial({ color: 0x15803d, roughness: 0.9 });
        const lawn = new THREE.Mesh(lawnGeo, lawnMat);
        lawn.rotation.x = -Math.PI / 2;
        lawn.receiveShadow = true;
        scene.add(lawn);

        const buildingBoxen = []; // Array für Kollisionen

        // Prozedurales Straßen- und Häuserraster generieren
        for (let x = -mapSize/2; x < mapSize/2; x += blockSize) {
            for (let z = -mapSize/2; z < mapSize/2; z += blockSize) {
                
                // 1. Straßen asphaltieren (Überall im Raster)
                createCustomRoad(x, z, blockSize);

                // Startzone im Zentrum (0,0) komplett frei von Gebäuden halten
                if (Math.abs(x) < blockSize && Math.abs(z) < blockSize) continue;

                // 2. Gehwege (Sidewalks) um die Häuserblöcke bauen
                createSidewalk(x, z, blockSize);

                // 3. Häuser auf den Blöcken platzieren
                if (Math.random() > 0.25) {
                    const hHeight = 25 + Math.random() * 65;
                    const hWidth = blockSize - roadWidth - (sidewalkW * 2);
                    const hDepth = blockSize - roadWidth - (sidewalkW * 2);

                    const houseColors = [0x94a3b8, 0xcbd5e1, 0xe2e8f0, 0x78716c, 0xf5f5f4];
                    const randomColor = houseColors[Math.floor(Math.random() * houseColors.length)];

                    // Haus-Körper
                    const bGeo = new THREE.BoxGeometry(hWidth, hHeight, hDepth);
                    const bMat = new THREE.MeshStandardMaterial({ color: randomColor, roughness: 0.5 });
                    const building = new THREE.Mesh(bGeo, bMat);
                    
                    // Positionierung perfekt auf dem Block innerhalb des Gehwegs
                    const posX = x + roadWidth/2 + sidewalkW + hWidth/2;
                    const posZ = z + roadWidth/2 + sidewalkW + hDepth/2;
                    building.position.set(posX, hHeight/2, posZ);
                    building.castShadow = true;
                    building.receiveShadow = true;
                    scene.add(building);

                    // Details hinzufügen: Fenster (visuelle Struktur)
                    addWindowsToBuilding(building, hWidth, hHeight, hDepth);

                    // Kollisionsbox für dieses Haus berechnen und speichern
                    const box = new THREE.Box3().setFromObject(building);
                    buildingBoxen.push(box);
                }
            }
        }

        // Funktion zur Erstellung detaillierter Straßen mit Fahrstreifen
        function createCustomRoad(x, z, size) {
            // Asphalt
            const rGeo = new THREE.PlaneGeometry(size, size);
            const rMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.8 }); // Anthrazit
            const road = new THREE.Mesh(rGeo, rMat);
            road.rotation.x = -Math.PI / 2;
            road.position.set(x + size/2, 0.02, z + size/2);
            road.receiveShadow = true;
            scene.add(road);

            // Fahrbahnmarkierung (Mittelstreifen) längs und quer simulieren
            const lineMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
            const lineGeoLong = new THREE.PlaneGeometry(0.2, size);
            const markerLong = new THREE.Mesh(lineGeoLong, lineMat);
            markerLong.rotation.x = -Math.PI / 2;
            markerLong.position.set(x + size/2, 0.03, z + size/2);
            scene.add(markerLong);
        }

        // Funktion zur Erstellung erhöhter Gehwege
        function createSidewalk(x, z, size) {
            const swWidth = size - roadWidth;
            const swGeo = new THREE.BoxGeometry(swWidth, 0.2, swWidth);
            const swMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.6 });
            const sw = new THREE.Mesh(swGeo, swMat);
            sw.position.set(x + roadWidth/2 + swWidth/2, 0.1, z + roadWidth/2 + swWidth/2);
            sw.receiveShadow = true;
            scene.add(sw);
        }

        // Fenster-Strukturen auf die Häuser projezieren
        function addWindowsToBuilding(building, w, h, d) {
            const winGeo = new THREE.PlaneGeometry(0.8, 1.2);
            const winMat = new THREE.MeshBasicMaterial({ color: 0xbae6fd }); // Hellblaue Fenster-Optik
            
            // Einfache Schleife für ein paar Fensterreihen an der Vorderseite
            for (let yHeight = 4; yHeight < h - 4; yHeight += 5) {
                for (let xPos = -w/2 + 3; xPos < w/2 - 3; xPos += 4) {
                    const win = new THREE.Mesh(winGeo, winMat);
                    win.position.set(xPos, yHeight - h/2, d/2 + 0.05); // Minimal vor der Wand platziert
                    building.add(win);
                }
            }
        }

        // --- 4. DAS 3D-AUTO (Sportwagen-Design) ---
        const car = new THREE.Group();
        
        // Hauptkarosserie
        const carBody = new THREE.Mesh(
            new THREE.BoxGeometry(2.2, 0.6, 4.4), 
            new THREE.MeshStandardMaterial({ color: 0xdc2626, metalness: 0.7, roughness: 0.2 }) // Sportliches Rot mit Glanz
        );
        carBody.position.y = 0.5;
        carBody.castShadow = true;
        car.add(carBody);

        // Fahrerkabine
        const cab = new THREE.Mesh(
            new THREE.BoxGeometry(1.7, 0.5, 2.0), 
            new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.2 })
        );
        cab.position.set(0, 0.9, -0.2);
        cab.castShadow = true;
        car.add(cab);

        // Scheinwerfer
        const lightGeo = new THREE.BoxGeometry(0.3, 0.15, 0.1);
        const lightMat = new THREE.MeshBasicMaterial({ color: 0xfef08a }); // Gelb-Weißes Licht
        const fLeft = new THREE.Mesh(lightGeo, lightMat); fLeft.position.set(-0.85, 0.5, 2.21); car.add(fLeft);
        const fRight = new THREE.Mesh(lightGeo, lightMat); fRight.position.set(0.85, 0.5, 2.21); car.add(fRight);

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

        // Startposition auf einer der Straßen im Zentrum
        car.position.set(8, 0, 8);
        scene.add(car);

        const carBox = new THREE.Box3();

        // --- 5. PHYSIK- & FAHRMECHANIK ---
        let speed = 0;
        const maxSpeed = 1.8;
        const accel = 0.04;
        const friction = 0.02;
        const brakePower = 0.07;
        let angle = 0;
        const turnSpeed = 0.045;

        // Input-Tracker
        const keys = { w: false, a: false, s: false, d: false, ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false };
        
        window.addEventListener('keydown', (e) => { 
            if (e.key in keys) { keys[e.key] = true; e.preventDefault(); }
        });
        window.addEventListener('keyup', (e) => { if (e.key in keys) keys[e.key] = false; });

        // --- 6. GAME LOOP ---
        function animate() {
            requestAnimationFrame(animate);

            // Gas geben / Bremsen
            if (keys.w || keys.ArrowUp) {
                if (speed < maxSpeed) speed += accel;
            } else if (keys.s || keys.ArrowDown) {
                if (speed > 0) speed -= brakePower; // Aktiv Bremsen
                else if (speed > -maxSpeed/2) speed -= accel; // Rückwärtsgang
            } else {
                // Reibungsverlust beim Rollen
                if (speed > 0) speed -= friction;
                else if (speed < 0) speed += friction;
                if (Math.abs(speed) < friction) speed = 0;
            }

            // Realistische Lenkung (nur in der Bewegung möglich)
            if (Math.abs(speed) > 0.05) {
                const dirModifier = speed > 0 ? 1 : -1;
                if (keys.a || keys.ArrowLeft) {
                    angle += turnSpeed * dirModifier;
                    wheels[0].rotation.y = 0.35; wheels[1].rotation.y = 0.35; // Visueller Lenkeinschlag vorne
                } else if (keys.d || keys.ArrowRight) {
                    angle -= turnSpeed * dirModifier;
                    wheels[0].rotation.y = -0.35; wheels[1].rotation.y = -0.35;
                } else {
                    wheels[0].rotation.y = 0; wheels[1].rotation.y = 0;
                }
            }

            // Raddrehung animieren
            wheels.forEach(w => w.rotation.x += speed * 0.4);

            car.rotation.y = angle;

            // --- KOLLISIONS-ABFRAGE VOR BEWEGUNG ---
            const oldX = car.position.x;
            const oldZ = car.position.z;

            // Berechne den nächsten Bewegungsschritt
            car.position.x += Math.sin(angle) * speed;
            car.position.z += Math.cos(angle) * speed;

            // Update der Fahrzeug-Kollisionsbox an der neuen Position
            carBox.setFromObject(carBody);

            let hit = false;
            for (let i = 0; i < buildingBoxen.length; i++) {
                if (carBox.intersectsBox(buildingBoxen[i])) {
                    hit = true;
                    break;
                }
            }

            // Falls Kollision: Bewegung rückgängig machen und Abprall-Physik einleiten
            if (hit) {
                car.position.x = oldX;
                car.position.z = oldZ;
                speed = -speed * 0.25; // Prallt elastisch ab
            }

            // Tacho auf UI-Layer schreiben
            document.getElementById('speed-val').innerText = Math.round(Math.abs(speed) * 110);

            // Flüssige Third-Person Kameraverfolgung (Kamera gleitet hinterher)
            const targetCamX = car.position.x - Math.sin(angle) * 14;
            const targetCamZ = car.position.z - Math.cos(angle) * 14;
            const targetCamY = car.position.y + 5.0;

            camera.position.x += (targetCamX - camera.position.x) * 0.1;
            camera.position.y += (targetCamY - camera.position.y) * 0.1;
            camera.position.z += (targetCamZ - camera.position.z) * 0.1;
            
            // Kamera blickt leicht vor die Stoßstange des Autos
            camera.lookAt(car.position.x + Math.sin(angle)*2, car.position.y + 0.8, car.position.z + Math.cos(angle)*2);

            renderer.render(scene, camera);
        }

        // Anpassung bei Event-Änderungen im Browserfenster
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

# Rendert das Spiel direkt in deiner Streamlit Web-App
components.html(game_html, height=640, scrolling=False)

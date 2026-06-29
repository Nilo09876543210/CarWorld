import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="3D Open World City Driver",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🚗 Realistischer 3D City Driver (Tagmodus)")
st.write("Klicke einmal in das Spielfeld. Steuerung mit WASD oder Pfeiltasten. Häuser blockieren jetzt die Durchfahrt!")

# HTML/JavaScript Code mit hellem Himmel, Straßen-Textur-Ersatz und Kollisionen
game_html = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; overflow: hidden; background-color: #7dd3fc; font-family: sans-serif; }
        #canvas-container { width: 100vw; height: 75vh; position: relative; border-radius: 12px; overflow: hidden; }
        #ui-layer {
            position: absolute; bottom: 20px; left: 20px; color: #0f172a;
            background: rgba(255, 255, 255, 0.9); padding: 15px 25px; border-radius: 10px;
            font-size: 24px; font-weight: bold; border: 2px solid #cbd5e1; pointer-events: none;
        }
        #ui-layer span { color: #3b82f6; }
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
        <div id="controls-hint">🕹️ <b>Einmal klicken zum Steuern</b><br>WASD / Pfeiltasten</div>
    </div>

    <script>
        // --- 1. SETUP & HELLER HIMMEL ---
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xbae6fd); // Heller, blauer Himmel (Tagmodus)
        scene.fog = new THREE.FogExp2(0xbae6fd, 0.008);

        const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        // --- 2. TAGESLICHT (Sonne) ---
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const sunLight = new THREE.DirectionalLight(0xfffbeb, 1.0); // Starke Sonne
        sunLight.position.set(100, 200, 70);
        sunLight.castShadow = true;
        scene.add(sunLight);

        // --- 3. STRASSENSYSTEM & GEBÄUDE ---
        const mapSize = 600;
        
        // Grüner Untergrund (Wiese neben den Straßen)
        const ground = new THREE.Mesh(
            new THREE.PlaneGeometry(mapSize, mapSize),
            new THREE.MeshStandardMaterial({ color: 0x22c55e, roughness: 0.9 })
        );
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        scene.add(ground);

        // Listen für Gebäude-Kollisionen
        const buildings = [];
        const buildingBoxen = [];

        // Stadt-Layout mit festen Straßenkreuzungen generieren
        const blockSize = 40;
        const roadWidth = 14;

        for (let x = -mapSize/2; x < mapSize/2; x += blockSize) {
            for (let z = -mapSize/2; z < mapSize/2; z += blockSize) {
                // Startbereich im Zentrum komplett freihalten für Straßen
                if (Math.abs(x) < 30 && Math.abs(z) < 30) {
                    createRoadPlane(x, z, blockSize);
                    continue;
                }

                // Asphalt-Fläche für Straßen erzeugen
                createRoadPlane(x, z, blockSize);

                // Häuserblöcke nur abseits der Straßen setzen (Zufall)
                if (Math.random() > 0.3) {
                    const hHeight = 20 + Math.random() * 50;
                    const hWidth = blockSize - roadWidth;
                    const hDepth = blockSize - roadWidth;

                    // Realistische Gebäudefarben (Grau, Beige, Weiß)
                    const colorPalette = [0x94a3b8, 0xe2e8f0, 0xcbd5e1, 0x64748b];
                    const randomColor = colorPalette[Math.floor(Math.random() * colorPalette.length)];

                    const bMat = new THREE.MeshStandardMaterial({ color: randomColor, roughness: 0.4 });
                    const bGeo = new THREE.BoxGeometry(hWidth, hHeight, hDepth);
                    const building = new THREE.Mesh(bGeo, bMat);
                    
                    // Positionierung genau im Raster-Zentrum des Blocks
                    building.position.set(x + roadWidth, hHeight/2, z + roadWidth);
                    building.castShadow = true;
                    building.receiveShadow = true;
                    
                    scene.add(building);
                    buildings.push(building);

                    // Unsichtbare 3D-Kollisionsbox für dieses Haus erstellen
                    const box = new THREE.Box3().setFromObject(building);
                    buildingBoxen.push(box);
                }
            }
        }

        // Hilfsfunktion für graue Asphalt-Straßen
        function createRoadPlane(x, z, size) {
            const road = new THREE.Mesh(
                new THREE.PlaneGeometry(size, size),
                new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.7 }) // Dunkelgrauer Asphalt
            );
            road.rotation.x = -Math.PI / 2;
            road.position.set(x + size/2, 0.02, z + size/2);
            road.receiveShadow = true;
            scene.add(road);
        }

        // --- 4. DAS AUTO ---
        const car = new THREE.Group();
        const carBody = new THREE.Mesh(
            new THREE.BoxGeometry(2, 0.6, 4), 
            new THREE.MeshStandardMaterial({ color: 0xef4444, metalness: 0.6, roughness: 0.2 }) // Roter Sportwagen
        );
        carBody.position.y = 0.5;
        carBody.castShadow = true;
        car.add(carBody);

        // Cockpit-Scheiben
        const glass = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.5, 1.8), new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.1 }));
        glass.position.set(0, 0.9, -0.1);
        car.add(glass);
        
        scene.add(car);

        // Kollisionsbox für das Auto initialisieren
        const carBox = new THREE.Box3();

        // --- 5. BEWEGUNG & KOLLISIONS-ABFRAGE ---
        let speed = 0, maxSpeed = 1.6, accel = 0.04, friction = 0.02, angle = 0, turnSpeed = 0.04;
        const keys = { w: false, a: false, s: false, d: false, ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false };
        
        window.addEventListener('keydown', (e) => { 
            if (e.key in keys) { keys[e.key] = true; e.preventDefault(); }
        });
        window.addEventListener('keyup', (e) => { if (e.key in keys) keys[e.key] = false; });

        // --- 6. GAME LOOP ---
        function animate() {
            requestAnimationFrame(animate);

            // Fahrphysik-Berechnung
            if (keys.w || keys.ArrowUp) { if (speed < maxSpeed) speed += accel; }
            else if (keys.s || keys.ArrowDown) { if (speed > -maxSpeed/2) speed -= accel; }
            else {
                if (speed > 0) speed -= friction;
                else if (speed < 0) speed += friction;
                if (Math.abs(speed) < friction) speed = 0;
            }

            if (Math.abs(speed) > 0.05) {
                const dir = speed > 0 ? 1 : -1;
                if (keys.a || keys.ArrowLeft) angle += turnSpeed * dir;
                if (keys.d || keys.ArrowRight) angle -= turnSpeed * dir;
            }

            car.rotation.y = angle;

            // --- KOLLISIONS-CHECK VOR DEM BEWEGEN ---
            // Wir berechnen die theoretisch neue Position vorab
            const nextX = car.position.x + Math.sin(angle) * speed;
            const nextZ = car.position.z + Math.cos(angle) * speed;

            // Temporär auf die neue Position setzen, um Box zu prüfen
            const oldX = car.position.x;
            const oldZ = car.position.z;
            car.position.x = nextX;
            car.position.z = nextZ;

            // Auto-Kollisionsbox updaten
            carBox.setFromObject(carBody);

            let kollision = false;
            // Prüfen, ob wir eine der Haus-Boxen berühren
            for (let i = 0; i < buildingBoxen.length; i++) {
                if (carBox.intersectsBox(buildingBoxen[i])) {
                    kollision = true;
                    break;
                }
            }

            if (kollision) {
                // Bei Kollision: Bewegung stoppen und leicht zurückbouncen
                car.position.x = oldX;
                car.position.z = oldZ;
                speed = -speed * 0.3; // Prallt ab
            }

            // Tacho aktualisieren
            document.getElementById('speed-val').innerText = Math.round(Math.abs(speed) * 100);

            // Smooth Third-Person Kameraverfolgung
            camera.position.x += (car.position.x - Math.sin(angle) * 14 - camera.position.x) * 0.1;
            camera.position.y += (car.position.y + 5.5 - camera.position.y) * 0.1;
            camera.position.z += (car.position.z - Math.cos(angle) * 14 - camera.position.z) * 0.1;
            camera.lookAt(car.position.x, car.position.y + 1, car.position.z);

            renderer.render(scene, camera);
        }

        animate();
    </script>
</body>
</html>
"""

components.html(game_html, height=640, scrolling=False)

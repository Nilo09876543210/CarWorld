import streamlit as st
import streamlit.components.v1 as components

# Seiten-Konfiguration für das perfekte Vollbild-Erlebnis
st.set_page_config(
    page_title="3D Open World City Driver",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# UI Styling für Streamlit
st.markdown("""
    <style>
    .reportview-container .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    h1 {
        color: #38bdf8 !important;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-weight: 800;
        margin-bottom: 5px;
    }
    .stMarkdown p {
        color: #94a3b8;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚗 3D Open World City Driver")
st.write("Erkunde die 3D-Metropole direkt im Browser. Steuere das Auto mit den Pfeiltasten oder WASD.")

# Das komplette HTML- und JavaScript-Paket (Three.js 3D-Engine)
game_html = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; overflow: hidden; background-color: #0b0f19; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        #canvas-container { width: 100vw; height: 70vh; position: relative; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.5); }
        #ui-layer {
            position: absolute;
            bottom: 20px;
            left: 20px;
            color: #38bdf8;
            background: rgba(15, 23, 42, 0.85);
            padding: 15px 25px;
            border-radius: 10px;
            font-size: 24px;
            font-weight: bold;
            border: 2px solid #1e293b;
            pointer-events: none;
            box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.3);
        }
        #ui-layer span { color: #f43f5e; }
        #controls-hint {
            position: absolute;
            top: 20px;
            right: 20px;
            color: #94a3b8;
            background: rgba(15, 23, 42, 0.85);
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 12px;
            border: 1px solid #1e293b;
            pointer-events: none;
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>

    <div id="canvas-container">
        <div id="ui-layer"><span id="speed-val">0</span> KM/H</div>
        <div id="controls-hint">Steuerung: <b>WASD</b> oder <b>Pfeiltasten</b></div>
    </div>

    <script>
        // --- 1. GAME SETUP ---
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0b0f19);
        scene.fog = new THREE.FogExp2(0x0b0f19, 0.012); // Realistischer Dunst in der Ferne

        const camera = new THREE.PerspectiveCamera(65, container.clientWidth / container.clientHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(renderer.domElement);

        // --- 2. BELEUCHTUNG (Atmosphärisches Nachtdesign) ---
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
        scene.add(ambientLight);

        const moonlight = new THREE.DirectionalLight(0x38bdf8, 0.6);
        moonlight.position.set(100, 200, 50);
        moonlight.castShadow = true;
        moonlight.shadow.mapSize.width = 2048;
        moonlight.shadow.mapSize.height = 2048;
        scene.add(moonlight);

        // --- 3. DIE OPEN-WORLD MAP ---
        const mapSize = 600;
        
        // Boden (Asphalt)
        const groundGeo = new THREE.PlaneGeometry(mapSize, mapSize);
        const groundMat = new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.8, metalness: 0.1 });
        const ground = new THREE.Mesh(groundGeo, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        scene.add(ground);

        // Straßenmarkierungen (Raster)
        const gridHelper = new THREE.GridHelper(mapSize, 30, 0x38bdf8, 0x1e293b);
        gridHelper.position.y = 0.01;
        scene.add(gridHelper);

        // Prozedurale Riesenstadt generieren
        const buildingGroup = new THREE.Group();
        const boxGeo = new THREE.BoxGeometry(1, 1, 1);
        
        for (let x = -mapSize/2; x < mapSize/2; x += 30) {
            for (let z = -mapSize/2; z < mapSize/2; z += 30) {
                // Startzone freihalten
                if (Math.abs(x) < 25 && Math.abs(z) < 25) continue;
                
                if (Math.random() > 0.3) {
                    const h = 20 + Math.random() * 70; // Zufällige Wolkenkratzer-Höhen
                    const w = 12 + Math.random() * 10;
                    const d = 12 + Math.random() * 10;
                    
                    // Cyberpunk/Neon-Farbpalette für die Gebäude
                    const hue = 0.55 + Math.random() * 0.15; // Blau bis Violett
                    const buildMat = new THREE.MeshStandardMaterial({ 
                        color: new THREE.Color().setHSL(hue, 0.7, 0.2),
                        roughness: 0.2,
                        metalness: 0.5
                    });
                    
                    const building = new THREE.Mesh(boxGeo, buildMat);
                    building.scale.set(w, h, d);
                    building.position.set(x + (Math.random()-0.5)*5, h / 2, z + (Math.random()-0.5)*5);
                    building.castShadow = true;
                    building.receiveShadow = true;
                    buildingGroup.add(building);
                }
            }
        }
        scene.add(buildingGroup);

        // --- 4. DAS 3D-AUTO ---
        const car = new THREE.Group();
        
        // Chassis (Hauptkörper)
        const bodyMat = new THREE.MeshStandardMaterial({ color: 0x3b82f6, roughness: 0.1, metalness: 0.8 });
        const bodyGeo = new THREE.BoxGeometry(2, 0.6, 4.2);
        const carBody = new THREE.Mesh(bodyGeo, bodyMat);
        carBody.position.y = 0.5;
        carBody.castShadow = true;
        carBody.receiveShadow = true;
        car.add(carBody);

        // Dach / Cockpit
        const cabGeo = new THREE.BoxGeometry(1.6, 0.5, 2.2);
        const cabMat = new THREE.MeshStandardMaterial({ color: 0x030712, roughness: 0.1 });
        const carCab = new THREE.Mesh(cabGeo, cabMat);
        carCab.position.set(0, 1.0, -0.2);
        carCab.castShadow = true;
        car.add(carCab);

        // Scheinwerfer (Vorne)
        const lightGeo = new THREE.BoxGeometry(0.3, 0.1, 0.1);
        const frontLightMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
        const leftLight = new THREE.Mesh(lightGeo, frontLightMat); leftLight.position.set(-0.8, 0.5, 2.1); car.add(leftLight);
        const rightLight = new THREE.Mesh(lightGeo, frontLightMat); rightLight.position.set(0.8, 0.5, 2.1); car.add(rightLight);

        // Rückleuchten / Bremslichter
        const brakeLightMat = new THREE.MeshStandardMaterial({ color: 0x991b1b, emissive: 0x000000 });
        const leftBrake = new THREE.Mesh(lightGeo, brakeLightMat); leftBrake.position.set(-0.8, 0.5, -2.1); car.add(leftBrake);
        const rightBrake = new THREE.Mesh(lightGeo, brakeLightMat); rightBrake.position.set(0.8, 0.5, -2.1); car.add(rightBrake);

        // Räder
        const wheelGeo = new THREE.CylinderGeometry(0.45, 0.45, 0.4, 24);
        const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.9 });
        wheelGeo.rotateZ(Math.PI / 2);

        const wheelPositions = [[-1.05, 0.45, 1.3], [1.05, 0.45, 1.3], [-1.05, 0.45, -1.3], [1.05, 0.45, -1.3]];
        const wheels = [];
        wheelPositions.forEach(pos => {
            const wheel = new THREE.Mesh(wheelGeo, wheelMat);
            wheel.position.set(pos[0], pos[1], pos[2]);
            wheel.castShadow = true;
            car.add(wheel);
            wheels.push(wheel);
        });
        
        scene.add(car);

        // --- 5. INTERAKTIVE PHYSIK-ENGINE ---
        let speed = 0;
        let maxSpeed = 1.4;
        let accel = 0.025;
        let friction = 0.012;
        let brakePower = 0.05;
        let turnSpeed = 0.035;
        let angle = 0;

        // Input-Abfrage
        const keys = { w: false, a: false, s: false, d: false, ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false };
        window.addEventListener('keydown', (e) => { if (e.key in keys) keys[e.key] = true; });
        window.addEventListener('keyup', (e) => { if (e.key in keys) keys[e.key] = false; });

        // --- 6. CORE GAME LOOP ---
        function animate() {
            requestAnimationFrame(animate);

            // Beschleunigen & Bremsen Logik
            if (keys.w || keys.ArrowUp) {
                if (speed < maxSpeed) speed += accel;
                brakeLightMat.emissive.setHex(0x000000); // Bremslichter aus
            } else if (keys.s || keys.ArrowDown) {
                if (speed > 0) {
                    speed -= brakePower; // Starkes Bremsen
                    brakeLightMat.emissive.setHex(0xff0000); // Bremslichter leuchten rot!
                } else if (speed > -maxSpeed / 2) {
                    speed -= accel; // Rückwärtsgang
                    brakeLightMat.emissive.setHex(0xaaaaaa); // Weißes Rückfahrlicht-Imitat
                }
            } else {
                // Physikalisches Ausrollen durch Reibung
                if (speed > 0) speed -= friction;
                else if (speed < 0) speed += friction;
                if (Math.abs(speed) < friction) speed = 0;
                brakeLightMat.emissive.setHex(0x000000);
            }

            // Realistische Lenkung (nur während der Fahrt möglich)
            if (Math.abs(speed) > 0.05) {
                const directionFactor = speed > 0 ? 1 : -1;
                if (keys.a || keys.ArrowLeft) {
                    angle += turnSpeed * directionFactor * (1.2 - Math.abs(speed)/maxSpeed*0.4);
                    wheels[0].rotation.y = 0.4; wheels[1].rotation.y = 0.4; // Rad-Einschlag visuell
                } else if (keys.d || keys.ArrowRight) {
                    angle -= turnSpeed * directionFactor * (1.2 - Math.abs(speed)/maxSpeed*0.4);
                    wheels[0].rotation.y = -0.4; wheels[1].rotation.y = -0.4;
                } else {
                    wheels[0].rotation.y = 0; wheels[1].rotation.y = 0;
                }
            }

            // Räder rotieren lassen basierend auf Geschwindigkeit
            wheels.forEach(w => w.rotation.x += speed * 0.5);

            // Auto-Ausrichtung updaten
            car.rotation.y = angle;
            car.position.x += Math.sin(angle) * speed;
            car.position.z += Math.cos(angle) * speed;

            // Tacho auf dem UI-Layer aktualisieren
            document.getElementById('speed-val').innerText = Math.round(Math.abs(speed) * 120);

            // Dynamic Camera Tracking (Verzögertes Hinterherziehen für Geschwindigkeitsgefühl)
            const targetCamX = car.position.x - Math.sin(angle) * 13;
            const targetCamZ = car.position.z - Math.cos(angle) * 13;
            const targetCamY = car.position.y + 4.8;

            camera.position.x += (targetCamX - camera.position.x) * 0.08;
            camera.position.y += (targetCamY - camera.position.y) * 0.08;
            camera.position.z += (targetCamZ - camera.position.z) * 0.08;
            
            // Fokuspunkt der Kamera liegt immer kurz vor dem Auto
            camera.lookAt(car.position.x + Math.sin(angle)*2, car.position.y + 0.8, car.position.z + Math.cos(angle)*2);

            renderer.render(scene, camera);
        }

        // Responsivität bei Größenänderung des Streamlit-Fensters
        window.addEventListener('resize', () => {
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        });

        // Spiel starten
        animate();
    </script>
</body>
</html>
"""

# Rendert das Spiel direkt nativ im Streamlit UI
components.html(game_html, height=620, scrolling=False)

st.markdown("""
---
### 🛠️ Open-World Tech Stack
* **Rendering:** WebGL über **Three.js** (vollständige GPU-Hardwarebeschleunigung).
* **Framework:** **Streamlit** (Python) fungiert als Webserver und Wrapper.
* **Hosting-Tipp:** Pushe diese Datei einfach in dein GitHub-Repository und schalte sie kostenlos über die *Streamlit Community Cloud* live.
""")

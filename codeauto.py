import streamlit as st
import streamlit.components.v1 as components

# Seiten-Konfiguration für das perfekte Dashboard-Gefühl
st.set_page_config(
    page_title="3D Open World City Driver",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 3D Open World Simulator")
st.write("Ein interaktives 3D-Fahrspiel direkt in Streamlit integriert. Nutze die Hardware-Power deines Browsers!")

# Der komplette HTML/JavaScript-Code für das 3D-Spiel
game_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; overflow: hidden; background-color: #0f172a; font-family: sans-serif; }
        #canvas-container { width: 100vw; height: 75vh; }
        #speedometer {
            position: absolute;
            bottom: 20px;
            left: 20px;
            color: #38bdf8;
            background: rgba(15, 23, 42, 0.8);
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 20px;
            font-weight: bold;
            border: 1px solid #38bdf8;
            pointer-events: none;
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>

    <div id="speedometer">Geschwindigkeit: <span id="speed-val">0</span> km/h</div>
    <div id="canvas-container"></div>

    <script>
        // --- 1. SCHNITTSTELLE & SETUP ---
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0f172a);
        scene.fog = new THREE.FogExp2(0x0f172a, 0.015);

        const camera = new THREE.PerspectiveCamera(70, container.clientWidth / container.clientHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        // --- 2. LICHT ---
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(50, 100, 50);
        dirLight.castShadow = true;
        scene.add(dirLight);

        // --- 3. WELT (Straße & Wolkenkratzer) ---
        const worldSize = 500;
        const groundGeo = new THREE.PlaneGeometry(worldSize, worldSize);
        const groundMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.8 });
        const ground = new THREE.Mesh(groundGeo, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        scene.add(ground);

        // Prozedurale Stadt generieren
        const buildingGroup = new THREE.Group();
        const boxGeo = new THREE.BoxGeometry(1, 1, 1);
        
        for (let x = -worldSize/2; x < worldSize/2; x += 25) {
            for (let z = -worldSize/2; z < worldSize/2; z += 25) {
                if (Math.abs(x) < 20 && Math.abs(z) < 20) continue; // Startplatz frei lassen
                
                if (Math.random() > 0.4) {
                    const h = 15 + Math.random() * 50;
                    const w = 10 + Math.random() * 8;
                    const d = 10 + Math.random() * 8;
                    
                    const buildMat = new THREE.MeshStandardMaterial({ 
                        color: new THREE.Color().setHSL(Math.random() * 0.1 + 0.55, 0.7, 0.25),
                        roughness: 0.3
                    });
                    
                    const building = new THREE.Mesh(boxGeo, buildMat);
                    building.scale.set(w, h, d);
                    building.position.set(x, h / 2, z);
                    building.castShadow = true;
                    building.receiveShadow = true;
                    buildingGroup.add(building);
                }
            }
        }
        scene.add(buildingGroup);

        // --- 4. DAS AUTO ---
        const car = new THREE.Group();
        const bodyMat = new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 0.2, metalness: 0.5 });
        const bodyGeo = new THREE.BoxGeometry(2, 0.6, 4);
        const carBody = new THREE.Mesh(bodyGeo, bodyMat);
        carBody.position.y = 0.5;
        carBody.castShadow = true;
        car.add(carBody);

        const cabGeo = new THREE.BoxGeometry(1.6, 0.5, 2);
        const cabMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.1 });
        const carCab = new THREE.Mesh(cabGeo, cabMat);
        carCab.position.set(0, 1, -0.2);
        car.add(carCab);

        const wheelGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.4, 16);
        const wheelMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.9 });
        wheelGeo.rotateZ(Math.PI / 2);

        const wheelPositions = [[-1, 0.4, 1.2], [1, 0.4, 1.2], [-1, 0.4, -1.2], [1, 0.4, -1.2]];
        wheelPositions.forEach(pos => {
            const wheel = new THREE.Mesh(wheelGeo, wheelMat);
            wheel.position.set(pos[0], pos[1], pos[2]);
            wheel.castShadow = true;
            car.add(wheel);
        });
        scene.add(car);

        // --- 5. STEUERUNG & PHYSIK ---
        let speed = 0;
        let maxSpeed = 1.2;
        let accel = 0.02;
        let friction = 0.01;
        let turnSpeed = 0.03;
        let angle = 0;

        const keys = { w: false, a: false, s: false, d: false, ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false };
        window.addEventListener('keydown', (e) => { if (e.key in keys) keys[e.key] = true; });
        window.addEventListener('keyup', (e) => { if (e.key in keys) keys[e.key] = false; });

        // --- 6. ANIMATION LOOP ---
        function animate() {
            requestAnimationFrame(animate);

            // Beschleunigung / Bremse
            if (keys.w || keys.ArrowUp) {
                if (speed < maxSpeed) speed += accel;
            } else if (keys.s || keys.ArrowDown) {
                if (speed > -maxSpeed/2) speed -= accel;
            } else {
                if (speed > 0) speed -= friction;
                else if (speed < 0) speed += friction;
                if (Math.abs(speed) < friction) speed = 0;
            }

            // Lenkung
            if (Math.abs(speed) > 0.05) {
                const dir = speed > 0 ? 1 : -1;
                if (keys.a || keys.ArrowLeft) angle += turnSpeed * dir;
                if (keys.d || keys.ArrowRight) angle -= turnSpeed * dir;
            }

            car.rotation.y = angle;
            car.position.x += Math.sin(angle) * speed;
            car.position.z += Math.cos(angle) * speed;

            // UI Tacho updaten
            document.getElementById('speed-val').innerText = Math.round(Math.abs(speed) * 100);

            // Kamera-Verfolgung (Smooth)
            const targetCamX = car.position.x - Math.sin(angle) * 12;
            const targetCamZ = car.position.z - Math.cos(angle) * 12;
            const targetCamY = car.position.y + 4.5;

            camera.position.x += (targetCamX - camera.position.x) * 0.1;
            camera.position.y += (targetCamY - camera.position.y) * 0.1;
            camera.position.z += (targetCamZ - camera.position.z) * 0.1;
            camera.lookAt(car.position.x, car.position.y + 1, car.position.z);

            renderer.render(scene, camera);
        }

        // Resize Anpassung innerhalb der Streamlit-Komponente
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

# Rendert die HTML-Komponente direkt in der Streamlit Page
components.html(game_html, height=600, scrolling=False)

st.markdown("""
### 🎮 Spielanleitung
* **W / Pfeiltaste oben:** Beschleunigen
* **S / Pfeiltaste unten:** Bremsen / Rückwärts fahren
* **A/D / Pfeiltasten links/rechts:** Lenken
---
*Entwickelt mit Python, Streamlit und Three.js.*
""")

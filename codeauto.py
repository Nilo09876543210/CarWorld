import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="3D Open World City Driver",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .reportview-container .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    h1 { color: #38bdf8 !important; font-family: sans-serif; font-weight: 800; margin-bottom: 5px; }
    .stMarkdown p { color: #94a3b8; }
    </style>
""", unsafe_allow_html=True)

st.title("🚗 3D Open World City Driver")
st.write("KLICKE EINMAL IN DAS SPIELFELD, um die Steuerung zu aktivieren! Nutze dann WASD oder die Pfeiltasten.")

# Optimierter HTML-Code mit Auto-Fokus
game_html = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; overflow: hidden; background-color: #0b0f19; font-family: sans-serif; }
        #canvas-container { width: 100vw; height: 70vh; position: relative; border-radius: 12px; overflow: hidden; cursor: pointer; }
        #ui-layer {
            position: absolute; bottom: 20px; left: 20px; color: #38bdf8;
            background: rgba(15, 23, 42, 0.85); padding: 15px 25px; border-radius: 10px;
            font-size: 24px; font-weight: bold; border: 2px solid #1e293b; pointer-events: none;
        }
        #ui-layer span { color: #f43f5e; }
        #controls-hint {
            position: absolute; top: 20px; right: 20px; color: #94a3b8;
            background: rgba(15, 23, 42, 0.85); padding: 10px 15px; border-radius: 8px;
            font-size: 13px; border: 1px solid #1e293b; pointer-events: none;
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>

    <div id="canvas-container" onclick="window.focus();">
        <div id="ui-layer"><span id="speed-val">0</span> KM/H</div>
        <div id="controls-hint">👉 <b>Hier klicken zum Aktivieren</b><br>Steuerung: WASD / Pfeiltasten</div>
    </div>

    <script>
        // --- 1. SETUP ---
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0b0f19);
        scene.fog = new THREE.FogExp2(0x0b0f19, 0.015);

        const camera = new THREE.PerspectiveCamera(65, container.clientWidth / container.clientHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        // --- 2. LIGHTS ---
        scene.add(new THREE.AmbientLight(0xffffff, 0.3));
        const light = new THREE.DirectionalLight(0x38bdf8, 0.8);
        light.position.set(50, 150, 50);
        scene.add(light);

        // --- 3. MAP (Stadt) ---
        const mapSize = 500;
        const ground = new THREE.Mesh(
            new THREE.PlaneGeometry(mapSize, mapSize),
            new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.8 })
        );
        ground.rotation.x = -Math.PI / 2;
        scene.add(ground);

        // Grid für Sichtbarkeit bei Nacht
        const grid = new THREE.GridHelper(mapSize, 40, 0x38bdf8, 0x1e293b);
        grid.position.y = 0.01;
        scene.add(grid);

        // Gebäude
        const buildingGroup = new THREE.Group();
        for (let x = -mapSize/2; x < mapSize/2; x += 30) {
            for (let z = -mapSize/2; z < mapSize/2; z += 30) {
                if (Math.abs(x) < 20 && Math.abs(z) < 20) continue;
                if (Math.random() > 0.4) {
                    const h = 15 + Math.random() * 50;
                    const b = new THREE.Mesh(
                        new THREE.BoxGeometry(12, h, 12),
                        new THREE.MeshStandardMaterial({ color: new THREE.Color().setHSL(0.6, 0.6, 0.2), roughness: 0.5 })
                    );
                    b.position.set(x, h/2, z);
                    buildingGroup.add(b);
                }
            }
        }
        scene.add(buildingGroup);

        // --- 4. AUTO ---
        const car = new THREE.Group();
        const carBody = new THREE.Mesh(new THREE.BoxGeometry(2, 0.6, 4), new THREE.MeshStandardMaterial({ color: 0x3b82f6 }));
        carBody.position.y = 0.5;
        car.add(carBody);
        
        // Scheinwerfer
        const sGeo = new THREE.BoxGeometry(0.2, 0.1, 0.1);
        const sMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
        const s1 = new THREE.Mesh(sGeo, sMat); s1.position.set(-0.7, 0.5, 2); car.add(s1);
        const s2 = new THREE.Mesh(sGeo, sMat); s2.position.set(0.7, 0.5, 2); car.add(s2);
        
        scene.add(car);

        // --- 5. INTERNE STEUERUNG LOGIK ---
        let speed = 0, maxSpeed = 1.5, accel = 0.03, friction = 0.015, angle = 0, turnSpeed = 0.04;
        const keys = { w: false, a: false, s: false, d: false, ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false };
        
        window.addEventListener('keydown', (e) => { 
            if (e.key in keys) {
                keys[e.key] = true;
                e.preventDefault(); // Verhindert Scrollen des Browsers
            }
        });
        window.addEventListener('keyup', (e) => { if (e.key in keys) keys[e.key] = false; });

        // Auto-Fokus Versuch bei Mausbewegung über das Spiel
        container.addEventListener('mouseenter', () => { window.focus(); });

        // --- 6. GAME LOOP ---
        function animate() {
            requestAnimationFrame(animate);

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
            car.position.x += Math.sin(angle) * speed;
            car.position.z += Math.cos(angle) * speed;

            document.getElementById('speed-val').innerText = Math.round(Math.abs(speed) * 100);

            // Kamera-Verfolgung
            camera.position.x += (car.position.x - Math.sin(angle) * 12 - camera.position.x) * 0.1;
            camera.position.y += (car.position.y + 4.5 - camera.position.y) * 0.1;
            camera.position.z += (car.position.z - Math.cos(angle) * 12 - camera.position.z) * 0.1;
            camera.lookAt(car.position.x, car.position.y + 1, car.position.z);

            renderer.render(scene, camera);
        }

        animate();
    </script>
</body>
</html>
"""

components.html(game_html, height=620, scrolling=False)

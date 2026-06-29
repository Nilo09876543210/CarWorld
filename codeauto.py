import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="3D Living City Simulator Pro",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🏙️ 3D Living Open World Simulator")
st.write("Klicke in das Spielfeld. Steuerung mit WASD / Pfeiltasten. Drücke **R**, um die Position zurückzusetzen!")

# Vollwertiges 3D-Spiel mit erweitertem Umfang und komplexen Systemen
game_html = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; overflow: hidden; background-color: #bae6fd; font-family: sans-serif; }
        #canvas-container { width: 100vw; height: 78vh; position: relative; border-radius: 12px; overflow: hidden; box-shadow: 0 15px 35px rgba(0,0,0,0.4); }
        #ui-layer {
            position: absolute; bottom: 25px; left: 25px; color: #0f172a;
            background: rgba(255, 255, 255, 0.95); padding: 15px 25px; border-radius: 12px;
            font-size: 24px; font-weight: bold; border: 2px solid #cbd5e1; pointer-events: none;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }
        #ui-layer span { color: #dc2626; }
        #controls-hint {
            position: absolute; top: 25px; right: 25px; color: #1e293b;
            background: rgba(255, 255, 255, 0.95); padding: 12px 18px; border-radius: 10px;
            font-size: 13px; border: 1px solid #cbd5e1; pointer-events: none;
        }
        #reset-btn {
            position: absolute; top: 25px; left: 25px; color: #ffffff;
            background: #dc2626; padding: 10px 20px; border-radius: 8px;
            font-size: 14px; font-weight: bold; border: none; cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2); z-index: 10;
        }
        #reset-btn:hover { background: #b91c1c; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>

    <div id="canvas-container" onclick="window.focus();">
        <button id="reset-btn" onclick="resetPlayer(); event.stopPropagation();">🔄 Auto zurücksetzen (R)</button>
        <div id="ui-layer"><span id="speed-val">0</span> KM/H</div>
        <div id="controls-hint">🕹️ <b>Klicken zum Aktivieren</b><br>Fahren: WASD / Pfeiltasten<br>Reset: R-Taste</div>
    </div>

    <script>
        // --- 1. ENGINE SETUP ---
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xbae6fd); 
        scene.fog = new THREE.FogExp2(0xbae6fd, 0.004);

        const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 1500);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(renderer.domElement);

        // --- 2. LIGHTING ---
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.65);
        scene.add(ambientLight);

        const sunLight = new THREE.DirectionalLight(0xfffbeb, 1.3);
        sunLight.position.set(200, 400, 150);
        sunLight.castShadow = true;
        sunLight.shadow.mapSize.width = 4096;
        sunLight.shadow.mapSize.height = 4096;
        scene.add(sunLight);

        // --- 3. GLOBAL ARRAYS & CONFIG ---
        const mapSize = 1200;
        const blockSize = 80;   
        const roadWidth = 22;   
        const sidewalkW = 3.5;  

        const collisionObstacles = []; 
        const npcTraffic = [];
        const npcPedestrians = [];

        const boxGeo = new THREE.BoxGeometry(1, 1, 1);
        const planeGeo = new THREE.PlaneGeometry(1, 1);
        const cylGeo = new THREE.CylinderGeometry(1, 1, 1, 16);

        // --- 4. GROUND ---
        const groundMat = new THREE.MeshStandardMaterial({ color: 0x16a34a, roughness: 0.9 });
        const ground = new THREE.Mesh(new THREE.PlaneGeometry(mapSize, mapSize), groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        scene.add(ground);

        // --- 5. DETAILED CITY GENERATOR ---
        for (let x = -mapSize/2; x < mapSize/2; x += blockSize) {
            for (let z = -mapSize/2; z < mapSize/2; z += blockSize) {
                createRealisticRoad(x, z, blockSize);
                if (Math.abs(x) < blockSize && Math.abs(z) < blockSize) {
                    createTree(x + 15, z + 15);
                    createTree(x - 15, z - 15);
                    continue;
                }
                createInfrastructure(x, z, blockSize);
                if (Math.random() > 0.2) {
                    generateDetailedBuilding(x, z);
                }
            }
        }

        function createRealisticRoad(x, z, size) {
            const rMat = new THREE.MeshStandardMaterial({ color: 0x27272a, roughness: 0.85 });
            const road = new THREE.Mesh(planeGeo, rMat);
            road.scale.set(size, size, 1);
            road.rotation.x = -Math.PI / 2;
            road.position.set(x + size/2, 0.02, z + size/2);
            road.receiveShadow = true;
            scene.add(road);

            const lineMat = new THREE.MeshBasicMaterial({ color: 0xeab308 });
            const line1 = new THREE.Mesh(planeGeo, lineMat);
            line1.scale.set(0.15, size, 1); line1.rotation.x = -Math.PI / 2;
            line1.position.set(x + size/2 - 0.2, 0.03, z + size/2);
            scene.add(line1);

            const line2 = new THREE.Mesh(planeGeo, lineMat);
            line2.scale.set(0.15, size, 1); line2.rotation.x = -Math.PI / 2;
            line2.position.set(x + size/2 + 0.2, 0.03, z + size/2);
            scene.add(line2);

            const zebraMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
            for (let i = -roadWidth/2; i < roadWidth/2; i += 2) {
                const stripe = new THREE.Mesh(planeGeo, zebraMat);
                stripe.scale.set(1.2, 4, 1); stripe.rotation.x = -Math.PI / 2;
                stripe.position.set(x + size/2 + i, 0.035, z + 3);
                scene.add(stripe);
            }
        }

        function createInfrastructure(x, z, size) {
            const innerW = size - roadWidth;
            const swMat = new THREE.MeshStandardMaterial({ color: 0xa1a1aa, roughness: 0.7 });
            const sw = new THREE.Mesh(boxGeo, swMat);
            sw.scale.set(innerW, 0.3, innerW);
            sw.position.set(x + roadWidth/2 + innerW/2, 0.15, z + roadWidth/2 + innerW/2);
            sw.receiveShadow = true;
            scene.add(sw);

            if (Math.random() > 0.4) createTree(x + roadWidth + 3, z + roadWidth + 3);
            if (Math.random() > 0.4) createTree(x + size - 5, z + size - 5);
        }

        function createTree(px, pz) {
            const tree = new THREE.Group();
            const trunkMat = new THREE.MeshStandardMaterial({ color: 0x713f12, roughness: 0.9 });
            const trunk = new THREE.Mesh(cylGeo, trunkMat);
            trunk.scale.set(0.4, 4, 0.4); trunk.position.y = 2; trunk.castShadow = true;
            tree.add(trunk);

            const leavesMat = new THREE.MeshStandardMaterial({ color: 0x166534, roughness: 0.6 });
            const leaves = new THREE.Mesh(boxGeo, leavesMat);
            leaves.scale.set(2.5, 3.5, 2.5); leaves.position.y = 4.5; leaves.castShadow = true;
            tree.add(leaves);

            tree.position.set(px, 0.2, pz);
            scene.add(tree);

            collisionObstacles.push({ mesh: trunk, box: new THREE.Box3().setFromObject(trunk), type: 'tree' });
        }

        function generateDetailedBuilding(x, z) {
            const hHeight = 30 + Math.random() * 80;
            const hWidth = blockSize - roadWidth - (sidewalkW * 2);
            const hDepth = blockSize - roadWidth - (sidewalkW * 2);

            const modernColors = [0x4b5563, 0xd4d4d8, 0xf4f4f5, 0x1e293b, 0x3f3f46];
            const bColor = modernColors[Math.floor(Math.random() * modernColors.length)];

            const buildingGroup = new THREE.Group();
            const bMat = new THREE.MeshStandardMaterial({ color: bColor, roughness: 0.4, metalness: 0.1 });
            const body = new THREE.Mesh(boxGeo, bMat);
            body.scale.set(hWidth, hHeight, hDepth); body.position.y = hHeight / 2;
            body.castShadow = true; body.receiveShadow = true;
            buildingGroup.add(body);

            const roofMat = new THREE.MeshStandardMaterial({ color: 0x18181b });
            const roofFrame = new THREE.Mesh(boxGeo, roofMat);
            roofFrame.scale.set(hWidth, 1.2, hDepth); roofFrame.position.y = hHeight + 0.6;
            buildingGroup.add(roofFrame);

            const doorMat = new THREE.MeshStandardMaterial({ color: 0x7f1d1d });
            const door = new THREE.Mesh(boxGeo, doorMat);
            door.scale.set(3, 4, 0.2); door.position.set(0, 2, hDepth/2 + 0.05);
            buildingGroup.add(door);

            const winGeo = new THREE.PlaneGeometry(1.2, 1.8);
            const winMat = new THREE.MeshBasicMaterial({ color: 0xfef08a });

            for (let y = 6; y < hHeight - 6; y += 6) {
                for (let fx = -hWidth/2 + 4; fx < hWidth/2 - 4; fx += 5) {
                    const w1 = new THREE.Mesh(winGeo, winMat); w1.position.set(fx, y, hDepth/2 + 0.06); buildingGroup.add(w1);
                    const w2 = new THREE.Mesh(winGeo, winMat); w2.position.set(fx, y, -hDepth/2 - 0.06); w2.rotation.y = Math.PI; buildingGroup.add(w2);
                }
            }

            const posX = x + roadWidth/2 + sidewalkW + hWidth/2;
            const posZ = z + roadWidth/2 + sidewalkW + hDepth/2;
            buildingGroup.position.set(posX, 0.3, posZ);
            scene.add(buildingGroup);

            const bBox = new THREE.Box3().setFromObject(body);
            collisionObstacles.push({ mesh: body, box: bBox, type: 'building' });
        }

        // --- 6. KI-VERKEHR ---
        const carColors = [0x2563eb, 0x16a34a, 0xd97706, 0x059669, 0x7c3aed];
        function spawnAICar(x, z, axis) {
            const ai = new THREE.Group();
            const body = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: carColors[Math.floor(Math.random() * carColors.length)], roughness: 0.3 }));
            body.scale.set(2, 0.7, 4); body.position.y = 0.5; body.castShadow = true;
            ai.add(body);

            const cab = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0x111827 }));
            cab.scale.set(1.6, 0.6, 2); cab.position.set(0, 1.15, -0.1);
            ai.add(cab);

            ai.position.set(x, 0.1, z);
            if (axis === 'Z') ai.rotation.y = Math.PI / 2;
            scene.add(ai);

            npcTraffic.push({ group: ai, mesh: body, box: new THREE.Box3(), axis: axis, speed: 0.4 + Math.random() * 0.4, dir: Math.random() > 0.5 ? 1 : -1 });
        }

        for (let i = -400; i < 400; i += 120) {
            spawnAICar(i, 12, 'X'); spawnAICar(-12, i, 'Z'); spawnAICar(i + 40, -12, 'X');
        }

        // --- 7. NPC MENSCHEN ---
        function spawnNPCUser(x, z) {
            const npc = new THREE.Group();
            const body = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0x2563eb }));
            body.scale.set(0.4, 1.2, 0.4); body.position.y = 0.6; body.castShadow = true;
            npc.add(body);

            const head = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0xffdbac }));
            head.scale.set(0.3, 0.3, 0.3); head.position.y = 1.35; head.castShadow = true;
            npc.add(head);

            npc.position.set(x, 0.3, z);
            scene.add(npc);

            npcPedestrians.push({
                group: npc, box: new THREE.Box3().setFromObject(body), mesh: body,
                targetX: x + (Math.random() - 0.5) * 40, targetZ: z + (Math.random() - 0.5) * 40,
                baseX: x, baseZ: z, speed: 0.04 + Math.random() * 0.04
            });
        }

        for (let k = -300; k < 300; k += 90) {
            spawnNPCUser(k + 25, 25); spawnNPCUser(25, k + 25);
        }

        // --- 8. SPIELER-FAHRZEUG ---
        const playerCar = new THREE.Group();
        const pBody = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0xe11d48, metalness: 0.8, roughness: 0.1 }));
        pBody.scale.set(2.2, 0.6, 4.5); pBody.position.y = 0.5; pBody.castShadow = true;
        playerCar.add(pBody);

        const pCab = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0x090d16, roughness: 0.1 }));
        pCab.scale.set(1.7, 0.5, 2.2); pCab.position.set(0, 1.0, -0.2);
        playerCar.add(pCab);

        const wing = new THREE.Mesh(boxGeo, new THREE.MeshStandardMaterial({ color: 0x111827 }));
        wing.scale.set(2.2, 0.1, 0.5); wing.position.set(0, 0.9, -2.1); playerCar.add(wing);

        const wMat = new THREE.MeshStandardMaterial({ color: 0x18181b, roughness: 0.85 });
        const wheels = [];
        const wPositions = [[-1.15, 0.5, 1.4], [1.15, 0.5, 1.4], [-1.15, 0.5, -1.4], [1.15, 0.5, -1.4]];
        
        wPositions.forEach(pos => {
            const wheel = new THREE.Mesh(cylGeo, wMat);
            wheel.scale.set(0.5, 0.4, 0.5); wheel.rotateZ(Math.PI / 2);
            wheel.position.set(pos[0], pos[1], pos[2]); wheel.castShadow = true;
            playerCar.add(wheel); wheels.push(wheel);
        });

        playerCar.position.set(6, 0.1, 6);
        scene.add(playerCar);

        const playerBox = new THREE.Box3();

        // --- 9. PHYSIK & RESET-LOGIK ---
        let speed = 0, maxSpeed = 2.2, accel = 0.05, friction = 0.022, angle = 0, turnSpeed = 0.048;
        const keys = { w: false, a: false, s: false, d: false, ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false };

        window.addEventListener('keydown', (e) => { 
            if (e.key in keys) { keys[e.key] = true; e.preventDefault(); }
            if (e.key.toLowerCase() === 'r') resetPlayer();
        });
        window.addEventListener('keyup', (e) => { if (e.key in keys) keys[e.key] = false; });

        function resetPlayer() {
            playerCar.position.set(6, 0.1, 6);
            angle = 0;
            speed = 0;
            playerCar.rotation.y = 0;
        }

        // --- 10. REAL-TIME ENGINE LOOP ---
        function animate() {
            requestAnimationFrame(animate);

            if (keys.w || keys.ArrowUp) { if (speed < maxSpeed) speed += accel; }
            else if (keys.s || keys.ArrowDown) {
                if (speed > 0) speed -= 0.09;
                else if (speed > -maxSpeed/1.5) speed -= accel;
            } else {
                if (speed > 0) speed -= friction;
                else if (speed < 0) speed += friction;
                if (Math.abs(speed) < friction) speed = 0;
            }

            if (Math.abs(speed) > 0.04) {
                const modifier = speed > 0 ? 1 : -1;
                if (keys.a || keys.ArrowLeft) { angle += turnSpeed * modifier; wheels[0].rotation.y = 0.35; wheels[1].rotation.y = 0.35; }
                else if (keys.d || keys.ArrowRight) { angle -= turnSpeed * modifier; wheels[0].rotation.y = -0.35; wheels[1].rotation.y = -0.35; }
                else { wheels[0].rotation.y = 0; wheels[1].rotation.y = 0; }
            }

            wheels.forEach(w => w.rotation.x += speed * 0.4);
            playerCar.rotation.y = angle;

            const oldX = playerCar.position.x;
            const oldZ = playerCar.position.z;

            // X-Achse
            playerCar.position.x += Math.sin(angle) * speed;
            playerBox.setFromObject(pBody);
            let collisionHit = false;
            for (let i = 0; i < collisionObstacles.length; i++) {
                if (playerBox.intersectsBox(collisionObstacles[i].box)) { collisionHit = true; break; }
            }
            if (collisionHit) { playerCar.position.x = oldX; speed *= -0.3; }

            // Z-Achse
            playerCar.position.z += Math.cos(angle) * speed;
            playerBox.setFromObject(pBody);
            collisionHit = false;
            for (let i = 0; i < collisionObstacles.length; i++) {
                if (playerBox.intersectsBox(collisionObstacles[i].box)) { collisionHit = true; break; }
            }
            if (collisionHit) { playerCar.position.z = oldZ; speed *= -0.3; }

            // KI Autos updaten
            npcTraffic.forEach(ai => {
                if (ai.axis === 'X') {
                    ai.group.position.x += ai.speed * ai.dir;
                    if (Math.abs(ai.group.position.x) > mapSize/2) ai.dir *= -1;
                } else {
                    ai.group.position.z += ai.speed * ai.dir;
                    if (Math.abs(ai.group.position.z) > mapSize/2) ai.dir *= -1;
                }
                ai.box.setFromObject(ai.mesh);

                if (playerBox.intersectsBox(ai.box)) {
                    playerCar.position.x = oldX; playerCar.position.z = oldZ;
                    speed = -speed * 0.4; ai.dir *= -1;
                }
            });

            // NPCs bewegen
            npcPedestrians.forEach(npc => {
                const dx = npc.targetX - npc.group.position.x;
                const dz = npc.targetZ - npc.group.position.z;
                const dist = Math.sqrt(dx*dx + dz*dz);
                if (dist < 1) {
                    npc.targetX = npc.baseX + (Math.random() - 0.5) * 30;
                    npc.targetZ = npc.baseZ + (Math.random() - 0.5) * 30;
                } else {
                    npc.group.position.x += (dx / dist) * npc.speed;
                    npc.group.position.z += (dz / dist) * npc.speed;
                    npc.group.rotation.y = Math.atan2(dx, dz);
                }
                npc.box.setFromObject(npc.mesh);
                if (playerBox.intersectsBox(npc.box)) { speed *= 0.5; }
            });

            document.getElementById('speed-val').innerText = Math.round(Math.abs(speed) * 120);

            // Kamera-Verfolgung
            const targetCamX = playerCar.position.x - Math.sin(angle) * 16;
            const targetCamZ = playerCar.position.z - Math.cos(angle) * 16;
            const targetCamY = playerCar.position.y + 6.0;

            camera.position.x += (targetCamX - camera.position.x) * 0.08;
            camera.position.y += (targetCamY - camera.position.y) * 0.08;
            camera.position.z += (targetCamZ - camera.position.z) * 0.08;
            camera.lookAt(playerCar.position.x + Math.sin(angle)*3, playerCar.position.y + 0.5, playerCar.position.z + Math.cos(angle)*3);

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

components.html(game_html, height=660, scrolling=False)

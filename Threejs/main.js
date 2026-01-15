let scene, camera, renderer, labelRenderer, controls;
let terrainMesh;
// 全局状态
let routeMeshes = []; 
let arrowMeshes = []; 
let timelineData = [];
// 交互相关
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

const CONFIG = {
    worldWidth: 250,
    worldHeight: 100,
    heightScale: 25,
    waterLevel: 2.0,
    colors: {
        sky: 0xaaccff, water: 0x3d85c6, riverLine: 0x2c6ba0,
        city: 0x44ff44, capital: 0xff0000, battle: 0xffaa00,
        attack: 0xd63031, retreat: 0x2d3436
    }
};

init();

function init() {
    // 1. 场景
    scene = new THREE.Scene();
    scene.background = new THREE.Color(CONFIG.colors.sky);
    scene.fog = new THREE.Fog(CONFIG.colors.sky, 50, 400);

    camera = new THREE.PerspectiveCamera(45, window.innerWidth/window.innerHeight, 1, 1000);
    camera.position.set(0, 100, 120);

    // 2. 渲染器
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    document.body.appendChild(renderer.domElement);

    // 3. 标签层
    labelRenderer = new THREE.CSS2DRenderer();
    labelRenderer.setSize(window.innerWidth, window.innerHeight);
    labelRenderer.domElement.style.position = 'absolute';
    labelRenderer.domElement.style.top = '0px';
    labelRenderer.domElement.style.pointerEvents = 'none'; // 关键：让鼠标能穿透标签点击模型
    document.body.appendChild(labelRenderer.domElement);

    // 4. 控制器
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    
    // 5. 灯光
    const sun = new THREE.DirectionalLight(0xffffee, 1.2);
    sun.position.set(-50, 100, 50);
    sun.castShadow = true;
    sun.shadow.mapSize.width = 2048; sun.shadow.mapSize.height = 2048;
    sun.shadow.camera.left = -150; sun.shadow.camera.right = 150;
    sun.shadow.camera.top = 150; sun.shadow.camera.bottom = -150;
    scene.add(sun);
    scene.add(new THREE.AmbientLight(0xffffff, 0.6));

    // 6. 加载
    loadResources();

    // 7. 监听
    window.addEventListener('resize', onResize);
    window.addEventListener('click', onMouseClick); // 新增点击监听

    animate();
}

function loadResources() {
    const texLoader = new THREE.TextureLoader();
    Promise.all([
        new Promise(resolve => texLoader.load('assets/heightmap.png', resolve)),
        new Promise(resolve => texLoader.load('assets/texture.png', resolve, undefined, () => resolve(null))),
        fetch('game_data.json').then(r => r.json())
    ]).then(([heightMap, textureMap, gameData]) => {
        document.getElementById('loading').style.display = 'none';
        buildWorld(heightMap, textureMap, gameData);
    }).catch(e => console.error(e));
}

function buildWorld(heightMap, textureMap, data) {
    // 地形 (修复纹理变暗问题: 有纹理则纯白底色)
    const mat = new THREE.MeshStandardMaterial({
        color: textureMap ? 0xffffff : 0x5da668,
        map: textureMap || null,
        displacementMap: heightMap,
        displacementScale: CONFIG.heightScale,
        roughness: 0.8
    });
    const geo = new THREE.PlaneGeometry(CONFIG.worldWidth, CONFIG.worldHeight, 256, 256);
    terrainMesh = new THREE.Mesh(geo, mat);
    terrainMesh.rotation.x = -Math.PI / 2;
    terrainMesh.receiveShadow = true;
    terrainMesh.castShadow = true;
    scene.add(terrainMesh);

    // 水面
    const water = new THREE.Mesh(
        new THREE.PlaneGeometry(CONFIG.worldWidth, CONFIG.worldHeight),
        new THREE.MeshStandardMaterial({ color: CONFIG.colors.water, transparent: true, opacity: 0.8 })
    );
    water.rotation.x = -Math.PI / 2;
    water.position.y = CONFIG.waterLevel;
    scene.add(water);

    // 绘制矢量
    setTimeout(() => drawVectors(data), 50);
}

function drawVectors(data) {
    if (data.timeline) {
        timelineData = data.timeline;
        setupTimeline();
    }

    if (data.rivers) data.rivers.forEach(pts => drawLine(pts, CONFIG.colors.riverLine));
    if (data.cities) data.cities.forEach(city => placeCity(city));

    if (data.routes) {
        data.routes.forEach(route => {
            const isAttack = route.type === 'attack';
            const mesh = createRouteTube(route.path, isAttack ? CONFIG.colors.attack : CONFIG.colors.retreat, isAttack ? 0.6 : 0.3);
            if (mesh) {
                mesh.visible = false;
                // === 关键：存入数据供射线检测使用 ===
                mesh.userData = { 
                    dateIdx: route.date_idx,
                    type: isAttack ? '进攻' : '撤退',
                    isRoute: true // 标记这是路线
                };
                routeMeshes.push(mesh);
            }
        });
        updateRouteVisibility(0);
    }
}

// === 交互逻辑 (AI 分析) ===

// 坐标反算 (World -> LatLon)
function unmapCoords(x, z) {
    // 对应 preprocess.py 的边界
    const bounds = { min_lon: 20.0, max_lon: 45.0, min_lat: 50.0, max_lat: 60.0 };
    const nx = (x / CONFIG.worldWidth) + 0.5;
    const lon = nx * (bounds.max_lon - bounds.min_lon) + bounds.min_lon;
    // z 轴是反的
    const ny = - (z / CONFIG.worldHeight) + 0.5;
    const lat = ny * (bounds.max_lat - bounds.min_lat) + bounds.min_lat;
    return { lon, lat };
}

function onMouseClick(event) {
    // 计算鼠标 NDC 坐标
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);

    // 只检测可见的路线
    const visibleRoutes = routeMeshes.filter(m => m.visible);
    const intersects = raycaster.intersectObjects(visibleRoutes);

    if (intersects.length > 0) {
        const hit = intersects[0];
        triggerAnalysis(hit.object, hit.point);
    }
}

async function triggerAnalysis(mesh, point) {
    const panel = document.getElementById('analysis-panel');
    const content = document.getElementById('analysis-content');
    
    panel.classList.add('active');
    content.innerHTML = `<div class="loading-text">📡 正在连接历史数据库...<br>分析地形与战略态势...</div>`;

    const coords = unmapCoords(point.x, point.z);
    const dateStr = timelineData[mesh.userData.dateIdx] || "1812年";
    const heightVal = point.y / CONFIG.heightScale;
    
    // 简单的地形描述
    let terrain = "平原";
    if (heightVal > 0.4) terrain = "丘陵/高地";
    if (heightVal > 0.8) terrain = "山脉阻隔";

    try {
        const res = await fetch('http://localhost:5000/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lat: coords.lat, lon: coords.lon,
                date: dateStr,
                type: mesh.userData.type,
                terrain_hint: `${terrain} (海拔系数 ${heightVal.toFixed(2)})`
            })
        });
        const json = await res.json();
        
        content.innerHTML = `
            <div style="font-size:12px; color:#999; margin-bottom:10px; border-bottom:1px solid #eee; padding-bottom:5px;">
                📍 ${coords.lat.toFixed(2)}°N, ${coords.lon.toFixed(2)}°E <br>
                📅 ${dateStr} | 法军${mesh.userData.type}
            </div>
            <div style="font-family:'Times New Roman', serif; line-height:1.6; color:#2c3e50; text-align:justify;">
                ${json.analysis.replace(/\n/g, '<br>')}
            </div>
        `;
    } catch (e) {
        console.error(e);
        content.innerHTML = `<p style="color:red">分析服务连接失败，请确认 server.py 已运行。</p>`;
    }
}

// === 时间轴 & 动画 ===
function setupTimeline() {
    const slider = document.getElementById('time-slider');
    const display = document.getElementById('date-display');
    slider.max = timelineData.length - 1;
    slider.addEventListener('input', (e) => {
        const idx = parseInt(e.target.value);
        if(timelineData[idx]) {
            display.innerText = timelineData[idx];
            updateRouteVisibility(idx);
        }
    });
}

function updateRouteVisibility(idx) {
    routeMeshes.forEach(m => m.visible = m.userData.dateIdx <= idx);
}

// === 辅助函数 ===
function createRouteTube(points, color, radius) {
    if (points.length < 2) return null;
    const vecs = points.map(p => new THREE.Vector3(p[0], Math.max(p[1]*CONFIG.heightScale, CONFIG.waterLevel)+1.0, p[2]));
    const curve = new THREE.CatmullRomCurve3(vecs);
    const geo = new THREE.TubeGeometry(curve, points.length*2, radius, 8, false);
    const mat = new THREE.MeshStandardMaterial({ color: color, roughness: 0.4 });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.castShadow = true;
    scene.add(mesh);
    return mesh;
}

function drawLine(points, color) {
    const v = [];
    points.forEach(p => v.push(p[0], Math.max(p[1]*CONFIG.heightScale, CONFIG.waterLevel)+0.2, p[2]));
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(v, 3));
    scene.add(new THREE.Line(geo, new THREE.LineBasicMaterial({ color: color, linewidth: 2 })));
}

function placeCity(city) {
    const y = Math.max(city.ny * CONFIG.heightScale, CONFIG.waterLevel);
    const grp = new THREE.Group();
    grp.position.set(city.x, y, city.z);

    let color = CONFIG.colors.city, scale = 1.0;
    if (city.t === 'capital') { color = CONFIG.colors.capital; scale = 1.5; }
    if (city.t === 'battle') { color = CONFIG.colors.battle; scale = 1.3; }

    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(0.2*scale, 0.5*scale, 1.2*scale, 6), new THREE.MeshStandardMaterial({color}));
    mesh.position.y = 0.6*scale; mesh.castShadow = true;
    grp.add(mesh);

    const div = document.createElement('div');
    div.className = city.t === 'battle' ? 'city-label battle-label' : 'city-label';
    div.textContent = city.n;
    const label = new THREE.CSS2DObject(div);
    label.position.set(0, 3*scale, 0);
    grp.add(label);

    if (['capital', 'battle'].includes(city.t)) createArrow(grp, color);
    scene.add(grp);
}

function createArrow(grp, color) {
    const arrow = new THREE.Mesh(new THREE.ConeGeometry(0.6, 1.5, 8), new THREE.MeshLambertMaterial({ color, emissive: 0x222222 }));
    arrow.rotation.x = Math.PI;
    grp.add(arrow);
    arrowMeshes.push({ mesh: arrow, baseY: 5, speed: 2+Math.random(), offset: Math.random()*Math.PI });
}

function onResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    labelRenderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    const t = Date.now() * 0.003;
    arrowMeshes.forEach(i => {
        i.mesh.position.y = i.baseY + Math.sin(t * i.speed + i.offset);
        i.mesh.rotation.y += 0.02;
    });
    renderer.render(scene, camera);
    labelRenderer.render(scene, camera);
}
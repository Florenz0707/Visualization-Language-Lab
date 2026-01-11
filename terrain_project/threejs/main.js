// main.js — 改进版
// 说明：把数据放在 Threejs/ 子目录（或修改 basePath），并确保 Threejs/info.json 存在

(async function(){
  const basePath = 'Threejs/'; // 如果你的数据在别处，改这里
  // 候选 info.json 路径（更鲁棒）
  const candidateInfoPaths = [
    basePath + 'info.json',
    'info.json',
    './info.json',
    '../info.json'
  ];

  // DOM
  const container = document.getElementById('container');
  const loadingEl = document.getElementById('loading');
  const segSelect = document.getElementById('segSelect');
  const zscaleEl = document.getElementById('zscale');
  const zval = document.getElementById('zval');
  const rebuildBtn = document.getElementById('rebuild');
  const resetBtn = document.getElementById('reset');
  const layerListDiv = document.getElementById('layer-list');

  zval.innerText = zscaleEl.value;

  // 尝试多个路径加载 info.json
  async function fetchAnyJSON(paths){
    for(const p of paths){
      try{
        const r = await fetch(p, {cache:'no-cache'});
        if(r.ok){
          const txt = await r.text();
          try { return JSON.parse(txt); }
          catch(e){ console.warn('解析 JSON 失败：', p, e); }
        } else {
          console.warn('info.json 尝试路径返回状态', p, r.status);
        }
      }catch(e){
        console.warn('fetch 失败：', p, e);
      }
    }
    throw new Error('未能在候选路径中找到 info.json: ' + paths.join(', '));
  }

  // 读取 info.json
  let info;
  try {
    info = await fetchAnyJSON(candidateInfoPaths);
  } catch(e){
    loadingEl.innerText = '加载 info.json 失败：' + e.message;
    console.error(e);
    return;
  }

  // 构建 height/texture 路径：优先使用 info 内指定的文件名（支持绝对或相对）
  function buildPathFromInfo(name){
    if(!name) return null;
    if(name.match(/^[a-zA-Z]+:\/\//) || name.startsWith('/')) return name; // 绝对 URL or root
    return basePath + name;
  }
  const heightmapPath = buildPathFromInfo(info.heightmap || info['heightmap.png'] || 'heightmap.png');
  const texturePath = buildPathFromInfo(info.texture || info.texture || 'texture.png');

  // 确保基本字段
  info.width = info.width || 512;
  info.height = info.height || 512;
  info.vmin = (typeof info.vmin !== 'undefined') ? info.vmin : (typeof info.elev_min !== 'undefined' ? info.elev_min : 0);
  info.vmax = (typeof info.vmax !== 'undefined') ? info.vmax : (typeof info.elev_max !== 'undefined' ? info.elev_max : 1);
  info.bounds = info.bounds || [0,0,1,1];

  const [minLon, minLat, maxLon, maxLat] = info.bounds;
  const widthDeg = maxLon - minLon, heightDeg = maxLat - minLat;

  // THREE 初始化
  const renderer = new THREE.WebGLRenderer({antialias:true});
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  renderer.setSize(window.innerWidth, window.innerHeight);
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xececec);

  const camera = new THREE.PerspectiveCamera(45, window.innerWidth/window.innerHeight, 0.01, 10000);
  const diag = Math.max(widthDeg, heightDeg);
  camera.position.set(minLon + widthDeg*0.5, minLat - heightDeg*0.8, diag*0.9);
  camera.up.set(0,0,1);
  camera.lookAt(minLon + widthDeg*0.5, minLat + heightDeg*0.5, 0);

  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.target.set(minLon + widthDeg*0.5, minLat + heightDeg*0.5, 0);
  controls.update();

  scene.add(new THREE.AmbientLight(0x888888));
  const dir = new THREE.DirectionalLight(0xffffff, 1.0); dir.position.set(1,-1,1); scene.add(dir);

  // 加载图片工具
  function loadImage(url){
    return new Promise((res, rej)=>{
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = ()=>res(img);
      img.onerror = e=>rej(new Error('加载图像失败: ' + url + ' - ' + e));
      img.src = url;
    });
  }

  // 加载 heightmap（必须）
  let heightImg, colorImg = null;
  try {
    heightImg = await loadImage(heightmapPath);
  } catch(e){
    loadingEl.innerText = '加载 heightmap 失败：' + (heightmapPath || '(未指定)');
    console.error(e);
    return;
  }
  // 加载 texture（可选）
  try { colorImg = await loadImage(texturePath); } catch(e){ console.warn('texture 加载失败（可忽略）:', texturePath, e); colorImg = null; }

  // 把 heightmap 放到隐藏 canvas 以便采样
  const hmCanvas = document.createElement('canvas');
  hmCanvas.width = heightImg.width; hmCanvas.height = heightImg.height;
  const hmCtx = hmCanvas.getContext('2d');
  hmCtx.drawImage(heightImg, 0, 0);
  const hmData = hmCtx.getImageData(0,0, hmCanvas.width, hmCanvas.height).data;

  function sampleElevation(lon, lat){
    const u = (lon - minLon) / (maxLon - minLon);
    const v = 1.0 - (lat - minLat) / (maxLat - minLat); // image origin upper
    const px = Math.floor(u * (hmCanvas.width - 1));
    const py = Math.floor(v * (hmCanvas.height - 1));
    if(px < 0 || py < 0 || px >= hmCanvas.width || py >= hmCanvas.height) return NaN;
    const idx = (py * hmCanvas.width + px) * 4;
    const val = hmData[idx]; // 假设灰度图 R=G=B
    const elev = info.vmin + (val / 255.0) * (info.vmax - info.vmin);
    return elev;
  }

  // 地形构造（直接把每个顶点 Z 设置为采样值）
  let terrainMesh = null;
  function buildTerrain(seg){
    if(terrainMesh){
      scene.remove(terrainMesh);
      terrainMesh.geometry.dispose();
      terrainMesh.material.dispose();
      terrainMesh = null;
    }
    const maxSegments = 512; // safety cap
    seg = Math.max(8, Math.min(maxSegments, seg));

    const geom = new THREE.PlaneGeometry(widthDeg, heightDeg, seg-1, seg-1);
    geom.translate(minLon + widthDeg/2, minLat + heightDeg/2, 0);

    const pos = geom.attributes.position;
    for(let i=0;i<pos.count;i++){
      const x = pos.getX(i), y = pos.getY(i);
      const elev = sampleElevation(x,y);
      // 把米转换成近似度数再乘以 z scale（与之前逻辑一致）
      const z = Number.isFinite(elev) ? ( (elev / 111132.0) * parseFloat(zscaleEl.value) ) : 0;
      pos.setZ(i, z);
    }
    pos.needsUpdate = true;
    geom.computeVertexNormals();

    const matOpts = { side: THREE.DoubleSide, metalness:0.0, roughness:1.0 };
    if(colorImg){
      const tex = new THREE.Texture(colorImg); tex.needsUpdate = true;
      matOpts.map = tex;
    } else {
      matOpts.color = 0x999999;
    }
    const material = new THREE.MeshStandardMaterial(matOpts);
    terrainMesh = new THREE.Mesh(geom, material);
    scene.add(terrainMesh);
  }

  // GeoJSON 图层配置（基于你提供的文件名）
  const files = {
    cities_1812: basePath + 'cities_1812_campaign.geojson',
    cities_major: basePath + 'cities_major.geojson',
    cities_all: basePath + 'cities.geojson',
    contours: basePath + 'contours.geojson',
    countries_eu: basePath + 'countries_eastern_europe.geojson',
    countries: basePath + 'countries.geojson',
    provinces: basePath + 'provinces.geojson',
    rivers: basePath + 'rivers.geojson'
  };

  const layerSpecs = [
    { id:'countries', name:'国家边界', url: files.countries, color:0x000000, width:2 },
    { id:'countries_eu', name:'东欧国家', url: files.countries_eu, color:0x222222, width:2 },
    { id:'provinces', name:'省/州', url: files.provinces, color:0xff8800, width:1 },
    { id:'rivers', name:'河流', url: files.rivers, color:0x0066ff, width:1 },
    { id:'contours', name:'等高线', url: files.contours, color:0x666666, width:1 },
    { id:'cities_major', name:'主要城市', url: files.cities_major, color:0xaa0000, size:0.04 },
    { id:'cities_1812', name:'历史城市 (1812)', url: files.cities_1812, color:0xff3333, size:0.035 },
    { id:'cities_all', name:'所有城市', url: files.cities_all, color:0xff6666, size:0.03 }
  ];

  const layerGroups = {};

  // UI：为每个图层创建复选框
  for(const spec of layerSpecs){
    const cb = document.createElement('input'); cb.type='checkbox'; cb.id = 'cb_' + spec.id;
    const lbl = document.createElement('label');
    lbl.appendChild(cb);
    lbl.appendChild(document.createTextNode(' ' + spec.name));
    layerListDiv.appendChild(lbl);

    cb.addEventListener('change', async ev => {
      if(ev.target.checked){
        try {
          const res = await fetch(spec.url);
          if(!res.ok){ console.warn('无法加载', spec.url, res.status); ev.target.checked = false; return; }
          const gj = await res.json();
          const group = new THREE.Group();
          for(const feat of gj.features){
            const g = feat.geometry;
            if(!g) continue;
            if(g.type === 'LineString'){
              addLineString(g.coordinates, spec.color, spec.width, group);
            } else if(g.type === 'MultiLineString'){
              for(const seg of g.coordinates) addLineString(seg, spec.color, spec.width, group);
            } else if(g.type === 'Polygon'){
              addLineString(g.coordinates[0], spec.color, spec.width, group);
            } else if(g.type === 'MultiPolygon'){
              for(const poly of g.coordinates) addLineString(poly[0], spec.color, spec.width, group);
            } else if(g.type === 'Point'){
              addPoint(g.coordinates, spec.color, spec.size, group);
            } else if(g.type === 'MultiPoint'){
              for(const p of g.coordinates) addPoint(p, spec.color, spec.size, group);
            }
          }
          layerGroups[spec.id] = group;
          scene.add(group);
        } catch(e){
          console.warn('加载 geojson 错误', spec.url, e);
          ev.target.checked = false;
        }
      } else {
        const grp = layerGroups[spec.id];
        if(grp){ scene.remove(grp); disposeGroup(grp); delete layerGroups[spec.id]; }
      }
    });
  }

  function addLineString(coords, color, width, group){
    const maxPts = 2000;
    const n = coords.length;
    const step = Math.max(1, Math.ceil(n / maxPts));
    const pts = [];
    for(let i=0;i<n;i+=step){
      const c = coords[i];
      const lon = c[0], lat = c[1];
      const elev = sampleElevation(lon, lat);
      if(!Number.isFinite(elev)) continue;
      const z = (elev / 111132.0) * parseFloat(zscaleEl.value) + 1e-6;
      pts.push(new THREE.Vector3(lon, lat, z));
    }
    if(pts.length < 2) return;
    const geom = new THREE.BufferGeometry().setFromPoints(pts);
    const mat = new THREE.LineBasicMaterial({ color: color || 0x000000, linewidth: width || 1 });
    const line = new THREE.Line(geom, mat);
    group.add(line);
  }

  function addPoint(coord, color, size, group){
    const lon = coord[0], lat = coord[1];
    const elev = sampleElevation(lon, lat);
    if(!Number.isFinite(elev)) return;
    const z = (elev / 111132.0) * parseFloat(zscaleEl.value) + 1e-6;
    const r = size || 0.03;
    const sph = new THREE.Mesh(new THREE.SphereGeometry(r, 8, 8), new THREE.MeshBasicMaterial({ color: color || 0xff0000 }));
    sph.position.set(lon, lat, z);
    group.add(sph);
  }

  function disposeGroup(group){
    group.traverse(o => {
      if(o.geometry) o.geometry.dispose();
      if(o.material){
        if(o.material.map) o.material.map.dispose();
        o.material.dispose();
      }
    });
  }

  // UI handlers
  rebuildBtn.addEventListener('click', ()=>{
    loadingEl.style.display = 'block';
    setTimeout(()=>{
      const seg = parseInt(segSelect.value, 10) || 256;
      buildTerrain(seg);
      loadingEl.style.display = 'none';
    }, 50);
  });

  resetBtn.addEventListener('click', ()=>{
    controls.reset();
    camera.position.set(minLon + widthDeg*0.5, minLat - heightDeg*0.8, diag*0.9);
    controls.update();
  });

  zscaleEl.addEventListener('input', ()=>{
    zval.innerText = zscaleEl.value;
    if(terrainMesh){
      const pos = terrainMesh.geometry.attributes.position;
      for(let i=0;i<pos.count;i++){
        const x = pos.getX(i), y = pos.getY(i);
        const elev = sampleElevation(x,y);
        const z = Number.isFinite(elev) ? ( (elev / 111132.0) * parseFloat(zscaleEl.value) ) : 0;
        pos.setZ(i, z);
      }
      pos.needsUpdate = true;
      terrainMesh.geometry.computeVertexNormals();
    }
  });

  // 初始 build
  buildTerrain(parseInt(segSelect.value, 10) || 256);
  loadingEl.style.display = 'none';

  // 渲染循环
  function animate(){
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }
  animate();

  window.addEventListener('resize', ()=>{ renderer.setSize(window.innerWidth, window.innerHeight); camera.aspect = window.innerWidth/window.innerHeight; camera.updateProjectionMatrix(); });
})();

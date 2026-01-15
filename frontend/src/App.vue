<template>
  <div id="app">
    <nav class="nav-bar">
      <router-link to="/" class="nav-link">2D地图</router-link>
      <router-link to="/3d" class="nav-link">3D地图</router-link>
      <router-link to="/napoleon" class="nav-link">拿破仑战役</router-link>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow: hidden;
}

#app {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

.nav-bar {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  display: flex;
  gap: 12px;
  background: rgba(255, 255, 255, 0.95);
  padding: 12px 20px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.nav-link {
  padding: 8px 16px;
  text-decoration: none;
  color: #64748b;
  font-weight: 600;
  font-size: 14px;
  border-radius: 8px;
  transition: all 0.2s;
}

.nav-link:hover {
  background: #f1f5f9;
  color: #1e293b;
}

.nav-link.router-link-active {
  background: #3b82f6;
  color: white;
}
</style>

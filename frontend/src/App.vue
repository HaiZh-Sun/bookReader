<template>
  <div class="app">
    <header class="app-header">
      <div class="logo" @click="$router.push('/')">BookReader</div>
      <nav>
        <router-link to="/">首页</router-link>
        <router-link to="/novels">小说列表</router-link>
        <router-link to="/settings">设置</router-link>
      </nav>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  background: #1a1a2e;
  color: #eee;
  flex-shrink: 0;
}
.logo {
  font-size: 20px;
  font-weight: bold;
  cursor: pointer;
}
nav {
  display: flex;
  gap: 16px;
}
nav a {
  color: #aaa;
  text-decoration: none;
  font-size: 14px;
}
nav a:hover, nav a.router-link-active {
  color: #fff;
}
.app-main {
  flex: 1;
  padding: 24px;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}
</style>

<script setup>
import { computed, reactive } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { isActiveMemberStatus, isRestrictedMemberStatus, memberStatusLabel } from "../utils/memberStatus";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const displayName = computed(() => authStore.currentUser?.displayName || "未登录用户");
const userType = computed(() => authStore.currentUser?.userType || "GUEST");
const memberStatus = computed(() => authStore.currentUser?.status || "");
const copyState = reactive({
  text: "",
  type: ""
});

const pageMetaMap = {
  dashboard: {
    title: "主页面",
    subtitle: "直接在此进行业务操作与智能 Agent 查询。"
  },
  profile: {
    title: "个人资料",
    subtitle: "查看会员基础信息、训练偏好和账号状态。"
  },
  "admin-members": {
    title: "会员管理",
    subtitle: "这里承接管理员的会员查询、会员详情、资料编辑和启停用。"
  },
  bookings: {
    title: "健身室管理",
    subtitle: "管理员可维护健身室信息并查询预约订单。"
  },
  courses: {
    title: "课程报名",
    subtitle: "这里承接课程列表、课程详情、报名课程、我的课程和退选。"
  },
  shop: {
    title: "商品与购物车",
    subtitle: "这里承接商品浏览、加入购物车、购物车维护和创建订单。"
  },
  orders: {
    title: "订单中心",
    subtitle: "这里承接会员订单列表、订单详情和下单后的结果回查。"
  }
};

const pageMeta = computed(() => {
  if (route.name === "courses" && userType.value === "ADMIN") {
    return {
      title: "课程管理",
      subtitle: "管理员可查看课程信息并单独新增课程。"
    };
  }
  if (route.name === "orders" && userType.value === "ADMIN") {
    return {
      title: "订单管理",
      subtitle: "管理员可查看全部订单、会员信息和支付状态。"
    };
  }
  return pageMetaMap[route.name] || pageMetaMap.dashboard;
});
const navItems = computed(() => {
  if (userType.value === "ADMIN") {
    return [
      { label: "主页面", to: "/dashboard", tag: "01" },
      { label: "会员管理", to: "/admin/members", tag: "02" },
      { label: "健身室管理", to: "/gym/bookings", tag: "03" },
      { label: "课程管理", to: "/courses", tag: "04" },
      { label: "商品与购物车", to: "/shop", tag: "05" },
      { label: "订单中心", to: "/orders", tag: "06" }
    ];
  }
  if (isRestrictedMemberStatus(memberStatus.value)) {
    return [
      { label: "主页面", to: "/dashboard", tag: "01" },
      { label: "商品与购物车", to: "/shop", tag: "02" },
      { label: "订单中心", to: "/orders", tag: "03" }
    ];
  }
  return [
    { label: "主页面", to: "/dashboard", tag: "01" },
    { label: "个人资料", to: "/members/profile", tag: "02" },
    { label: "健身室预约", to: "/gym/bookings", tag: "03" },
    { label: "课程报名", to: "/courses", tag: "04" },
    { label: "商品与购物车", to: "/shop", tag: "05" },
    { label: "订单中心", to: "/orders", tag: "06" }
  ];
});

const accessBadge = computed(() => {
  if (userType.value !== "MEMBER") {
    return userType.value;
  }
  return isActiveMemberStatus(memberStatus.value)
    ? "会员已启用"
    : `会员${memberStatusLabel(memberStatus.value)}`;
});

async function handleLogout() {
  await authStore.logout();
  await router.push("/login");
}

function setCopyState(text, type) {
  copyState.text = text;
  copyState.type = type;
}

async function handleCopyToken() {
  const token = authStore.token || "";
  if (!token) {
    setCopyState("当前没有可复制的 token，请先登录。", "error");
    return;
  }

  try {
    await navigator.clipboard.writeText(token);
    setCopyState("token 已复制到剪贴板", "success");
  } catch (error) {
    setCopyState("复制失败，请在浏览器控制台读取 localStorage 中的 gym-auth-token", "error");
  }
}
</script>

<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <!-- User Profile moved to sidebar top -->
      <div class="user-pill sidebar-user">
        <div class="user-avatar">{{ displayName.slice(0, 1) }}</div>
        <div class="user-text">
          <strong>{{ displayName }}</strong>
          <span>{{ accessBadge }}</span>
        </div>
        <button class="button-ghost mini" type="button" @click="handleLogout">退出</button>
      </div>

      <div class="brand-card">
        <small>Gym System</small>
        <h1>Control Deck</h1>
        <p>自助健身室管理系统，覆盖预约、课程、商城、订单与会员管理。</p>
      </div>

      <div class="nav-group">
        <div class="nav-title">Workspace</div>
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          class="nav-link"
          :to="item.to"
        >
          <span>{{ item.label }}</span>
          <span>{{ item.tag }}</span>
        </RouterLink>
      </div>
    </aside>

    <main class="app-main">
      <p v-if="copyState.text" class="notice floating-notice" :class="copyState.type">
        {{ copyState.text }}
      </p>

      <div class="main-content-scroll">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<style scoped>
.sidebar-user {
  margin-bottom: 24px;
  width: 100%;
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--surface-strong);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--line);
}

.button-ghost.mini {
  padding: 6px 12px;
  font-size: 13px;
  border-radius: 12px;
}

.app-main {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  padding: 0;
}

.main-content-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.floating-notice {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 1000;
  box-shadow: var(--shadow-lg);
}

/* Ensure Dashboard full-screen doesn't cause double scroll */
:deep(.full-layout) {
  height: calc(100vh - 48px); /* Account for app-main padding/offset if any */
}
</style>

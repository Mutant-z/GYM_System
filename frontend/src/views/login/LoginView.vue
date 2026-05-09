<script setup>
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../../stores/auth";
import { isActiveMemberStatus } from "../../utils/memberStatus";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const activeTab = ref("member");
const loading = ref(false);
const notice = reactive({
  text: "",
  type: ""
});

const memberForm = reactive({
  username: typeof route.query.username === "string" ? route.query.username : "member001",
  password: "123456"
});

const adminForm = reactive({
  username: "admin001",
  password: "123456"
});

function setNotice(text, type) {
  notice.text = text;
  notice.type = type;
}

function clearNotice() {
  notice.text = "";
  notice.type = "";
}

async function redirectAfterLogin() {
  const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "";
  const target = isActiveMemberStatus(authStore.currentUser?.status) || authStore.currentUser?.userType !== "MEMBER"
    ? redirect || "/dashboard"
    : ["/shop", "/orders"].includes(redirect)
    ? redirect
    : "/shop";
  await router.push(target);
}

async function handleMemberLogin() {
  clearNotice();
  loading.value = true;
  try {
    await authStore.loginAsMember(memberForm);
    setNotice("会员登录成功", "success");
    await redirectAfterLogin();
  } catch (error) {
    setNotice(error.message, "error");
  } finally {
    loading.value = false;
  }
}

async function handleAdminLogin() {
  clearNotice();
  loading.value = true;
  try {
    await authStore.loginAsAdmin(adminForm);
    setNotice("管理员登录成功", "success");
    await redirectAfterLogin();
  } catch (error) {
    setNotice(error.message, "error");
  } finally {
    loading.value = false;
  }
}

</script>

<template>
  <main class="login-shell">
    <section class="login-hero">
      <div class="login-brand-mark">GYM</div>
      <div class="login-hero-copy">
        <p class="eyebrow">Self-Service Gym</p>
        <h1>GYM System</h1>
        <p>
          会员预约、课程报名、商城订单与后台运营集中在一个工作台中完成。
        </p>
      </div>

      <dl class="login-snapshot">
        <div>
          <dt>Member</dt>
          <dd>预约 · 课程 · 商城</dd>
        </div>
        <div>
          <dt>Admin</dt>
          <dd>会员 · 场地 · 订单</dd>
        </div>
        <div>
          <dt>Agent</dt>
          <dd>自然语言业务入口</dd>
        </div>
      </dl>
    </section>

    <section class="login-card">
      <div>
        <p class="eyebrow">Authentication</p>
        <h3 class="page-title">登录系统</h3>
        <p class="page-subtitle">选择身份登录，进入对应的系统工作台。</p>
      </div>

      <div class="login-tabs">
        <button
          class="login-tab"
          :class="{ active: activeTab === 'member' }"
          type="button"
          @click="activeTab = 'member'"
        >
          会员登录
        </button>
        <button
          class="login-tab"
          :class="{ active: activeTab === 'admin' }"
          type="button"
          @click="activeTab = 'admin'"
        >
          管理员登录
        </button>
      </div>

      <div class="login-form-panel">
        <form v-if="activeTab === 'member'" class="form-grid" @submit.prevent="handleMemberLogin">
          <label class="field">
            <span>会员账号</span>
            <input v-model.trim="memberForm.username" placeholder="请输入会员账号" />
          </label>
          <label class="field">
            <span>会员密码</span>
            <input v-model="memberForm.password" type="password" placeholder="请输入会员密码" />
          </label>
          <div class="actions">
            <button class="button" :disabled="loading" type="submit">
              {{ loading ? "登录中..." : "会员登录" }}
            </button>
          </div>
        </form>

        <form v-else class="form-grid" @submit.prevent="handleAdminLogin">
          <label class="field">
            <span>管理员账号</span>
            <input v-model.trim="adminForm.username" placeholder="请输入管理员账号" />
          </label>
          <label class="field">
            <span>管理员密码</span>
            <input v-model="adminForm.password" type="password" placeholder="请输入管理员密码" />
          </label>
          <div class="actions">
            <button class="button" :disabled="loading" type="submit">
              {{ loading ? "登录中..." : "管理员登录" }}
            </button>
          </div>
        </form>
      </div>

      <p class="page-subtitle">
        还没有会员账号？<RouterLink class="text-link" to="/register">创建会员账号</RouterLink>
      </p>

      <div class="login-token-panel">
        <div>
          <p class="muted">当前 token</p>
          <div class="token-box">{{ authStore.token || "尚未登录" }}</div>
        </div>
        <p v-if="notice.text" class="notice" :class="notice.type">{{ notice.text }}</p>
      </div>
    </section>
  </main>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { memberRegister } from "../../api/auth";
import { memberStatusLabel } from "../../utils/memberStatus";

const router = useRouter();
const loading = ref(false);
const notice = reactive({
  text: "",
  type: ""
});

const registerForm = reactive({
  username: "",
  password: "",
  confirmPassword: "",
  nickname: "",
  phone: "",
  email: ""
});

function setNotice(text, type) {
  notice.text = text;
  notice.type = type;
}

function clearNotice() {
  notice.text = "";
  notice.type = "";
}

async function handleMemberRegister() {
  clearNotice();
  if (registerForm.password !== registerForm.confirmPassword) {
    setNotice("两次输入的密码不一致", "error");
    return;
  }

  loading.value = true;
  try {
    const payload = await memberRegister({
      username: registerForm.username,
      password: registerForm.password,
      nickname: registerForm.nickname,
      phone: registerForm.phone,
      email: registerForm.email || null
    });
    setNotice(`注册成功，账号状态：${memberStatusLabel(payload.data.status)}。正在返回登录页。`, "success");
    setTimeout(() => {
      router.push({
        path: "/login",
        query: {
          username: registerForm.username
        }
      });
    }, 700);
  } catch (error) {
    setNotice(error.message, "error");
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <main class="login-shell register-shell">
    <section class="login-hero register-hero">
      <div class="login-brand-mark">JOIN</div>
      <div class="login-hero-copy">
        <p class="eyebrow">Member Access</p>
        <h1>创建会员账号</h1>
        <p>注册后可先浏览商城与订单，管理员启用会员状态后即可使用预约和课程功能。</p>
      </div>

      <dl class="login-snapshot">
        <div>
          <dt>Profile</dt>
          <dd>基础资料与训练目标</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>注册后等待启用</dd>
        </div>
        <div>
          <dt>Next</dt>
          <dd>登录后进入会员工作台</dd>
        </div>
      </dl>
    </section>

    <section class="login-card register-card">
      <div>
        <p class="eyebrow">Registration</p>
        <h3 class="page-title">会员注册</h3>
        <p class="page-subtitle">填写账号信息后即可返回登录页。</p>
      </div>

      <form class="form-grid register-grid" @submit.prevent="handleMemberRegister">
        <label class="field">
          <span>会员账号</span>
          <input v-model.trim="registerForm.username" placeholder="请输入会员账号" />
        </label>
        <label class="field">
          <span>会员昵称</span>
          <input v-model.trim="registerForm.nickname" placeholder="请输入会员昵称" />
        </label>
        <label class="field">
          <span>会员密码</span>
          <input v-model="registerForm.password" type="password" placeholder="请输入密码" />
        </label>
        <label class="field">
          <span>确认密码</span>
          <input v-model="registerForm.confirmPassword" type="password" placeholder="再次输入密码" />
        </label>
        <label class="field">
          <span>手机号</span>
          <input v-model.trim="registerForm.phone" placeholder="请输入手机号" />
        </label>
        <label class="field">
          <span>邮箱</span>
          <input v-model.trim="registerForm.email" placeholder="请输入邮箱（可选）" />
        </label>

        <div class="actions field-span-2 register-actions">
          <button class="button" :disabled="loading" type="submit">
            {{ loading ? "注册中..." : "提交注册" }}
          </button>
          <RouterLink class="button-ghost" to="/login">返回登录</RouterLink>
        </div>
      </form>

      <p v-if="notice.text" class="notice" :class="notice.type">{{ notice.text }}</p>
    </section>
  </main>
</template>

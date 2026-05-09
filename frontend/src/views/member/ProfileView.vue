<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { fetchMyProfile, updateMyProfile } from "../../api/member";
import { useAuthStore } from "../../stores/auth";
import { memberStatusLabel } from "../../utils/memberStatus";

const authStore = useAuthStore();
const displayName = computed(() => authStore.currentUser?.displayName || "未登录用户");
const userType = computed(() => authStore.currentUser?.userType || "GUEST");
const loading = ref(false);
const saving = ref(false);
const profile = ref(null);
const notice = reactive({
  text: "",
  type: ""
});

const form = reactive({
  nickname: "",
  realName: "",
  gender: "",
  phone: "",
  email: "",
  birthday: "",
  heightCm: "",
  weightKg: "",
  fitnessGoal: "",
  preferredTrainingTime: "",
  injuryNotes: ""
});

const fields = computed(() => [
  { label: "会员 ID", value: profile.value?.id || authStore.currentUser?.userId || "--" },
  { label: "账号", value: profile.value?.username || authStore.currentUser?.username || "--" },
  { label: "昵称", value: profile.value?.nickname || "--" },
  { label: "会员状态", value: memberStatusLabel(profile.value?.membershipStatus || authStore.currentUser?.status || "") },
  { label: "身高", value: profile.value?.heightCm ? `${profile.value.heightCm} cm` : "--" },
  { label: "体重", value: profile.value?.weightKg ? `${profile.value.weightKg} kg` : "--" }
]);

function setNotice(text, type) {
  notice.text = text;
  notice.type = type;
}

function fillForm(data) {
  form.nickname = data?.nickname || "";
  form.realName = data?.realName || "";
  form.gender = data?.gender || "";
  form.phone = data?.phone || "";
  form.email = data?.email || "";
  form.birthday = data?.birthday || "";
  form.heightCm = data?.heightCm ?? "";
  form.weightKg = data?.weightKg ?? "";
  form.fitnessGoal = data?.fitnessGoal || "";
  form.preferredTrainingTime = data?.preferredTrainingTime || "";
  form.injuryNotes = data?.injuryNotes || "";
}

function buildPayload() {
  return {
    nickname: form.nickname,
    realName: form.realName,
    gender: form.gender,
    phone: form.phone,
    email: form.email,
    birthday: form.birthday || null,
    heightCm: form.heightCm === "" ? null : Number(form.heightCm),
    weightKg: form.weightKg === "" ? null : Number(form.weightKg),
    fitnessGoal: form.fitnessGoal,
    preferredTrainingTime: form.preferredTrainingTime,
    injuryNotes: form.injuryNotes
  };
}

async function loadProfile() {
  loading.value = true;
  notice.text = "";
  try {
    const payload = await fetchMyProfile();
    profile.value = payload.data;
    fillForm(payload.data);
  } catch (error) {
    setNotice(error.message, "error");
  } finally {
    loading.value = false;
  }
}

async function handleSaveProfile() {
  saving.value = true;
  notice.text = "";
  try {
    const payload = await updateMyProfile(buildPayload());
    profile.value = payload.data;
    fillForm(payload.data);
    await authStore.loadCurrentUser();
    setNotice("个人资料已保存", "success");
  } catch (error) {
    setNotice(error.message, "error");
  } finally {
    saving.value = false;
  }
}

onMounted(loadProfile);
</script>

<template>
  <div class="profile-container">
    <!-- Profile Header Summary -->
    <header class="section-card profile-header">
      <div class="user-main-info">
        <div class="avatar-large">{{ (form.nickname || displayName).slice(0, 1) }}</div>
        <div class="info-block">
          <div class="eyebrow">{{ userType }} ACCOUNT</div>
          <h2>{{ form.nickname || displayName }}</h2>
          <div class="status-row">
            <span class="badge" :class="authStore.currentUser?.status === 'ACTIVE' ? 'success' : 'warning'">
              {{ memberStatusLabel(authStore.currentUser?.status) }}
            </span>
            <span class="muted-text">ID: {{ profile?.id || authStore.currentUser?.userId }}</span>
          </div>
        </div>
      </div>
      <div class="quick-stats">
        <div class="stat-item">
          <span class="stat-label">身高</span>
          <span class="stat-value">{{ profile?.heightCm ? `${profile.heightCm} cm` : "--" }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">体重</span>
          <span class="stat-value">{{ profile?.weightKg ? `${profile.weightKg} kg` : "--" }}</span>
        </div>
      </div>
    </header>

    <div class="profile-content-grid">
      <!-- Edit Section -->
      <section class="section-card edit-section">
        <div class="section-head">
          <h3>编辑个人资料</h3>
          <p>请按分类完善您的详细信息，以便我们提供更好的健身服务。</p>
        </div>

        <div v-if="loading && !profile" class="loading-state">
          <div class="spinner"></div>
          <p>正在同步您的详细资料...</p>
        </div>

        <form v-else class="profile-form" @submit.prevent="handleSaveProfile">
          <!-- Category: Basic -->
          <div class="form-group">
            <div class="group-title">
              <span class="icon">👤</span>
              <h4>基本资料</h4>
            </div>
            <div class="form-grid-inner">
              <label class="field">
                <span>昵称 <span class="required">*</span></span>
                <input v-model.trim="form.nickname" placeholder="如何称呼您" required />
              </label>
              <label class="field">
                <span>真实姓名</span>
                <input v-model.trim="form.realName" placeholder="您的真实姓名" />
              </label>
              <label class="field">
                <span>性别</span>
                <select v-model="form.gender" class="filter-select">
                  <option value="">未设置</option>
                  <option value="MALE">男</option>
                  <option value="FEMALE">女</option>
                  <option value="OTHER">其他</option>
                </select>
              </label>
              <label class="field">
                <span>手机号 <span class="required">*</span></span>
                <input v-model.trim="form.phone" placeholder="接收动态通知" required />
              </label>
              <label class="field field-span-2">
                <span>邮箱地址</span>
                <input v-model.trim="form.email" type="email" placeholder="example@gym.com" />
              </label>
              <label class="field">
                <span>生理生日</span>
                <input v-model="form.birthday" type="date" />
              </label>
            </div>
          </div>

          <!-- Category: Health & Fitness -->
          <div class="form-group">
            <div class="group-title">
              <span class="icon">🔥</span>
              <h4>健身与健康</h4>
            </div>
            <div class="form-grid-inner">
              <label class="field">
                <span>身高 (cm)</span>
                <input v-model="form.heightCm" type="number" min="1" max="300" step="0.1" />
              </label>
              <label class="field">
                <span>体重 (kg)</span>
                <input v-model="form.weightKg" type="number" min="1" max="500" step="0.1" />
              </label>
              <label class="field field-span-2">
                <span>训练目标</span>
                <input v-model.trim="form.fitnessGoal" placeholder="例如：增肌、减脂、保持健康" />
              </label>
              <label class="field">
                <span>偏好时段</span>
                <input v-model.trim="form.preferredTrainingTime" placeholder="例如：工作日晚上" />
              </label>
              <label class="field">
                <span>伤病记录</span>
                <input v-model.trim="form.injuryNotes" placeholder="例如：无、膝盖旧伤" />
              </label>
            </div>
          </div>

          <div class="form-actions">
            <button class="button save-btn" :disabled="saving" type="submit">
              {{ saving ? "正在同步..." : "更新资料" }}
            </button>
            <button class="button-soft" :disabled="loading" type="button" @click="loadProfile">
              重置修改
            </button>
          </div>
        </form>

        <p v-if="notice.text" class="notice notice-float" :class="notice.type">
          {{ notice.text }}
        </p>
      </section>

      <!-- Sidebar Support/Tips -->
      <aside class="profile-sidebar">
        <article class="section-card tip-card">
          <h4>安全提醒</h4>
          <p>您的个人隐私受到保护。身高体重数据将仅用于健身分析与课程推荐。</p>
        </article>
        <article class="section-card account-card">
          <h4>账号安全</h4>
          <div class="account-item">
            <span>用户名</span>
            <strong>{{ profile?.username || authStore.currentUser?.username }}</strong>
          </div>
          <div class="account-item">
            <span>密码管理</span>
            <span class="muted-text">如需修改密码请联系客服</span>
          </div>
        </article>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.profile-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 32px;
  background: linear-gradient(135deg, var(--surface-strong) 0%, #fffcf8 100%);
}

.user-main-info {
  display: flex;
  align-items: center;
  gap: 24px;
}

.avatar-large {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: linear-gradient(135deg, var(--accent), var(--accent-deep));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 800;
  box-shadow: 0 8px 16px var(--accent-soft);
}

.info-block h2 {
  margin: 4px 0 12px;
  font-size: 32px;
  letter-spacing: 0;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.muted-text {
  font-size: 13px;
  color: var(--muted);
}

.quick-stats {
  display: flex;
  gap: 32px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.stat-label {
  font-size: 12px;
  color: var(--muted);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-value {
  font-size: 24px;
  font-weight: 800;
  color: var(--accent-deep);
}

.profile-content-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 24px;
  align-items: start;
}

.group-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--accent-soft);
}

.group-title h4 {
  margin: 0;
  font-size: 18px;
}

.form-group {
  margin-bottom: 40px;
}

.form-grid-inner {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.required {
  color: var(--error);
}

.form-actions {
  display: flex;
  gap: 16px;
  padding-top: 24px;
  border-top: 1px solid var(--line);
}

.save-btn {
  padding-left: 32px;
  padding-right: 32px;
}

.profile-sidebar {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.account-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px dashed var(--line);
  font-size: 14px;
}

.tip-card {
  background: var(--accent-soft);
  border: none;
}

.tip-card h4 {
  color: var(--accent-deep);
  margin-top: 0;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
  color: var(--muted);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--accent-soft);
  border-top: 4px solid var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.notice-float {
  margin-top: 20px;
}

@media (max-width: 1024px) {
  .profile-content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .form-grid-inner {
    grid-template-columns: 1fr;
  }
  .field-span-2 {
    grid-column: span 1;
  }
  .profile-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  .quick-stats {
    margin-top: 24px;
    width: 100%;
    justify-content: center;
  }
}
</style>

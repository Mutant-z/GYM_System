<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import {
  disableAdminMember,
  enableAdminMember,
  fetchAdminMemberDetail,
  fetchAdminMembers,
  updateAdminMember
} from "../../api/admin";
import { useAuthStore } from "../../stores/auth";
import { memberStatusLabel } from "../../utils/memberStatus";

const authStore = useAuthStore();
const isAdmin = computed(() => authStore.currentUser?.userType === "ADMIN");

const loadingMembers = ref(false);
const loadingDetail = ref(false);
const saving = ref(false);
const members = ref([]);
const selectedMemberId = ref(null);
const memberDetail = ref(null);
const responseText = ref('{\n  "message": "会员管理接口状态" \n}');
const notice = reactive({
  text: "",
  type: ""
});

const query = reactive({
  username: "",
  nickname: "",
  phone: "",
  membershipStatus: ""
});

const memberForm = reactive({
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

const activeCount = computed(() =>
  members.value.filter((item) => item.membershipStatus === "ACTIVE").length
);

const disabledCount = computed(() =>
  members.value.filter((item) => item.membershipStatus === "DISABLED").length
);

const pendingCount = computed(() =>
  members.value.filter((item) => item.membershipStatus === "PENDING").length
);

function setNotice(text, type) {
  notice.text = text;
  notice.type = type;
}

function clearNotice() {
  notice.text = "";
  notice.type = "";
}

function setResponse(payload) {
  responseText.value = JSON.stringify(payload, null, 2);
}

function formatDateTime(value) {
  if (!value) {
    return "--";
  }
  return String(value).replace("T", " ");
}

function formatNullable(value) {
  return value === null || value === undefined || value === "" ? "--" : value;
}

function fillForm(detail) {
  memberForm.nickname = detail?.nickname || "";
  memberForm.realName = detail?.realName || "";
  memberForm.gender = detail?.gender || "";
  memberForm.phone = detail?.phone || "";
  memberForm.email = detail?.email || "";
  memberForm.birthday = detail?.birthday || "";
  memberForm.heightCm = detail?.heightCm ?? "";
  memberForm.weightKg = detail?.weightKg ?? "";
  memberForm.fitnessGoal = detail?.fitnessGoal || "";
  memberForm.preferredTrainingTime = detail?.preferredTrainingTime || "";
  memberForm.injuryNotes = detail?.injuryNotes || "";
}

async function loadMembers() {
  if (!isAdmin.value) {
    return;
  }
  loadingMembers.value = true;
  clearNotice();
  try {
    const payload = await fetchAdminMembers(query);
    members.value = payload.data || [];
    setResponse(payload);
    if (!selectedMemberId.value && members.value.length > 0) {
      await selectMember(members.value[0].id);
      return;
    }
    if (
      selectedMemberId.value &&
      !members.value.some((item) => item.id === selectedMemberId.value)
    ) {
      selectedMemberId.value = null;
      memberDetail.value = null;
    }
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    loadingMembers.value = false;
  }
}

async function selectMember(id) {
  selectedMemberId.value = id;
  loadingDetail.value = true;
  clearNotice();
  try {
    const payload = await fetchAdminMemberDetail(id);
    memberDetail.value = payload.data;
    fillForm(payload.data);
    setResponse(payload);
  } catch (error) {
    memberDetail.value = null;
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    loadingDetail.value = false;
  }
}

async function handleUpdateMember() {
  if (!selectedMemberId.value) {
    setNotice("请先选择一个会员", "error");
    return;
  }
  saving.value = true;
  clearNotice();
  try {
    const payload = await updateAdminMember(selectedMemberId.value, {
      nickname: memberForm.nickname,
      realName: memberForm.realName,
      gender: memberForm.gender,
      phone: memberForm.phone,
      email: memberForm.email,
      birthday: memberForm.birthday || null,
      heightCm: memberForm.heightCm === "" ? null : Number(memberForm.heightCm),
      weightKg: memberForm.weightKg === "" ? null : Number(memberForm.weightKg),
      fitnessGoal: memberForm.fitnessGoal,
      preferredTrainingTime: memberForm.preferredTrainingTime,
      injuryNotes: memberForm.injuryNotes
    });
    memberDetail.value = payload.data;
    fillForm(payload.data);
    setResponse(payload);
    setNotice("会员信息已更新", "success");
    await loadMembers();
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    saving.value = false;
  }
}

async function handleUpdateStatus(nextStatus) {
  if (!selectedMemberId.value) {
    setNotice("请先选择一个会员", "error");
    return;
  }
  clearNotice();
  try {
    const payload =
      nextStatus === "ACTIVE"
        ? await enableAdminMember(selectedMemberId.value)
        : await disableAdminMember(selectedMemberId.value);
    setResponse(payload);
    setNotice(nextStatus === "ACTIVE" ? "会员已启用" : "会员已停用", "success");
    await loadMembers();
    await selectMember(selectedMemberId.value);
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  }
}

onMounted(async () => {
  await loadMembers();
});
</script>

<template>
  <div class="page-grid">
    <section class="hero-card admin-members-hero">
      <div>
        <div class="eyebrow">Admin Members</div>
        <h3>会员管理工作台</h3>
        <p>
          这里承接管理员的会员查询、详情查看、资料编辑和启停用操作。后端已经联通会员详情统计，
          可以直接看到预约、课程和订单概览。
        </p>
      </div>
      <div class="metric-grid compact-metrics admin-members-metrics">
        <article class="metric-card">
          <div class="metric-label">会员总数</div>
          <div class="metric-value">{{ members.length }}</div>
          <div class="metric-foot">当前筛选结果中的会员数量</div>
        </article>
        <article class="metric-card">
          <div class="metric-label">正常会员</div>
          <div class="metric-value">{{ activeCount }}</div>
          <div class="metric-foot">可正常预约、报名和下单</div>
        </article>
        <article class="metric-card">
          <div class="metric-label">停用会员</div>
          <div class="metric-value">{{ disabledCount }}</div>
          <div class="metric-foot">已暂停使用会员功能</div>
        </article>
        <article class="metric-card">
          <div class="metric-label">未启用会员</div>
          <div class="metric-value">{{ pendingCount }}</div>
          <div class="metric-foot">等待完成启用流程</div>
        </article>
      </div>
    </section>

    <section v-if="!isAdmin" class="section-card">
      <div class="section-head">
        <div>
          <h3>访问受限</h3>
          <p>当前页面只对管理员开放。请使用管理员账号登录后访问。</p>
        </div>
        <span class="badge warning">Admin Only</span>
      </div>
    </section>

    <template v-else>
      <section class="booking-layout">
        <div class="booking-column">
          <section class="section-card">
            <div class="section-head">
              <div>
                <h3>会员筛选</h3>
                <p>按账号、昵称、手机号和状态查询。</p>
              </div>
            </div>
            <div class="form-grid admin-query-grid">
              <label class="field">
                <span>账号</span>
                <input v-model.trim="query.username" placeholder="member001" />
              </label>
              <label class="field">
                <span>昵称</span>
                <input v-model.trim="query.nickname" placeholder="会员昵称" />
              </label>
              <label class="field">
                <span>手机号</span>
                <input v-model.trim="query.phone" placeholder="138..." />
              </label>
              <label class="field">
                <span>状态</span>
                <select v-model="query.membershipStatus" class="filter-select">
                  <option value="">全部状态</option>
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="PENDING">PENDING</option>
                  <option value="DISABLED">DISABLED</option>
                </select>
              </label>
              <div class="actions field-span-2">
                <button class="button" :disabled="loadingMembers" type="button" @click="loadMembers">
                  {{ loadingMembers ? "查询中..." : "查询会员" }}
                </button>
                <button class="button-ghost" type="button" @click="selectMember(selectedMemberId)" :disabled="!selectedMemberId">
                  刷新当前详情
                </button>
              </div>
            </div>
          </section>

          <section class="section-card">
            <div class="section-head">
              <div>
                <h3>会员列表</h3>
                <p>选择一个会员后，右侧会显示详情和编辑表单。</p>
              </div>
              <span class="badge success">{{ members.length }} Members</span>
            </div>

            <div v-if="loadingMembers" class="empty-inline">会员列表加载中...</div>
            <div v-else-if="members.length === 0" class="empty-inline">当前没有符合条件的会员。</div>
            <div v-else class="list-grid scroll-list member-scroll-list">
              <article
                v-for="item in members"
                :key="item.id"
                class="list-item selectable member-list-item"
                :class="{ selected: item.id === selectedMemberId }"
                @click="selectMember(item.id)"
              >
                <div class="booking-item-head">
                  <strong>{{ item.nickname }}</strong>
                  <span class="badge" :class="item.membershipStatus === 'ACTIVE' ? 'success' : 'warning'">
                    {{ memberStatusLabel(item.membershipStatus) }}
                  </span>
                </div>
                <p>账号：{{ item.username }}</p>
                <p>姓名：{{ formatNullable(item.realName) }}</p>
                <p>手机：{{ item.phone }}</p>
                <p>创建时间：{{ formatDateTime(item.createdAt) }}</p>
              </article>
            </div>
          </section>
        </div>

        <div class="booking-column">
          <section class="section-card">
            <div class="section-head">
              <div>
                <h3>会员详情</h3>
                <p>包含基础信息和关联业务概览。</p>
              </div>
            </div>

            <div v-if="loadingDetail" class="empty-inline">会员详情加载中...</div>
            <div v-else-if="!memberDetail" class="empty-inline">请选择一个会员。</div>
            <div v-else>
              <div class="placeholder-grid">
                <article class="placeholder-card"><strong>账号</strong><p>{{ memberDetail.username }}</p></article>
                <article class="placeholder-card"><strong>昵称</strong><p>{{ memberDetail.nickname }}</p></article>
                <article class="placeholder-card"><strong>姓名</strong><p>{{ formatNullable(memberDetail.realName) }}</p></article>
                <article class="placeholder-card"><strong>状态</strong><p>{{ memberStatusLabel(memberDetail.membershipStatus) }}</p></article>
                <article class="placeholder-card"><strong>预约数</strong><p>{{ memberDetail.bookingCount }}</p></article>
                <article class="placeholder-card"><strong>课程报名数</strong><p>{{ memberDetail.enrolledCourseCount }}</p></article>
                <article class="placeholder-card"><strong>订单数</strong><p>{{ memberDetail.orderCount }}</p></article>
                <article class="placeholder-card"><strong>最后登录</strong><p>{{ formatDateTime(memberDetail.lastLoginAt) }}</p></article>
              </div>
              <div class="detail-description">
                训练目标：{{ formatNullable(memberDetail.fitnessGoal) }}<br />
                偏好训练时间：{{ formatNullable(memberDetail.preferredTrainingTime) }}<br />
                伤病备注：{{ formatNullable(memberDetail.injuryNotes) }}
              </div>
              <div class="actions detail-actions">
                <button
                  class="button-soft"
                  type="button"
                  :disabled="memberDetail.membershipStatus === 'ACTIVE'"
                  @click="handleUpdateStatus('ACTIVE')"
                >
                  启用会员
                </button>
                <button
                  class="button-danger"
                  type="button"
                  :disabled="memberDetail.membershipStatus === 'DISABLED'"
                  @click="handleUpdateStatus('DISABLED')"
                >
                  停用会员
                </button>
              </div>
            </div>
          </section>

          <section class="section-card">
            <div class="section-head">
              <div>
                <h3>编辑会员信息</h3>
                <p>维护会员基础资料、训练目标、偏好时间和健康备注。</p>
              </div>
            </div>

            <div v-if="!memberDetail" class="empty-inline">请选择一个会员后再编辑。</div>
            <div v-else class="form-grid admin-query-grid">
              <label class="field">
                <span>昵称</span>
                <input v-model.trim="memberForm.nickname" />
              </label>
              <label class="field">
                <span>真实姓名</span>
                <input v-model.trim="memberForm.realName" />
              </label>
              <label class="field">
                <span>性别</span>
                <input v-model.trim="memberForm.gender" />
              </label>
              <label class="field">
                <span>手机号</span>
                <input v-model.trim="memberForm.phone" />
              </label>
              <label class="field">
                <span>邮箱</span>
                <input v-model.trim="memberForm.email" />
              </label>
              <label class="field">
                <span>生日</span>
                <input v-model="memberForm.birthday" type="date" />
              </label>
              <label class="field">
                <span>身高(cm)</span>
                <input v-model="memberForm.heightCm" type="number" step="0.01" />
              </label>
              <label class="field">
                <span>体重(kg)</span>
                <input v-model="memberForm.weightKg" type="number" step="0.01" />
              </label>
              <label class="field field-span-2">
                <span>训练目标</span>
                <input v-model.trim="memberForm.fitnessGoal" />
              </label>
              <label class="field">
                <span>偏好训练时间</span>
                <input v-model.trim="memberForm.preferredTrainingTime" />
              </label>
              <label class="field">
                <span>伤病备注</span>
                <input v-model.trim="memberForm.injuryNotes" />
              </label>
              <div class="actions field-span-2">
                <button class="button" :disabled="saving" type="button" @click="handleUpdateMember">
                  {{ saving ? "保存中..." : "保存会员信息" }}
                </button>
              </div>
            </div>
          </section>

          <p v-if="notice.text" class="notice" :class="notice.type">{{ notice.text }}</p>
        </div>
      </section>
    </template>
  </div>
</template>

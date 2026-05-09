<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import {
  adminCancelEnrollment,
  cancelEnrollment,
  createCourse,
  disableCourse,
  enableCourse,
  enrollCourse,
  fetchCourseDetail,
  fetchCourseEnrollments,
  fetchCourses,
  fetchMyCourses,
  updateCourse
} from "../../api/course";
import { useAuthStore } from "../../stores/auth";

const authStore = useAuthStore();
const isMember = computed(() => authStore.currentUser?.userType === "MEMBER");
const isAdmin = computed(() => authStore.currentUser?.userType === "ADMIN");

const loadingCourses = ref(false);
const loadingDetail = ref(false);
const loadingMine = ref(false);
const loadingAdminEnrollments = ref(false);
const submitting = ref(false);
const submittingAdmin = ref(false);
const coursePanelMode = ref("list");
const adminCourseMode = ref("info");
const courses = ref([]);
const selectedCourseId = ref(null);
const courseDetail = ref(null);
const myCourses = ref([]);
const adminEnrollments = ref([]);
const courseStatus = ref("");
const myCourseStatus = ref("");
const responseText = ref('{\n  "message": "课程模块接口状态" \n}');
const notice = reactive({
  text: "",
  type: ""
});

const courseForm = reactive({
  name: "",
  coachId: "",
  gymRoomId: "",
  courseType: "",
  startTime: "",
  endTime: "",
  capacity: 20,
  price: "0.00",
  description: "",
  status: "OPEN"
});

const selectedEnrollment = computed(() =>
  myCourses.value.find((item) => item.courseId === selectedCourseId.value) || null
);

const coursePanelTitle = computed(() =>
  isAdmin.value ? "课程列表" : coursePanelMode.value === "mine" ? "我的课程" : "课程列表"
);

const coursePanelSubtitle = computed(() =>
  isAdmin.value
    ? "点击课程后，右侧会显示当前课程的完整信息和报名名单。"
    : coursePanelMode.value === "mine"
    ? "查看当前账号已报名的课程，并可直接取消报名。"
    : "点击课程后，右侧会显示课程详情和报名操作。"
);

const coursePanelCount = computed(() =>
  coursePanelMode.value === "mine" ? myCourses.value.length : courses.value.length
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

function normalizeDateTime(value) {
  return value ? `${value}:00` : "";
}

function fillFormFromDetail(detail) {
  courseForm.name = detail?.name || "";
  courseForm.coachId = detail?.coachId ?? "";
  courseForm.gymRoomId = detail?.gymRoomId ?? "";
  courseForm.courseType = detail?.courseType || "";
  courseForm.startTime = detail?.startTime ? detail.startTime.slice(0, 16) : "";
  courseForm.endTime = detail?.endTime ? detail.endTime.slice(0, 16) : "";
  courseForm.capacity = detail?.capacity ?? 20;
  courseForm.price = detail?.price ?? "0.00";
  courseForm.description = detail?.description || "";
  courseForm.status = detail?.status || "OPEN";
}

function resetCreateForm() {
  courseForm.name = "";
  courseForm.coachId = "";
  courseForm.gymRoomId = "";
  courseForm.courseType = "";
  courseForm.startTime = "";
  courseForm.endTime = "";
  courseForm.capacity = 20;
  courseForm.price = "0.00";
  courseForm.description = "";
  courseForm.status = "OPEN";
}

async function loadCourses() {
  loadingCourses.value = true;
  clearNotice();
  try {
    const payload = await fetchCourses(courseStatus.value);
    courses.value = payload.data || [];
    setResponse(payload);
    if (!selectedCourseId.value && courses.value.length > 0) {
      await selectCourse(courses.value[0].id);
    }
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    loadingCourses.value = false;
  }
}

async function selectCourse(id) {
  selectedCourseId.value = id;
  loadingDetail.value = true;
  clearNotice();
  try {
    const payload = await fetchCourseDetail(id);
    courseDetail.value = payload.data;
    setResponse(payload);
    if (isAdmin.value) {
      fillFormFromDetail(payload.data);
      await loadSelectedCourseEnrollments(id);
    }
  } catch (error) {
    courseDetail.value = null;
    adminEnrollments.value = [];
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    loadingDetail.value = false;
  }
}

async function loadMyCourses() {
  loadingMine.value = true;
  clearNotice();
  try {
    const payload = await fetchMyCourses(myCourseStatus.value);
    myCourses.value = payload.data || [];
    setResponse(payload);
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    loadingMine.value = false;
  }
}

async function showMyCourses() {
  coursePanelMode.value = "mine";
  await loadMyCourses();
}

async function showCourseList() {
  coursePanelMode.value = "list";
  await loadCourses();
}

async function showAdminCourseInfo() {
  adminCourseMode.value = "info";
  await loadCourses();
}

function showAdminCourseCreate() {
  adminCourseMode.value = "create";
  resetCreateForm();
}

async function loadSelectedCourseEnrollments(courseId = selectedCourseId.value) {
  loadingAdminEnrollments.value = true;
  clearNotice();
  try {
    const payload = await fetchCourseEnrollments({
      courseId,
      status: "ENROLLED"
    });
    adminEnrollments.value = payload.data || [];
    setResponse(payload);
  } catch (error) {
    adminEnrollments.value = [];
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    loadingAdminEnrollments.value = false;
  }
}

async function handleEnroll() {
  if (!selectedCourseId.value) {
    setNotice("请先选择一个课程", "error");
    return;
  }
  submitting.value = true;
  clearNotice();
  try {
    const payload = await enrollCourse(selectedCourseId.value);
    setResponse(payload);
    setNotice("课程报名成功", "success");
    await loadCourses();
    await selectCourse(selectedCourseId.value);
    await loadMyCourses();
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    submitting.value = false;
  }
}

async function handleCancelEnrollment(id) {
  clearNotice();
  try {
    const payload = await cancelEnrollment(id);
    setResponse(payload);
    setNotice("课程报名已取消", "success");
    await loadMyCourses();
    await loadCourses();
    if (selectedCourseId.value) {
      await selectCourse(selectedCourseId.value);
    }
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  }
}

async function handleCreateCourse() {
  submittingAdmin.value = true;
  clearNotice();
  try {
    const payload = await createCourse({
      name: courseForm.name,
      coachId: courseForm.coachId ? Number(courseForm.coachId) : null,
      gymRoomId: courseForm.gymRoomId ? Number(courseForm.gymRoomId) : null,
      courseType: courseForm.courseType,
      startTime: normalizeDateTime(courseForm.startTime),
      endTime: normalizeDateTime(courseForm.endTime),
      capacity: Number(courseForm.capacity),
      price: Number(courseForm.price),
      description: courseForm.description,
      status: courseForm.status
    });
    setResponse(payload);
    setNotice("课程新增成功", "success");
    resetCreateForm();
    adminCourseMode.value = "info";
    await loadCourses();
    if (payload.data?.id) {
      await selectCourse(payload.data.id);
    }
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    submittingAdmin.value = false;
  }
}

async function handleUpdateCourse() {
  if (!selectedCourseId.value) {
    setNotice("请先选择一个课程", "error");
    return;
  }
  submittingAdmin.value = true;
  clearNotice();
  try {
    const payload = await updateCourse(selectedCourseId.value, {
      name: courseForm.name,
      coachId: courseForm.coachId ? Number(courseForm.coachId) : null,
      gymRoomId: courseForm.gymRoomId ? Number(courseForm.gymRoomId) : null,
      courseType: courseForm.courseType,
      startTime: normalizeDateTime(courseForm.startTime),
      endTime: normalizeDateTime(courseForm.endTime),
      capacity: Number(courseForm.capacity),
      price: Number(courseForm.price),
      description: courseForm.description,
      status: courseForm.status
    });
    setResponse(payload);
    setNotice("课程编辑成功", "success");
    await loadCourses();
    await selectCourse(selectedCourseId.value);
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    submittingAdmin.value = false;
  }
}

async function handleDisableCourse() {
  if (!selectedCourseId.value) {
    setNotice("请先选择一个课程", "error");
    return;
  }
  clearNotice();
  try {
    const payload = await disableCourse(selectedCourseId.value);
    setResponse(payload);
    setNotice("课程已停用", "success");
    await loadCourses();
    await selectCourse(selectedCourseId.value);
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  }
}

async function handleEnableCourse() {
  if (!selectedCourseId.value) {
    setNotice("请先选择一个课程", "error");
    return;
  }
  clearNotice();
  try {
    const payload = await enableCourse(selectedCourseId.value);
    setResponse(payload);
    setNotice("课程已启用", "success");
    await loadCourses();
    await selectCourse(selectedCourseId.value);
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  }
}

async function handleAdminCancelEnrollment(id) {
  clearNotice();
  try {
    const payload = await adminCancelEnrollment(id);
    setResponse(payload);
    setNotice("管理员已协助取消课程报名", "success");
    await loadCourses();
    if (selectedCourseId.value) {
      await selectCourse(selectedCourseId.value);
    }
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  }
}

onMounted(async () => {
  await loadCourses();
  if (isMember.value) {
    await loadMyCourses();
  }
});
</script>

<template>
  <div class="page-grid">
    <section class="hero-card">
      <div>
        <div class="eyebrow">Course Module</div>
        <h3>{{ isAdmin ? "课程管理" : "课程报名中心" }}</h3>
        <p>
          <template v-if="isAdmin">
            当前页面拆成课程信息、报名名单和课程新增三个工作区，避免把管理动作堆在一个界面里。
          </template>
          <template v-else>
            当前页面已经接入课程列表、课程详情、报名课程、我的课程和取消报名。
          </template>
        </p>
      </div>
      <div class="button-row">
        <button
          v-if="isAdmin"
          class="button-soft"
          :class="{ active: adminCourseMode === 'info' }"
          :disabled="loadingCourses"
          type="button"
          @click="showAdminCourseInfo"
        >
          课程信息
        </button>
        <button
          v-if="isAdmin"
          class="button-soft"
          :class="{ active: adminCourseMode === 'create' }"
          type="button"
          @click="showAdminCourseCreate"
        >
          课程新增
        </button>
        <button
          v-if="isMember"
          class="button-soft"
          :disabled="loadingMine || coursePanelMode === 'mine'"
          type="button"
          @click="showMyCourses"
        >
          我的课程
        </button>
        <button
          v-if="isMember && coursePanelMode === 'mine'"
          class="button-soft"
          :disabled="loadingCourses"
          type="button"
          @click="showCourseList"
        >
          返回课程列表
        </button>
      </div>
    </section>

    <section v-if="!isAdmin || adminCourseMode === 'info'" class="booking-layout">
      <div class="booking-column">
        <section class="section-card">
          <div class="section-head">
            <div>
              <h3>{{ coursePanelTitle }}</h3>
              <p>{{ coursePanelSubtitle }}</p>
            </div>
            <div class="actions">
              <template v-if="coursePanelMode === 'list'">
                <select v-model="courseStatus" class="filter-select" @change="loadCourses">
                  <option value="">全部状态</option>
                  <option value="OPEN">OPEN</option>
                  <option value="CLOSED">CLOSED</option>
                </select>
              </template>
              <button
                v-if="isMember && coursePanelMode === 'mine'"
                class="button-soft"
                :disabled="loadingCourses"
                type="button"
                @click="showCourseList"
              >
                返回课程列表
              </button>
              <span class="badge success">{{ coursePanelCount }} Items</span>
            </div>
          </div>

          <div v-if="coursePanelMode === 'list'">
            <div v-if="loadingCourses" class="empty-inline">课程列表加载中...</div>
            <div v-else-if="courses.length === 0" class="empty-inline">当前没有课程数据。</div>
            <div v-else class="list-grid scroll-list course-scroll-list">
              <article
                v-for="course in courses"
                :key="course.id"
                class="list-item selectable"
                :class="{ selected: course.id === selectedCourseId }"
                @click="selectCourse(course.id)"
              >
                <div class="booking-item-head">
                  <strong>{{ course.name }}</strong>
                  <span class="badge" :class="course.status === 'OPEN' ? 'success' : 'warning'">
                    {{ course.status }}
                  </span>
                </div>
                <p>类型：{{ course.courseType || "--" }}</p>
                <p>教练：{{ course.coachName || "--" }}</p>
                <p>场地：{{ course.gymRoomName || "--" }}</p>
                <p>时间：{{ course.startTime }} 到 {{ course.endTime }}</p>
                <p>人数：{{ course.enrolledCount }}/{{ course.capacity }}</p>
              </article>
            </div>
          </div>

          <div v-else>
            <div v-if="loadingMine" class="empty-inline">我的课程加载中...</div>
            <div v-else-if="myCourses.length === 0" class="empty-inline">当前没有课程报名记录。</div>
            <div v-else class="list-grid">
              <article
                v-for="item in myCourses"
                :key="item.enrollmentId"
                class="list-item selectable"
                :class="{ selected: item.courseId === selectedCourseId }"
                @click="selectCourse(item.courseId)"
              >
                <div class="booking-item-head">
                  <strong>{{ item.courseName }}</strong>
                  <span class="badge" :class="item.enrollmentStatus === 'ENROLLED' ? 'success' : 'warning'">
                    {{ item.enrollmentStatus }}
                  </span>
                </div>
                <p>报名编号：{{ item.enrollmentNo }}</p>
                <p>教练：{{ item.coachName || "--" }}</p>
                <p>场地：{{ item.gymRoomName || "--" }}</p>
                <p>时间：{{ item.startTime }} 到 {{ item.endTime }}</p>
                <p>价格：{{ item.price }}</p>
              </article>
            </div>
          </div>
        </section>
      </div>

      <div class="booking-column">
        <section class="section-card">
          <div class="section-head">
            <div>
              <h3>{{ isAdmin ? "课程信息" : "报名信息" }}</h3>
              <p>{{ isAdmin ? "右侧展示当前选中课程的完整信息、报名名单和基础管理动作。" : "右侧保持当前选中课程的详情、状态和报名操作。" }}</p>
            </div>
          </div>

          <div v-if="loadingDetail" class="empty-inline">课程详情加载中...</div>
          <div v-else-if="!courseDetail" class="empty-inline">请选择一个课程。</div>
          <div v-else-if="!isAdmin" class="placeholder-grid">
            <article class="placeholder-card"><strong>课程名称</strong><p>{{ courseDetail.name }}</p></article>
            <article class="placeholder-card"><strong>课程类型</strong><p>{{ courseDetail.courseType || "--" }}</p></article>
            <article class="placeholder-card"><strong>教练</strong><p>{{ courseDetail.coachName || "--" }}</p></article>
            <article class="placeholder-card"><strong>场地</strong><p>{{ courseDetail.gymRoomName || "--" }}</p></article>
            <article class="placeholder-card"><strong>开课时间</strong><p>{{ courseDetail.startTime }}</p></article>
            <article class="placeholder-card"><strong>结束时间</strong><p>{{ courseDetail.endTime }}</p></article>
            <article class="placeholder-card"><strong>容量 / 已报名</strong><p>{{ courseDetail.capacity }} / {{ courseDetail.enrolledCount }}</p></article>
            <article class="placeholder-card"><strong>价格</strong><p>{{ courseDetail.price }}</p></article>
            <article class="placeholder-card"><strong>状态</strong><p>{{ courseDetail.status }}</p></article>
            <article class="placeholder-card"><strong>可报名</strong><p>{{ courseDetail.enrollable ? "是" : "否" }}</p></article>
          </div>
          <div v-else class="form-grid admin-query-grid">
            <label class="field">
              <span>课程名称</span>
              <input v-model.trim="courseForm.name" placeholder="请输入课程名称" />
            </label>
            <label class="field">
              <span>课程类型</span>
              <input v-model.trim="courseForm.courseType" placeholder="如 STRENGTH" />
            </label>
            <label class="field">
              <span>教练 ID</span>
              <input v-model="courseForm.coachId" type="number" placeholder="如 1" />
            </label>
            <label class="field">
              <span>健身室 ID</span>
              <input v-model="courseForm.gymRoomId" type="number" placeholder="如 1" />
            </label>
            <label class="field">
              <span>开始时间</span>
              <input v-model="courseForm.startTime" type="datetime-local" />
            </label>
            <label class="field">
              <span>结束时间</span>
              <input v-model="courseForm.endTime" type="datetime-local" />
            </label>
            <label class="field">
              <span>容量</span>
              <input v-model="courseForm.capacity" type="number" min="1" />
            </label>
            <label class="field">
              <span>价格</span>
              <input v-model="courseForm.price" type="number" min="0" step="0.01" />
            </label>
            <label class="field">
              <span>状态</span>
              <select v-model="courseForm.status" class="filter-select">
                <option value="OPEN">OPEN</option>
                <option value="CLOSED">CLOSED</option>
              </select>
            </label>
            <label class="field">
              <span>已报名</span>
              <input :value="courseDetail.enrolledCount" disabled />
            </label>
            <label class="field field-span-2">
              <span>课程描述</span>
              <input v-model.trim="courseForm.description" placeholder="请输入课程描述" />
            </label>
          </div>
          <div v-if="!isAdmin && courseDetail?.description" class="detail-description">{{ courseDetail.description }}</div>
          <div v-if="coursePanelMode === 'mine' && selectedEnrollment" class="detail-description">
            <strong>报名记录</strong>
            <div class="order-meta">
              <span>报名编号：{{ selectedEnrollment.enrollmentNo }}</span>
              <span>报名状态：{{ selectedEnrollment.enrollmentStatus }}</span>
              <span>报名时间：{{ selectedEnrollment.startTime }} 到 {{ selectedEnrollment.endTime }}</span>
            </div>
          </div>
          <div v-if="isAdmin && courseDetail" class="detail-description">
            <strong>报名名单</strong>
            <div class="order-meta">
              <span>课程：{{ courseDetail.name }}</span>
              <span>已报名：{{ courseDetail.enrolledCount }}</span>
              <span>当前显示：{{ adminEnrollments.length }}</span>
            </div>
            <div v-if="loadingAdminEnrollments" class="empty-inline">报名名单加载中...</div>
            <div v-else-if="adminEnrollments.length === 0" class="empty-inline">当前课程还没有报名记录。</div>
            <div v-else class="list-grid course-scroll-list">
              <article
                v-for="item in adminEnrollments"
                :key="item.enrollmentId"
                class="list-item"
              >
                <div class="booking-item-head">
                  <strong>{{ item.memberDisplayName || item.memberUsername }}</strong>
                  <span class="badge" :class="item.enrollmentStatus === 'ENROLLED' ? 'success' : 'warning'">
                    {{ item.enrollmentStatus }}
                  </span>
                </div>
                <p>账号：{{ item.memberUsername }}</p>
                <p>报名编号：{{ item.enrollmentNo }}</p>
                <p>报名时间：{{ item.createdAt }}</p>
              </article>
            </div>
          </div>
          <div v-if="isMember && coursePanelMode === 'list'" class="actions detail-actions">
            <button class="button" :disabled="submitting || !courseDetail?.enrollable" type="button" @click="handleEnroll">
              {{ submitting ? "报名中..." : "报名课程" }}
            </button>
          </div>
          <div v-if="isMember && coursePanelMode === 'mine' && selectedEnrollment" class="actions detail-actions">
            <button
              class="button-danger"
              :disabled="selectedEnrollment.enrollmentStatus !== 'ENROLLED'"
              type="button"
              @click="handleCancelEnrollment(selectedEnrollment.enrollmentId)"
            >
              取消报名
            </button>
          </div>
          <div v-if="isAdmin && courseDetail" class="actions detail-actions">
            <button class="button" :disabled="submittingAdmin || !selectedCourseId" type="button" @click="handleUpdateCourse">
              {{ submittingAdmin ? "保存中..." : "保存课程信息" }}
            </button>
            <button
              class="button-soft"
              :disabled="!selectedCourseId || courseDetail.status === 'OPEN'"
              type="button"
              @click="handleEnableCourse"
            >
              启用当前课程
            </button>
            <button
              class="button-danger"
              :disabled="!selectedCourseId || courseDetail.status === 'CLOSED'"
              type="button"
              @click="handleDisableCourse"
            >
              停用当前课程
            </button>
          </div>
        </section>

        <p v-if="notice.text" class="notice" :class="notice.type">{{ notice.text }}</p>
      </div>
    </section>

    <section v-if="isAdmin && adminCourseMode === 'create'" class="section-card">
      <div class="section-head">
        <div>
          <h3>课程新增</h3>
          <p>新增课程单独放在这里，避免和课程列表、课程详情挤在一起。</p>
        </div>
        <span class="badge warning">Create</span>
      </div>

      <div class="form-grid admin-query-grid">
        <label class="field">
          <span>课程名称</span>
          <input v-model.trim="courseForm.name" placeholder="请输入课程名称" />
        </label>
        <label class="field">
          <span>课程类型</span>
          <input v-model.trim="courseForm.courseType" placeholder="如 STRENGTH" />
        </label>
        <label class="field">
          <span>教练 ID</span>
          <input v-model="courseForm.coachId" type="number" placeholder="如 1" />
        </label>
        <label class="field">
          <span>健身室 ID</span>
          <input v-model="courseForm.gymRoomId" type="number" placeholder="如 1" />
        </label>
        <label class="field">
          <span>开始时间</span>
          <input v-model="courseForm.startTime" type="datetime-local" />
        </label>
        <label class="field">
          <span>结束时间</span>
          <input v-model="courseForm.endTime" type="datetime-local" />
        </label>
        <label class="field">
          <span>容量</span>
          <input v-model="courseForm.capacity" type="number" min="1" />
        </label>
        <label class="field">
          <span>价格</span>
          <input v-model="courseForm.price" type="number" min="0" step="0.01" />
        </label>
        <label class="field">
          <span>状态</span>
          <select v-model="courseForm.status" class="filter-select">
            <option value="OPEN">OPEN</option>
            <option value="CLOSED">CLOSED</option>
          </select>
        </label>
        <label class="field field-span-2">
          <span>课程描述</span>
          <input v-model.trim="courseForm.description" placeholder="请输入课程描述" />
        </label>
      </div>

      <div class="actions detail-actions">
        <button class="button" :disabled="submittingAdmin" type="button" @click="handleCreateCourse">
          {{ submittingAdmin ? "提交中..." : "新增课程" }}
        </button>
        <button class="button-ghost" type="button" @click="resetCreateForm">
          清空表单
        </button>
      </div>
      <p v-if="notice.text" class="notice" :class="notice.type">{{ notice.text }}</p>
    </section>
  </div>
</template>

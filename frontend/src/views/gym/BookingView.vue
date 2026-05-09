<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import {
  createAdminGymRoom,
  adminCancelGymBooking,
  disableAdminGymRoom,
  enableAdminGymRoom,
  fetchAdminBookings,
  fetchAdminGymRoomDetail,
  fetchAdminGymRooms,
  cancelGymBooking,
  createGymBooking,
  fetchGymRoomDetail,
  fetchGymRooms,
  fetchMyBookings,
  updateAdminGymRoom
} from "../../api/gym";
import { useAuthStore } from "../../stores/auth";

const authStore = useAuthStore();
const isAdmin = computed(() => authStore.currentUser?.userType === "ADMIN");
const isMember = computed(() => authStore.currentUser?.userType === "MEMBER");

const loadingRooms = ref(false);
const loadingDetail = ref(false);
const loadingBookings = ref(false);
const submitting = ref(false);
const submittingAdmin = ref(false);
const rooms = ref([]);
const selectedRoomId = ref(null);
const roomDetail = ref(null);
const myBookings = ref([]);
const adminBookings = ref([]);
const adminPanelMode = ref("rooms");
const selectedBookingId = ref(null);
const bookingStatus = ref("");
const adminQuery = reactive({
  bookingNo: "",
  memberUsername: "",
  gymRoomId: "",
  status: ""
});
const roomForm = reactive({
  name: "",
  location: "",
  capacity: 1,
  openTime: "",
  closeTime: "",
  status: "OPEN",
  description: ""
});
const responseText = ref('{\n  "message": "预约模块接口状态" \n}');
const notice = reactive({
  text: "",
  type: ""
});

const bookingForm = reactive({
  gymRoomId: null,
  startTime: "",
  endTime: "",
  headCount: 1,
  remark: ""
});

const selectedRoom = computed(() =>
  rooms.value.find((item) => item.id === selectedRoomId.value) || null
);

const selectedBooking = computed(() =>
  adminBookings.value.find((item) => item.id === selectedBookingId.value) || null
);

const adminPanelTitle = computed(() =>
  adminPanelMode.value === "rooms" ? "健身室管理" : "预约订单查询"
);

const adminPanelSubtitle = computed(() =>
  adminPanelMode.value === "rooms"
    ? "管理员可以维护健身室信息，并执行激活/停用等操作。"
    : "管理员可以按条件查询预约订单，并协助取消预约。"
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

function toDateTimeLocalString(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function formatTimeValue(value) {
  return value ? String(value).slice(0, 5) : "";
}

function fillRoomForm(room) {
  roomForm.name = room?.name || "";
  roomForm.location = room?.location || "";
  roomForm.capacity = room?.capacity ?? 1;
  roomForm.openTime = formatTimeValue(room?.openTime);
  roomForm.closeTime = formatTimeValue(room?.closeTime);
  roomForm.status = room?.status || "OPEN";
  roomForm.description = room?.description || "";
}

function resetRoomForm() {
  roomForm.name = "";
  roomForm.location = "";
  roomForm.capacity = 1;
  roomForm.openTime = "";
  roomForm.closeTime = "";
  roomForm.status = "OPEN";
  roomForm.description = "";
}

function fillBookingForm(room) {
  bookingForm.gymRoomId = room?.id || null;
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(10, 0, 0, 0);
  const tomorrowEnd = new Date(tomorrow);
  tomorrowEnd.setHours(11, 0, 0, 0);
  bookingForm.startTime = toDateTimeLocalString(tomorrow);
  bookingForm.endTime = toDateTimeLocalString(tomorrowEnd);
  bookingForm.headCount = 1;
  bookingForm.remark = room ? `预约 ${room.name}` : "";
}

async function loadRooms() {
  loadingRooms.value = true;
  clearNotice();
  try {
    const payload = isAdmin.value ? await fetchAdminGymRooms() : await fetchGymRooms();
    rooms.value = payload.data || [];
    setResponse(payload);
    if (!selectedRoomId.value && rooms.value.length > 0) {
      await selectRoom(rooms.value[0].id);
    }
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    loadingRooms.value = false;
  }
}

async function selectRoom(id) {
  selectedRoomId.value = id;
  bookingForm.gymRoomId = id;
  loadingDetail.value = true;
  clearNotice();
  try {
    const payload = isAdmin.value ? await fetchAdminGymRoomDetail(id) : await fetchGymRoomDetail(id);
    roomDetail.value = payload.data;
    setResponse(payload);
    fillBookingForm(payload.data);
    if (isAdmin.value) {
      fillRoomForm(payload.data);
    }
  } catch (error) {
    roomDetail.value = null;
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    loadingDetail.value = false;
  }
}

async function loadMyBookings() {
  loadingBookings.value = true;
  clearNotice();
  try {
    const payload = await fetchMyBookings(bookingStatus.value);
    myBookings.value = payload.data || [];
    setResponse(payload);
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    loadingBookings.value = false;
  }
}

async function loadAdminBookings() {
  loadingBookings.value = true;
  clearNotice();
  try {
    const payload = await fetchAdminBookings({
      bookingNo: adminQuery.bookingNo,
      memberUsername: adminQuery.memberUsername,
      gymRoomId: adminQuery.gymRoomId,
      status: adminQuery.status
    });
    adminBookings.value = payload.data || [];
    if (!adminBookings.value.some((item) => item.id === selectedBookingId.value)) {
      selectedBookingId.value = adminBookings.value.length > 0 ? adminBookings.value[0].id : null;
    }
    if (!selectedBookingId.value && adminBookings.value.length > 0) {
      selectedBookingId.value = adminBookings.value[0].id;
    }
    setResponse(payload);
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    loadingBookings.value = false;
  }
}

function showAdminRoomManager() {
  adminPanelMode.value = "rooms";
  if (rooms.value.length > 0) {
    selectRoom(selectedRoomId.value || rooms.value[0].id);
  } else {
    loadRooms();
  }
}

async function showAdminBookingQuery() {
  adminPanelMode.value = "bookings";
  await loadAdminBookings();
}

async function handleAdminRoomCreate() {
  submittingAdmin.value = true;
  clearNotice();
  try {
    const payload = await createAdminGymRoom({
      name: roomForm.name,
      location: roomForm.location,
      capacity: Number(roomForm.capacity),
      openTime: roomForm.openTime || null,
      closeTime: roomForm.closeTime || null,
      status: roomForm.status,
      description: roomForm.description
    });
    setResponse(payload);
    setNotice("健身室创建成功", "success");
    await loadRooms();
    if (payload.data?.id) {
      await selectRoom(payload.data.id);
    }
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    submittingAdmin.value = false;
  }
}

async function handleAdminRoomUpdate() {
  if (!selectedRoomId.value) {
    setNotice("请先选择一个健身室", "error");
    return;
  }
  submittingAdmin.value = true;
  clearNotice();
  try {
    const payload = await updateAdminGymRoom(selectedRoomId.value, {
      name: roomForm.name,
      location: roomForm.location,
      capacity: Number(roomForm.capacity),
      openTime: roomForm.openTime || null,
      closeTime: roomForm.closeTime || null,
      status: roomForm.status,
      description: roomForm.description
    });
    setResponse(payload);
    setNotice("健身室信息已更新", "success");
    await loadRooms();
    await selectRoom(selectedRoomId.value);
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    submittingAdmin.value = false;
  }
}

async function handleAdminRoomEnable() {
  if (!selectedRoomId.value) {
    setNotice("请先选择一个健身室", "error");
    return;
  }
  clearNotice();
  try {
    const payload = await enableAdminGymRoom(selectedRoomId.value);
    setResponse(payload);
    setNotice("健身室已激活", "success");
    await loadRooms();
    await selectRoom(selectedRoomId.value);
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  }
}

async function handleAdminRoomDisable() {
  if (!selectedRoomId.value) {
    setNotice("请先选择一个健身室", "error");
    return;
  }
  clearNotice();
  try {
    const payload = await disableAdminGymRoom(selectedRoomId.value);
    setResponse(payload);
    setNotice("健身室已停用", "success");
    await loadRooms();
    await selectRoom(selectedRoomId.value);
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  }
}

async function handleCreateBooking() {
  submitting.value = true;
  clearNotice();
  try {
    const payload = await createGymBooking({
      gymRoomId: bookingForm.gymRoomId,
      startTime: bookingForm.startTime ? `${bookingForm.startTime}:00` : "",
      endTime: bookingForm.endTime ? `${bookingForm.endTime}:00` : "",
      headCount: Number(bookingForm.headCount),
      remark: bookingForm.remark
    });
    setResponse(payload);
    setNotice("预约创建成功", "success");
    await loadMyBookings();
    if (selectedRoomId.value) {
      await selectRoom(selectedRoomId.value);
    }
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    submitting.value = false;
  }
}

async function handleCancelBooking(id) {
  clearNotice();
  try {
    const payload = await cancelGymBooking(id);
    setResponse(payload);
    setNotice("预约取消成功", "success");
    await loadMyBookings();
    if (selectedRoomId.value) {
      await selectRoom(selectedRoomId.value);
    }
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  }
}

async function handleAdminCancelBooking(id) {
  clearNotice();
  try {
    const payload = await adminCancelGymBooking(id);
    setResponse(payload);
    setNotice("管理员已协助取消预约", "success");
    await loadAdminBookings();
    if (selectedRoomId.value) {
      await selectRoom(selectedRoomId.value);
    }
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  }
}

onMounted(async () => {
  await loadRooms();
  if (isAdmin.value) {
    fillRoomForm(selectedRoom.value);
    await loadAdminBookings();
    return;
  }
  if (isMember.value) {
    await loadMyBookings();
  }
});
</script>

<template>
  <div class="page-grid">
    <section class="hero-card">
      <div>
        <div class="eyebrow">Gym Booking</div>
        <h3>{{ isAdmin ? "健身室管理中心" : "健身室预约中心" }}</h3>
        <p>
          <template v-if="isAdmin">
            从管理员视角维护健身室信息，并查询和管理预约订单。
          </template>
          <template v-else>
            查看可用健身室、提交预约申请，并在同一页面管理个人预约记录。
          </template>
        </p>
      </div>
      <div class="button-row">
        <template v-if="isAdmin">
          <button class="button-soft" :disabled="loadingRooms || adminPanelMode === 'rooms'" type="button" @click="showAdminRoomManager">
            健身室管理
          </button>
          <button class="button-soft" :disabled="loadingBookings || adminPanelMode === 'bookings'" type="button" @click="showAdminBookingQuery">
            预约订单查询
          </button>
        </template>
        <template v-else>
          <button class="button-soft" :disabled="loadingRooms" type="button" @click="loadRooms">
            刷新房间列表
          </button>
          <button
            class="button-soft"
            :disabled="loadingBookings"
            type="button"
            @click="loadMyBookings"
          >
            刷新我的预约
          </button>
        </template>
      </div>
    </section>

    <section v-if="isAdmin" class="booking-layout">
      <div class="booking-column">
        <section class="section-card">
          <div class="section-head">
            <div>
              <h3>{{ adminPanelTitle }}</h3>
              <p>{{ adminPanelSubtitle }}</p>
            </div>
            <span class="badge warning">Admin</span>
          </div>
        </section>

        <section v-if="adminPanelMode === 'rooms'" class="section-card">
          <div class="section-head">
            <div>
              <h3>健身室列表</h3>
              <p>可查看所有健身室，并点击进入右侧详情与编辑。</p>
            </div>
            <span class="badge success">{{ rooms.length }} Rooms</span>
          </div>

          <div v-if="loadingRooms" class="empty-inline">房间列表加载中...</div>
          <div v-else-if="rooms.length === 0" class="empty-inline">当前没有可展示的健身室。</div>
          <div v-else class="list-grid scroll-list gym-room-scroll-list">
            <article
              v-for="room in rooms"
              :key="room.id"
              class="list-item selectable gym-room-list-item"
              :class="{ selected: room.id === selectedRoomId }"
              @click="selectRoom(room.id)"
            >
              <div class="booking-item-head">
                <strong>{{ room.name }}</strong>
                <span class="badge" :class="room.status === 'OPEN' ? 'success' : 'warning'">
                  {{ room.status }}
                </span>
              </div>
              <p>{{ room.location || "未设置位置" }}</p>
              <p>容量：{{ room.capacity }} 人</p>
              <p>开放时间：{{ room.openTime || "--" }} - {{ room.closeTime || "--" }}</p>
            </article>
          </div>
        </section>

        <section v-else class="section-card">
          <div class="section-head">
            <div>
              <h3>预约订单查询</h3>
              <p>按预约编号、会员账号、健身室和状态筛选记录。</p>
            </div>
            <span class="badge success">{{ adminBookings.length }} Records</span>
          </div>

          <div class="form-grid admin-query-grid">
            <label class="field">
              <span>预约编号</span>
              <input v-model.trim="adminQuery.bookingNo" placeholder="如 bk_test_existing_001" />
            </label>
            <label class="field">
              <span>会员账号</span>
              <input v-model.trim="adminQuery.memberUsername" placeholder="如 member001" />
            </label>
            <label class="field">
              <span>健身室 ID</span>
              <input v-model.trim="adminQuery.gymRoomId" type="number" placeholder="如 1" />
            </label>
            <label class="field">
              <span>状态</span>
              <select v-model="adminQuery.status" class="filter-select">
                <option value="">全部状态</option>
                <option value="CONFIRMED">CONFIRMED</option>
                <option value="CANCELED">CANCELED</option>
              </select>
            </label>
          </div>
          <div class="actions">
            <button class="button" :disabled="loadingBookings" type="button" @click="loadAdminBookings">
              查询预约
            </button>
            <button
              class="button-ghost"
              type="button"
              @click="adminQuery.bookingNo=''; adminQuery.memberUsername=''; adminQuery.gymRoomId=''; adminQuery.status=''; loadAdminBookings();"
            >
              重置条件
            </button>
          </div>

          <div v-if="loadingBookings" class="empty-inline">预约记录加载中...</div>
          <div v-else-if="adminBookings.length === 0" class="empty-inline">当前没有匹配的预约记录。</div>
          <div v-else class="list-grid">
            <article
              v-for="booking in adminBookings"
              :key="booking.id"
              class="list-item selectable"
              :class="{ selected: booking.id === selectedBookingId }"
              @click="selectedBookingId = booking.id"
            >
              <div class="booking-item-head">
                <strong>{{ booking.gymRoomName }}</strong>
                <span class="badge" :class="booking.status === 'CONFIRMED' ? 'success' : 'warning'">
                  {{ booking.status }}
                </span>
              </div>
              <p>会员账号：{{ booking.memberUsername }}</p>
              <p>会员名称：{{ booking.memberDisplayName || "--" }}</p>
              <p>预约编号：{{ booking.bookingNo }}</p>
              <p>时间：{{ booking.startTime }} 到 {{ booking.endTime }}</p>
              <p>人数：{{ booking.headCount }} 人</p>
            </article>
          </div>
        </section>
      </div>

      <div class="booking-column">
        <section v-if="adminPanelMode === 'rooms'" class="section-card">
          <div class="section-head">
            <div>
              <h3>健身室详情</h3>
              <p>可新增、编辑、激活和停用健身室信息。</p>
            </div>
          </div>

          <div v-if="loadingDetail" class="empty-inline">房间详情加载中...</div>
          <div v-else-if="!roomDetail" class="empty-inline">请选择一个健身室。</div>
          <div v-else class="placeholder-grid">
            <article class="placeholder-card">
              <strong>名称</strong>
              <p>{{ roomDetail.name }}</p>
            </article>
            <article class="placeholder-card">
              <strong>位置</strong>
              <p>{{ roomDetail.location || "--" }}</p>
            </article>
            <article class="placeholder-card">
              <strong>容量</strong>
              <p>{{ roomDetail.capacity }} 人</p>
            </article>
            <article class="placeholder-card">
              <strong>今日已预约</strong>
              <p>{{ roomDetail.todayBookedHeadCount }} 人</p>
            </article>
            <article class="placeholder-card">
              <strong>状态</strong>
              <p>{{ roomDetail.status }}</p>
            </article>
            <article class="placeholder-card">
              <strong>可预约</strong>
              <p>{{ roomDetail.bookable ? "是" : "否" }}</p>
            </article>
          </div>
          <div v-if="roomDetail?.description" class="detail-description">
            {{ roomDetail.description }}
          </div>

          <div class="form-grid admin-query-grid">
            <label class="field">
              <span>名称</span>
              <input v-model.trim="roomForm.name" placeholder="请输入健身室名称" />
            </label>
            <label class="field">
              <span>位置</span>
              <input v-model.trim="roomForm.location" placeholder="请输入位置" />
            </label>
            <label class="field">
              <span>容量</span>
              <input v-model.number="roomForm.capacity" type="number" min="1" />
            </label>
            <label class="field">
              <span>开放时间</span>
              <input v-model="roomForm.openTime" type="time" />
            </label>
            <label class="field">
              <span>关闭时间</span>
              <input v-model="roomForm.closeTime" type="time" />
            </label>
            <label class="field">
              <span>状态</span>
              <select v-model="roomForm.status" class="filter-select">
                <option value="OPEN">OPEN</option>
                <option value="CLOSED">CLOSED</option>
              </select>
            </label>
            <label class="field field-span-2">
              <span>描述</span>
              <input v-model.trim="roomForm.description" placeholder="请输入健身室描述" />
            </label>
          </div>

          <div class="actions detail-actions">
            <button class="button" :disabled="submittingAdmin" type="button" @click="handleAdminRoomCreate">
              {{ submittingAdmin ? "提交中..." : "新增健身室" }}
            </button>
            <button class="button-soft" :disabled="submittingAdmin || !selectedRoomId" type="button" @click="handleAdminRoomUpdate">
              更新当前健身室
            </button>
            <button class="button-soft" :disabled="!selectedRoomId" type="button" @click="handleAdminRoomEnable">
              激活当前健身室
            </button>
            <button class="button-danger" :disabled="!selectedRoomId" type="button" @click="handleAdminRoomDisable">
              停用当前健身室
            </button>
            <button class="button-ghost" type="button" @click="resetRoomForm">
              清空表单
            </button>
          </div>
        </section>

        <section v-else class="section-card">
          <div class="section-head">
            <div>
              <h3>预约订单详情</h3>
              <p>查看当前选中的预约，并可协助取消。</p>
            </div>
          </div>

          <div v-if="loadingBookings && adminBookings.length === 0" class="empty-inline">预约记录加载中...</div>
          <div v-else-if="!selectedBooking" class="empty-inline">请选择一条预约记录。</div>
          <div v-else class="placeholder-grid">
            <article class="placeholder-card"><strong>预约编号</strong><p>{{ selectedBooking.bookingNo }}</p></article>
            <article class="placeholder-card"><strong>会员账号</strong><p>{{ selectedBooking.memberUsername }}</p></article>
            <article class="placeholder-card"><strong>会员名称</strong><p>{{ selectedBooking.memberDisplayName || "--" }}</p></article>
            <article class="placeholder-card"><strong>健身室</strong><p>{{ selectedBooking.gymRoomName }}</p></article>
            <article class="placeholder-card"><strong>状态</strong><p>{{ selectedBooking.status }}</p></article>
            <article class="placeholder-card"><strong>人数</strong><p>{{ selectedBooking.headCount }} 人</p></article>
            <article class="placeholder-card"><strong>开始时间</strong><p>{{ selectedBooking.startTime }}</p></article>
            <article class="placeholder-card"><strong>结束时间</strong><p>{{ selectedBooking.endTime }}</p></article>
          </div>
          <div v-if="selectedBooking?.remark" class="detail-description">
            {{ selectedBooking.remark }}
          </div>
          <div class="actions detail-actions">
            <button
              class="button-danger"
              :disabled="!selectedBooking || selectedBooking.status !== 'CONFIRMED'"
              type="button"
              @click="handleAdminCancelBooking(selectedBooking.id)"
            >
              协助取消
            </button>
          </div>
        </section>
        <p v-if="notice.text" class="notice" :class="notice.type">{{ notice.text }}</p>
      </div>
    </section>

    <section v-else class="booking-layout">
      <div class="booking-column">
        <section class="section-card">
          <div class="section-head">
            <div>
              <h3>健身室列表</h3>
              <p>点击任意房间可查看详情，并自动填充预约表单。</p>
            </div>
            <span class="badge success">{{ rooms.length }} Rooms</span>
          </div>

          <div v-if="loadingRooms" class="empty-inline">房间列表加载中...</div>
          <div v-else-if="rooms.length === 0" class="empty-inline">当前没有可展示的健身室。</div>
          <div v-else class="list-grid">
            <article
              v-for="room in rooms"
              :key="room.id"
              class="list-item selectable"
              :class="{ selected: room.id === selectedRoomId }"
              @click="selectRoom(room.id)"
            >
              <div class="booking-item-head">
                <strong>{{ room.name }}</strong>
                <span class="badge" :class="room.status === 'OPEN' ? 'success' : 'warning'">
                  {{ room.status }}
                </span>
              </div>
              <p>{{ room.location || "未设置位置" }}</p>
              <p>容量：{{ room.capacity }} 人</p>
              <p>开放时间：{{ room.openTime || "--" }} - {{ room.closeTime || "--" }}</p>
            </article>
          </div>
        </section>

        <section class="section-card">
          <div class="section-head">
            <div>
              <h3>房间详情</h3>
              <p>后端当前返回今日预约人数和可预约状态。</p>
            </div>
          </div>

          <div v-if="loadingDetail" class="empty-inline">房间详情加载中...</div>
          <div v-else-if="!roomDetail" class="empty-inline">请选择一个健身室。</div>
          <div v-else class="placeholder-grid">
            <article class="placeholder-card">
              <strong>名称</strong>
              <p>{{ roomDetail.name }}</p>
            </article>
            <article class="placeholder-card">
              <strong>位置</strong>
              <p>{{ roomDetail.location || "--" }}</p>
            </article>
            <article class="placeholder-card">
              <strong>容量</strong>
              <p>{{ roomDetail.capacity }} 人</p>
            </article>
            <article class="placeholder-card">
              <strong>今日已预约</strong>
              <p>{{ roomDetail.todayBookedHeadCount }} 人</p>
            </article>
            <article class="placeholder-card">
              <strong>状态</strong>
              <p>{{ roomDetail.status }}</p>
            </article>
            <article class="placeholder-card">
              <strong>可预约</strong>
              <p>{{ roomDetail.bookable ? "是" : "否" }}</p>
            </article>
          </div>
          <div v-if="roomDetail?.description" class="detail-description">
            {{ roomDetail.description }}
          </div>
        </section>
      </div>

      <div class="booking-column">
        <section v-if="isMember" class="section-card">
          <div class="section-head">
            <div>
              <h3>创建预约</h3>
              <p>先用最直接的时间表单打通后端闭环。</p>
            </div>
            <span class="badge warning">MVP</span>
          </div>

          <form class="form-grid" @submit.prevent="handleCreateBooking">
            <label class="field">
              <span>健身室 ID</span>
              <input v-model.number="bookingForm.gymRoomId" type="number" placeholder="请选择房间" />
            </label>
            <label class="field">
              <span>开始时间</span>
              <input v-model="bookingForm.startTime" type="datetime-local" />
            </label>
            <label class="field">
              <span>结束时间</span>
              <input v-model="bookingForm.endTime" type="datetime-local" />
            </label>
            <label class="field">
              <span>预约人数</span>
              <input v-model.number="bookingForm.headCount" type="number" min="1" />
            </label>
            <label class="field">
              <span>备注</span>
              <input v-model.trim="bookingForm.remark" placeholder="可选，最多 255 字符" />
            </label>
            <div class="actions">
              <button class="button" :disabled="submitting" type="submit">
                {{ submitting ? "提交中..." : "提交预约" }}
              </button>
              <button
                class="button-ghost"
                :disabled="!selectedRoom"
                type="button"
                @click="fillBookingForm(selectedRoom)"
              >
                重新填充默认时间
              </button>
            </div>
          </form>
        </section>

        <section v-if="isMember" class="section-card">
          <div class="section-head">
            <div>
              <h3>我的预约</h3>
              <p>支持按状态筛选，并直接取消未开始的预约。</p>
            </div>
            <select v-model="bookingStatus" class="filter-select" @change="loadMyBookings">
              <option value="">全部状态</option>
              <option value="CONFIRMED">CONFIRMED</option>
              <option value="CANCELED">CANCELED</option>
            </select>
          </div>

          <div v-if="loadingBookings" class="empty-inline">预约记录加载中...</div>
          <div v-else-if="myBookings.length === 0" class="empty-inline">当前没有预约记录。</div>
          <div v-else class="list-grid">
            <article v-for="booking in myBookings" :key="booking.id" class="list-item">
              <div class="booking-item-head">
                <strong>{{ booking.gymRoomName }}</strong>
                <span class="badge" :class="booking.status === 'CONFIRMED' ? 'success' : 'warning'">
                  {{ booking.status }}
                </span>
              </div>
              <p>预约编号：{{ booking.bookingNo }}</p>
              <p>时间：{{ booking.startTime }} 到 {{ booking.endTime }}</p>
              <p>人数：{{ booking.headCount }} 人</p>
              <p>备注：{{ booking.remark || "--" }}</p>
              <div class="actions">
                <button
                  class="button-danger"
                  :disabled="booking.status !== 'CONFIRMED'"
                  type="button"
                  @click="handleCancelBooking(booking.id)"
                >
                  取消预约
                </button>
              </div>
            </article>
          </div>
        </section>

        <p v-if="notice.text" class="notice" :class="notice.type">{{ notice.text }}</p>
      </div>
    </section>
  </div>
</template>

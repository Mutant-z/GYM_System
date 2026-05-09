<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { fetchOrderDetail, fetchOrders } from "../../api/shop";
import { useAuthStore } from "../../stores/auth";

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();
const isMember = computed(() => authStore.currentUser?.userType === "MEMBER");
const isAdmin = computed(() => authStore.currentUser?.userType === "ADMIN");
const loadingOrders = ref(false);
const loadingDetail = ref(false);
const orders = ref([]);
const selectedOrderId = ref(null);
const orderDetail = ref(null);
const responseText = ref('{\n  "message": "订单模块接口状态" \n}');
const notice = reactive({
  text: "",
  type: ""
});

const orderCount = computed(() => orders.value.length);
const unpaidCount = computed(() =>
  orders.value.filter((item) => item.paymentStatus === "UNPAID").length
);
const canceledCount = computed(() =>
  orders.value.filter((item) => item.paymentStatus === "CANCELED").length
);
const paidAmount = computed(() =>
  orders.value
    .filter((item) => item.paymentStatus === "PAID")
    .reduce((sum, item) => sum + Number(item.totalAmount || 0), 0)
    .toFixed(2)
);

function formatCurrency(value) {
  return `¥${Number(value || 0).toFixed(2)}`;
}

function formatDateTime(value) {
  if (!value) {
    return "--";
  }
  return String(value).replace("T", " ");
}

function paymentStatusLabel(status) {
  if (status === "UNPAID") {
    return "待支付";
  }
  if (status === "PAID") {
    return "已支付";
  }
  if (status === "CANCELED") {
    return "取消支付";
  }
  return status || "--";
}

function paymentStatusBadgeClass(status) {
  if (status === "UNPAID") {
    return "warning";
  }
  if (status === "CANCELED") {
    return "warning";
  }
  return "success";
}

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

async function loadOrders() {
  loadingOrders.value = true;
  clearNotice();
  try {
    const payload = await fetchOrders();
    orders.value = payload.data || [];
    setResponse(payload);
    const preferredId = Number(route.query.orderId || selectedOrderId.value || 0);
    const targetOrder = orders.value.find((item) => item.id === preferredId) || orders.value[0];
    if (targetOrder) {
      await selectOrder(targetOrder.id);
    } else {
      selectedOrderId.value = null;
      orderDetail.value = null;
    }
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    loadingOrders.value = false;
  }
}

async function selectOrder(id) {
  selectedOrderId.value = id;
  loadingDetail.value = true;
  clearNotice();
  try {
    const payload = await fetchOrderDetail(id);
    orderDetail.value = payload.data;
    setResponse(payload);
  } catch (error) {
    orderDetail.value = null;
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    loadingDetail.value = false;
  }
}

function openShopPage() {
  router.push("/shop");
}

onMounted(async () => {
  await loadOrders();
});
</script>

<template>
  <div class="page-grid">
    <section class="hero-card order-hero-card">
      <div>
        <div class="eyebrow">Order Module</div>
        <h3>{{ isAdmin ? "订单管理中心" : "订单列表与详情视图" }}</h3>
        <p>
          <template v-if="isAdmin">
            当前页面展示全部会员订单，包括待支付、已支付和取消支付记录。
          </template>
          <template v-else>
            当前页面承接会员订单列表和订单详情展示，便于完成购买链最后一环。
          </template>
        </p>
      </div>
      <div class="order-hero-side">
        <div class="metric-grid compact-metrics order-hero-metrics">
          <article class="metric-card">
            <div class="metric-label">{{ isAdmin ? "全部订单" : "订单总数" }}</div>
            <div class="metric-value">{{ orderCount }}</div>
            <div class="metric-foot">{{ isAdmin ? "系统中所有会员的订单记录" : "当前登录会员的订单记录" }}</div>
          </article>
          <article class="metric-card">
            <div class="metric-label">待支付</div>
            <div class="metric-value">{{ unpaidCount }}</div>
            <div class="metric-foot">支付状态为 UNPAID 的订单</div>
          </article>
          <article class="metric-card">
            <div class="metric-label">取消支付</div>
            <div class="metric-value">{{ canceledCount }}</div>
            <div class="metric-foot">支付状态为 CANCELED 的订单</div>
          </article>
          <article class="metric-card">
            <div class="metric-label">累计已支付金额</div>
            <div class="metric-value order-paid-amount">{{ formatCurrency(paidAmount) }}</div>
            <div class="metric-foot">仅统计支付状态为 PAID 的订单</div>
          </article>
        </div>
        <div class="button-row metric-actions order-hero-actions">
          <button class="button-soft" :disabled="loadingOrders" type="button" @click="loadOrders">
            刷新订单列表
          </button>
          <button class="button-ghost" type="button" @click="openShopPage">
            返回商品页
          </button>
        </div>
      </div>
    </section>

    <section class="booking-layout">
      <div class="booking-column">
        <section class="section-card">
          <div class="section-head">
            <div>
              <h3>{{ isAdmin ? "全部订单" : "我的订单" }}</h3>
              <p>{{ isAdmin ? "点击订单记录可查看会员信息、支付状态和商品明细。" : "点击订单记录可查看订单详情与明细。" }}</p>
            </div>
            <span class="badge success">{{ orders.length }} Orders</span>
          </div>

          <div v-if="loadingOrders" class="empty-inline">订单列表加载中...</div>
          <div v-else-if="orders.length === 0" class="empty-inline">当前没有订单记录。</div>
          <div v-else class="list-grid scroll-list order-scroll-list">
            <article
              v-for="item in orders"
              :key="item.id"
              class="list-item selectable order-list-item"
              :class="{ selected: item.id === selectedOrderId }"
              @click="selectOrder(item.id)"
            >
                <div class="booking-item-head">
                  <strong>{{ item.orderNo }}</strong>
                  <span class="badge" :class="paymentStatusBadgeClass(item.paymentStatus)">
                    {{ paymentStatusLabel(item.paymentStatus) }}
                  </span>
                </div>
                <p v-if="isAdmin">会员：{{ item.memberDisplayName || item.memberUsername || "--" }}</p>
                <p v-if="isAdmin">账号：{{ item.memberUsername || "--" }}</p>
                <p>订单状态：{{ item.status }}</p>
                <p>订单金额：{{ formatCurrency(item.totalAmount) }}</p>
                <p>收货人：{{ item.receiverName }}</p>
                <p>创建时间：{{ formatDateTime(item.createdAt) }}</p>
              </article>
          </div>
        </section>
      </div>

      <div class="booking-column">
        <section class="section-card">
          <div class="section-head">
            <div>
              <h3>订单详情</h3>
              <p>展示订单收货信息和商品明细快照。</p>
            </div>
          </div>

          <div v-if="loadingDetail" class="empty-inline">订单详情加载中...</div>
          <div v-else-if="!orderDetail" class="empty-inline">请选择一个订单。</div>
          <div v-else>
            <div class="placeholder-grid">
              <article class="placeholder-card"><strong>订单编号</strong><p>{{ orderDetail.orderNo }}</p></article>
              <article v-if="isAdmin" class="placeholder-card"><strong>会员</strong><p>{{ orderDetail.memberDisplayName || orderDetail.memberUsername || "--" }}</p></article>
              <article v-if="isAdmin" class="placeholder-card"><strong>会员账号</strong><p>{{ orderDetail.memberUsername || "--" }}</p></article>
              <article class="placeholder-card"><strong>订单状态</strong><p>{{ orderDetail.status }}</p></article>
              <article class="placeholder-card"><strong>支付状态</strong><p>{{ paymentStatusLabel(orderDetail.paymentStatus) }}</p></article>
              <article class="placeholder-card"><strong>订单金额</strong><p>{{ formatCurrency(orderDetail.totalAmount) }}</p></article>
              <article class="placeholder-card"><strong>收货人</strong><p>{{ orderDetail.receiverName }}</p></article>
              <article class="placeholder-card"><strong>联系电话</strong><p>{{ orderDetail.receiverPhone }}</p></article>
            </div>
            <div class="detail-description">{{ orderDetail.receiverAddress }}</div>
            <div class="order-meta">
              <span>创建时间：{{ formatDateTime(orderDetail.createdAt) }}</span>
              <span>支付时间：{{ formatDateTime(orderDetail.paymentTime) }}</span>
            </div>
            <div class="section-head booking-list-head">
              <div>
                <h3>订单明细</h3>
                <p>以下内容来自订单快照，不受商品信息更新影响。</p>
              </div>
            </div>
            <div class="list-grid">
              <article v-for="item in orderDetail.items || []" :key="item.id" class="list-item">
                <div class="booking-item-head">
                  <strong>{{ item.commodityNameSnapshot }}</strong>
                  <span class="badge success">x{{ item.quantity }}</span>
                </div>
                <p>商品 ID：{{ item.commodityId }}</p>
                <p>单价：{{ formatCurrency(item.unitPrice) }}</p>
                <p>小计：{{ formatCurrency(item.subtotalAmount) }}</p>
              </article>
            </div>
          </div>
        </section>

        <p v-if="notice.text" class="notice" :class="notice.type">{{ notice.text }}</p>
      </div>
    </section>

  </div>
</template>

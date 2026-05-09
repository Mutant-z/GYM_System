<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import {
  addCartItem,
  createCommodity,
  createOrder,
  deleteCartItem,
  fetchAdminCommodities,
  fetchAdminCommodityDetail,
  fetchCartItems,
  fetchCommodityDetail,
  fetchCommodities,
  updateCommodity,
  updateCartItem
} from "../../api/shop";
import { useAuthStore } from "../../stores/auth";

const authStore = useAuthStore();
const router = useRouter();
const isMember = computed(() => authStore.currentUser?.userType === "MEMBER");
const isAdmin = computed(() => authStore.currentUser?.userType === "ADMIN");

const loadingGoods = ref(false);
const loadingDetail = ref(false);
const loadingCart = ref(false);
const submitting = ref(false);
const savingCommodity = ref(false);
const creatingOrder = ref(false);
const shopPanelMode = ref("goods");
const adminCommodityMode = ref("edit");

const commodities = ref([]);
const selectedCommodityId = ref(null);
const commodityDetail = ref(null);
const cartItems = ref([]);
const latestOrder = ref(null);
const responseText = ref('{\n  "message": "商品模块接口状态" \n}');
const notice = reactive({
  text: "",
  type: ""
});

const addCartForm = reactive({
  commodityId: null,
  quantity: 1
});

const commodityForm = reactive({
  name: "",
  category: "",
  price: "0.00",
  stock: 1,
  coverImage: "",
  description: "",
  status: "ON_SALE"
});

const orderForm = reactive({
  receiverName: "张三",
  receiverPhone: "13800000001",
  receiverAddress: "广东省广州市天河区体育中心1号"
});

const selectedCartItemIds = computed(() =>
  cartItems.value.filter((item) => item.selected).map((item) => item.id)
);

const selectedCartItems = computed(() => cartItems.value.filter((item) => item.selected));

const selectedCartQuantity = computed(() =>
  selectedCartItems.value.reduce((sum, item) => sum + Number(item.quantity || 0), 0)
);

const cartTotalAmount = computed(() =>
  selectedCartItems.value
    .reduce((sum, item) => sum + Number(item.subtotalAmount || 0), 0)
    .toFixed(2)
);

const onSaleCount = computed(() =>
  commodities.value.filter((item) => item.status === "ON_SALE").length
);

const lowStockCount = computed(() =>
  commodities.value.filter((item) => Number(item.stock || 0) > 0 && Number(item.stock || 0) <= 5).length
);

const lowStockCommodities = computed(() =>
  commodities.value.filter((item) => Number(item.stock || 0) > 0 && Number(item.stock || 0) <= 5)
);

const shopPanelTitle = computed(() =>
  shopPanelMode.value === "cart"
    ? "购物车"
    : isAdmin.value
    ? "商品管理"
    : "商品列表"
);

const shopPanelSubtitle = computed(() =>
  shopPanelMode.value === "cart"
    ? "查看已加入购物车的商品，并在右侧创建订单。"
    : isAdmin.value
    ? "滚动浏览全部商品，选中后可在右侧直接编辑，或切换到新增商品界面。"
    : "先选择商品，再查看详情与加入购物车。"
);

const shopPanelCount = computed(() =>
  shopPanelMode.value === "cart" ? cartItems.value.length : commodities.value.length
);

function formatCurrency(value) {
  return `¥${Number(value || 0).toFixed(2)}`;
}

function commodityStatusLabel(status) {
  if (status === "ON_SALE") {
    return "在售";
  }
  if (status === "OFF_SALE") {
    return "已下架";
  }
  return status || "--";
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

function clearCommodityForm() {
  commodityForm.name = "";
  commodityForm.category = "";
  commodityForm.price = "0.00";
  commodityForm.stock = 1;
  commodityForm.coverImage = "";
  commodityForm.description = "";
  commodityForm.status = "ON_SALE";
}

function fillCommodityForm(detail) {
  commodityForm.name = detail?.name || "";
  commodityForm.category = detail?.category || "";
  commodityForm.price = detail?.price ?? "0.00";
  commodityForm.stock = detail?.stock ?? 1;
  commodityForm.coverImage = detail?.coverImage || "";
  commodityForm.description = detail?.description || "";
  commodityForm.status = detail?.status || "ON_SALE";
}

function buildCommodityPayload() {
  return {
    name: commodityForm.name,
    category: commodityForm.category,
    price: Number(commodityForm.price),
    stock: Number(commodityForm.stock),
    coverImage: commodityForm.coverImage,
    description: commodityForm.description,
    status: commodityForm.status
  };
}

async function loadCommodities() {
  loadingGoods.value = true;
  clearNotice();
  try {
    const payload = isAdmin.value ? await fetchAdminCommodities() : await fetchCommodities();
    commodities.value = payload.data || [];
    if (
      selectedCommodityId.value &&
      !commodities.value.some((item) => item.id === selectedCommodityId.value)
    ) {
      selectedCommodityId.value = null;
      commodityDetail.value = null;
    }
    setResponse(payload);
    if (!selectedCommodityId.value && commodities.value.length > 0 && adminCommodityMode.value !== "create") {
      await selectCommodity(commodities.value[0].id);
    }
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    loadingGoods.value = false;
  }
}

async function selectCommodity(id) {
  selectedCommodityId.value = id;
  addCartForm.commodityId = id;
  loadingDetail.value = true;
  if (isAdmin.value) {
    adminCommodityMode.value = "edit";
  }
  clearNotice();
  try {
    const payload = isAdmin.value
      ? await fetchAdminCommodityDetail(id)
      : await fetchCommodityDetail(id);
    commodityDetail.value = payload.data;
    setResponse(payload);
    addCartForm.quantity = 1;
    if (isAdmin.value) {
      fillCommodityForm(payload.data);
    }
  } catch (error) {
    commodityDetail.value = null;
    if (isAdmin.value) {
      clearCommodityForm();
    }
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    loadingDetail.value = false;
  }
}

async function loadCartItems() {
  if (!isMember.value) {
    return;
  }
  loadingCart.value = true;
  clearNotice();
  try {
    const payload = await fetchCartItems();
    cartItems.value = payload.data || [];
    setResponse(payload);
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    loadingCart.value = false;
  }
}

async function showGoods() {
  shopPanelMode.value = "goods";
  if (isAdmin.value) {
    adminCommodityMode.value = "edit";
  }
  await loadCommodities();
}

async function showCreateCommodity() {
  if (!isAdmin.value) {
    return;
  }
  shopPanelMode.value = "goods";
  adminCommodityMode.value = "create";
  selectedCommodityId.value = null;
  commodityDetail.value = null;
  addCartForm.commodityId = null;
  clearCommodityForm();
}

async function showCart() {
  if (!isMember.value) {
    return;
  }
  shopPanelMode.value = "cart";
  await loadCartItems();
}

async function handleAddCart() {
  if (!selectedCommodityId.value) {
    setNotice("请先选择一个商品", "error");
    return;
  }
  submitting.value = true;
  clearNotice();
  try {
    const payload = await addCartItem({
      commodityId: selectedCommodityId.value,
      quantity: Number(addCartForm.quantity)
    });
    setResponse(payload);
    setNotice("已加入购物车", "success");
    await loadCartItems();
    await loadCommodities();
    await selectCommodity(selectedCommodityId.value);
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    submitting.value = false;
  }
}

async function handleCreateCommodity() {
  if (!isAdmin.value) {
    return;
  }
  savingCommodity.value = true;
  clearNotice();
  try {
    const payload = await createCommodity(buildCommodityPayload());
    setResponse(payload);
    setNotice("商品新增成功", "success");
    adminCommodityMode.value = "edit";
    await loadCommodities();
    if (payload.data?.id) {
      await selectCommodity(payload.data.id);
    }
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    savingCommodity.value = false;
  }
}

async function handleUpdateCommodity() {
  if (!isAdmin.value) {
    return;
  }
  if (!selectedCommodityId.value) {
    setNotice("请先选择一个商品", "error");
    return;
  }
  savingCommodity.value = true;
  clearNotice();
  try {
    const payload = await updateCommodity(selectedCommodityId.value, buildCommodityPayload());
    setResponse(payload);
    setNotice("商品信息已保存", "success");
    await loadCommodities();
    await selectCommodity(selectedCommodityId.value);
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    savingCommodity.value = false;
  }
}

async function handleToggleSelected(item) {
  clearNotice();
  try {
    const payload = await updateCartItem(item.id, {
      quantity: item.quantity,
      selected: !item.selected
    });
    setResponse(payload);
    await loadCartItems();
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  }
}

async function handleChangeQuantity(item, delta) {
  const nextQuantity = item.quantity + delta;
  if (nextQuantity < 1) {
    return;
  }
  clearNotice();
  try {
    const payload = await updateCartItem(item.id, {
      quantity: nextQuantity,
      selected: item.selected
    });
    setResponse(payload);
    await loadCartItems();
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  }
}

async function handleDeleteCartItem(id) {
  clearNotice();
  try {
    const payload = await deleteCartItem(id);
    setResponse(payload);
    setNotice("购物车项已删除", "success");
    await loadCartItems();
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  }
}

async function handleCreateOrder() {
  if (selectedCartItemIds.value.length === 0) {
    setNotice("请至少勾选一个购物车商品", "error");
    return;
  }
  creatingOrder.value = true;
  clearNotice();
  try {
    const payload = await createOrder({
      cartItemIds: selectedCartItemIds.value,
      receiverName: orderForm.receiverName,
      receiverPhone: orderForm.receiverPhone,
      receiverAddress: orderForm.receiverAddress
    });
    latestOrder.value = payload.data || null;
    setResponse(payload);
    setNotice("订单创建成功", "success");
    await loadCartItems();
    await loadCommodities();
    if (selectedCommodityId.value) {
      await selectCommodity(selectedCommodityId.value);
    }
  } catch (error) {
    setResponse({ error: error.message });
    setNotice(error.message, "error");
  } finally {
    creatingOrder.value = false;
  }
}

function goToOrderCenter() {
  if (latestOrder.value?.id) {
    router.push({
      path: "/orders",
      query: {
        orderId: latestOrder.value.id
      }
    });
    return;
  }
  router.push("/orders");
}

onMounted(async () => {
  await loadCommodities();
  await loadCartItems();
});
</script>

<template>
  <div class="page-grid">
    <section class="hero-card shop-hero-card">
      <div>
        <div class="eyebrow">Shop Module</div>
        <h3>{{ isMember ? "健身商城" : "商品模块工作区" }}</h3>
        <p>
          <template v-if="isMember">
            当前页面已经接入商品列表、商品详情、加入购物车、修改购物车和创建订单。
          </template>
          <template v-else>
            管理员可滚动浏览全部商品、直接编辑商品信息，并新增商品。
          </template>
        </p>
      </div>
      <div class="metric-grid compact-metrics shop-hero-metrics">
        <article class="metric-card">
          <div class="metric-label">在售商品</div>
          <div class="metric-value">{{ onSaleCount }}</div>
          <div class="metric-foot">当前商品接口返回的可售商品数</div>
        </article>
        <article class="metric-card">
          <div class="metric-label">低库存商品</div>
          <div class="metric-value">{{ lowStockCount }}</div>
          <div class="metric-foot">库存 1-5 件，建议及时补货</div>
          <div v-if="lowStockCommodities.length > 0" class="metric-tags">
            <span v-for="item in lowStockCommodities" :key="item.id" class="metric-tag">
              {{ item.name }} / {{ item.stock }}
            </span>
          </div>
          <div v-else class="metric-foot">当前没有低库存商品。</div>
        </article>
        <article v-if="isMember" class="metric-card">
          <div class="metric-label">已选购物车项</div>
          <div class="metric-value">{{ selectedCartItemIds.length }}</div>
          <div class="metric-foot">共 {{ selectedCartQuantity }} 件，待结算 {{ formatCurrency(cartTotalAmount) }}</div>
        </article>
        <div class="button-row metric-actions shop-hero-actions">
          <button
            v-if="isAdmin"
            class="button-soft"
            :class="{ active: adminCommodityMode === 'create' }"
            :disabled="loadingGoods && adminCommodityMode === 'create'"
            type="button"
            @click="showCreateCommodity"
          >
            新增商品
          </button>
          <button v-if="isMember" class="button-soft" :disabled="loadingCart || shopPanelMode === 'cart'" type="button" @click="showCart">
            购物车
          </button>
          <button v-if="isMember" class="button-ghost" type="button" @click="goToOrderCenter">
            查看订单中心
          </button>
        </div>
      </div>
    </section>

    <section class="shop-browser-layout">
      <div class="shop-list-column">
        <section class="section-card">
          <div class="section-head">
            <div>
              <h3>{{ shopPanelTitle }}</h3>
              <p>{{ shopPanelSubtitle }}</p>
            </div>
            <span class="badge success">{{ shopPanelCount }} Items</span>
          </div>

          <div v-if="shopPanelMode === 'goods'">
            <div v-if="loadingGoods" class="empty-inline">商品列表加载中...</div>
            <div v-else-if="commodities.length === 0" class="empty-inline">{{ isAdmin ? "当前没有商品数据。" : "当前没有可售商品。" }}</div>
            <div v-else class="list-grid scroll-list shop-scroll-list">
              <article
                v-for="item in commodities"
                :key="item.id"
                class="list-item selectable"
                :class="{ selected: item.id === selectedCommodityId }"
                @click="selectCommodity(item.id)"
              >
                <div class="booking-item-head">
                  <strong>{{ item.name }}</strong>
                  <span class="badge" :class="item.status === 'ON_SALE' ? 'success' : 'warning'">
                    {{ commodityStatusLabel(item.status) }}
                  </span>
                </div>
                <p>分类：{{ item.category || "--" }}</p>
                <p>价格：{{ formatCurrency(item.price) }}</p>
                <p>库存：{{ item.stock }}</p>
                <p>状态：{{ commodityStatusLabel(item.status) }}</p>
              </article>
            </div>
          </div>

          <div v-else>
            <div v-if="loadingCart" class="empty-inline">购物车加载中...</div>
            <div v-else-if="cartItems.length === 0" class="empty-inline">购物车当前为空。</div>
            <div v-else class="list-grid">
              <article v-for="item in cartItems" :key="item.id" class="list-item">
                <div class="booking-item-head">
                  <strong>{{ item.commodityName }}</strong>
                  <span class="badge" :class="item.selected ? 'success' : 'warning'">
                    {{ item.selected ? "已勾选" : "未勾选" }}
                  </span>
                </div>
                <p>单价：{{ formatCurrency(item.commodityPrice) }}</p>
                <p>库存：{{ item.commodityStock }}</p>
                <p>数量：{{ item.quantity }}</p>
                <p>小计：{{ formatCurrency(item.subtotalAmount) }}</p>
                <div class="actions">
                  <button class="button-soft" type="button" @click="handleToggleSelected(item)">
                    {{ item.selected ? "取消勾选" : "勾选商品" }}
                  </button>
                  <button class="button-ghost" type="button" @click="handleChangeQuantity(item, -1)">-1</button>
                  <button class="button-ghost" type="button" @click="handleChangeQuantity(item, 1)">+1</button>
                  <button class="button-danger" type="button" @click="handleDeleteCartItem(item.id)">删除</button>
                </div>
              </article>
            </div>
          </div>
        </section>
      </div>

      <div class="shop-detail-column">
        <section class="section-card">
          <div class="section-head">
            <div>
              <h3>{{ shopPanelMode === 'cart' ? '创建订单' : isAdmin && adminCommodityMode === 'create' ? '新增商品' : '商品详情' }}</h3>
              <p>
                <template v-if="shopPanelMode === 'cart'">
                  只会对当前购物车中已勾选的商品创建订单。
                </template>
                <template v-else-if="isAdmin && adminCommodityMode === 'create'">
                  填写商品基础信息后即可提交新增。
                </template>
                <template v-else>
                  选中商品后可直接修改基础信息并保存。
                </template>
              </p>
            </div>
          </div>

          <div v-if="shopPanelMode === 'goods'">
            <div v-if="isAdmin">
              <div v-if="adminCommodityMode === 'create'">
                <div class="placeholder-grid">
                  <article class="placeholder-card"><strong>模式</strong><p>新增商品</p></article>
                  <article class="placeholder-card"><strong>状态</strong><p>默认在售</p></article>
                  <article class="placeholder-card"><strong>库存</strong><p>默认 1</p></article>
                  <article class="placeholder-card"><strong>图片</strong><p>可选</p></article>
                </div>
                <div class="form-grid admin-query-grid">
                  <label class="field">
                    <span>商品名称</span>
                    <input v-model.trim="commodityForm.name" placeholder="请输入商品名称" />
                  </label>
                  <label class="field">
                    <span>分类</span>
                    <input v-model.trim="commodityForm.category" placeholder="如 PROTEIN" />
                  </label>
                  <label class="field">
                    <span>价格</span>
                    <input v-model="commodityForm.price" type="number" min="0" step="0.01" />
                  </label>
                  <label class="field">
                    <span>库存</span>
                    <input v-model="commodityForm.stock" type="number" min="0" />
                  </label>
                  <label class="field field-span-2">
                    <span>封面图</span>
                    <input v-model.trim="commodityForm.coverImage" placeholder="请输入封面图地址" />
                  </label>
                  <label class="field field-span-2">
                    <span>状态</span>
                    <select v-model="commodityForm.status" class="filter-select">
                      <option value="ON_SALE">ON_SALE</option>
                      <option value="OFF_SALE">OFF_SALE</option>
                    </select>
                  </label>
                  <label class="field field-span-2">
                    <span>商品描述</span>
                    <input v-model.trim="commodityForm.description" placeholder="请输入商品描述" />
                  </label>
                </div>
                <div class="actions detail-actions">
                  <button class="button" :disabled="savingCommodity" type="button" @click="handleCreateCommodity">
                    {{ savingCommodity ? "提交中..." : "新增商品" }}
                  </button>
                  <button class="button-ghost" type="button" @click="clearCommodityForm">
                    清空表单
                  </button>
                </div>
              </div>
              <div v-else>
                <div v-if="loadingDetail" class="empty-inline">商品详情加载中...</div>
                <div v-else-if="!commodityDetail" class="empty-inline">请选择一个商品。</div>
                <div v-else>
                  <div class="placeholder-grid">
                    <article class="placeholder-card"><strong>商品编号</strong><p>{{ commodityDetail.id }}</p></article>
                    <article class="placeholder-card"><strong>可购买</strong><p>{{ commodityDetail.purchasable ? "是" : "否" }}</p></article>
                    <article class="placeholder-card"><strong>状态</strong><p>{{ commodityStatusLabel(commodityDetail.status) }}</p></article>
                    <article class="placeholder-card"><strong>库存</strong><p>{{ commodityDetail.stock }}</p></article>
                  </div>
                  <div class="form-grid admin-query-grid">
                    <label class="field">
                      <span>商品名称</span>
                      <input v-model.trim="commodityForm.name" placeholder="请输入商品名称" />
                    </label>
                    <label class="field">
                      <span>分类</span>
                      <input v-model.trim="commodityForm.category" placeholder="如 PROTEIN" />
                    </label>
                    <label class="field">
                      <span>价格</span>
                      <input v-model="commodityForm.price" type="number" min="0" step="0.01" />
                    </label>
                    <label class="field">
                      <span>库存</span>
                      <input v-model="commodityForm.stock" type="number" min="0" />
                    </label>
                    <label class="field field-span-2">
                      <span>封面图</span>
                      <input v-model.trim="commodityForm.coverImage" placeholder="请输入封面图地址" />
                    </label>
                    <label class="field field-span-2">
                      <span>状态</span>
                      <select v-model="commodityForm.status" class="filter-select">
                        <option value="ON_SALE">ON_SALE</option>
                        <option value="OFF_SALE">OFF_SALE</option>
                      </select>
                    </label>
                    <label class="field field-span-2">
                      <span>商品描述</span>
                      <input v-model.trim="commodityForm.description" placeholder="请输入商品描述" />
                    </label>
                  </div>
                  <div v-if="commodityDetail?.description" class="detail-description">{{ commodityDetail.description }}</div>
                  <div v-if="commodityDetail?.coverImage" class="detail-description">封面图：{{ commodityDetail.coverImage }}</div>
                  <div class="actions detail-actions">
                    <button class="button" :disabled="savingCommodity" type="button" @click="handleUpdateCommodity">
                      {{ savingCommodity ? "保存中..." : "保存商品信息" }}
                    </button>
                    <button class="button-soft" type="button" @click="showCreateCommodity">
                      新增商品
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <div v-else>
              <div v-if="loadingDetail" class="empty-inline">商品详情加载中...</div>
              <div v-else-if="!commodityDetail" class="empty-inline">请选择一个商品。</div>
              <div v-else class="placeholder-grid">
                <article class="placeholder-card"><strong>商品名称</strong><p>{{ commodityDetail.name }}</p></article>
                <article class="placeholder-card"><strong>分类</strong><p>{{ commodityDetail.category || "--" }}</p></article>
                <article class="placeholder-card"><strong>价格</strong><p>{{ formatCurrency(commodityDetail.price) }}</p></article>
                <article class="placeholder-card"><strong>库存</strong><p>{{ commodityDetail.stock }}</p></article>
                <article class="placeholder-card"><strong>状态</strong><p>{{ commodityStatusLabel(commodityDetail.status) }}</p></article>
                <article class="placeholder-card"><strong>可购买</strong><p>{{ commodityDetail.purchasable ? "是" : "否" }}</p></article>
              </div>
              <div v-if="!isAdmin && commodityDetail?.description" class="detail-description">{{ commodityDetail.description }}</div>
              <div v-if="isMember && commodityDetail" class="actions detail-actions">
                <label class="field inline-field">
                  <span>数量</span>
                  <input v-model.number="addCartForm.quantity" type="number" min="1" />
                </label>
                <button class="button" :disabled="submitting || !commodityDetail?.purchasable" type="button" @click="handleAddCart">
                  {{ submitting ? "加入中..." : "加入购物车" }}
                </button>
              </div>
            </div>
          </div>

          <div v-else>
            <div class="placeholder-grid">
              <article class="placeholder-card"><strong>已选商品</strong><p>{{ selectedCartItemIds.length }}</p></article>
              <article class="placeholder-card"><strong>商品件数</strong><p>{{ selectedCartQuantity }}</p></article>
              <article class="placeholder-card"><strong>结算金额</strong><p>{{ formatCurrency(cartTotalAmount) }}</p></article>
              <article class="placeholder-card"><strong>待创建订单</strong><p>{{ selectedCartItems.length }}</p></article>
            </div>

            <div class="form-grid">
              <label class="field">
                <span>收货人</span>
                <input v-model.trim="orderForm.receiverName" placeholder="请输入收货人" />
              </label>
              <label class="field">
                <span>联系电话</span>
                <input v-model.trim="orderForm.receiverPhone" placeholder="请输入联系电话" />
              </label>
              <label class="field">
                <span>收货地址</span>
                <input v-model.trim="orderForm.receiverAddress" placeholder="请输入收货地址" />
              </label>
              <div class="selection-summary">
                <strong>本次结算</strong>
                <p>已勾选 {{ selectedCartItemIds.length }} 项，共 {{ selectedCartQuantity }} 件商品。</p>
                <div v-if="selectedCartItems.length > 0" class="selection-tags">
                  <span v-for="item in selectedCartItems" :key="item.id" class="selection-tag">
                    {{ item.commodityName }} x{{ item.quantity }}
                  </span>
                </div>
              </div>
              <div class="actions">
                <button class="button" :disabled="creatingOrder || selectedCartItemIds.length === 0" type="button" @click="handleCreateOrder">
                  {{ creatingOrder ? "下单中..." : `创建订单（${selectedCartItemIds.length}项）` }}
                </button>
                <button class="button-ghost" type="button" @click="goToOrderCenter">
                  查看订单页
                </button>
              </div>
            </div>
          </div>
        </section>

        <section v-if="isMember && latestOrder && shopPanelMode === 'cart'" class="section-card">
          <div class="section-head">
            <div>
              <h3>最近创建订单</h3>
              <p>订单创建后可以直接跳转到订单中心查看详情。</p>
            </div>
            <span class="badge success">{{ latestOrder.orderNo }}</span>
          </div>
          <div class="placeholder-grid">
            <article class="placeholder-card"><strong>订单编号</strong><p>{{ latestOrder.orderNo }}</p></article>
            <article class="placeholder-card"><strong>订单状态</strong><p>{{ latestOrder.status }}</p></article>
            <article class="placeholder-card"><strong>支付状态</strong><p>{{ latestOrder.paymentStatus }}</p></article>
            <article class="placeholder-card"><strong>订单金额</strong><p>{{ formatCurrency(latestOrder.totalAmount) }}</p></article>
          </div>
          <div class="actions detail-actions">
            <button class="button" type="button" @click="goToOrderCenter">打开订单详情</button>
          </div>
        </section>

        <p v-if="notice.text" class="notice" :class="notice.type">{{ notice.text }}</p>
      </div>
    </section>
  </div>
</template>

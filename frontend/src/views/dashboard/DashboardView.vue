<script setup>
import { computed, nextTick, ref } from "vue";
import { useAuthStore } from "../../stores/auth";
import { chatWithAgent } from "../../api/agent";

const authStore = useAuthStore();

// Assistant logic
const inputText = ref("");
const loading = ref(false);
const conversationId = ref(`conv-${Date.now()}`);
const messages = ref([
  {
    role: "assistant",
    content: "在这里可以直接查询订单、预约、课程、会员和商品信息。"
  }
]);
const messageListRef = ref(null);

const currentUserId = computed(() => authStore.currentUser?.userId || "");

function scrollToBottom() {
  nextTick(() => {
    const element = messageListRef.value;
    if (!element) {
      return;
    }
    element.scrollTop = element.scrollHeight;
  });
}

async function handleSend() {
  const text = inputText.value.trim();
  if (!text || loading.value) {
    return;
  }

  loading.value = true;
  messages.value.push({
    role: "user",
    content: text
  });
  scrollToBottom();

  try {
    const payload = await chatWithAgent({
      text,
      userId: currentUserId.value,
      conversationId: conversationId.value,
      metadata: { source: "dashboard" }
    });

    messages.value.push({
      role: "assistant",
      content: payload.answer || "未返回回复"
    });
    inputText.value = "";
  } catch (error) {
    messages.value.push({
      role: "assistant",
      content: `请求失败：${error.message || "未知错误"}`
    });
  } finally {
    loading.value = false;
    scrollToBottom();
  }
}

function startNewConversation() {
  conversationId.value = `conv-${Date.now()}`;
  messages.value = [
    {
      role: "assistant",
      content: "新的会话已开始。你可以继续查询系统信息。"
    }
  ];
}
</script>

<template>
  <div class="full-layout">
    <section class="assistant-section-fullscreen">
      <div class="section-head">
        <div>
          <h3>智能助手 (Agent)</h3>
          <p>直接输入指令，如“帮我查订单”或“有哪些课程”，Agent 将为您服务。</p>
        </div>
        <button class="button-soft mini" type="button" @click="startNewConversation">新会话</button>
      </div>

      <div ref="messageListRef" class="assistant-thread fullscreen-chat">
        <article
          v-for="(message, index) in messages"
          :key="`${message.role}-${index}`"
          class="assistant-message"
          :class="message.role"
        >
          <div class="message-role">{{ message.role === "user" ? "你" : "Agent" }}</div>
          <p class="message-content">{{ message.content }}</p>
        </article>
      </div>

      <div class="assistant-composer">
        <textarea
          v-model="inputText"
          class="composer-input"
          rows="3"
          placeholder="请输入查询指令..."
          :disabled="loading"
          @keydown.enter.prevent="handleSend"
        />
        <button class="button large-send" type="button" :disabled="loading" @click="handleSend">
          {{ loading ? "处理中..." : "发送" }}
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.full-layout {
  display: flex;
  height: 100vh;
  padding: 0;
  overflow: hidden;
}

.assistant-section-fullscreen {
  width: 100%;
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border: none;
  border-radius: 0;
  box-shadow: none;
}

.section-head {
  padding: 24px 32px;
  background: white;
  border-bottom: 1px solid var(--line);
  margin-bottom: 0;
}

.fullscreen-chat {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: rgba(255, 255, 255, 0.2);
}

.assistant-message {
  max-width: min(80%, 650px);
  padding: 16px 20px;
  border-radius: 20px;
  box-shadow: var(--shadow-sm);
  line-height: 1.6;
}

.assistant-message.assistant {
  align-self: flex-start;
  background: white;
  border-bottom-left-radius: 4px;
}

.assistant-message.user {
  align-self: flex-end;
  background: linear-gradient(135deg, var(--accent), var(--accent-deep));
  color: white;
  border-bottom-right-radius: 4px;
}

.message-role {
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
  opacity: 0.7;
}

.message-content {
  margin: 0;
  font-size: 15px;
}

.assistant-composer {
  padding: 24px 32px;
  max-width: 1000px;
  margin: 0 auto;
  width: 100%;
  background: transparent;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.composer-input {
  width: 100%;
  border-radius: 12px;
  padding: 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  resize: none;
}

.large-send {
  width: 100%;
  padding: 16px;
  font-size: 16px;
  border-radius: 12px;
}

.button-soft.mini {
  padding: 8px 16px;
}
</style>

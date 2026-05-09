import { defineStore } from "pinia";
import {
  adminLogin,
  fetchCurrentUser,
  logout as logoutApi,
  memberLogin,
  readToken,
  saveToken
} from "../api/auth";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: readToken(),
    currentUser: null,
    initialized: false
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token)
  },
  actions: {
    setToken(token) {
      this.token = token || "";
      saveToken(this.token);
    },
    async loginAsMember(form) {
      const payload = await memberLogin(form);
      this.setToken(payload.data.token);
      this.currentUser = {
        userId: payload.data.userId,
        username: payload.data.username,
        displayName: payload.data.displayName,
        userType: payload.data.userType,
        role: payload.data.role,
        status: payload.data.status
      };
      this.initialized = true;
      return payload;
    },
    async loginAsAdmin(form) {
      const payload = await adminLogin(form);
      this.setToken(payload.data.token);
      this.currentUser = {
        userId: payload.data.userId,
        username: payload.data.username,
        displayName: payload.data.displayName,
        userType: payload.data.userType,
        role: payload.data.role,
        status: payload.data.status
      };
      this.initialized = true;
      return payload;
    },
    async restoreSession() {
      if (!this.token) {
        this.initialized = true;
        return null;
      }
      try {
        const payload = await fetchCurrentUser();
        this.currentUser = payload.data;
        this.initialized = true;
        return payload;
      } catch (error) {
        this.clearAuth();
        this.initialized = true;
        return null;
      }
    },
    async loadCurrentUser() {
      const payload = await fetchCurrentUser();
      this.currentUser = payload.data;
      this.initialized = true;
      return payload;
    },
    async logout() {
      try {
        if (this.token) {
          await logoutApi();
        }
      } finally {
        this.clearAuth();
      }
    },
    clearAuth() {
      this.setToken("");
      this.currentUser = null;
    }
  }
});

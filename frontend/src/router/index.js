import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";
import DashboardView from "../views/dashboard/DashboardView.vue";
import CourseView from "../views/course/CourseView.vue";
import BookingView from "../views/gym/BookingView.vue";
import LoginView from "../views/login/LoginView.vue";
import RegisterView from "../views/login/RegisterView.vue";
import AdminMembersView from "../views/admin/AdminMembersView.vue";
import ProfileView from "../views/member/ProfileView.vue";
import ShopView from "../views/shop/ShopView.vue";
import OrderView from "../views/order/OrderView.vue";
import MainLayout from "../layouts/MainLayout.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      name: "login",
      component: LoginView,
      meta: {
        guestOnly: true
      }
    },
    {
      path: "/register",
      name: "register",
      component: RegisterView,
      meta: {
        guestOnly: true
      }
    },
    {
      path: "/",
      component: MainLayout,
      meta: {
        requiresAuth: true
      },
      children: [
        {
          path: "",
          redirect: "/dashboard"
        },
        {
          path: "dashboard",
          name: "dashboard",
          component: DashboardView
        },
        {
          path: "members/profile",
          name: "profile",
          component: ProfileView
        },
        {
          path: "admin/members",
          name: "admin-members",
          component: AdminMembersView,
          meta: {
            adminOnly: true
          }
        },
        {
          path: "gym/bookings",
          name: "bookings",
          component: BookingView
        },
        {
          path: "courses",
          name: "courses",
          component: CourseView
        },
        {
          path: "shop",
          name: "shop",
          component: ShopView
        },
        {
          path: "orders",
          name: "orders",
          component: OrderView
        },
      ]
    }
  ]
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  if (authStore.token && !authStore.initialized) {
    await authStore.restoreSession();
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      path: "/login",
      query: {
        redirect: to.fullPath
      }
    };
  }

  if (to.meta.adminOnly && authStore.currentUser?.userType !== "ADMIN") {
    return "/dashboard";
  }

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return "/dashboard";
  }

  const currentStatus = authStore.currentUser?.status || "";
  const isRestrictedMember =
    authStore.currentUser?.userType === "MEMBER" && currentStatus && currentStatus !== "ACTIVE";
  if (isRestrictedMember) {
    const allowedRoutes = new Set(["shop", "orders"]);
    if (!allowedRoutes.has(String(to.name || ""))) {
      return "/shop";
    }
  }

  return true;
});

export default router;

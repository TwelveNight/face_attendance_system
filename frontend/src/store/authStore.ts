/**
 * 认证状态管理
 * 管理用户登录状态、Token等
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi } from '../api/client';

interface AuthState {
  // 状态
  token: string | null;
  userType: 'admin' | 'user' | null;
  currentUser: any | null;
  isAuthenticated: boolean;

  // 操作
  adminLogin: (username: string, password: string) => Promise<void>;
  userLogin: (username: string, password: string) => Promise<void>;
  logout: () => void;
  setToken: (token: string, userType: 'admin' | 'user') => void;
  fetchCurrentUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // 初始状态
      token: null,
      userType: null,
      currentUser: null,
      isAuthenticated: false,

      // 管理员登录
      adminLogin: async (username: string, password: string) => {
        try {
          const response = await authApi.adminLogin(username, password);
          const { token, admin } = response.data;

          // 保存Token到localStorage
          localStorage.setItem('token', token);
          localStorage.setItem('userType', 'admin');

          set({
            token,
            userType: 'admin',
            currentUser: admin,
            isAuthenticated: true,
          });
        } catch (error: any) {
          console.error('管理员登录失败:', error);
          throw error;
        }
      },

      // 普通用户登录
      userLogin: async (username: string, password: string) => {
        try {
          const response = await authApi.userLogin(username, password);
          const { token, user } = response.data;

          // 保存Token到localStorage
          localStorage.setItem('token', token);
          localStorage.setItem('userType', 'user');

          set({
            token,
            userType: 'user',
            currentUser: user,
            isAuthenticated: true,
          });
        } catch (error: any) {
          console.error('用户登录失败:', error);
          throw error;
        }
      },

      // 登出
      logout: () => {
        const { userType } = get();

        // 调用后端登出API
        try {
          if (userType === 'admin') {
            authApi.adminLogout();
          } else if (userType === 'user') {
            authApi.userLogout();
          }
        } catch (error) {
          console.error('登出API调用失败:', error);
        }

        // 清除本地存储
        localStorage.removeItem('token');
        localStorage.removeItem('userType');

        set({
          token: null,
          userType: null,
          currentUser: null,
          isAuthenticated: false,
        });
      },

      // 设置Token
      setToken: (token: string, userType: 'admin' | 'user') => {
        localStorage.setItem('token', token);
        localStorage.setItem('userType', userType);

        set({
          token,
          userType,
          isAuthenticated: true,
        });
      },

      // 获取当前用户信息
      fetchCurrentUser: async () => {
        const { token, userType } = get();

        if (!token || !userType) {
          return;
        }

        try {
          let response;
          if (userType === 'admin') {
            response = await authApi.getAdminInfo();
          } else {
            response = await authApi.getUserInfo();
          }

          set({
            currentUser: response.data,
            isAuthenticated: true,
          });
        } catch (error) {
          console.error('获取用户信息失败:', error);
          // Token可能已过期，清除状态
          get().logout();
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        userType: state.userType,
        currentUser: state.currentUser,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

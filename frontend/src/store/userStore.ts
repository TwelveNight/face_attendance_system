/**
 * 用户状态管理
 */
import { create } from 'zustand';
import type { User } from '../types';
import { userApi } from '../api/client';

interface UserState {
  users: User[];
  currentUser: User | null;
  loading: boolean;
  error: string | null;
  
  // Actions
  fetchUsers: (keyword?: string) => Promise<void>;
  fetchUser: (userId: number) => Promise<void>;
  createUser: (data: { username: string; student_id?: string; face_images?: string[] }) => Promise<User | null>;
  updateUser: (userId: number, data: Partial<User>) => Promise<void>;
  deleteUser: (userId: number) => Promise<void>;
  setCurrentUser: (user: User | null) => void;
  clearError: () => void;
}

export const useUserStore = create<UserState>((set) => ({
  users: [],
  currentUser: null,
  loading: false,
  error: null,

  fetchUsers: async (keyword?: string) => {
    set({ loading: true, error: null });
    try {
      const response = await userApi.getUsers(keyword);
      set({ users: response.data, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  fetchUser: async (userId: number) => {
    set({ loading: true, error: null });
    try {
      const response = await userApi.getUser(userId);
      set({ currentUser: response.data, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  createUser: async (data) => {
    set({ loading: true, error: null });
    try {
      const response = await userApi.registerUser(data);
      set((state) => ({
        users: [response.data, ...state.users],
        loading: false,
      }));
      return response.data;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
      return null;
    }
  },

  updateUser: async (userId, data) => {
    set({ loading: true, error: null });
    try {
      const response = await userApi.updateUser(userId, data);
      set((state) => ({
        users: state.users.map((u) => (u.id === userId ? response.data : u)),
        loading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  deleteUser: async (userId) => {
    set({ loading: true, error: null });
    try {
      await userApi.deleteUser(userId);
      set((state) => ({
        users: state.users.filter((u) => u.id !== userId),
        loading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  setCurrentUser: (user) => set({ currentUser: user }),
  clearError: () => set({ error: null }),
}));

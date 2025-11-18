/**
 * 考勤状态管理
 */
import { create } from 'zustand';
import type { Attendance, Statistics, CheckInResult } from '../types';
import { attendanceApi, statisticsApi } from '../api/client';

interface AttendanceState {
  records: Attendance[];
  todayRecords: Attendance[];
  statistics: Statistics | null;
  loading: boolean;
  error: string | null;
  
  // Actions
  checkIn: (image: string) => Promise<CheckInResult | null>;
  fetchHistory: (params: any) => Promise<void>;
  fetchTodayRecords: () => Promise<void>;
  fetchDailyStats: (date?: string) => Promise<void>;
  clearError: () => void;
}

export const useAttendanceStore = create<AttendanceState>((set) => ({
  records: [],
  todayRecords: [],
  statistics: null,
  loading: false,
  error: null,

  checkIn: async (image: string) => {
    set({ loading: true, error: null });
    try {
      const response = await attendanceApi.checkIn(image);
      if (response.data.success) {
        // 刷新今日记录
        const todayResponse = await attendanceApi.getTodayAttendance();
        set({ todayRecords: todayResponse.data, loading: false });
        return response.data;
      } else {
        set({ error: response.data.message, loading: false });
        return response.data;
      }
    } catch (error) {
      const errorMsg = (error as Error).message;
      set({ error: errorMsg, loading: false });
      return { success: false, message: errorMsg };
    }
  },

  fetchHistory: async (params) => {
    set({ loading: true, error: null });
    try {
      const response = await attendanceApi.getHistory(params);
      set({ records: response.data.items, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  fetchTodayRecords: async () => {
    set({ loading: true, error: null });
    try {
      const response = await attendanceApi.getTodayAttendance();
      set({ todayRecords: response.data, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  fetchDailyStats: async (date?: string) => {
    set({ loading: true, error: null });
    try {
      const response = await statisticsApi.getDaily(date);
      set({ statistics: response.data, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  clearError: () => set({ error: null }),
}));

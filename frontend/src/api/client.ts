/**
 * API客户端
 * 封装所有后端API调用
 */
import axios, { type AxiosInstance, AxiosError } from 'axios';
import type { ApiResponse, User, Attendance, Statistics, CheckInResult, SystemStatus, PaginatedData } from '../types';

// API基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8088';

// 创建axios实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    console.log('API请求:', config.method?.toUpperCase(), config.url);
    
    // 添加Token到请求头
    const token = localStorage.getItem('token');
    const userType = localStorage.getItem('userType');
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('Token已添加到请求头, 用户类型:', userType);
    } else {
      console.warn('⚠️ 没有找到Token，请先登录');
    }
    
    if (config.data && config.url?.includes('register')) {
      console.log('注册数据:', {
        username: config.data.username,
        student_id: config.data.student_id,
        face_images_count: config.data.face_images?.length || 0,
      });
    }
    return config;
  },
  (error) => {
    console.error('请求拦截器错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    console.log('API响应:', response.config.url, '状态:', response.status);
    return response.data;
  },
  (error: AxiosError<ApiResponse>) => {
    console.error('API错误:', error.config?.url, error.response?.status);
    console.error('错误详情:', error.response?.data);
    const message = error.response?.data?.message || error.message || '请求失败';
    return Promise.reject(new Error(message));
  }
);

// ==================== 认证API ====================

export const authApi = {
  // 管理员登录
  adminLogin: (username: string, password: string) => {
    return apiClient.post<any, ApiResponse<{ token: string; admin: any }>>('/api/admin/login', {
      username,
      password,
    });
  },

  // 管理员登出
  adminLogout: () => {
    return apiClient.post<any, ApiResponse>('/api/admin/logout');
  },

  // 获取当前管理员信息
  getAdminInfo: () => {
    return apiClient.get<any, ApiResponse<any>>('/api/admin/me');
  },

  // 修改管理员密码
  changeAdminPassword: (oldPassword: string, newPassword: string) => {
    return apiClient.put<any, ApiResponse>('/api/admin/password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  // 普通用户登录
  userLogin: (username: string, password: string) => {
    return apiClient.post<any, ApiResponse<{ token: string; user: User }>>('/api/auth/login', {
      username,
      password,
    });
  },

  // 普通用户登出
  userLogout: () => {
    return apiClient.post<any, ApiResponse>('/api/auth/logout');
  },

  // 获取当前用户信息
  getUserInfo: () => {
    return apiClient.get<any, ApiResponse<User>>('/api/auth/me');
  },

  // 修改用户密码
  changeUserPassword: (oldPassword: string, newPassword: string) => {
    return apiClient.put<any, ApiResponse>('/api/auth/password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  // 首次设置密码
  setPassword: (username: string, studentId: string, newPassword: string) => {
    return apiClient.post<any, ApiResponse>('/api/auth/set-password', {
      username,
      student_id: studentId,
      new_password: newPassword,
    });
  },

  // 检查密码状态
  checkPassword: (username: string) => {
    return apiClient.post<any, ApiResponse<{ has_password: boolean; username: string; student_id: string }>>('/api/auth/check-password', {
      username,
    });
  },
};

// ==================== 用户管理API ====================

export const userApi = {
  // 获取用户列表
  getUsers: (keyword?: string, activeOnly: boolean = true) => {
    return apiClient.get<any, ApiResponse<User[]>>('/api/users', {
      params: { keyword, active_only: activeOnly },
    });
  },

  // 获取用户详情
  getUser: (userId: number) => {
    return apiClient.get<any, ApiResponse<User>>(`/api/users/${userId}`);
  },

  // 注册用户
  registerUser: (data: { username: string; student_id?: string; face_images?: string[] }) => {
    return apiClient.post<any, ApiResponse<User>>('/api/users/register', data);
  },

  // 更新用户
  updateUser: (userId: number, data: Partial<User>) => {
    return apiClient.put<any, ApiResponse<User>>(`/api/users/${userId}`, data);
  },

  // 更新用户人脸
  updateUserFaces: (userId: number, faceImages: string[]) => {
    return apiClient.post<any, ApiResponse>(`/api/users/${userId}/faces`, {
      face_images: faceImages,
    });
  },

  // 删除用户（默认硬删除）
  deleteUser: (userId: number, hard: boolean = true) => {
    return apiClient.delete<any, ApiResponse>(`/api/users/${userId}`, {
      params: { hard },
    });
  },

  // 用户统计
  getUserStatistics: () => {
    return apiClient.get<any, ApiResponse<any>>('/api/users/statistics');
  },
};

// ==================== 考勤管理API ====================

export const attendanceApi = {
  // 实时识别预览（不保存记录）
  preview: (image: string) => {
    return apiClient.post<any, ApiResponse<any>>('/api/attendance/preview', {
      image,
    });
  },

  // 打卡
  checkIn: (image: string, status: string = 'present') => {
    return apiClient.post<any, ApiResponse<CheckInResult>>('/api/attendance/check-in', {
      image,
      status,
    });
  },

  // 考勤历史
  getHistory: (params: {
    page?: number;
    per_page?: number;
    user_id?: number;
    status?: string;
    start_date?: string;
    end_date?: string;
  }) => {
    return apiClient.get<any, ApiResponse<PaginatedData<Attendance>>>('/api/attendance/history', {
      params,
    });
  },

  // 用户考勤记录
  getUserAttendance: (userId: number, limit: number = 100) => {
    return apiClient.get<any, ApiResponse<Attendance[]>>(`/api/attendance/user/${userId}`, {
      params: { limit },
    });
  },

  // 今日考勤
  getTodayAttendance: (userId?: number) => {
    return apiClient.get<any, ApiResponse<Attendance[]>>('/api/attendance/today', {
      params: { user_id: userId },
    });
  },

  // 导出CSV
  exportCSV: (startDate: string, endDate: string) => {
    return apiClient.get('/api/attendance/export', {
      params: { start_date: startDate, end_date: endDate },
      responseType: 'blob',
    });
  },

  // 删除考勤记录
  deleteAttendance: (attendanceId: number) => {
    return apiClient.delete<any, ApiResponse>(`/api/attendance/${attendanceId}`);
  },
};

// ==================== 统计分析API ====================

export const statisticsApi = {
  // 每日统计
  getDaily: (date?: string) => {
    return apiClient.get<any, ApiResponse<Statistics>>('/api/statistics/daily', {
      params: { date },
    });
  },

  // 每日统计（带部门筛选）
  getDailyWithDept: (date?: string, departmentId?: number) => {
    return apiClient.get<any, ApiResponse<Statistics>>('/api/statistics/daily', {
      params: { date, department_id: departmentId },
    });
  },

  // 周统计
  getWeekly: (startDate?: string) => {
    return apiClient.get<any, ApiResponse<Statistics>>('/api/statistics/weekly', {
      params: { start_date: startDate },
    });
  },

  // 月统计
  getMonthly: (year?: number, month?: number) => {
    return apiClient.get<any, ApiResponse<Statistics>>('/api/statistics/monthly', {
      params: { year, month },
    });
  },

  // 用户统计
  getUserStats: (userId: number, days: number = 30) => {
    return apiClient.get<any, ApiResponse<Statistics>>(`/api/statistics/user/${userId}`, {
      params: { days },
    });
  },
};

// ==================== 系统管理API ====================

export const systemApi = {
  // 健康检查
  healthCheck: () => {
    return apiClient.get<any, ApiResponse<SystemStatus>>('/api/system/health');
  },

  // 模型状态
  getModelStatus: () => {
    return apiClient.get<any, ApiResponse<any>>('/api/system/models');
  },

  // 系统日志
  getLogs: (limit: number = 100, level?: string) => {
    return apiClient.get<any, ApiResponse<any[]>>('/api/system/logs', {
      params: { limit, level },
    });
  },

  // 系统配置
  getConfig: () => {
    return apiClient.get<any, ApiResponse<any>>('/api/system/config');
  },
};

// ==================== 部门API ====================

export const departmentApi = {
  // 获取部门列表
  getAll: (tree: boolean = false, includeInactive: boolean = false) => {
    return apiClient.get<any, ApiResponse<any>>('/api/departments', {
      params: { tree, include_inactive: includeInactive },
    });
  },

  // 获取部门详情
  getById: (id: number) => {
    return apiClient.get<any, ApiResponse<any>>(`/api/departments/${id}`);
  },

  // 创建部门
  create: (data: any) => {
    return apiClient.post<any, ApiResponse<any>>('/api/departments', data);
  },

  // 更新部门
  update: (id: number, data: any) => {
    return apiClient.put<any, ApiResponse<any>>(`/api/departments/${id}`, data);
  },

  // 删除部门
  delete: (id: number, force: boolean = false) => {
    return apiClient.delete<any, ApiResponse>(`/api/departments/${id}`, {
      params: { force },
    });
  },

  // 获取部门下的用户
  getUsers: (id: number, includeChildren: boolean = false) => {
    return apiClient.get<any, ApiResponse<User[]>>(`/api/departments/${id}/users`, {
      params: { include_children: includeChildren },
    });
  },

  // 搜索部门
  search: (keyword: string) => {
    return apiClient.get<any, ApiResponse<any[]>>('/api/departments/search', {
      params: { keyword },
    });
  },
};

// ==================== 考勤规则API ====================

export const attendanceRuleApi = {
  // 获取所有规则
  getAll: (includeInactive: boolean = false) => {
    return apiClient.get<any, ApiResponse<any[]>>('/api/attendance-rules', {
      params: { include_inactive: includeInactive },
    });
  },

  // 获取规则详情
  getById: (id: number) => {
    return apiClient.get<any, ApiResponse<any>>(`/api/attendance-rules/${id}`);
  },

  // 获取默认规则
  getDefault: () => {
    return apiClient.get<any, ApiResponse<any>>('/api/attendance-rules/default');
  },

  // 获取部门规则
  getByDepartment: (departmentId: number) => {
    return apiClient.get<any, ApiResponse<any>>(`/api/attendance-rules/department/${departmentId}`);
  },

  // 获取用户规则
  getByUser: (userId: number) => {
    return apiClient.get<any, ApiResponse<any>>(`/api/attendance-rules/user/${userId}`);
  },

  // 创建规则
  create: (data: any) => {
    return apiClient.post<any, ApiResponse<any>>('/api/attendance-rules', data);
  },

  // 更新规则
  update: (id: number, data: any) => {
    return apiClient.put<any, ApiResponse<any>>(`/api/attendance-rules/${id}`, data);
  },

  // 删除规则
  delete: (id: number) => {
    return apiClient.delete<any, ApiResponse>(`/api/attendance-rules/${id}`);
  },

  // 检查打卡状态
  checkStatus: (data: any) => {
    return apiClient.post<any, ApiResponse<any>>('/api/attendance-rules/check', data);
  },
};

// 视频流URL
export const getVideoFeedUrl = () => `${API_BASE_URL}/api/video/feed`;

export default apiClient;

/**
 * 类型定义
 */

// 用户类型
export interface User {
  id: number;
  username: string;
  student_id?: string;
  created_at: string;
  avatar_path?: string;
  is_active: boolean;
}

// 考勤记录类型
export interface Attendance {
  id: number;
  user_id: number;
  username?: string;
  student_id?: string;
  timestamp: string;
  status: 'present' | 'late' | 'absent';
  confidence?: number;
  image_path?: string;
  notes?: string;
}

// 统计数据类型
export interface Statistics {
  total: number;
  status_distribution: Record<string, number>;
  unique_users: number;
  attendance_rate?: number;
  date?: string;
}

// API响应类型
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

// 分页数据类型
export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// 打卡结果类型
export interface CheckInResult {
  success: boolean;
  user_id?: number;
  username?: string;
  student_id?: string;
  confidence?: number;
  timestamp?: string;
  message: string;
}

// 系统状态类型
export interface SystemStatus {
  status: string;
  database: string;
  models_loaded: boolean;
  gpu_available?: boolean;
  gpu_memory?: {
    allocated_mb: number;
    reserved_mb: number;
    total_mb: number;
    free_mb: number;
  };
}

/**
 * 类型定义
 */

// 管理员类型
export interface Admin {
  id: number;
  username: string;
  real_name?: string;
  email?: string;
  phone?: string;
  is_super: boolean;
  is_active: boolean;
  last_login_at?: string;
  created_at: string;
}

// 部门类型
export interface Department {
  id: number;
  name: string;
  code?: string;
  parent_id?: number;
  manager_id?: number;
  manager_name?: string;
  description?: string;
  level: number;
  sort_order: number;
  is_active: boolean;
  user_count: number;
  created_at: string;
  children?: Department[];
}

// 考勤规则类型
export interface AttendanceRule {
  id: number;
  name: string;
  work_start_time: string;
  work_end_time: string;
  late_threshold: number;
  early_threshold: number;
  work_days: string;
  work_days_list: string[];
  department_id?: number;
  department_name?: string;
  is_default: boolean;
  is_active: boolean;
  is_open_mode: boolean;
  description?: string;
  created_at: string;
}

// 用户类型
export interface User {
  id: number;
  username: string;
  student_id?: string;
  department_id?: number;
  position?: string;
  email?: string;
  phone?: string;
  entry_date?: string;
  created_at: string;
  avatar_path?: string;
  is_active: boolean;
  password?: string; // 仅用于更新密码
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
  status?: string;
  is_late?: boolean;
  is_early?: boolean;
  message: string;
  rule?: {
    id: number;
    name: string;
    work_start_time: string;
    work_end_time: string;
    is_open_mode: boolean;
  };
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

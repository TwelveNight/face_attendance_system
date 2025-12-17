/**
 * 日志管理API
 */
import request from '../utils/request';

export const logApi = {
  /**
   * 获取系统日志
   */
  getSystemLogs: (params: {
    page?: number;
    size?: number;
    event_type?: string;
    level?: string;
    module?: string;
    user_id?: number;
    admin_id?: number;
    start_date?: string;
    end_date?: string;
  }) => {
    return request.get('/api/log/system-logs', { params });
  },

  /**
   * 获取登录日志
   */
  getLoginLogs: (params: {
    page?: number;
    size?: number;
    admin_id?: number;
    start_date?: string;
    end_date?: string;
    status?: string;
  }) => {
    return request.get('/api/log/admin/login-logs', { params });
  },

  /**
   * 获取登录统计
   */
  getLoginStatistics: (days: number = 7) => {
    return request.get('/api/log/login-statistics', {
      params: { days }
    });
  },

  /**
   * 获取系统日志统计
   */
  getSystemLogStatistics: (days: number = 7) => {
    return request.get('/api/log/system-log-statistics', {
      params: { days }
    });
  },

  /**
   * 清理旧日志
   */
  cleanupLogs: (days: number) => {
    return request.post('/api/log/cleanup', { days });
  }
};

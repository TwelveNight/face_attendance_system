/**
 * HTTP 请求工具
 */
import axios from 'axios';
import { message } from 'antd';

// 创建 axios 实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8088',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const res = response.data;
    
    // 如果是二进制数据（如文件下载），直接返回
    if (response.config.responseType === 'blob') {
      return response;
    }
    
    // 处理业务错误
    if (res.success === false) {
      message.error(res.message || '请求失败');
      return Promise.reject(new Error(res.message || '请求失败'));
    }
    
    return res;
  },
  (error) => {
    // 处理HTTP错误
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 401: {
          message.error('未授权，请重新登录');
          // 清除token并跳转到登录页
          const userType = localStorage.getItem('userType');
          localStorage.removeItem('token');
          localStorage.removeItem('userType');
          // 根据用户类型跳转到对应的登录页
          window.location.href = userType === 'admin' ? '/admin/login' : '/login';
          break;
        }
        case 403:
          message.error('无权限访问');
          break;
        case 404:
          message.error('请求的资源不存在');
          break;
        case 500:
          message.error(data.message || '服务器错误');
          break;
        default:
          message.error(data.message || `请求失败: ${status}`);
      }
    } else if (error.request) {
      message.error('网络错误，请检查网络连接');
    } else {
      message.error('请求配置错误');
    }
    
    return Promise.reject(error);
  }
);

export default request;

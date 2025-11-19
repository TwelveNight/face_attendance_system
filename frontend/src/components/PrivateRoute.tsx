/**
 * 路由守卫组件
 * 用于保护需要登录或特定权限的路由
 */
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

/**
 * 管理员路由守卫
 * 只有管理员可以访问
 */
export const AdminRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, userType } = useAuthStore();
  
  if (!isAuthenticated || userType !== 'admin') {
    return <Navigate to="/admin/login" replace />;
  }
  
  return <>{children}</>;
};

/**
 * 用户路由守卫
 * 需要登录（管理员或普通用户）
 */
export const UserRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuthStore();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

/**
 * 公开路由
 * 任何人都可以访问
 */
export const PublicRoute = ({ children }: { children: React.ReactNode }) => {
  return <>{children}</>;
};

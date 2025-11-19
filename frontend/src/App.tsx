import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import MainLayout from './components/Layout/MainLayout';
import Dashboard from './pages/Dashboard';
import Attendance from './pages/Attendance';
import Users from './pages/Users';
import History from './pages/History';
import Statistics from './pages/Statistics';
import AdminLogin from './pages/AdminLogin';
import UserLogin from './pages/UserLogin';
import SetPassword from './pages/SetPassword';
import MyAttendance from './pages/MyAttendance';
import Profile from './pages/Profile';
import { AdminRoute, UserRoute } from './components/PrivateRoute';
import './App.css';

function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1890ff',
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          {/* 登录页面（独立路由） */}
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/login" element={<UserLogin />} />
          <Route path="/set-password" element={<SetPassword />} />
          
          {/* 主应用路由 */}
          <Route path="/" element={<MainLayout />}>
            {/* 默认跳转到考勤打卡 */}
            <Route index element={<Navigate to="/attendance" replace />} />
            
            {/* 公开路由 - 考勤打卡 */}
            <Route path="attendance" element={<Attendance />} />
            
            {/* 用户路由 - 需要登录 */}
            <Route path="my-attendance" element={<UserRoute><MyAttendance /></UserRoute>} />
            <Route path="profile" element={<UserRoute><Profile /></UserRoute>} />
            
            {/* 管理员路由 */}
            <Route path="dashboard" element={<AdminRoute><Dashboard /></AdminRoute>} />
            <Route path="users" element={<AdminRoute><Users /></AdminRoute>} />
            <Route path="history" element={<AdminRoute><History /></AdminRoute>} />
            <Route path="statistics" element={<AdminRoute><Statistics /></AdminRoute>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;

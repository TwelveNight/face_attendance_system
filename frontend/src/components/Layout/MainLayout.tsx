/**
 * 主布局组件
 */
import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, theme, Dropdown, Button, message } from 'antd';
import type { MenuProps } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  ClockCircleOutlined,
  BarChartOutlined,
  CameraOutlined,
  LoginOutlined,
  LogoutOutlined,
  DownOutlined,
  ApartmentOutlined,
  SettingOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../../store/authStore';

const { Header, Sider, Content } = Layout;

const MainLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();
  
  // 获取认证状态
  const { isAuthenticated, currentUser, userType, logout } = useAuthStore();

  // 根据用户类型生成菜单项
  const getMenuItems = () => {
    // 未登录：只显示考勤打卡
    if (!isAuthenticated) {
      return [
        {
          key: '/attendance',
          icon: <CameraOutlined />,
          label: '考勤打卡',
        },
      ];
    }

    // 管理员：显示所有菜单
    if (userType === 'admin') {
      return [
        {
          key: '/dashboard',
          icon: <DashboardOutlined />,
          label: '仪表盘',
        },
        {
          key: '/attendance',
          icon: <CameraOutlined />,
          label: '考勤打卡',
        },
        {
          key: '/users',
          icon: <UserOutlined />,
          label: '用户管理',
        },
        {
          key: '/departments',
          icon: <ApartmentOutlined />,
          label: '部门管理',
        },
        {
          key: '/attendance-rules',
          icon: <SettingOutlined />,
          label: '考勤规则',
        },
        {
          key: '/history',
          icon: <ClockCircleOutlined />,
          label: '考勤历史',
        },
        {
          key: '/statistics',
          icon: <BarChartOutlined />,
          label: '统计分析',
        },
        {
          key: '/system-log',
          icon: <FileTextOutlined />,
          label: '日志管理',
        },
      ];
    }

    // 普通用户：显示个人相关菜单
    return [
      {
        key: '/attendance',
        icon: <CameraOutlined />,
        label: '考勤打卡',
      },
      {
        key: '/my-attendance',
        icon: <ClockCircleOutlined />,
        label: '我的考勤',
      },
      {
        key: '/profile',
        icon: <UserOutlined />,
        label: '个人中心',
      },
    ];
  };

  const menuItems = getMenuItems();

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  // 用户菜单 - 根据用户类型显示不同菜单
  const getUserMenuItems = (): MenuProps['items'] => {
    if (userType === 'admin') {
      // 管理员只显示登出
      return [
        {
          key: 'logout',
          icon: <LogoutOutlined />,
          label: '登出',
          danger: true,
        },
      ];
    }
    
    // 普通用户显示个人信息和登出
    return [
      {
        key: 'profile',
        icon: <UserOutlined />,
        label: '个人信息',
      },
      {
        type: 'divider',
      },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '登出',
        danger: true,
      },
    ];
  };

  const handleUserMenuClick = ({ key }: { key: string }) => {
    if (key === 'logout') {
      logout();
      message.success('已登出');
      // 根据用户类型跳转到不同的登录页
      navigate(userType === 'admin' ? '/admin/login' : '/login');
    } else if (key === 'profile') {
      navigate('/profile');
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: collapsed ? 16 : 20,
            fontWeight: 'bold',
          }}
        >
          {collapsed ? '考勤' : '人脸识别考勤系统'}
        </div>
        <Menu
          theme="dark"
          selectedKeys={[location.pathname]}
          mode="inline"
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: '0 24px',
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <h2 style={{ margin: 0 }}>人脸识别考勤系统</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <div style={{ color: '#666' }}>
              {new Date().toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                weekday: 'long',
              })}
            </div>
            {isAuthenticated ? (
              <Dropdown menu={{ items: getUserMenuItems(), onClick: handleUserMenuClick }} placement="bottomRight">
                <Button type="text">
                  {userType === 'admin' ? '👑 ' : ''}
                  {currentUser?.real_name || currentUser?.username || '用户'} <DownOutlined />
                </Button>
              </Dropdown>
            ) : (
              <div style={{ display: 'flex', gap: '10px' }}>
                <Button onClick={() => navigate('/login')}>
                  用户登录
                </Button>
                <Button type="primary" icon={<LoginOutlined />} onClick={() => navigate('/admin/login')}>
                  管理员登录
                </Button>
              </div>
            )}
          </div>
        </Header>
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;

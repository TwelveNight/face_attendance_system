/**
 * 管理员登录页面
 */
import { useState } from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import './style.css';

export default function AdminLogin() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const adminLogin = useAuthStore((state) => state.adminLogin);

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      await adminLogin(values.username, values.password);
      message.success('登录成功！');
      navigate('/');
    } catch (error: any) {
      message.error(error.message || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-login-container">
      <Card className="login-card" title="管理员登录">
        <Form
          name="admin-login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div className="login-tips">
          <p>默认账号: admin</p>
          <p>默认密码: admin123</p>
        </div>
      </Card>
    </div>
  );
}

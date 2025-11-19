/**
 * 普通用户登录页面
 */
import { useState } from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import './style.css';

export default function UserLogin() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const userLogin = useAuthStore((state) => state.userLogin);

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      await userLogin(values.username, values.password);
      message.success('登录成功！');
      navigate('/');
    } catch (error: any) {
      message.error(error.message || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="user-login-container">
      <Card className="login-card" title="用户登录">
        <Form
          name="user-login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名或学号' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名或学号"
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

        <div className="login-footer">
          <div className="login-links">
            <a onClick={() => navigate('/admin/login')}>切换到管理员登录</a>
            <span className="divider">|</span>
            <a onClick={() => navigate('/attendance')}>直接打卡</a>
          </div>
          <div className="login-links" style={{ marginTop: '10px' }}>
            <a onClick={() => navigate('/set-password')}>首次设置密码</a>
          </div>
          <div className="login-tips">
            <p>提示：首次登录请先设置密码</p>
          </div>
        </div>
      </Card>
    </div>
  );
}

/**
 * 首次设置密码页面
 */
import { useState } from 'react';
import { Form, Input, Button, Card, message, Steps } from 'antd';
import { UserOutlined, IdcardOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../../api/client';
import './style.css';

const { Step } = Steps;

export default function SetPassword() {
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [userInfo, setUserInfo] = useState<any>(null);
  const navigate = useNavigate();

  // 第一步：检查用户
  const onCheckUser = async (values: { username: string }) => {
    setLoading(true);
    try {
      const response = await authApi.checkPassword(values.username);
      const { has_password, username, student_id } = response.data;
      
      if (has_password) {
        message.warning('该用户已设置密码，请直接登录');
        navigate('/login');
        return;
      }
      
      setUserInfo({ username, student_id });
      setCurrentStep(1);
      message.success('验证成功，请设置密码');
    } catch (error: any) {
      message.error(error.message || '用户不存在');
    } finally {
      setLoading(false);
    }
  };

  // 第二步：设置密码
  const onSetPassword = async (values: { password: string; confirmPassword: string }) => {
    if (values.password !== values.confirmPassword) {
      message.error('两次密码输入不一致');
      return;
    }

    setLoading(true);
    try {
      await authApi.setPassword(userInfo.username, userInfo.student_id, values.password);
      message.success('密码设置成功！请登录');
      navigate('/login');
    } catch (error: any) {
      message.error(error.message || '设置失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="set-password-container">
      <Card className="set-password-card" title="首次设置密码">
        <Steps current={currentStep} style={{ marginBottom: 30 }}>
          <Step title="验证身份" />
          <Step title="设置密码" />
        </Steps>

        {currentStep === 0 && (
          <Form
            name="check-user"
            onFinish={onCheckUser}
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

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
              >
                下一步
              </Button>
            </Form.Item>

            <div className="form-footer">
              <a onClick={() => navigate('/login')}>返回登录</a>
            </div>
          </Form>
        )}

        {currentStep === 1 && (
          <Form
            name="set-password"
            onFinish={onSetPassword}
            autoComplete="off"
            size="large"
          >
            <Form.Item label="用户名">
              <Input value={userInfo?.username} disabled prefix={<UserOutlined />} />
            </Form.Item>

            <Form.Item label="学号">
              <Input value={userInfo?.student_id} disabled prefix={<IdcardOutlined />} />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少6位' }
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="新密码（至少6位）"
              />
            </Form.Item>

            <Form.Item
              name="confirmPassword"
              rules={[{ required: true, message: '请确认密码' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="确认密码"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
              >
                设置密码
              </Button>
            </Form.Item>

            <div className="form-footer">
              <a onClick={() => setCurrentStep(0)}>返回上一步</a>
            </div>
          </Form>
        )}
      </Card>
    </div>
  );
}

/**
 * 系统设置页面 - 管理员账户设置
 */
import { useState } from 'react';
import { Card, Form, Input, Button, Divider, Typography, App } from 'antd';
import { UserOutlined, LockOutlined, EditOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useAuthStore } from '../../store/authStore';
import { authApi } from '../../api/client';

const { Title } = Typography;

const SystemConfig = () => {
  const { message, notification } = App.useApp();
  const { currentUser, fetchCurrentUser } = useAuthStore();
  const [usernameForm] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [usernameLoading, setUsernameLoading] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);

  // 修改用户名
  const handleUpdateUsername = async (values: { username: string }) => {
    if (values.username === currentUser?.username) {
      message.info('用户名未变更');
      return;
    }

    setUsernameLoading(true);
    try {
      await authApi.updateAdminProfile(values.username);
      notification.success({
        message: '修改成功',
        description: '用户名已更新为: ' + values.username,
        icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
      });
      await fetchCurrentUser();
      usernameForm.setFieldsValue({ username: values.username });
    } catch (error: any) {
      message.error(error.message || '修改失败');
    } finally {
      setUsernameLoading(false);
    }
  };

  // 修改密码
  const handleChangePassword = async (values: { oldPassword: string; newPassword: string; confirmPassword: string }) => {
    if (values.newPassword !== values.confirmPassword) {
      message.error('两次输入的新密码不一致');
      return;
    }

    setPasswordLoading(true);
    try {
      await authApi.changeAdminPassword(values.oldPassword, values.newPassword);
      notification.success({
        message: '修改成功',
        description: '密码已成功更新，下次登录请使用新密码',
        icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
      });
      passwordForm.resetFields();
    } catch (error: any) {
      message.error(error.message || '修改失败');
    } finally {
      setPasswordLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <Title level={2}>
        <UserOutlined /> 账户设置
      </Title>

      {/* 修改用户名 */}
      <Card title={<><EditOutlined /> 修改用户名</>} style={{ marginBottom: '24px' }}>
        <Form
          form={usernameForm}
          layout="vertical"
          onFinish={handleUpdateUsername}
          initialValues={{ username: currentUser?.username }}
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 2, max: 50, message: '用户名长度应在2-50个字符之间' },
            ]}
          >
            <Input prefix={<UserOutlined />} placeholder="请输入新用户名" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={usernameLoading}>
              保存用户名
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Divider />

      {/* 修改密码 */}
      <Card title={<><LockOutlined /> 修改密码</>}>
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handleChangePassword}
        >
          <Form.Item
            name="oldPassword"
            label="当前密码"
            rules={[{ required: true, message: '请输入当前密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请输入当前密码" />
          </Form.Item>
          <Form.Item
            name="newPassword"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码长度不能少于6位' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请输入新密码" />
          </Form.Item>
          <Form.Item
            name="confirmPassword"
            label="确认新密码"
            rules={[
              { required: true, message: '请确认新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('newPassword') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请再次输入新密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={passwordLoading}>
              修改密码
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default SystemConfig;

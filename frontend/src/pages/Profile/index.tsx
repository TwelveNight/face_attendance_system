/**
 * 个人中心页面
 * 显示个人信息和修改密码
 */
import { useState } from 'react';
import { Card, Descriptions, Button, Modal, Form, Input, message, Row, Col } from 'antd';
import { UserOutlined, LockOutlined, EditOutlined } from '@ant-design/icons';
import { useAuthStore } from '../../store/authStore';
import { authApi } from '../../api/client';
import './style.css';

export default function Profile() {
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const { currentUser } = useAuthStore();

  const handleChangePassword = async () => {
    try {
      const values = await form.validateFields();
      
      if (values.newPassword !== values.confirmPassword) {
        message.error('两次密码输入不一致');
        return;
      }

      setLoading(true);
      await authApi.changeUserPassword(values.oldPassword, values.newPassword);
      message.success('密码修改成功');
      setIsPasswordModalOpen(false);
      form.resetFields();
      
      // 可以选择自动登出
      // logout();
      // navigate('/login');
    } catch (error: any) {
      message.error(error.message || '密码修改失败');
    } finally {
      setLoading(false);
    }
  };

  if (!currentUser) {
    return (
      <div className="profile-container">
        <Card>
          <p>请先登录</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="profile-container">
      <Row gutter={16}>
        <Col span={16}>
          <Card
            title={
              <span>
                <UserOutlined /> 个人信息
              </span>
            }
          >
            <Descriptions column={2} bordered>
              <Descriptions.Item label="用户名">
                {currentUser.username}
              </Descriptions.Item>
              <Descriptions.Item label="学号">
                {currentUser.student_id || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="所属部门" span={2}>
                {currentUser.department_name || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="职位">
                {currentUser.position || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="邮箱">
                {currentUser.email || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="手机号">
                {currentUser.phone || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="账号状态">
                {currentUser.is_active ? '正常' : '禁用'}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间" span={2}>
                {currentUser.created_at}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        <Col span={8}>
          <Card
            title={
              <span>
                <LockOutlined /> 安全设置
              </span>
            }
          >
            <div className="security-item">
              <div className="security-title">登录密码</div>
              <div className="security-desc">定期更换密码可以保护账号安全</div>
              <Button
                type="primary"
                icon={<EditOutlined />}
                onClick={() => setIsPasswordModalOpen(true)}
                style={{ marginTop: 12 }}
              >
                修改密码
              </Button>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 修改密码对话框 */}
      <Modal
        title="修改密码"
        open={isPasswordModalOpen}
        onOk={handleChangePassword}
        onCancel={() => {
          setIsPasswordModalOpen(false);
          form.resetFields();
        }}
        confirmLoading={loading}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 24 }}>
          <Form.Item
            label="原密码"
            name="oldPassword"
            rules={[{ required: true, message: '请输入原密码' }]}
          >
            <Input.Password placeholder="请输入原密码" />
          </Form.Item>

          <Form.Item
            label="新密码"
            name="newPassword"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6位' }
            ]}
          >
            <Input.Password placeholder="请输入新密码（至少6位）" />
          </Form.Item>

          <Form.Item
            label="确认密码"
            name="confirmPassword"
            rules={[{ required: true, message: '请确认密码' }]}
          >
            <Input.Password placeholder="请再次输入新密码" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

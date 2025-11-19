/**
 * 用户管理页面
 */
import { useEffect, useState } from 'react';
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  message,
  Popconfirm,
  Tag,
  Card,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, UserOutlined, CameraOutlined, LockOutlined } from '@ant-design/icons';
import { useAuthStore } from '../../store/authStore';
import { useUserStore } from '../../store/userStore';
import { userApi } from '../../api/client';
import type { User } from '../../types';
import dayjs from 'dayjs';
import FaceCapture from '../../components/FaceCapture';

const Users = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [isFaceCaptureOpen, setIsFaceCaptureOpen] = useState(false);
  const [pendingUserData, setPendingUserData] = useState<any>(null);
  const [capturingUserId, setCapturingUserId] = useState<number | null>(null);
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const [passwordUserId, setPasswordUserId] = useState<number | null>(null);
  const [form] = Form.useForm();
  const [passwordForm] = Form.useForm();
  
  const { userType } = useAuthStore();

  const { users, loading, fetchUsers, createUser, updateUser, deleteUser } = useUserStore();

  useEffect(() => {
    loadUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadUsers = () => {
    fetchUsers();
  };

  // 打开新增/编辑对话框
  const handleOpenModal = (user?: User) => {
    if (user) {
      setEditingUser(user);
      form.setFieldsValue({
        username: user.username,
        student_id: user.student_id,
        department_id: user.department_id,
        position: user.position,
        email: user.email,
        phone: user.phone,
      });
    } else {
      setEditingUser(null);
      form.resetFields();
    }
    setIsModalOpen(true);
  };

  // 关闭对话框
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingUser(null);
    form.resetFields();
  };

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      if (editingUser) {
        // 更新用户
        await updateUser(editingUser.id, values);
        message.success('用户更新成功');
        handleCloseModal();
        loadUsers();
      } else {
        // 创建新用户 - 先保存数据，然后打开人脸采集
        setPendingUserData(values);
        handleCloseModal();
        setIsFaceCaptureOpen(true);
      }
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  // 人脸采集完成
  const handleFaceCaptureComplete = async (images: string[]) => {
    console.log('人脸采集完成，图片数量:', images.length);
    console.log('第一张图片前100字符:', images[0]?.substring(0, 100));
    
    try {
      if (capturingUserId) {
        // 为现有用户更新人脸
        console.log('更新用户人脸，用户ID:', capturingUserId);
        const response = await userApi.updateUserFaces(capturingUserId, images);
        console.log('更新人脸响应:', response);
        message.success('人脸更新成功');
        setCapturingUserId(null);
      } else if (pendingUserData) {
        // 创建新用户并包含人脸
        console.log('创建新用户，数据:', pendingUserData);
        console.log('包含人脸图片数量:', images.length);
        
        const userData = {
          ...pendingUserData,
          face_images: images,
        };
        console.log('发送到后端的数据:', {
          username: userData.username,
          student_id: userData.student_id,
          face_images_count: userData.face_images.length,
        });
        
        const result = await createUser(userData);
        console.log('创建用户结果:', result);
        
        if (result) {
          message.success('用户创建成功，人脸已录入');
        } else {
          message.error('用户创建失败');
        }
        setPendingUserData(null);
      }
      setIsFaceCaptureOpen(false);
      loadUsers();
    } catch (error: any) {
      console.error('人脸采集错误详情:', error);
      console.error('错误响应:', error.response?.data);
      message.error(`操作失败: ${error.response?.data?.message || error.message}`);
    }
  };

  // 打开人脸采集（为现有用户）
  const handleCaptureFace = (user: User) => {
    setCapturingUserId(user.id);
    setIsFaceCaptureOpen(true);
  };

  // 删除用户
  const handleDelete = async (userId: number) => {
    try {
      await deleteUser(userId);
      message.success('用户删除成功');
      loadUsers();
    } catch {
      message.error('删除失败');
    }
  };

  // 打开设置密码对话框
  const handleOpenPasswordModal = (userId: number) => {
    setPasswordUserId(userId);
    setIsPasswordModalOpen(true);
    passwordForm.resetFields();
  };

  // 设置密码
  const handleSetPassword = async () => {
    try {
      const values = await passwordForm.validateFields();
      if (values.password !== values.confirmPassword) {
        message.error('两次密码输入不一致');
        return;
      }
      
      // 调用后端API设置密码
      await userApi.updateUser(passwordUserId!, { password: values.password });
      message.success('密码设置成功');
      setIsPasswordModalOpen(false);
      passwordForm.resetFields();
    } catch (error: any) {
      message.error(error.message || '密码设置失败');
    }
  };

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '学号',
      dataIndex: 'student_id',
      key: 'student_id',
      render: (text: string) => text || '-',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'success' : 'default'}>{active ? '活跃' : '禁用'}</Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 350,
      render: (_: any, record: User) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<LockOutlined />}
            onClick={() => handleOpenPasswordModal(record.id)}
          >
            设置密码
          </Button>
          <Button
            type="link"
            size="small"
            icon={<CameraOutlined />}
            onClick={() => handleCaptureFace(record)}
          >
            采集人脸
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          >
            编辑
          </Button>
          {userType === 'admin' && (
            <Popconfirm
              title="确定删除该用户吗？"
              description="删除后将无法恢复，且会删除该用户的人脸数据。"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" size="small" danger icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title={
          <Space>
            <UserOutlined />
            <span>用户管理</span>
          </Space>
        }
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
            添加用户
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>

      {/* 新增/编辑用户对话框 */}
      <Modal
        title={editingUser ? '编辑用户' : '添加用户'}
        open={isModalOpen}
        onOk={handleSubmit}
        onCancel={handleCloseModal}
        okText="确定"
        cancelText="取消"
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 24 }}>
          <Form.Item
            label="用户名"
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>

          <Form.Item label="学号" name="student_id">
            <Input placeholder="请输入学号（可选）" />
          </Form.Item>

          <Form.Item label="职位/班级" name="position">
            <Input placeholder="例如：计算机科学与技术2021级1班" />
          </Form.Item>

          <Form.Item label="邮箱" name="email">
            <Input placeholder="请输入邮箱" type="email" />
          </Form.Item>

          <Form.Item label="手机号" name="phone">
            <Input placeholder="请输入手机号" />
          </Form.Item>

          {!editingUser && (
            <div style={{ color: '#999', fontSize: 12, marginTop: -16, marginBottom: 16 }}>
              提示：点击确定后将打开摄像头进行人脸采集
            </div>
          )}
        </Form>
      </Modal>

      {/* 设置密码对话框 */}
      <Modal
        title="设置用户密码"
        open={isPasswordModalOpen}
        onOk={handleSetPassword}
        onCancel={() => {
          setIsPasswordModalOpen(false);
          passwordForm.resetFields();
        }}
        okText="确定"
        cancelText="取消"
      >
        <Form form={passwordForm} layout="vertical" style={{ marginTop: 24 }}>
          <Form.Item
            label="新密码"
            name="password"
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
            <Input.Password placeholder="请再次输入密码" />
          </Form.Item>

          <div style={{ color: '#999', fontSize: 12 }}>
            提示：设置密码后，用户可以使用用户名/学号和密码登录系统
          </div>
        </Form>
      </Modal>

      {/* 人脸采集对话框 */}
      <FaceCapture
        open={isFaceCaptureOpen}
        onCancel={() => {
          setIsFaceCaptureOpen(false);
          setPendingUserData(null);
          setCapturingUserId(null);
        }}
        onComplete={handleFaceCaptureComplete}
        minImages={3}
        maxImages={10}
      />
    </div>
  );
};

export default Users;

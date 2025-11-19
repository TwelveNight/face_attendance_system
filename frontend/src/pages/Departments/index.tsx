/**
 * 部门管理页面
 * 树形展示部门结构，支持CRUD操作
 */
import { useEffect, useState } from 'react';
import {
  Card, Tree, Button, Modal, Form, Input, Select, Space, message,
  Row, Col, Descriptions, Badge, Popconfirm
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, TeamOutlined,
  ApartmentOutlined
} from '@ant-design/icons';
import { departmentApi } from '../../api/client';
import type { Department } from '../../types';
import type { DataNode } from 'antd/es/tree';
import './style.css';

const { TextArea } = Input;

export default function Departments() {
  const [loading, setLoading] = useState(false);
  const [departmentTree, setDepartmentTree] = useState<Department[]>([]);
  const [selectedDepartment, setSelectedDepartment] = useState<Department | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalType, setModalType] = useState<'create' | 'edit'>('create');
  const [form] = Form.useForm();

  useEffect(() => {
    loadDepartments();
  }, []);

  const loadDepartments = async () => {
    setLoading(true);
    try {
      const response = await departmentApi.getAll(true);
      setDepartmentTree(response.data || []);
    } catch (error: any) {
      message.error(error.message || '获取部门列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 转换为Tree组件需要的数据格式
  const convertToTreeData = (departments: Department[]): DataNode[] => {
    return departments.map(dept => ({
      key: dept.id,
      title: (
        <span>
          {dept.name}
          {dept.code && <span style={{ color: '#999', marginLeft: 8 }}>({dept.code})</span>}
          <Badge
            count={dept.user_count}
            style={{ marginLeft: 8, backgroundColor: '#52c41a' }}
          />
        </span>
      ),
      children: dept.children ? convertToTreeData(dept.children) : undefined,
    }));
  };

  const handleSelect = async (selectedKeys: React.Key[]) => {
    if (selectedKeys.length === 0) {
      setSelectedDepartment(null);
      return;
    }

    const deptId = selectedKeys[0] as number;
    try {
      const response = await departmentApi.getById(deptId);
      setSelectedDepartment(response.data);
    } catch (error: any) {
      message.error(error.message || '获取部门详情失败');
    }
  };

  const handleCreate = (parentId?: number) => {
    setModalType('create');
    form.resetFields();
    if (parentId) {
      form.setFieldsValue({ parent_id: parentId });
    }
    setIsModalOpen(true);
  };

  const handleEdit = () => {
    if (!selectedDepartment) return;
    setModalType('edit');
    form.setFieldsValue({
      name: selectedDepartment.name,
      code: selectedDepartment.code,
      parent_id: selectedDepartment.parent_id,
      description: selectedDepartment.description,
      sort_order: selectedDepartment.sort_order,
    });
    setIsModalOpen(true);
  };

  const handleDelete = async () => {
    if (!selectedDepartment) return;

    try {
      await departmentApi.delete(selectedDepartment.id);
      message.success('删除成功');
      setSelectedDepartment(null);
      loadDepartments();
    } catch (error: any) {
      message.error(error.message || '删除失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (modalType === 'create') {
        await departmentApi.create(values);
        message.success('创建成功');
      } else {
        if (!selectedDepartment) return;
        await departmentApi.update(selectedDepartment.id, values);
        message.success('更新成功');
      }

      setIsModalOpen(false);
      form.resetFields();
      loadDepartments();
    } catch (error: any) {
      message.error(error.message || '操作失败');
    }
  };

  // 获取所有部门的平铺列表（用于父部门选择）
  const getFlatDepartments = (depts: Department[], result: Department[] = []): Department[] => {
    depts.forEach(dept => {
      result.push(dept);
      if (dept.children) {
        getFlatDepartments(dept.children, result);
      }
    });
    return result;
  };

  const flatDepartments = getFlatDepartments(departmentTree);

  return (
    <div className="departments-container">
      <Row gutter={16}>
        {/* 左侧：部门树 */}
        <Col span={10}>
          <Card
            title={
              <Space>
                <ApartmentOutlined />
                <span>部门结构</span>
              </Space>
            }
            extra={
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => handleCreate()}
              >
                添加根部门
              </Button>
            }
          >
            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>加载中...</div>
            ) : (
              <Tree
                showLine
                defaultExpandAll
                treeData={convertToTreeData(departmentTree)}
                onSelect={handleSelect}
              />
            )}
          </Card>
        </Col>

        {/* 右侧：部门详情 */}
        <Col span={14}>
          <Card
            title={
              <Space>
                <TeamOutlined />
                <span>部门详情</span>
              </Space>
            }
            extra={
              selectedDepartment && (
                <Space>
                  <Button
                    icon={<PlusOutlined />}
                    onClick={() => handleCreate(selectedDepartment.id)}
                  >
                    添加子部门
                  </Button>
                  <Button
                    icon={<EditOutlined />}
                    onClick={handleEdit}
                  >
                    编辑
                  </Button>
                  <Popconfirm
                    title="确定删除该部门吗？"
                    description="删除后无法恢复，且该部门下的用户将不再属于任何部门"
                    onConfirm={handleDelete}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button
                      danger
                      icon={<DeleteOutlined />}
                    >
                      删除
                    </Button>
                  </Popconfirm>
                </Space>
              )
            }
          >
            {selectedDepartment ? (
              <Descriptions column={2} bordered>
                <Descriptions.Item label="部门名称" span={2}>
                  {selectedDepartment.name}
                </Descriptions.Item>
                <Descriptions.Item label="部门代码">
                  {selectedDepartment.code || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="部门层级">
                  第 {selectedDepartment.level} 级
                </Descriptions.Item>
                <Descriptions.Item label="人员数量">
                  {selectedDepartment.user_count} 人
                </Descriptions.Item>
                <Descriptions.Item label="排序">
                  {selectedDepartment.sort_order}
                </Descriptions.Item>
                <Descriptions.Item label="负责人">
                  {selectedDepartment.manager_name || '未设置'}
                </Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Badge
                    status={selectedDepartment.is_active ? 'success' : 'error'}
                    text={selectedDepartment.is_active ? '启用' : '禁用'}
                  />
                </Descriptions.Item>
                <Descriptions.Item label="创建时间" span={2}>
                  {selectedDepartment.created_at}
                </Descriptions.Item>
                <Descriptions.Item label="部门描述" span={2}>
                  {selectedDepartment.description || '-'}
                </Descriptions.Item>
              </Descriptions>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                请从左侧选择一个部门查看详情
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 创建/编辑对话框 */}
      <Modal
        title={modalType === 'create' ? '创建部门' : '编辑部门'}
        open={isModalOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setIsModalOpen(false);
          form.resetFields();
        }}
        okText="确定"
        cancelText="取消"
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 24 }}>
          <Form.Item
            label="部门名称"
            name="name"
            rules={[{ required: true, message: '请输入部门名称' }]}
          >
            <Input placeholder="例如：计算机学院" />
          </Form.Item>

          <Form.Item
            label="部门代码"
            name="code"
            rules={[{ pattern: /^[A-Z0-9_]+$/, message: '只能包含大写字母、数字和下划线' }]}
          >
            <Input placeholder="例如：CS_DEPT" />
          </Form.Item>

          <Form.Item
            label="上级部门"
            name="parent_id"
          >
            <Select
              placeholder="选择上级部门（不选则为根部门）"
              allowClear
              showSearch
              optionFilterProp="children"
            >
              {flatDepartments
                .filter(dept => modalType === 'create' || dept.id !== selectedDepartment?.id)
                .map(dept => (
                  <Select.Option key={dept.id} value={dept.id}>
                    {'　'.repeat(dept.level - 1)}{dept.name}
                  </Select.Option>
                ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="排序"
            name="sort_order"
            initialValue={0}
          >
            <Input type="number" placeholder="数字越小越靠前" />
          </Form.Item>

          <Form.Item
            label="部门描述"
            name="description"
          >
            <TextArea rows={4} placeholder="请输入部门描述" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

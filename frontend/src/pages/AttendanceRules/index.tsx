/**
 * 考勤规则管理页面
 */
import { useEffect, useState } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  TimePicker,
  InputNumber,
  Select,
  Switch,
  message,
  Popconfirm,
  Tag,
  Checkbox,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { attendanceRuleApi, departmentApi } from '../../api/client';
import type { AttendanceRule, Department } from '../../types';
import dayjs from 'dayjs';
import './style.css';

const { TextArea } = Input;

const AttendanceRules = () => {
  const [loading, setLoading] = useState(false);
  const [rules, setRules] = useState<AttendanceRule[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<AttendanceRule | null>(null);
  const [form] = Form.useForm();

  // 工作日选项
  const weekDayOptions = [
    { label: '周一', value: '1' },
    { label: '周二', value: '2' },
    { label: '周三', value: '3' },
    { label: '周四', value: '4' },
    { label: '周五', value: '5' },
    { label: '周六', value: '6' },
    { label: '周日', value: '7' },
  ];

  useEffect(() => {
    loadRules();
    loadDepartments();
  }, []);

  const loadRules = async () => {
    setLoading(true);
    try {
      const response = await attendanceRuleApi.getAll(true); // 包含未启用的规则
      setRules(response.data || []);
    } catch (error: any) {
      message.error(error.message || '加载规则失败');
    } finally {
      setLoading(false);
    }
  };

  // 排序部门列表（树形结构）
  const sortDepartments = (depts: Department[]): Department[] => {
    // 构建父子关系映射
    const childrenMap = new Map<number, Department[]>();
    const rootDepts: Department[] = [];

    depts.forEach(dept => {
      if (dept.parent_id === null || dept.parent_id === undefined) {
        rootDepts.push(dept);
      } else {
        if (!childrenMap.has(dept.parent_id)) {
          childrenMap.set(dept.parent_id, []);
        }
        childrenMap.get(dept.parent_id)!.push(dept);
      }
    });

    // 递归排序
    const sortedList: Department[] = [];
    const addDeptAndChildren = (dept: Department, level: number) => {
      sortedList.push({ ...dept, level });
      const children = childrenMap.get(dept.id) || [];
      children.sort((a, b) => a.sort_order - b.sort_order);
      children.forEach(child => addDeptAndChildren(child, level + 1));
    };

    rootDepts.sort((a, b) => a.sort_order - b.sort_order);
    rootDepts.forEach(dept => addDeptAndChildren(dept, 0));

    return sortedList;
  };

  const loadDepartments = async () => {
    try {
      const response = await departmentApi.getAll(false);
      const sorted = sortDepartments(response.data || []);
      setDepartments(sorted);
    } catch (error: any) {
      console.error('获取部门列表失败:', error);
    }
  };

  const handleOpenModal = (rule?: AttendanceRule) => {
    if (rule) {
      setEditingRule(rule);
      form.setFieldsValue({
        name: rule.name,
        work_start_time: dayjs(rule.work_start_time, 'HH:mm:ss'),
        work_end_time: dayjs(rule.work_end_time, 'HH:mm:ss'),
        late_threshold: rule.late_threshold,
        early_threshold: rule.early_threshold,
        work_days: rule.work_days_list,
        department_id: rule.department_id,
        is_default: rule.is_default,
        is_open_mode: rule.is_open_mode,
        is_active: rule.is_active,
        description: rule.description,
        checkin_before_minutes: rule.checkin_before_minutes,
        enable_once_per_day: rule.enable_once_per_day,
      });
    } else {
      setEditingRule(null);
      form.resetFields();
      // 设置默认值
      form.setFieldsValue({
        work_start_time: dayjs('09:00:00', 'HH:mm:ss'),
        work_end_time: dayjs('18:00:00', 'HH:mm:ss'),
        late_threshold: 0,
        early_threshold: 0,
        work_days: ['1', '2', '3', '4', '5'],
        is_default: false,
        is_open_mode: false,
        is_active: true,
        checkin_before_minutes: 0,
        enable_once_per_day: true,
      });
    }
    setIsModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      const data = {
        name: values.name,
        work_start_time: values.work_start_time.format('HH:mm:ss'),
        work_end_time: values.work_end_time.format('HH:mm:ss'),
        late_threshold: values.late_threshold || 0,
        early_threshold: values.early_threshold || 0,
        work_days: values.work_days.join(','),
        department_id: values.department_id,
        is_default: values.is_default || false,
        is_open_mode: values.is_open_mode || false,
        is_active: values.is_active !== false,
        description: values.description,
        checkin_before_minutes: values.checkin_before_minutes || 0,
        enable_once_per_day: values.enable_once_per_day !== false,
      };

      if (editingRule) {
        await attendanceRuleApi.update(editingRule.id, data);
        message.success('更新成功');
      } else {
        await attendanceRuleApi.create(data);
        message.success('创建成功');
      }

      setIsModalOpen(false);
      loadRules();
    } catch (error: any) {
      message.error(error.message || '操作失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await attendanceRuleApi.delete(id);
      message.success('删除成功');
      loadRules();
    } catch (error: any) {
      message.error(error.message || '删除失败');
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '规则名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: AttendanceRule) => (
        <Space>
          {text}
          {record.is_default && <Tag color="blue">默认</Tag>}
          {record.is_open_mode && <Tag color="green">开放模式</Tag>}
        </Space>
      ),
    },
    {
      title: '上班时间',
      dataIndex: 'work_start_time',
      key: 'work_start_time',
      width: 100,
    },
    {
      title: '下班时间',
      dataIndex: 'work_end_time',
      key: 'work_end_time',
      width: 100,
    },
    {
      title: '迟到阈值',
      dataIndex: 'late_threshold',
      key: 'late_threshold',
      width: 100,
      render: (value: number) => `${value} 分钟`,
    },
    {
      title: '早退阈值',
      dataIndex: 'early_threshold',
      key: 'early_threshold',
      width: 100,
      render: (value: number) => `${value} 分钟`,
    },
    {
      title: '工作日',
      dataIndex: 'work_days_list',
      key: 'work_days',
      width: 150,
      render: (days: string[]) => {
        const dayMap: Record<string, string> = {
          '1': '一', '2': '二', '3': '三', '4': '四',
          '5': '五', '6': '六', '7': '日',
        };
        return days.map(d => `周${dayMap[d]}`).join(', ');
      },
    },
    {
      title: '关联部门',
      dataIndex: 'department_name',
      key: 'department_name',
      render: (text: string) => text || <Tag>全局</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active: boolean) => (
        <Tag color={active ? 'success' : 'default'}>
          {active ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: AttendanceRule) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这条规则吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              disabled={record.is_default}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="attendance-rules-container">
      <Card
        title={
          <Space>
            <ClockCircleOutlined />
            <span>考勤规则管理</span>
          </Space>
        }
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
            添加规则
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={rules}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条规则`,
          }}
        />
      </Card>

      {/* 新增/编辑对话框 */}
      <Modal
        title={editingRule ? '编辑考勤规则' : '新增考勤规则'}
        open={isModalOpen}
        onOk={handleSubmit}
        onCancel={() => setIsModalOpen(false)}
        width={600}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="规则名称"
            name="name"
            rules={[{ required: true, message: '请输入规则名称' }]}
          >
            <Input placeholder="例如：标准工作日规则" />
          </Form.Item>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item
              label="上班时间"
              name="work_start_time"
              rules={[{ required: true, message: '请选择上班时间' }]}
            >
              <TimePicker format="HH:mm:ss" />
            </Form.Item>

            <Form.Item
              label="下班时间"
              name="work_end_time"
              rules={[{ required: true, message: '请选择下班时间' }]}
            >
              <TimePicker format="HH:mm:ss" />
            </Form.Item>
          </Space>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item label="迟到阈值（分钟）" name="late_threshold">
              <InputNumber min={0} max={120} placeholder="0" />
            </Form.Item>

            <Form.Item label="早退阈值（分钟）" name="early_threshold">
              <InputNumber min={0} max={120} placeholder="0" />
            </Form.Item>
          </Space>

          <Form.Item
            label="工作日"
            name="work_days"
            rules={[{ required: true, message: '请选择工作日' }]}
          >
            <Checkbox.Group options={weekDayOptions} />
          </Form.Item>

          <Form.Item label="关联部门" name="department_id">
            <Select
              placeholder="不选择则为全局规则"
              allowClear
              showSearch
              optionFilterProp="children"
            >
              {departments.map(dept => {
                const indent = '　'.repeat(dept.level);
                const prefix = dept.level > 0 ? '├─ ' : '';
                return (
                  <Select.Option key={dept.id} value={dept.id}>
                    {indent}{prefix}{dept.name}
                  </Select.Option>
                );
              })}
            </Select>
          </Form.Item>

          <Form.Item label="描述" name="description">
            <TextArea rows={3} placeholder="规则说明（可选）" />
          </Form.Item>

          <Space size="large">
            <Form.Item label="默认规则" name="is_default" valuePropName="checked">
              <Switch />
            </Form.Item>

            <Form.Item label="开放模式" name="is_open_mode" valuePropName="checked">
              <Switch />
            </Form.Item>

            <Form.Item label="启用" name="is_active" valuePropName="checked">
              <Switch />
            </Form.Item>
          </Space>

          <div style={{ color: '#999', fontSize: 12, marginTop: -10, marginBottom: 16 }}>
            <p>• 默认规则：未设置专属规则的部门将使用此规则</p>
            <p>• 开放模式：任何时间打卡都视为正常，不判断迟到早退</p>
          </div>

          <div style={{ 
            background: '#f5f5f5', 
            padding: 16, 
            borderRadius: 8,
            marginTop: 16 
          }}>
            <div style={{ fontWeight: 'bold', marginBottom: 12, color: '#1890ff' }}>
              ⏰ 打卡时间限制（可选）
            </div>

            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <Form.Item label="每天只能打卡一次" name="enable_once_per_day" valuePropName="checked">
                <Switch />
              </Form.Item>

              <Form.Item 
                label="上班可提前打卡（分钟）" 
                name="checkin_before_minutes"
                tooltip="设置为0表示不限制最早打卡时间"
              >
                <InputNumber min={0} max={180} placeholder="0" style={{ width: 200 }} />
              </Form.Item>
            </Space>

            <div style={{ color: '#999', fontSize: 12, marginTop: 8 }}>
              <p>• 每天只能打卡一次：启用后，上班打卡一次、下班打卡一次（共两次）</p>
              <p>• 上班可提前打卡：限制用户最早可以在上班时间前多久打卡</p>
              <p>  - 设置为0：不限制最早打卡时间</p>
              <p>  - 设置为30：上班9:00，最早8:30可以打卡</p>
              <p>• 迟到/早退判断：由"迟到阈值"和"早退阈值"控制</p>
              <p>• 打卡类型自动判断：根据上下班时间中点自动区分上班/下班打卡</p>
            </div>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default AttendanceRules;

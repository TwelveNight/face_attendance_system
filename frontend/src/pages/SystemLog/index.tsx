/**
 * 系统日志管理页面
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  DatePicker,
  Select,
  Space,
  Tag,
  Row,
  Col,
  Statistic,
  Tabs,
  Input,
  Tooltip,
  App
} from 'antd';
import {
  ReloadOutlined,
  DeleteOutlined,
  LoginOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import { logApi } from '../../api/client';
import dayjs from 'dayjs';
import styles from './index.module.css';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Search } = Input;
const { TabPane } = Tabs;

interface LoginLog {
  id: number;
  admin_id: number | null;
  username: string;
  login_time: string;
  login_ip: string;
  user_agent: string;
  login_status: string;
  failure_reason: string | null;
}

interface SystemLog {
  id: number;
  event_type: string;
  message: string;
  level: string;
  timestamp: string;
  user_id: number | null;
  admin_id: number | null;
  module: string | null;
  ip_address: string | null;
  extra_data: string | null;
}

interface LoginStats {
  total_logins: number;
  success_logins: number;
  failed_logins: number;
  success_rate: number;
  daily_stats: { date: string; count: number }[];
}

interface SystemStats {
  level_stats: {
    debug: number;
    info: number;
    warning: number;
    error: number;
    critical: number;
  };
  event_stats: { event_type: string; count: number }[];
  module_stats: { module: string; count: number }[];
}

const SystemLogPage: React.FC = () => {
  const { modal, message } = App.useApp();
  const [activeTab, setActiveTab] = useState('system');
  const [systemLogs, setSystemLogs] = useState<SystemLog[]>([]);
  const [loginLogs, setLoginLogs] = useState<LoginLog[]>([]);
  const [loginStats, setLoginStats] = useState<LoginStats | null>(null);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [eventType, setEventType] = useState<string>('');
  const [level, setLevel] = useState<string>('');
  const [module, setModule] = useState<string>('');
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });

  // 加载系统日志
  const loadSystemLogs = async () => {
    setLoading(true);
    try {
      const params: any = {
        page: pagination.current,
        size: pagination.pageSize
      };
      
      if (dateRange) {
        params.start_date = dateRange[0].format('YYYY-MM-DD');
        params.end_date = dateRange[1].format('YYYY-MM-DD');
      }
      if (eventType) params.event_type = eventType;
      if (level) params.level = level;
      if (module) params.module = module;
      
      const response: any = await logApi.getSystemLogs(params);
      setSystemLogs(response.data?.logs || []);
      setPagination(prev => ({
        ...prev,
        total: response.data?.total || 0
      }));
    } catch {
      message.error('加载系统日志失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载登录日志
  const loadLoginLogs = async () => {
    setLoading(true);
    try {
      const params: any = {
        page: pagination.current,
        size: pagination.pageSize
      };
      
      if (dateRange) {
        params.start_date = dateRange[0].format('YYYY-MM-DD');
        params.end_date = dateRange[1].format('YYYY-MM-DD');
      }
      
      const response: any = await logApi.getLoginLogs(params);
      setLoginLogs(response.data?.logs || []);
      setPagination(prev => ({
        ...prev,
        total: response.data?.total || 0
      }));
    } catch {
      message.error('加载登录日志失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载登录统计
  const loadLoginStats = async () => {
    try {
      const response: any = await logApi.getLoginStatistics();
      setLoginStats(response.data);
    } catch {
      console.error('加载登录统计失败');
    }
  };

  // 加载系统日志统计
  const loadSystemStats = async () => {
    try {
      const response: any = await logApi.getSystemLogStatistics();
      setSystemStats(response.data);
    } catch {
      console.error('加载系统日志统计失败');
    }
  };

  // 初始化加载数据
  useEffect(() => {
    if (activeTab === 'system') {
      loadSystemLogs();
      loadSystemStats();
    } else if (activeTab === 'login') {
      loadLoginLogs();
      loadLoginStats();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  // 筛选条件变化时重新加载
  useEffect(() => {
    if (activeTab === 'system') {
      loadSystemLogs();
    } else if (activeTab === 'login') {
      loadLoginLogs();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pagination.current, dateRange, eventType, level, module]);

  // 清理旧日志
  const handleCleanup = () => {
    modal.confirm({
      title: '清理日志',
      content: '确定要清理90天前的所有日志吗？此操作不可恢复。',
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          const response: any = await logApi.cleanupLogs(90);
          message.success(response.data?.message || '清理成功');
          loadSystemLogs();
          loadLoginLogs();
        } catch {
          message.error('清理失败');
        }
      }
    });
  };

  // 删除系统日志
  const handleDeleteSystemLog = (logId: number) => {
    modal.confirm({
      title: '删除确认',
      content: '确定要删除这条系统日志吗？',
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          const response: any = await logApi.deleteSystemLog(logId);
          if (response.success) {
            message.success('删除成功');
            loadSystemLogs();
            loadSystemStats();
          } else {
            message.error(response.message || '删除失败');
          }
        } catch {
          message.error('删除失败');
        }
      }
    });
  };

  // 删除登录日志
  const handleDeleteLoginLog = (logId: number) => {
    modal.confirm({
      title: '删除确认',
      content: '确定要删除这条登录日志吗？',
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          const response: any = await logApi.deleteLoginLog(logId);
          if (response.success) {
            message.success('删除成功');
            loadLoginLogs();
            loadLoginStats();
          } else {
            message.error(response.message || '删除失败');
          }
        } catch {
          message.error('删除失败');
        }
      }
    });
  };

  // 获取日志级别颜色
  const getLevelColor = (level: string) => {
    const colors: { [key: string]: string } = {
      DEBUG: 'default',
      INFO: 'blue',
      WARNING: 'orange',
      ERROR: 'red',
      CRITICAL: 'red'
    };
    return colors[level] || 'default';
  };

  // 获取登录状态颜色
  const getStatusColor = (status: string) => {
    return status === 'success' ? 'green' : 'red';
  };

  // 系统日志表格列
  const systemLogColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (timestamp: string) => dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 100,
      render: (level: string) => <Tag color={getLevelColor(level)}>{level}</Tag>
    },
    {
      title: '事件类型',
      dataIndex: 'event_type',
      key: 'event_type',
      width: 150
    },
    {
      title: '模块',
      dataIndex: 'module',
      key: 'module',
      width: 120,
      render: (module: string) => module || '-'
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
      render: (message: string) => (
        <Tooltip title={message}>
          <span>{message}</span>
        </Tooltip>
      )
    },
    {
      title: 'IP地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 120,
      render: (ip: string) => ip || '-'
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: SystemLog) => (
        <Button
          type="link"
          danger
          size="small"
          onClick={() => handleDeleteSystemLog(record.id)}
        >
          删除
        </Button>
      )
    }
  ];

  // 登录日志表格列
  const loginLogColumns = [
    {
      title: '时间',
      dataIndex: 'login_time',
      key: 'login_time',
      width: 180,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss')
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 120
    },
    {
      title: '状态',
      dataIndex: 'login_status',
      key: 'login_status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {status === 'success' ? '成功' : '失败'}
        </Tag>
      )
    },
    {
      title: 'IP地址',
      dataIndex: 'login_ip',
      key: 'login_ip',
      width: 120
    },
    {
      title: '失败原因',
      dataIndex: 'failure_reason',
      key: 'failure_reason',
      width: 150,
      render: (reason: string) => reason || '-'
    },
    {
      title: '浏览器信息',
      dataIndex: 'user_agent',
      key: 'user_agent',
      ellipsis: true,
      render: (agent: string) => (
        <Tooltip title={agent}>
          <span>{agent}</span>
        </Tooltip>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: LoginLog) => (
        <Button
          type="link"
          danger
          size="small"
          onClick={() => handleDeleteLoginLog(record.id)}
        >
          删除
        </Button>
      )
    }
  ];

  return (
    <div className={styles.container}>
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="系统日志" key="system">
            {/* 统计卡片 */}
            {systemStats && (
              <Row gutter={16} className={styles.statsRow}>
                <Col span={6}>
                  <Card>
                    <Statistic
                      title="INFO日志"
                      value={systemStats.level_stats.info}
                      prefix={<InfoCircleOutlined />}
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card>
                    <Statistic
                      title="WARNING日志"
                      value={systemStats.level_stats.warning}
                      prefix={<WarningOutlined />}
                      valueStyle={{ color: '#faad14' }}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card>
                    <Statistic
                      title="ERROR日志"
                      value={systemStats.level_stats.error}
                      prefix={<CloseCircleOutlined />}
                      valueStyle={{ color: '#ff4d4f' }}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card>
                    <Statistic
                      title="CRITICAL日志"
                      value={systemStats.level_stats.critical}
                      prefix={<CloseCircleOutlined />}
                      valueStyle={{ color: '#cf1322' }}
                    />
                  </Card>
                </Col>
              </Row>
            )}
            
            {/* 筛选条件 */}
            <Row gutter={16} className={styles.filterRow}>
              <Col span={6}>
                <RangePicker
                  style={{ width: '100%' }}
                  onChange={(dates) => setDateRange(dates as any)}
                />
              </Col>
              <Col span={4}>
                <Select
                  style={{ width: '100%' }}
                  placeholder="日志级别"
                  allowClear
                  onChange={setLevel}
                >
                  <Option value="DEBUG">DEBUG</Option>
                  <Option value="INFO">INFO</Option>
                  <Option value="WARNING">WARNING</Option>
                  <Option value="ERROR">ERROR</Option>
                  <Option value="CRITICAL">CRITICAL</Option>
                </Select>
              </Col>
              <Col span={4}>
                <Input
                  placeholder="事件类型"
                  value={eventType}
                  onChange={(e) => setEventType(e.target.value)}
                  allowClear
                />
              </Col>
              <Col span={4}>
                <Input
                  placeholder="模块"
                  value={module}
                  onChange={(e) => setModule(e.target.value)}
                  allowClear
                />
              </Col>
              <Col span={6}>
                <Space>
                  <Button
                    type="primary"
                    icon={<ReloadOutlined />}
                    onClick={loadSystemLogs}
                  >
                    刷新
                  </Button>
                  <Button
                    danger
                    icon={<DeleteOutlined />}
                    onClick={handleCleanup}
                  >
                    清理旧日志
                  </Button>
                </Space>
              </Col>
            </Row>
            
            {/* 日志表格 */}
            <Table
              columns={systemLogColumns}
              dataSource={systemLogs}
              rowKey="id"
              loading={loading}
              pagination={{
                ...pagination,
                onChange: (page, pageSize) => {
                  setPagination({
                    ...pagination,
                    current: page,
                    pageSize: pageSize || 20
                  });
                }
              }}
            />
          </TabPane>
          
          <TabPane tab="登录日志" key="login">
            {/* 统计卡片 */}
            {loginStats && (
              <Row gutter={16} className={styles.statsRow}>
                <Col span={6}>
                  <Card>
                    <Statistic
                      title="总登录次数"
                      value={loginStats.total_logins}
                      prefix={<LoginOutlined />}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card>
                    <Statistic
                      title="成功次数"
                      value={loginStats.success_logins}
                      prefix={<CheckCircleOutlined />}
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card>
                    <Statistic
                      title="失败次数"
                      value={loginStats.failed_logins}
                      prefix={<CloseCircleOutlined />}
                      valueStyle={{ color: '#ff4d4f' }}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card>
                    <Statistic
                      title="成功率"
                      value={loginStats.success_rate}
                      suffix="%"
                      precision={2}
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Card>
                </Col>
              </Row>
            )}
            
            {/* 筛选条件 */}
            <Row gutter={16} className={styles.filterRow}>
              <Col span={8}>
                <RangePicker
                  style={{ width: '100%' }}
                  onChange={(dates) => setDateRange(dates as any)}
                />
              </Col>
              <Col span={6}>
                <Search
                  placeholder="搜索用户名"
                  style={{ width: '100%' }}
                />
              </Col>
              <Col span={4}>
                <Button
                  type="primary"
                  icon={<ReloadOutlined />}
                  onClick={loadLoginLogs}
                >
                  刷新
                </Button>
              </Col>
            </Row>
            
            {/* 登录日志表格 */}
            <Table
              columns={loginLogColumns}
              dataSource={loginLogs}
              rowKey="id"
              loading={loading}
              pagination={{
                ...pagination,
                onChange: (page, pageSize) => {
                  setPagination({
                    ...pagination,
                    current: page,
                    pageSize: pageSize || 20
                  });
                }
              }}
            />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default SystemLogPage;

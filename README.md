# 人脸识别考勤系统

基于深度学习的智能考勤管理系统，采用 YOLO + FaceNet 实现高精度人脸识别打卡。

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- MySQL 5.7+
- CUDA 11.x（可选，用于GPU加速）

### 后端启动

```bash
cd backend
pip install -r requirements.txt
pip install apscheduler
python run.py
```

### 前端启动

```bash
cd frontend
npm install
npm start
```

### 访问地址
- 前端: http://localhost:3000
- 后端API: http://localhost:5000

### 默认账号
- 管理员: `admin` / `admin123`
- 用户: 需要先注册

## 📊 数据库结构

系统使用7张表：

1. **user** - 用户表
2. **admin** - 管理员表
3. **department** - 部门表（树形结构）
4. **attendance_rule** - 考勤规则表
5. **attendance** - 考勤记录表
6. **admin_login_log** - 管理员登录日志表
7. **system_log** - 系统日志表

详细的数据库结构请参考项目根目录下的SQL脚本。

## ✨ 核心功能

### 1. 人脸识别打卡
- YOLO v8 人脸检测
- FaceNet 人脸识别
- 自动判断上班/下班打卡
- 实时预览识别结果

### 2. 考勤规则管理
- 灵活的规则配置
- 部门规则和默认规则
- 开放模式（测试用）
- 打卡时间窗口限制

### 3. 自动缺勤记录
- 定时任务（每天23:00）
- 区分上班/下班缺勤
- 工作日智能判断

### 4. 统计分析
- 16个统计指标
- 多维度筛选
- 可视化展示

### 5. 报表导出
- 个人月报导出
- 全员考勤导出
- 统计报表导出
- CSV格式（Excel兼容）

### 6. 权限管理
- 双端登录（管理员/用户）
- JWT Token认证
- 细粒度权限控制

### 7. 部门管理
- 树形组织架构
- 多级部门嵌套
- 部门负责人设置

## 🏗️ 技术栈

### 后端
- Python 3.8+
- Flask 2.x
- SQLAlchemy 1.4+
- APScheduler 3.x
- PyTorch 2.x
- YOLO v8
- FaceNet
- OpenCV 4.x

### 前端
- React 18
- TypeScript 4.x
- Ant Design 5.x
- Zustand
- Axios
- Day.js

### 数据库
- MySQL 5.7+
- InnoDB引擎
- UTF8MB4字符集

## 📁 项目结构

```
face_attendance_system/
├── backend/                 # 后端代码
│   ├── api/                # API路由
│   ├── services/           # 业务逻辑
│   ├── database/           # 数据访问
│   ├── models/             # AI模型
│   ├── utils/              # 工具函数
│   ├── config/             # 配置
│   └── saved_models/       # 模型文件
├── frontend/                # 前端代码
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   ├── components/     # 公共组件
│   │   ├── api/            # API客户端
│   │   ├── store/          # 状态管理
│   │   └── types/          # 类型定义
│   └── public/             # 静态资源
└── docs/                    # 文档
    ├── PROJECT_SUMMARY.md  # 项目总结（详细）
    └── README.md           # 本文档
```

## 📖 文档

- [项目总结文档](./PROJECT_SUMMARY.md) - 完整的项目说明和技术文档
- [功能完成总结](./PROJECT_COMPLETION_SUMMARY.md) - 功能实现清单
- [打卡限制说明](./CHECKIN_RESTRICTIONS.md) - 打卡规则详解

## 🎯 使用指南

### 管理员操作
1. 登录管理员账号
2. 创建部门结构
3. 配置考勤规则
4. 管理用户账号
5. 查看统计分析
6. 导出考勤报表

### 用户操作
1. 注册账号并采集人脸
2. 登录用户账号
3. 进行人脸打卡
4. 查看个人考勤
5. 导出个人月报

## 🔧 配置说明

### 后端配置
编辑 `backend/config/settings.py`:
```python
# 数据库配置
DATABASE_URI = 'mysql+pymysql://root:password@localhost/face_attendance'

# JWT配置
SECRET_KEY = 'your-secret-key'

# CORS配置
CORS_ORIGINS = ['http://localhost:3000']
```

### 前端配置
编辑 `frontend/src/api/client.ts`:
```typescript
const API_BASE_URL = 'http://localhost:5000';
```

## 🎓 项目特色

1. **智能打卡** - 自动判断上班/下班，无需手动选择
2. **灵活规则** - 支持部门规则和默认规则，可配置打卡时间窗口
3. **自动缺勤** - 定时任务自动检测并记录缺勤
4. **全面统计** - 16个统计指标，多维度数据分析
5. **完善导出** - 3个导出入口，CSV格式报表
6. **高性能** - GPU加速，实时人脸识别
7. **现代化** - React + TypeScript，美观易用

## 📊 项目数据

- **代码量**: ~10000行
- **功能模块**: 7个
- **页面数量**: 12个
- **API接口**: 45+个
- **数据表**: 7个
- **导出功能**: 3个

## 📝 版本信息

- **当前版本**: v3.0
- **发布日期**: 2025-11-19
- **项目状态**: ✅ 已完成

## 📞 联系方式

如有问题，请查看 [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) 中的常见问题部分。

---

**项目名称**: 基于深度学习的人脸识别考勤系统  
**开发时间**: 2025年11月  
**技术栈**: Python + Flask + React + TypeScript + FaceNet + YOLO  
**项目状态**: ✅ 已完成

# FaceNet 人脸识别训练

使用facenet-pytorch (PyTorch版FaceNet) 进行人脸识别训练。

## 训练流程

### 1. 采集人脸数据

```bash
# 交互模式(推荐) - 可连续采集多个用户
python collect_faces.py --interactive

# 或单用户模式
python collect_faces.py --user zhangsan --num 10
```

采集时注意:
- 保持不同角度(正面、侧面、仰头、低头)
- 不同表情(微笑、严肃、惊讶)
- 不同光照条件
- 系统会自动间隔采集,避免图像过于相似

数据将保存到:
```
dataset/
├── user1/
│   ├── user1_1.jpg
│   ├── user1_2.jpg
│   └── ...
├── user2/
│   └── ...
```

**或者从旧项目复制数据:**
```bash
# 复制已有数据集
cp -r ../../../emotion_attendance_system/dataset/* ./dataset/
```

### 2. 训练模型

```bash
python train.py
```

训练过程:
1. 使用YOLO检测每张图像中的人脸
2. 使用FaceNet提取512维嵌入向量
3. 训练SVM分类器进行人脸识别
4. 评估模型并输出准确率

模型保存到:
- `../../saved_models/facenet_embeddings.npz` - 人脸嵌入数据
- `../../saved_models/facenet_svm.pkl` - SVM分类器

### 3. 测试模型

```bash
python test.py
```

实时测试人脸识别效果。

## 技术细节

### FaceNet模型

- 使用 `facenet-pytorch` 库
- 预训练权重: VGGFace2
- 输出: 512维嵌入向量
- 人脸尺寸: 160x160

### 人脸检测

- 使用YOLO (替代MTCNN)
- 统一的检测接口
- 支持边距调整

### 分类器

- SVM with linear kernel
- 支持概率输出
- 多类分类

## 注意事项

1. **数据质量**: 每个用户至少10张不同角度的清晰人脸图像
2. **光照条件**: 采集时保持良好光照,避免过暗或过曝
3. **数据平衡**: 尽量保证每个用户的图像数量相近
4. **GPU加速**: 训练和推理都支持CUDA加速

## 性能优化

- 预训练FaceNet模型保证高准确率
- SVM训练速度快
- 推理时间: ~50ms/张(GPU)

## 故障排除

### 采集时检测不到人脸
- 检查YOLO模型是否正确加载
- 调整光照条件
- 确保人脸清晰可见

### 训练准确率低
- 增加每个用户的图像数量
- 提高图像质量
- 检查数据集是否有错误标注

### 推理速度慢
- 使用GPU加速
- 减少置信度阈值

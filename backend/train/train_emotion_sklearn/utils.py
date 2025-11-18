"""
MediaPipe面部特征提取工具
提取468个面部关键点并转换为特征向量
"""
import cv2
import numpy as np
import mediapipe as mp
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class FacialLandmarkExtractor:
    """面部特征点提取器(使用MediaPipe)"""
    
    def __init__(
        self,
        static_image_mode: bool = True,
        max_num_faces: int = 1,
        min_detection_confidence: float = 0.5
    ):
        """
        初始化MediaPipe面部网格检测器
        
        Args:
            static_image_mode: 静态图像模式
            max_num_faces: 最大检测人脸数
            min_detection_confidence: 最小检测置信度
        """
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=static_image_mode,
            max_num_faces=max_num_faces,
            min_detection_confidence=min_detection_confidence
        )
    
    def extract_landmarks(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        提取面部关键点
        
        Args:
            image: BGR图像
        
        Returns:
            468个关键点坐标 (x, y, z) -> shape: (468, 3) -> flatten to (1404,)
            如果检测失败返回None
        """
        # 转RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 检测
        results = self.face_mesh.process(image_rgb)
        
        if not results.multi_face_landmarks:
            return None
        
        # 获取第一个人脸的关键点
        face_landmarks = results.multi_face_landmarks[0]
        
        # 提取坐标
        landmarks = []
        for landmark in face_landmarks.landmark:
            landmarks.append([landmark.x, landmark.y, landmark.z])
        
        # 转换为numpy数组并展平
        landmarks_array = np.array(landmarks, dtype=np.float32)
        landmarks_flat = landmarks_array.flatten()  # (468, 3) -> (1404,)
        
        return landmarks_flat
    
    def extract_normalized_landmarks(
        self,
        image: np.ndarray
    ) -> Optional[np.ndarray]:
        """
        提取归一化的面部关键点
        
        归一化方法:
        1. 提取所有关键点
        2. 计算中心点
        3. 所有点减去中心点(平移归一化)
        4. 计算最大距离并缩放到[-1, 1]
        
        Returns:
            归一化后的关键点 (1404,)
        """
        landmarks = self.extract_landmarks(image)
        
        if landmarks is None:
            return None
        
        # reshape回(468, 3)
        landmarks_3d = landmarks.reshape(468, 3)
        
        # 计算中心点
        center = np.mean(landmarks_3d, axis=0)
        
        # 平移到原点
        landmarks_centered = landmarks_3d - center
        
        # 计算最大距离
        max_dist = np.max(np.abs(landmarks_centered))
        
        # 缩放到[-1, 1]
        if max_dist > 0:
            landmarks_normalized = landmarks_centered / max_dist
        else:
            landmarks_normalized = landmarks_centered
        
        # 展平
        return landmarks_normalized.flatten()
    
    def extract_geometric_features(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        提取几何特征(距离和角度)
        
        这种方法提取更紧凑的特征向量,包括:
        - 关键点之间的距离
        - 特定三角形的角度
        - 面部区域的面积比
        
        Returns:
            几何特征向量 (维度较小,约100-200维)
        """
        landmarks = self.extract_landmarks(image)
        
        if landmarks is None:
            return None
        
        landmarks_3d = landmarks.reshape(468, 3)
        
        features = []
        
        # 1. 选择关键点对,计算距离
        # 例如: 眼睛宽度, 嘴巴宽度, 眉毛高度等
        key_pairs = [
            (33, 133),   # 左眼宽度
            (362, 263),  # 右眼宽度
            (61, 291),   # 嘴巴宽度
            (0, 17),     # 脸部中线
            # 可以添加更多关键点对
        ]
        
        for p1, p2 in key_pairs:
            dist = np.linalg.norm(landmarks_3d[p1] - landmarks_3d[p2])
            features.append(dist)
        
        # 2. 归一化(使用整个人脸的尺度)
        face_scale = np.linalg.norm(
            landmarks_3d[0] - landmarks_3d[17]  # 鼻尖到额头
        )
        
        if face_scale > 0:
            features = [f / face_scale for f in features]
        
        # 目前只实现了简单的距离特征
        # 可以扩展为包含角度、面积等
        
        return np.array(features, dtype=np.float32)
    
    def visualize_landmarks(
        self,
        image: np.ndarray,
        landmarks: np.ndarray = None
    ) -> np.ndarray:
        """
        可视化面部关键点
        
        Args:
            image: 原始图像
            landmarks: 关键点 (1404,), 如果为None则重新检测
        
        Returns:
            绘制了关键点的图像
        """
        if landmarks is None:
            landmarks = self.extract_landmarks(image)
            if landmarks is None:
                return image
        
        landmarks_3d = landmarks.reshape(468, 3)
        
        vis_image = image.copy()
        h, w = image.shape[:2]
        
        # 绘制关键点
        for landmark in landmarks_3d:
            x = int(landmark[0] * w)
            y = int(landmark[1] * h)
            cv2.circle(vis_image, (x, y), 1, (0, 255, 0), -1)
        
        return vis_image
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()


def preprocess_image_for_mediapipe(image: np.ndarray) -> np.ndarray:
    """
    预处理图像用于MediaPipe检测
    
    Args:
        image: BGR图像
    
    Returns:
        预处理后的图像
    """
    # MediaPipe工作良好,通常不需要特殊预处理
    # 但可以添加一些增强
    
    # 确保图像不是太小
    h, w = image.shape[:2]
    min_size = 200
    
    if h < min_size or w < min_size:
        scale = max(min_size / h, min_size / w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        image = cv2.resize(image, (new_w, new_h))
    
    return image


if __name__ == '__main__':
    # 测试特征提取器
    logging.basicConfig(level=logging.INFO)
    
    extractor = FacialLandmarkExtractor()
    
    # 创建测试图像
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    landmarks = extractor.extract_landmarks(test_image)
    
    if landmarks is not None:
        print(f"提取到关键点形状: {landmarks.shape}")
        print(f"特征维度: {len(landmarks)}")
    else:
        print("未检测到人脸(这是正常的,因为是空白图像)")
    
    print("\n特征提取器初始化成功!")

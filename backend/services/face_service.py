"""
人脸服务
处理人脸检测和识别的业务逻辑
"""
import numpy as np
import cv2
from typing import Optional, Tuple, List, Dict
from pathlib import Path

from models.model_manager import model_manager
from config.settings import Config


class FaceService:
    """人脸检测和识别服务"""
    
    def __init__(self):
        """初始化人脸服务"""
        # 确保模型已加载
        if not model_manager.is_loaded():
            model_manager.load_models()
        
        self.detector = model_manager.yolo_detector
        self.recognizer = model_manager.facenet_recognizer
    
    def detect_and_recognize(self, image: np.ndarray) -> List[Dict]:
        """
        检测并识别图像中的所有人脸
        
        Args:
            image: 输入图像 (BGR格式)
            
        Returns:
            List of {
                'bbox': (x1, y1, x2, y2),
                'user_id': int or None,
                'confidence': float,
                'detection_confidence': float
            }
        """
        results = []
        
        # 检测人脸
        faces = self.detector.detect_faces(image, return_confidence=True)
        
        for face in faces:
            x1, y1, x2, y2, det_conf = face
            
            # 裁剪人脸
            face_img = self.detector.crop_face(image, face)
            
            if face_img is not None and face_img.size > 0:
                # 识别
                user_id, rec_conf = self.recognizer.recognize(face_img)
                
                results.append({
                    'bbox': (x1, y1, x2, y2),
                    'user_id': user_id,
                    'confidence': rec_conf,
                    'detection_confidence': det_conf
                })
        
        return results
    
    def detect_largest_face_and_recognize(self, image: np.ndarray) -> Optional[Dict]:
        """
        检测最大的人脸并识别
        
        Args:
            image: 输入图像
            
        Returns:
            {
                'bbox': (x1, y1, x2, y2),
                'user_id': int or None,
                'confidence': float,
                'detection_confidence': float
            } or None
        """
        # 检测最大人脸
        face = self.detector.detect_largest_face(image)
        
        if face is None:
            return None
        
        x1, y1, x2, y2, det_conf = face
        
        # 裁剪并识别
        face_img = self.detector.crop_face(image, face)
        
        if face_img is None or face_img.size == 0:
            return None
        
        user_id, rec_conf = self.recognizer.recognize(face_img)
        
        return {
            'bbox': (x1, y1, x2, y2),
            'user_id': user_id,
            'confidence': rec_conf,
            'detection_confidence': det_conf
        }
    
    def register_user_faces(self, user_id: int, images: List[np.ndarray]) -> bool:
        """
        注册用户人脸
        
        Args:
            user_id: 用户ID
            images: 人脸图像列表
            
        Returns:
            是否成功
        """
        try:
            # 从每张图像中提取人脸
            face_images = []
            
            for image in images:
                # 检测最大人脸
                face = self.detector.detect_largest_face(image)
                
                if face is not None:
                    # 裁剪人脸
                    face_img = self.detector.crop_face(image, face)
                    if face_img is not None and face_img.size > 0:
                        face_images.append(face_img)
            
            if len(face_images) == 0:
                print(f"未检测到人脸")
                return False
            
            # 添加到识别器
            self.recognizer.add_user(user_id, face_images)
            
            print(f"✓ 用户 {user_id} 注册成功 ({len(face_images)} 张人脸)")
            return True
        
        except Exception as e:
            print(f"✗ 用户注册失败: {e}")
            return False
    
    def update_user_faces(self, user_id: int, images: List[np.ndarray]) -> bool:
        """
        更新用户人脸
        
        Args:
            user_id: 用户ID
            images: 新的人脸图像列表
            
        Returns:
            是否成功
        """
        try:
            # 先删除旧数据
            self.recognizer.remove_user(user_id)
            
            # 重新注册
            return self.register_user_faces(user_id, images)
        
        except Exception as e:
            print(f"✗ 更新用户人脸失败: {e}")
            return False
    
    def remove_user_faces(self, user_id: int) -> bool:
        """
        删除用户人脸数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        try:
            self.recognizer.remove_user(user_id)
            print(f"✓ 用户 {user_id} 人脸数据已删除")
            return True
        
        except Exception as e:
            print(f"✗ 删除用户人脸数据失败: {e}")
            return False
    
    def collect_faces_from_video(self, video_source: int = 0, 
                                 count: int = None) -> List[np.ndarray]:
        """
        从视频流采集人脸
        
        Args:
            video_source: 视频源(摄像头索引或视频文件路径)
            count: 采集数量
            
        Returns:
            采集到的人脸图像列表
        """
        if count is None:
            count = Config.REGISTER_FACE_COUNT
        
        cap = cv2.VideoCapture(video_source)
        collected_faces = []
        
        print(f"开始采集人脸 (目标: {count} 张)")
        print("按 'c' 采集, 'q' 退出")
        
        while len(collected_faces) < count:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 检测人脸
            face = self.detector.detect_largest_face(frame)
            
            display = frame.copy()
            
            if face is not None:
                x1, y1, x2, y2, conf = face
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(display, f"Conf: {conf:.2f}", (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # 显示进度
            progress = f"Collected: {len(collected_faces)}/{count}"
            cv2.putText(display, progress, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            cv2.imshow('Face Collection', display)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('c') and face is not None:
                # 采集人脸
                face_img = self.detector.crop_face(frame, face)
                if face_img is not None:
                    collected_faces.append(face_img)
                    print(f"  采集 {len(collected_faces)}/{count}")
            
            elif key == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        print(f"✓ 采集完成: {len(collected_faces)} 张人脸")
        return collected_faces
    
    def draw_results(self, image: np.ndarray, results: List[Dict]) -> np.ndarray:
        """
        在图像上绘制检测和识别结果
        
        Args:
            image: 输入图像
            results: 检测识别结果
            
        Returns:
            绘制后的图像
        """
        output = image.copy()
        
        for result in results:
            x1, y1, x2, y2 = result['bbox']
            user_id = result['user_id']
            confidence = result['confidence']
            
            # 颜色: 绿色(已识别) 红色(未识别)
            color = (0, 255, 0) if user_id is not None else (0, 0, 255)
            
            # 绘制边界框
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
            
            # 绘制文本
            if user_id is not None:
                text = f"User {user_id} ({confidence:.2f})"
            else:
                text = "Unknown"
            
            cv2.putText(output, text, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return output
    
    def get_registered_user_count(self) -> int:
        """获取已注册用户数量"""
        return self.recognizer.get_user_count()


if __name__ == '__main__':
    # 测试人脸服务
    service = FaceService()
    
    print(f"已注册用户数: {service.get_registered_user_count()}")
    
    # 测试实时识别
    cap = cv2.VideoCapture(0)
    
    print("按 'q' 退出")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 检测并识别
        results = service.detect_and_recognize(frame)
        
        # 绘制结果
        output = service.draw_results(frame, results)
        
        cv2.imshow('Face Service Test', output)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

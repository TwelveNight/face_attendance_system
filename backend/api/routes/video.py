"""
视频流API路由
"""
from flask import Blueprint, Response
import cv2
import time

from models.model_manager import model_manager
from config.settings import Config
from api.middleware import error_response

video_bp = Blueprint('video', __name__)


def generate_frames():
    """生成视频帧"""
    camera = cv2.VideoCapture(Config.CAMERA_INDEX)
    
    try:
        detector = model_manager.yolo_detector
        recognizer = model_manager.facenet_recognizer
        
        while True:
            success, frame = camera.read()
            if not success:
                break
            
            # 检测人脸
            faces = detector.detect_faces(frame, return_confidence=True)
            
            # 识别并绘制
            for face in faces:
                x1, y1, x2, y2, det_conf = face
                
                # 裁剪并识别
                face_img = detector.crop_face(frame, face)
                if face_img is not None:
                    user_id, rec_conf = recognizer.recognize(face_img)
                    
                    # 绘制
                    color = (0, 255, 0) if user_id is not None else (0, 0, 255)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    
                    if user_id is not None:
                        text = f"User {user_id} ({rec_conf:.2f})"
                    else:
                        text = "Unknown"
                    
                    cv2.putText(frame, text, (x1, y1 - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # 编码为JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            # 生成multipart响应
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(1 / Config.VIDEO_FPS)
    
    finally:
        camera.release()


@video_bp.route('/feed', methods=['GET'])
def video_feed():
    """视频流"""
    try:
        return Response(
            generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        return error_response("视频流失败", 500, str(e))

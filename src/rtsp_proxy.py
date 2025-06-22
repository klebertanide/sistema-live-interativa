import cv2
import threading
import time
from flask import Response
import logging

class RTSPProxy:
    def __init__(self):
        self.streams = {}
        self.active_streams = {}
        
    def start_stream(self, camera_id, rtsp_url):
        """Iniciar captura de stream RTSP"""
        if camera_id in self.active_streams:
            return True
            
        try:
            # Criar thread para captura
            thread = threading.Thread(
                target=self._capture_stream,
                args=(camera_id, rtsp_url),
                daemon=True
            )
            thread.start()
            
            self.active_streams[camera_id] = {
                'thread': thread,
                'url': rtsp_url,
                'active': True
            }
            
            print(f"📹 Stream {camera_id} iniciado: {rtsp_url}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao iniciar stream {camera_id}: {e}")
            return False
    
    def stop_stream(self, camera_id):
        """Parar captura de stream"""
        if camera_id in self.active_streams:
            self.active_streams[camera_id]['active'] = False
            del self.active_streams[camera_id]
            if camera_id in self.streams:
                del self.streams[camera_id]
            print(f"🛑 Stream {camera_id} parado")
    
    def _capture_stream(self, camera_id, rtsp_url):
        """Capturar frames do RTSP e converter para MJPEG"""
        cap = None
        retry_count = 0
        max_retries = 3
        
        while camera_id in self.active_streams and self.active_streams[camera_id]['active']:
            try:
                if cap is None:
                    print(f"🔄 Conectando ao stream {camera_id}: {rtsp_url}")
                    cap = cv2.VideoCapture(rtsp_url)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    cap.set(cv2.CAP_PROP_FPS, 15)
                    
                    if not cap.isOpened():
                        raise Exception("Não foi possível conectar ao stream RTSP")
                
                ret, frame = cap.read()
                
                if ret:
                    # Redimensionar frame para otimizar
                    height, width = frame.shape[:2]
                    if width > 640:
                        scale = 640 / width
                        new_width = int(width * scale)
                        new_height = int(height * scale)
                        frame = cv2.resize(frame, (new_width, new_height))
                    
                    # Converter para JPEG
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    
                    # Armazenar frame
                    self.streams[camera_id] = buffer.tobytes()
                    retry_count = 0
                    
                else:
                    raise Exception("Falha ao ler frame")
                    
                time.sleep(1/15)  # 15 FPS
                
            except Exception as e:
                print(f"❌ Erro no stream {camera_id}: {e}")
                retry_count += 1
                
                if cap:
                    cap.release()
                    cap = None
                
                if retry_count >= max_retries:
                    print(f"🛑 Stream {camera_id} falhou após {max_retries} tentativas")
                    break
                
                print(f"🔄 Tentativa {retry_count}/{max_retries} em 5 segundos...")
                time.sleep(5)
        
        if cap:
            cap.release()
        print(f"🏁 Thread do stream {camera_id} finalizada")
    
    def get_mjpeg_stream(self, camera_id):
        """Gerar stream MJPEG para HTTP"""
        def generate():
            while camera_id in self.active_streams and self.active_streams[camera_id]['active']:
                if camera_id in self.streams:
                    frame = self.streams[camera_id]
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                else:
                    # Frame placeholder se não há dados
                    placeholder = self._generate_placeholder(camera_id)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')
                
                time.sleep(1/15)  # 15 FPS
        
        return Response(
            generate(),
            mimetype='multipart/x-mixed-replace; boundary=frame',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    def _generate_placeholder(self, camera_id):
        """Gerar frame placeholder quando não há dados"""
        import numpy as np
        
        # Criar imagem preta com texto
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Adicionar texto
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = f"Conectando Câmera {camera_id}..."
        text_size = cv2.getTextSize(text, font, 1, 2)[0]
        text_x = (img.shape[1] - text_size[0]) // 2
        text_y = (img.shape[0] + text_size[1]) // 2
        
        cv2.putText(img, text, (text_x, text_y), font, 1, (0, 255, 0), 2)
        
        # Converter para JPEG
        _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return buffer.tobytes()

# Instância global do proxy
rtsp_proxy = RTSPProxy()


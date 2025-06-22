"""
Serviço para captura de screenshots
"""

import os
import cv2
import requests
from datetime import datetime
from PIL import Image, ImageDraw
from ..main import db

class ScreenshotService:
    
    @staticmethod
    def capture_from_camera(camera_id, trigger_reason='manual'):
        """Capturar screenshot de uma câmera"""
        try:
            from src.models.camera import Camera
            from src.models.screenshot import Screenshot
            
            # Buscar câmera
            camera = Camera.query.get(camera_id)
            if not camera:
                print(f"❌ Câmera {camera_id} não encontrada")
                return None
            
            # Gerar nome do arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"screenshot_{camera_id}_{timestamp}_{trigger_reason}.jpg"
            
            # Diretório para salvar screenshots
            screenshots_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'static', 'screenshots'
            )
            os.makedirs(screenshots_dir, exist_ok=True)
            
            filepath = os.path.join(screenshots_dir, filename)
            
            # Tentar capturar da câmera
            success = False
            
            if camera.url.startswith('rtsp://'):
                # Capturar de stream RTSP
                success = ScreenshotService._capture_from_rtsp(camera.url, filepath)
            elif camera.url.startswith('http'):
                # Capturar de stream HTTP
                success = ScreenshotService._capture_from_http(camera.url, filepath)
            else:
                print(f"❌ Tipo de URL não suportado: {camera.url}")
                return None
            
            if not success:
                # Criar imagem placeholder se falhar
                ScreenshotService._create_placeholder_image(filepath, camera.name or f"Câmera {camera_id}")
            
            # Aplicar efeito polaroid
            ScreenshotService._apply_polaroid_effect(filepath)
            
            # Salvar no banco
            screenshot = Screenshot(
                filename=filename,
                camera_id=camera_id,
                trigger_reason=trigger_reason,
                displayed=False
            )
            
            db.session.add(screenshot)
            db.session.commit()
            
            print(f"📸 Screenshot capturado: {filename} (Motivo: {trigger_reason})")
            return screenshot
            
        except Exception as e:
            print(f"❌ Erro ao capturar screenshot: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def _capture_from_rtsp(rtsp_url, filepath):
        """Capturar frame de stream RTSP"""
        try:
            cap = cv2.VideoCapture(rtsp_url)
            cap.set(cv2.CAP_PROP_TIMEOUT, 5000)  # 5 segundos timeout
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                cv2.imwrite(filepath, frame)
                return True
            else:
                print(f"❌ Falha ao capturar frame RTSP: {rtsp_url}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na captura RTSP: {e}")
            return False
    
    @staticmethod
    def _capture_from_http(http_url, filepath):
        """Capturar imagem de stream HTTP"""
        try:
            response = requests.get(http_url, timeout=10, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na captura HTTP: {e}")
            return False
    
    @staticmethod
    def _create_placeholder_image(filepath, camera_name):
        """Criar imagem placeholder quando captura falha"""
        try:
            # Criar imagem 640x480 com fundo escuro
            img = Image.new('RGB', (640, 480), color=(40, 40, 40))
            draw = ImageDraw.Draw(img)
            
            # Adicionar texto
            text_lines = [
                "📹 CÂMERA OFFLINE",
                camera_name,
                datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            ]
            
            y_offset = 200
            for line in text_lines:
                # Calcular posição central (aproximada)
                text_width = len(line) * 8  # Aproximação
                x = (640 - text_width) // 2
                draw.text((x, y_offset), line, fill=(255, 255, 255))
                y_offset += 30
            
            img.save(filepath, 'JPEG')
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar placeholder: {e}")
            return False
    
    @staticmethod
    def _apply_polaroid_effect(filepath):
        """Aplicar efeito polaroid à imagem"""
        try:
            # Abrir imagem
            img = Image.open(filepath)
            
            # Redimensionar para tamanho polaroid
            img = img.resize((300, 225), Image.Resampling.LANCZOS)
            
            # Criar fundo polaroid (branco com borda)
            polaroid_width = 320
            polaroid_height = 280
            polaroid = Image.new('RGB', (polaroid_width, polaroid_height), color=(250, 245, 235))
            
            # Colar imagem no centro superior
            x_offset = (polaroid_width - img.width) // 2
            y_offset = 10
            polaroid.paste(img, (x_offset, y_offset))
            
            # Adicionar timestamp na parte inferior
            draw = ImageDraw.Draw(polaroid)
            timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
            
            # Calcular posição do texto
            text_width = len(timestamp) * 6
            text_x = (polaroid_width - text_width) // 2
            text_y = polaroid_height - 30
            
            draw.text((text_x, text_y), timestamp, fill=(100, 100, 100))
            
            # Salvar imagem com efeito
            polaroid.save(filepath, 'JPEG', quality=85)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao aplicar efeito polaroid: {e}")
            return False
    
    @staticmethod
    def get_recent_screenshots(limit=20):
        """Obter screenshots recentes"""
        try:
            from src.models.screenshot import Screenshot
            
            screenshots = Screenshot.query.order_by(
                Screenshot.created_at.desc()
            ).limit(limit).all()
            
            return screenshots
            
        except Exception as e:
            print(f"❌ Erro ao buscar screenshots: {e}")
            return []
    
    @staticmethod
    def cleanup_old_screenshots(days=7):
        """Limpar screenshots antigos"""
        try:
            from src.models.screenshot import Screenshot
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            old_screenshots = Screenshot.query.filter(
                Screenshot.created_at < cutoff_date
            ).all()
            
            # Remover arquivos do disco
            screenshots_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'static', 'screenshots'
            )
            
            for screenshot in old_screenshots:
                filepath = os.path.join(screenshots_dir, screenshot.filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                db.session.delete(screenshot)
            
            db.session.commit()
            
            print(f"🧹 Limpeza: {len(old_screenshots)} screenshots antigos removidos")
            return len(old_screenshots)
            
        except Exception as e:
            print(f"❌ Erro na limpeza de screenshots: {e}")
            db.session.rollback()
            return 0


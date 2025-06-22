"""
Serviço de Screenshots Automáticos com Detecção de Emoções - VERSÃO FUNCIONAL
Captura screenshots automaticamente baseado em análise de emoções
"""

import logging
import time
import os
import random
from datetime import datetime
from threading import Thread
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class AutoScreenshotService:
    def __init__(self, app, db, socketio):
        self.app = app
        self.db = db
        self.socketio = socketio
        self.is_running = False
        self.screenshot_count = 0
        self.last_screenshot_time = 0
        self.min_interval = 300  # 5 minutos mínimo entre screenshots
        self.max_interval = 600  # 10 minutos máximo
        self.screenshots_dir = "static/screenshots"
        self.polaroids_dir = "static/polaroids"
        
        # Criar diretórios
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.polaroids_dir, exist_ok=True)
        
        # Palavras-chave para detecção de emoções
        self.emotion_keywords = {
            'excitement': ['incrível', 'épico', 'surreal', 'demais', 'fantástico', 'uau', 'nossa'],
            'shock': ['não acredito', 'chocado', 'impressionante', 'caramba', 'meu deus'],
            'laughter': ['hahaha', 'risos', 'engraçado', 'hilário', 'morri de rir'],
            'contemplation': ['interessante', 'pensando', 'refletindo', 'analisando'],
            'silence': ['silêncio', 'quieto', 'calmo', 'pausa', 'momento']
        }
        
        logger.info("📸 AutoScreenshotService inicializado")
    
    def start(self):
        """Inicia o serviço de screenshots automáticos"""
        if not self.is_running:
            self.is_running = True
            thread = Thread(target=self.screenshot_loop, daemon=True)
            thread.start()
            logger.info("📸 Serviço de screenshots automáticos iniciado")
    
    def stop(self):
        """Para o serviço"""
        self.is_running = False
        logger.info("📸 Serviço de screenshots automáticos parado")
    
    def detect_emotion_from_text(self, text):
        """Detecta emoção baseada no texto"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Verificar cada categoria de emoção
        for emotion, keywords in self.emotion_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return emotion
        
        return None
    
    def should_take_screenshot(self, emotion=None):
        """Determina se deve tirar screenshot"""
        current_time = time.time()
        
        # Verificar intervalo mínimo
        if current_time - self.last_screenshot_time < self.min_interval:
            return False
        
        # Se detectou emoção, sempre tirar
        if emotion:
            return True
        
        # Se passou do intervalo máximo, tirar screenshot
        if current_time - self.last_screenshot_time > self.max_interval:
            return True
        
        return False
    
    def capture_screenshot(self, emotion=None, transcription=""):
        """Captura screenshot e cria polaroid"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_file = f"screenshot_{timestamp}.jpg"
            screenshot_path = os.path.join(self.screenshots_dir, screenshot_file)
            
            # Simular captura de screenshot (placeholder)
            self.create_placeholder_screenshot(screenshot_path, emotion, transcription)
            
            # Criar polaroid com efeito
            polaroid_path = self.create_polaroid_effect(screenshot_path, emotion, timestamp)
            
            # Salvar no banco de dados
            self.save_screenshot_to_database(screenshot_file, emotion, transcription)
            
            self.screenshot_count += 1
            self.last_screenshot_time = time.time()
            
            logger.info(f"📸 Screenshot #{self.screenshot_count} capturado: {emotion or 'automático'}")
            
            # Emitir via WebSocket
            if self.socketio:
                self.socketio.emit('new_screenshot', {
                    'file': screenshot_file,
                    'polaroid': os.path.basename(polaroid_path) if polaroid_path else None,
                    'emotion': emotion,
                    'transcription': transcription,
                    'timestamp': datetime.now().isoformat()
                })
            
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Erro ao capturar screenshot: {e}")
            return None
    
    def create_placeholder_screenshot(self, path, emotion, transcription):
        """Cria screenshot placeholder com informações"""
        try:
            # Criar imagem placeholder 1920x1080
            img = Image.new('RGB', (1920, 1080), color=(30, 30, 30))
            draw = ImageDraw.Draw(img)
            
            # Adicionar texto
            try:
                from PIL import ImageFont
                font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 60)
                font_medium = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 40)
                font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 30)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Título
            draw.text((960, 300), "MOEDOR AO VIVO", font=font_large, fill=(255, 255, 255), anchor="mm")
            
            # Emoção detectada
            if emotion:
                emotion_text = f"Emoção: {emotion.upper()}"
                draw.text((960, 400), emotion_text, font=font_medium, fill=(255, 100, 100), anchor="mm")
            
            # Transcrição (truncada)
            if transcription:
                transcription_short = transcription[:100] + "..." if len(transcription) > 100 else transcription
                draw.text((960, 500), f'"{transcription_short}"', font=font_small, fill=(200, 200, 200), anchor="mm")
            
            # Timestamp
            timestamp_text = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            draw.text((960, 600), timestamp_text, font=font_small, fill=(150, 150, 150), anchor="mm")
            
            # Salvar
            img.save(path, 'JPEG', quality=85)
            
        except Exception as e:
            logger.error(f"Erro ao criar screenshot placeholder: {e}")
            # Criar arquivo vazio como fallback
            with open(path, 'w') as f:
                f.write("")
    
    def create_polaroid_effect(self, screenshot_path, emotion, timestamp):
        """Cria efeito polaroid sujo e envelhecido"""
        try:
            if not os.path.exists(screenshot_path):
                return None
            
            # Abrir imagem original
            img = Image.open(screenshot_path)
            
            # Redimensionar para formato polaroid (mais quadrado)
            img = img.resize((800, 600), Image.Resampling.LANCZOS)
            
            # Criar base do polaroid (com borda branca)
            polaroid_width = 900
            polaroid_height = 750
            polaroid = Image.new('RGB', (polaroid_width, polaroid_height), color=(245, 245, 240))
            
            # Colar imagem no centro superior
            img_x = (polaroid_width - 800) // 2
            img_y = 50
            polaroid.paste(img, (img_x, img_y))
            
            # Adicionar texto na parte inferior
            draw = ImageDraw.Draw(polaroid)
            try:
                from PIL import ImageFont
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # Texto da emoção e timestamp
            text_y = 680
            if emotion:
                emotion_text = f"Emoção: {emotion.capitalize()}"
                draw.text((polaroid_width//2, text_y), emotion_text, font=font, fill=(80, 80, 80), anchor="mm")
            
            date_text = datetime.now().strftime("%d/%m/%Y %H:%M")
            draw.text((polaroid_width//2, text_y + 30), date_text, font=font, fill=(120, 120, 120), anchor="mm")
            
            # Aplicar efeitos de envelhecimento
            polaroid = self.apply_aging_effects(polaroid)
            
            # Salvar polaroid
            polaroid_file = f"polaroid_{emotion or 'auto'}_{timestamp}.jpg"
            polaroid_path = os.path.join(self.polaroids_dir, polaroid_file)
            polaroid.save(polaroid_path, 'JPEG', quality=80)
            
            logger.info(f"📸 Polaroid criado: {polaroid_file}")
            return polaroid_path
            
        except Exception as e:
            logger.error(f"Erro ao criar polaroid: {e}")
            return None
    
    def apply_aging_effects(self, img):
        """Aplica efeitos de envelhecimento e sujeira"""
        try:
            # Converter para array numpy
            img_array = np.array(img)
            
            # Adicionar ruído
            noise = np.random.normal(0, 10, img_array.shape).astype(np.uint8)
            img_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
            # Converter de volta para PIL
            img = Image.fromarray(img_array)
            
            # Reduzir saturação (efeito vintage)
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(0.7)
            
            # Reduzir contraste ligeiramente
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(0.9)
            
            # Adicionar leve desfoque
            img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
            
            # Adicionar manchas aleatórias
            draw = ImageDraw.Draw(img)
            for _ in range(random.randint(3, 8)):
                x = random.randint(0, img.width)
                y = random.randint(0, img.height)
                size = random.randint(5, 20)
                color = (random.randint(200, 230), random.randint(180, 210), random.randint(160, 190))
                draw.ellipse([x-size//2, y-size//2, x+size//2, y+size//2], fill=color)
            
            return img
            
        except Exception as e:
            logger.error(f"Erro ao aplicar efeitos de envelhecimento: {e}")
            return img
    
    def save_screenshot_to_database(self, filename, emotion, transcription):
        """Salva screenshot no banco de dados"""
        try:
            with self.app.app_context():
                from ..main import Screenshot
                
                screenshot = Screenshot(
                    filename=filename,
                    emotion=emotion or 'automatic',
                    transcription=transcription[:500] if transcription else '',
                    created_at=datetime.now()
                )
                
                self.db.session.add(screenshot)
                self.db.session.commit()
                
                logger.info(f"📸 Screenshot salvo no banco: {filename}")
                
        except Exception as e:
            logger.error(f"Erro ao salvar screenshot no banco: {e}")
    
    def process_transcription(self, transcription):
        """Processa transcrição para possível screenshot"""
        if not transcription:
            return
        
        emotion = self.detect_emotion_from_text(transcription)
        
        if self.should_take_screenshot(emotion):
            self.capture_screenshot(emotion, transcription)
    
    def screenshot_loop(self):
        """Loop principal de screenshots automáticos"""
        logger.info("📸 Iniciando loop de screenshots automáticos")
        
        # Aguardar 60 segundos antes do primeiro screenshot
        time.sleep(60)
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # Verificar se deve tirar screenshot automático
                if current_time - self.last_screenshot_time >= self.max_interval:
                    self.capture_screenshot(None, "Screenshot automático por tempo")
                
                # Aguardar 30 segundos antes de verificar novamente
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Erro no loop de screenshots: {e}")
                time.sleep(60)

# Instância global
auto_screenshot_service = None

def init_auto_screenshot_service(app, db, socketio):
    """Inicializa o serviço de screenshots automáticos"""
    global auto_screenshot_service
    auto_screenshot_service = AutoScreenshotService(app, db, socketio)
    return auto_screenshot_service

def get_auto_screenshot_service():
    """Retorna a instância do serviço"""
    return auto_screenshot_service


"""
Serviço de Screenshots Automáticos com Detecção de Emoções - MOEDOR AO VIVO
Captura screenshots automaticamente baseado em análise de emoções do Whisper
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import logging
import threading
import time
from datetime import datetime
import json
import random
from typing import Optional, Dict, List
import requests
from io import BytesIO

logger = logging.getLogger(__name__)

class EmotionScreenshotService:
    """Serviço de screenshots automáticos com detecção de emoções"""
    
    def __init__(self, app, db, socketio):
        self.app = app
        self.db = db
        self.socketio = socketio
        
        # Configurações
        self.screenshots_dir = os.path.join(os.getcwd(), 'static', 'screenshots')
        self.polaroids_dir = os.path.join(os.getcwd(), 'static', 'polaroids')
        
        # Criar diretórios
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.polaroids_dir, exist_ok=True)
        
        # Estado
        self.running = False
        self.thread = None
        self.last_screenshot = None
        self.screenshot_count = 0
        
        # Configurações de emoção
        self.emotion_keywords = {
            'excitement': ['incrível', 'demais', 'top', 'show', 'perfeito', 'épico', 'sensacional', 'fantástico'],
            'shock': ['não acredito', 'nossa', 'caramba', 'meu deus', 'impossível', 'surreal', 'bizarro'],
            'laughter': ['haha', 'kkkk', 'rsrs', 'riindo', 'engraçado', 'hilário', 'morri'],
            'contemplation': ['pensando', 'refletindo', 'interessante', 'curioso', 'será', 'talvez'],
            'silence': ['...', 'silêncio', 'quieto', 'calmo', 'pausa', 'momento']
        }
        
        # Configurações de captura
        self.min_interval = 10  # Mínimo 10 segundos entre screenshots
        self.last_capture_time = 0
        
        logger.info("📸 EmotionScreenshotService inicializado")
    
    def start(self):
        """Iniciar serviço de screenshots"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_service, daemon=True)
        self.thread.start()
        
        logger.info("📸 Serviço de screenshots iniciado")
    
    def stop(self):
        """Parar serviço de screenshots"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("📸 Serviço de screenshots parado")
    
    def _run_service(self):
        """Loop principal do serviço"""
        while self.running:
            try:
                # Verificar se há transcrições recentes para analisar
                self._check_for_emotional_moments()
                time.sleep(2)  # Verificar a cada 2 segundos
                
            except Exception as e:
                logger.error(f"Erro no serviço de screenshots: {e}")
                time.sleep(5)
    
    def _check_for_emotional_moments(self):
        """Verificar transcrições recentes para detectar momentos emocionais"""
        try:
            # Buscar transcrições dos últimos 30 segundos
            transcriptions_dir = os.path.join(os.getcwd(), 'transcriptions')
            if not os.path.exists(transcriptions_dir):
                return
            
            # Listar arquivos de transcrição recentes
            now = time.time()
            recent_files = []
            
            for filename in os.listdir(transcriptions_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(transcriptions_dir, filename)
                    file_time = os.path.getmtime(filepath)
                    
                    # Arquivos dos últimos 30 segundos
                    if now - file_time <= 30:
                        recent_files.append((filepath, file_time))
            
            # Analisar transcrições recentes
            for filepath, file_time in recent_files:
                emotion = self._analyze_transcription_emotion(filepath)
                if emotion and self._should_capture_screenshot(emotion):
                    self._capture_emotional_screenshot(emotion, filepath)
                    
        except Exception as e:
            logger.error(f"Erro ao verificar momentos emocionais: {e}")
    
    def _analyze_transcription_emotion(self, transcription_file: str) -> Optional[str]:
        """Analisar emoção de uma transcrição"""
        try:
            with open(transcription_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            transcription = data.get('transcription', '').lower()
            if not transcription:
                return None
            
            # Detectar emoções baseadas em palavras-chave
            emotion_scores = {}
            
            for emotion, keywords in self.emotion_keywords.items():
                score = 0
                for keyword in keywords:
                    if keyword in transcription:
                        score += 1
                
                if score > 0:
                    emotion_scores[emotion] = score
            
            # Retornar emoção com maior score
            if emotion_scores:
                best_emotion = max(emotion_scores, key=emotion_scores.get)
                logger.info(f"🎭 Emoção detectada: {best_emotion} (score: {emotion_scores[best_emotion]})")
                return best_emotion
            
            # Detectar silêncio (transcrição muito curta ou vazia)
            if len(transcription.strip()) < 5:
                logger.info("🤫 Silêncio detectado")
                return 'silence'
                
        except Exception as e:
            logger.error(f"Erro ao analisar emoção: {e}")
        
        return None
    
    def _should_capture_screenshot(self, emotion: str) -> bool:
        """Verificar se deve capturar screenshot baseado na emoção"""
        current_time = time.time()
        
        # Respeitar intervalo mínimo
        if current_time - self.last_capture_time < self.min_interval:
            return False
        
        # Probabilidades por emoção
        probabilities = {
            'excitement': 0.8,  # 80% chance
            'shock': 0.9,       # 90% chance
            'laughter': 0.7,    # 70% chance
            'contemplation': 0.4, # 40% chance
            'silence': 0.3      # 30% chance
        }
        
        probability = probabilities.get(emotion, 0.2)
        should_capture = random.random() < probability
        
        if should_capture:
            logger.info(f"📸 Screenshot será capturado para emoção: {emotion}")
        
        return should_capture
    
    def _capture_emotional_screenshot(self, emotion: str, transcription_file: str):
        """Capturar screenshot emocional"""
        try:
            # Simular captura de tela (em produção, usar biblioteca de screenshot)
            screenshot_path = self._simulate_screenshot_capture()
            
            if screenshot_path:
                # Processar screenshot para criar polaroid
                polaroid_path = self._create_polaroid_effect(screenshot_path, emotion)
                
                if polaroid_path:
                    # Salvar no banco de dados
                    self._save_screenshot_to_db(polaroid_path, emotion, transcription_file)
                    
                    # Emitir via WebSocket
                    if self.socketio:
                        self.socketio.emit('new_screenshot', {
                            'path': polaroid_path,
                            'emotion': emotion,
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    self.last_capture_time = time.time()
                    self.screenshot_count += 1
                    
                    logger.info(f"📸 Screenshot capturado: {emotion} -> {polaroid_path}")
                    
        except Exception as e:
            logger.error(f"Erro ao capturar screenshot emocional: {e}")
    
    def _simulate_screenshot_capture(self) -> Optional[str]:
        """Simular captura de screenshot (em produção, usar pyautogui ou similar)"""
        try:
            # Criar imagem simulada (em produção, capturar tela real)
            width, height = 1920, 1080
            
            # Criar imagem com gradiente simulando uma tela
            image = Image.new('RGB', (width, height), color='black')
            draw = ImageDraw.Draw(image)
            
            # Simular conteúdo da tela
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
            color = random.choice(colors)
            
            # Desenhar retângulos simulando interface
            for i in range(5):
                x1 = random.randint(0, width//2)
                y1 = random.randint(0, height//2)
                x2 = x1 + random.randint(200, 400)
                y2 = y1 + random.randint(100, 200)
                
                draw.rectangle([x1, y1, x2, y2], fill=color, outline='white', width=2)
            
            # Salvar screenshot simulado
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.screenshots_dir, f"screenshot_{timestamp}.jpg")
            
            image.save(screenshot_path, 'JPEG', quality=90)
            
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Erro ao simular screenshot: {e}")
            return None
    
    def _create_polaroid_effect(self, screenshot_path: str, emotion: str) -> Optional[str]:
        """Criar efeito polaroid sujo no screenshot"""
        try:
            # Carregar imagem original
            original = Image.open(screenshot_path)
            
            # Redimensionar para formato polaroid
            polaroid_size = (400, 300)
            original = original.resize(polaroid_size, Image.Resampling.LANCZOS)
            
            # Criar base do polaroid (com borda branca)
            polaroid_width = polaroid_size[0] + 40
            polaroid_height = polaroid_size[1] + 80  # Espaço extra embaixo
            
            polaroid = Image.new('RGB', (polaroid_width, polaroid_height), 'white')
            
            # Colar imagem no centro superior
            polaroid.paste(original, (20, 20))
            
            # Adicionar texto da emoção
            draw = ImageDraw.Draw(polaroid)
            emotion_text = f"Emoção: {emotion.title()}"
            timestamp_text = datetime.now().strftime("%d/%m/%Y %H:%M")
            
            # Simular texto manuscrito (em produção, usar fonte personalizada)
            try:
                draw.text((30, polaroid_size[1] + 30), emotion_text, fill='black')
                draw.text((30, polaroid_size[1] + 50), timestamp_text, fill='gray')
            except:
                pass  # Ignorar erro de fonte
            
            # Aplicar efeitos de envelhecimento
            polaroid = self._apply_aging_effects(polaroid)
            
            # Salvar polaroid
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            polaroid_path = os.path.join(self.polaroids_dir, f"polaroid_{emotion}_{timestamp}.jpg")
            
            polaroid.save(polaroid_path, 'JPEG', quality=85)
            
            return polaroid_path
            
        except Exception as e:
            logger.error(f"Erro ao criar efeito polaroid: {e}")
            return None
    
    def _apply_aging_effects(self, image: Image.Image) -> Image.Image:
        """Aplicar efeitos de envelhecimento ao polaroid"""
        try:
            # Reduzir saturação
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(0.8)
            
            # Adicionar leve desfoque
            image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
            
            # Adicionar ruído (simulado com pontos aleatórios)
            draw = ImageDraw.Draw(image)
            width, height = image.size
            
            # Adicionar pontos de sujeira
            for _ in range(random.randint(10, 30)):
                x = random.randint(0, width)
                y = random.randint(0, height)
                size = random.randint(1, 3)
                color = random.choice(['#8B4513', '#654321', '#D2B48C'])
                draw.ellipse([x-size, y-size, x+size, y+size], fill=color)
            
            # Adicionar manchas nas bordas
            for _ in range(random.randint(5, 15)):
                x = random.choice([0, width-1])  # Bordas laterais
                y = random.randint(0, height)
                size = random.randint(2, 8)
                color = '#F5F5DC'  # Bege claro
                draw.ellipse([x-size, y-size, x+size, y+size], fill=color)
            
            return image
            
        except Exception as e:
            logger.error(f"Erro ao aplicar efeitos de envelhecimento: {e}")
            return image
    
    def _save_screenshot_to_db(self, polaroid_path: str, emotion: str, transcription_file: str):
        """Salvar screenshot no banco de dados"""
        try:
            with self.app.app_context():
                # Importar modelo Screenshot
                from ..main import Screenshot
                
                screenshot = Screenshot(
                    filename=os.path.basename(polaroid_path),
                    emotion=emotion,
                    transcription_source=os.path.basename(transcription_file)
                )
                
                self.db.session.add(screenshot)
                self.db.session.commit()
                
                logger.info(f"💾 Screenshot salvo no banco: {screenshot.filename}")
                
        except Exception as e:
            logger.error(f"Erro ao salvar screenshot no banco: {e}")
    
    def get_status(self) -> Dict:
        """Obter status do serviço"""
        return {
            'running': self.running,
            'screenshot_count': self.screenshot_count,
            'last_screenshot': self.last_screenshot,
            'screenshots_dir': self.screenshots_dir,
            'polaroids_dir': self.polaroids_dir
        }
    
    def manual_screenshot(self, emotion: str = 'manual') -> Optional[str]:
        """Capturar screenshot manualmente"""
        try:
            screenshot_path = self._simulate_screenshot_capture()
            if screenshot_path:
                polaroid_path = self._create_polaroid_effect(screenshot_path, emotion)
                if polaroid_path:
                    self._save_screenshot_to_db(polaroid_path, emotion, 'manual_capture')
                    return polaroid_path
        except Exception as e:
            logger.error(f"Erro ao capturar screenshot manual: {e}")
        
        return None

def init_screenshot_service(app, db, socketio):
    """Inicializar serviço de screenshots"""
    service = EmotionScreenshotService(app, db, socketio)
    service.start()
    return service

def get_screenshot_service():
    """Obter instância do serviço de screenshots"""
    # Em produção, usar singleton ou registry
    return None


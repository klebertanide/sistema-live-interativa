"""
Whisper Leve - Sistema de Transcrição Simplificado
Versão FINAL CORRIGIDA - Sem erros SQLAlchemy
"""

import os
import sys
import time
import tempfile
import threading
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleWhisperService:
    """Serviço de transcrição simplificado usando Whisper"""
    
    def __init__(self, app, db, socketio):
        self.app = app
        self.db = db
        self.socketio = socketio
        self.is_running = False
        self.worker_thread = None
        self.check_interval = 30  # 30 segundos
        self.transcription_buffer = []
        self.max_buffer_size = 20
        
        # Configurar diretório de transcrições
        self.transcriptions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'transcriptions')
        os.makedirs(self.transcriptions_dir, exist_ok=True)
        
        logger.info("🎤 SimpleWhisperService inicializado")
    
    def start(self):
        """Iniciar serviço de transcrição"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._transcription_loop, daemon=True)
            self.worker_thread.start()
            logger.info("🎤 Iniciando loop de transcrição")
            logger.info("🎤 Whisper leve iniciado")
    
    def stop(self):
        """Parar serviço de transcrição"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("🎤 Whisper leve parado")
    
    def _transcription_loop(self):
        """Loop principal de transcrição"""
        while self.is_running:
            try:
                # Buscar URL da live
                live_url = self._get_live_url()
                
                if live_url:
                    logger.info(f"🔄 Processando live: {live_url}")
                    
                    # Capturar e transcrever áudio
                    transcription = self._capture_and_transcribe(live_url)
                    
                    if transcription:
                        self._process_transcription(transcription)
                
                # Aguardar próximo ciclo
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"❌ Erro no loop de transcrição: {e}")
                time.sleep(10)  # Aguardar mais tempo em caso de erro
    
    def _get_live_url(self):
        """Buscar URL da live oficial - VERSÃO CORRIGIDA"""
        try:
            # Usar contexto da aplicação Flask corretamente
            with self.app.app_context():
                # Importar modelos dentro do contexto
                from main import LiveSession
                
                # Usar self.db para acessar o banco
                session = self.db.session.query(LiveSession).filter_by(active=True).first()
                
                if session and session.live_oficial_url:
                    logger.info(f"🔄 URL da live oficial encontrada: {session.live_oficial_url}")
                    return session.live_oficial_url
                elif session and session.youtube_url:  # Compatibilidade
                    logger.info(f"🔄 URL da live (compatibilidade) encontrada: {session.youtube_url}")
                    return session.youtube_url
                else:
                    logger.warning("⚠️ Nenhuma live ativa encontrada no banco")
                    return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar URL da live: {e}")
            return None
    
    def _capture_and_transcribe(self, live_url):
        """Capturar áudio da live e transcrever"""
        try:
            # Criar arquivo temporário para áudio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
            
            # Configurações do yt-dlp para capturar áudio
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_audio_path,
                'quiet': True,
                'no_warnings': True,
                'extractaudio': True,
                'audioformat': 'wav',
                'audioquality': '192K',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'postprocessor_args': [
                    '-ss', '0',  # Começar do início
                    '-t', '30',  # Capturar apenas 30 segundos
                ],
            }
            
            # Capturar áudio usando yt-dlp
            import yt_dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([live_url])
            
            # Verificar se arquivo foi criado
            if not os.path.exists(temp_audio_path):
                logger.error("❌ Arquivo de áudio não foi criado")
                return None
            
            # Transcrever usando Whisper
            import whisper
            model = whisper.load_model("tiny")  # Modelo mais leve
            result = model.transcribe(temp_audio_path, language="pt")
            
            # Limpar arquivo temporário
            try:
                os.unlink(temp_audio_path)
            except:
                pass
            
            # Retornar apenas o texto
            transcription_text = result["text"].strip()
            if transcription_text:
                logger.info(f"🎤 Transcrição: {transcription_text[:100]}...")
                return transcription_text
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao capturar/transcrever áudio: {e}")
            return None
    
    def _process_transcription(self, transcription):
        """Processar transcrição e salvar"""
        try:
            # Adicionar ao buffer
            self.transcription_buffer.append({
                'text': transcription,
                'timestamp': datetime.now()
            })
            
            # Manter tamanho do buffer
            if len(self.transcription_buffer) > self.max_buffer_size:
                self.transcription_buffer.pop(0)
            
            # Salvar em arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcription_{timestamp}.txt"
            filepath = os.path.join(self.transcriptions_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Transcrição: {transcription}\n")
            
            logger.info(f"💾 Transcrição salva: {filename}")
            
            # Emitir via WebSocket
            self.socketio.emit('new_transcription', {
                'text': transcription,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar transcrição: {e}")
    
    def get_recent_transcriptions(self, count=10):
        """Obter transcrições recentes do buffer"""
        return self.transcription_buffer[-count:] if self.transcription_buffer else []

def init_simple_whisper_service(app, db, socketio):
    """Inicializar serviço de Whisper simplificado"""
    return SimpleWhisperService(app, db, socketio)


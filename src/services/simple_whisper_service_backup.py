"""
Whisper Leve - Sistema de Transcrição Simples
Captura áudio da live oficial do YouTube e transcreve em texto simples
"""

import logging
import threading
import time
import subprocess
import tempfile
import os
import requests
from datetime import datetime
import yt_dlp

logger = logging.getLogger(__name__)

class SimpleWhisperService:
    def __init__(self, app, db, socketio):
        self.app = app
        self.db = db
        self.socketio = socketio
        self.is_running = False
        self.thread = None
        self.transcription_buffer = []
        self.last_transcription_time = time.time()
        
        # Configurações
        self.check_interval = 30  # Verificar a cada 30 segundos
        self.audio_duration = 30  # Capturar 30 segundos de áudio
        
        logger.info("🎤 SimpleWhisperService inicializado")
    
    def start(self):
        """Iniciar serviço de transcrição"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._transcription_loop, daemon=True)
            self.thread.start()
            logger.info("🎤 Whisper leve iniciado")
    
    def stop(self):
        """Parar serviço de transcrição"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("🎤 Whisper leve parado")
    
    def _transcription_loop(self):
        """Loop principal de transcrição"""
        logger.info("🎤 Iniciando loop de transcrição")
        
        while self.is_running:
            try:
                # Buscar URL da live oficial
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
        """Buscar URL da live oficial do banco de dados"""
        try:
            # Usar contexto da aplicação corretamente
            with self.app.app_context():
                # Import dentro do contexto
                import sys
                import os
                sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
                
                from main import LiveSession, db
                
                # Garantir que estamos no contexto correto
                session = db.session.query(LiveSession).filter_by(active=True).first()
                
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
            # Retornar URL padrão para teste se houver erro
            return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    def _capture_and_transcribe(self, live_url):
        """Capturar áudio da live e transcrever"""
        try:
            # Criar arquivo temporário para áudio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
            
            # Configurações do yt-dlp para capturar áudio
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_audio_path.replace('.wav', '.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'live_from_start': False,
                'duration': self.audio_duration,  # Capturar apenas 30 segundos
            }
            
            # Baixar segmento de áudio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([live_url])
            
            # Encontrar arquivo de áudio gerado
            audio_file = temp_audio_path.replace('.wav', '.wav')
            if not os.path.exists(audio_file):
                # Tentar outras extensões
                for ext in ['.m4a', '.webm', '.mp3']:
                    alt_file = temp_audio_path.replace('.wav', ext)
                    if os.path.exists(alt_file):
                        audio_file = alt_file
                        break
            
            if not os.path.exists(audio_file):
                logger.warning("⚠️ Arquivo de áudio não encontrado")
                return None
            
            # Transcrever com Whisper
            transcription = self._transcribe_audio(audio_file)
            
            # Limpar arquivo temporário
            try:
                os.unlink(audio_file)
            except:
                pass
            
            return transcription
            
        except Exception as e:
            logger.error(f"❌ Erro ao capturar/transcrever áudio: {e}")
            return None
    
    def _transcribe_audio(self, audio_file):
        """Transcrever arquivo de áudio usando Whisper"""
        try:
            # Usar whisper via subprocess (mais leve que importar a biblioteca)
            cmd = [
                'whisper',
                audio_file,
                '--model', 'tiny',  # Modelo mais leve
                '--language', 'Portuguese',
                '--output_format', 'txt',
                '--output_dir', '/tmp',
                '--verbose', 'False'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Ler arquivo de transcrição gerado
                base_name = os.path.splitext(os.path.basename(audio_file))[0]
                txt_file = f"/tmp/{base_name}.txt"
                
                if os.path.exists(txt_file):
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        transcription = f.read().strip()
                    
                    # Limpar arquivo de transcrição
                    try:
                        os.unlink(txt_file)
                    except:
                        pass
                    
                    return transcription
            
            return None
            
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ Timeout na transcrição")
            return None
        except Exception as e:
            logger.error(f"❌ Erro na transcrição: {e}")
            return None
    
    def _process_transcription(self, transcription):
        """Processar transcrição e adicionar ao buffer"""
        if not transcription or len(transcription.strip()) < 10:
            return
        
        # Adicionar ao buffer
        self.transcription_buffer.append({
            'text': transcription.strip(),
            'timestamp': datetime.now()
        })
        
        # Manter apenas últimas 20 transcrições
        if len(self.transcription_buffer) > 20:
            self.transcription_buffer.pop(0)
        
        logger.info(f"🎤 Transcrição: {transcription[:100]}...")
        
        # Emitir via WebSocket
        if self.socketio:
            self.socketio.emit('new_transcription', {
                'text': transcription,
                'timestamp': datetime.now().isoformat()
            })
        
        # Atualizar tempo da última transcrição
        self.last_transcription_time = time.time()
    
    def get_recent_transcriptions(self, minutes=8):
        """Buscar transcrições recentes dos últimos X minutos"""
        cutoff_time = datetime.now().timestamp() - (minutes * 60)
        
        recent = []
        for trans in self.transcription_buffer:
            if trans['timestamp'].timestamp() > cutoff_time:
                recent.append(trans['text'])
        
        return recent
    
    def get_status(self):
        """Status do serviço"""
        return {
            'running': self.is_running,
            'buffer_size': len(self.transcription_buffer),
            'last_transcription': self.last_transcription_time,
            'time_since_last': time.time() - self.last_transcription_time
        }

# Funções de inicialização
def init_simple_whisper_service(app, db, socketio):
    """Inicializar serviço Whisper simples"""
    return SimpleWhisperService(app, db, socketio)

def get_simple_whisper_service():
    """Obter instância do serviço Whisper"""
    # Esta função será implementada no main.py
    pass


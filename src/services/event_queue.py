"""
Sistema de filas de eventos para evitar sobreposição
Garante que eventos sejam processados sequencialmente
"""

import threading
import time
import queue
from datetime import datetime
import logging

class EventQueue:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.queue = queue.Queue()
        self.processing = False
        self.worker_thread = None
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # Configurações
        self.event_delay = 1.0  # 1 segundo entre eventos
        self.message_display_time = 8.0  # 8 segundos para mensagens
        self.poll_display_time = 30.0  # 30 segundos para enquetes
        
        # Iniciar worker thread
        self.start_worker()
        
    def start_worker(self):
        """Iniciar thread worker para processar eventos"""
        if self.worker_thread and self.worker_thread.is_alive():
            return
            
        self.worker_thread = threading.Thread(
            target=self._process_queue,
            daemon=True
        )
        self.worker_thread.start()
        self.logger.info("Worker thread da fila de eventos iniciado")
        
    def add_event(self, event_type, data, priority=1):
        """Adicionar evento à fila"""
        event = {
            'type': event_type,
            'data': data,
            'priority': priority,
            'timestamp': datetime.now(),
            'id': f"{event_type}_{int(time.time() * 1000)}"
        }
        
        self.queue.put(event)
        self.logger.info(f"Evento adicionado à fila: {event_type} (ID: {event['id']})")
        
    def _process_queue(self):
        """Processar fila de eventos"""
        self.logger.info("Iniciando processamento da fila de eventos")
        
        while True:
            try:
                # Aguardar próximo evento
                event = self.queue.get(timeout=1)
                
                with self.lock:
                    self.processing = True
                    
                # Processar evento
                self._process_event(event)
                
                # Aguardar antes do próximo evento
                time.sleep(self.event_delay)
                
                with self.lock:
                    self.processing = False
                    
                # Marcar evento como processado
                self.queue.task_done()
                
            except queue.Empty:
                # Timeout normal, continuar
                continue
            except Exception as e:
                self.logger.error(f"Erro ao processar evento: {e}")
                with self.lock:
                    self.processing = False
                    
    def _process_event(self, event):
        """Processar evento individual"""
        event_type = event['type']
        data = event['data']
        event_id = event['id']
        
        self.logger.info(f"Processando evento: {event_type} (ID: {event_id})")
        
        try:
            if event_type == 'message':
                self._process_message_event(data, event_id)
            elif event_type == 'poll':
                self._process_poll_event(data, event_id)
            elif event_type == 'screenshot':
                self._process_screenshot_event(data, event_id)
            elif event_type == 'live_update':
                self._process_live_update_event(data, event_id)
            else:
                self.logger.warning(f"Tipo de evento desconhecido: {event_type}")
                
        except Exception as e:
            self.logger.error(f"Erro ao processar evento {event_type}: {e}")
            
    def _process_message_event(self, data, event_id):
        """Processar evento de mensagem"""
        if not self.socketio:
            return
            
        # Emitir evento para overlay de mensagens
        self.socketio.emit('overlay_message', {
            'id': event_id,
            'name': data.get('name', 'Anônimo'),
            'content': data.get('content', ''),
            'timestamp': data.get('created_at', datetime.now().isoformat()),
            'display_time': self.message_display_time
        }, room='overlay_messages')
        
        # Emitir para página principal
        self.socketio.emit('new_message', data)
        
        self.logger.info(f"Mensagem processada: {data.get('name')} - {data.get('content')[:50]}...")
        
        # Aguardar tempo de exibição
        time.sleep(self.message_display_time)
        
        # Sinalizar fim da exibição
        self.socketio.emit('overlay_message_end', {
            'id': event_id
        }, room='overlay_messages')
        
    def _process_poll_event(self, data, event_id):
        """Processar evento de enquete"""
        if not self.socketio:
            return
            
        # Emitir evento para overlay de enquetes
        self.socketio.emit('overlay_poll', {
            'id': event_id,
            'question': data.get('question', ''),
            'options': data.get('options', []),
            'votes': data.get('votes', []),
            'display_time': self.poll_display_time
        }, room='overlay_polls')
        
        # Emitir para página principal
        self.socketio.emit('new_poll', data)
        
        self.logger.info(f"Enquete processada: {data.get('question', '')[:50]}...")
        
        # Aguardar tempo de exibição
        time.sleep(self.poll_display_time)
        
        # Sinalizar fim da exibição
        self.socketio.emit('overlay_poll_end', {
            'id': event_id
        }, room='overlay_polls')
        
    def _process_screenshot_event(self, data, event_id):
        """Processar evento de screenshot"""
        if not self.socketio:
            return
            
        # Emitir evento para todas as páginas
        self.socketio.emit('new_screenshot', {
            'id': event_id,
            'filename': data.get('filename', ''),
            'camera_id': data.get('camera_id'),
            'reason': data.get('reason', ''),
            'timestamp': data.get('created_at', datetime.now().isoformat())
        })
        
        self.logger.info(f"Screenshot processado: {data.get('filename', '')}")
        
    def _process_live_update_event(self, data, event_id):
        """Processar evento de atualização de live"""
        if not self.socketio:
            return
            
        # Emitir para todas as páginas
        self.socketio.emit('live_updated', data)
        
        self.logger.info(f"Live atualizada: {data.get('title', '')}")
        
    def get_status(self):
        """Obter status da fila"""
        return {
            'queue_size': self.queue.qsize(),
            'processing': self.processing,
            'worker_alive': self.worker_thread.is_alive() if self.worker_thread else False
        }
        
    def clear_queue(self):
        """Limpar fila de eventos"""
        with self.queue.mutex:
            self.queue.queue.clear()
        self.logger.info("Fila de eventos limpa")
        
    def stop(self):
        """Parar processamento da fila"""
        # Adicionar evento especial para parar
        self.queue.put({'type': 'stop', 'data': {}, 'priority': 0, 'timestamp': datetime.now()})

# Instância global da fila
event_queue = EventQueue()

def init_event_queue(socketio):
    """Inicializar fila de eventos com socketio"""
    global event_queue
    event_queue.socketio = socketio
    return event_queue


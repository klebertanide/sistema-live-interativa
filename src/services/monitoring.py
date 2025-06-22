"""
Sistema de monitoramento e performance para alta concorrência
Garante estabilidade para milhares de usuários simultâneos
"""

import os
import psutil
import threading
import time
import logging
from datetime import datetime, timedelta
from collections import deque
import json

class PerformanceMonitor:
    def __init__(self, app=None, socketio=None):
        self.app = app
        self.socketio = socketio
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Métricas
        self.cpu_usage = deque(maxlen=60)  # Últimos 60 valores
        self.memory_usage = deque(maxlen=60)
        self.active_connections = 0
        self.requests_per_minute = deque(maxlen=60)
        self.response_times = deque(maxlen=100)
        
        # Contadores
        self.total_requests = 0
        self.total_errors = 0
        self.uptime_start = datetime.now()
        
        # Alertas
        self.alerts = []
        self.alert_thresholds = {
            'cpu_high': 80.0,
            'memory_high': 85.0,
            'response_time_high': 2.0,
            'error_rate_high': 5.0
        }
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
    def start_monitoring(self):
        """Iniciar monitoramento"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("Monitoramento de performance iniciado")
        
    def stop_monitoring(self):
        """Parar monitoramento"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Monitoramento de performance parado")
        
    def _monitoring_loop(self):
        """Loop principal de monitoramento"""
        while self.is_monitoring:
            try:
                # Coletar métricas
                self._collect_system_metrics()
                self._check_alerts()
                
                # Emitir métricas via WebSocket
                if self.socketio:
                    self._emit_metrics()
                    
                time.sleep(5)  # Coletar a cada 5 segundos
                
            except Exception as e:
                self.logger.error(f"Erro no monitoramento: {e}")
                time.sleep(10)
                
    def _collect_system_metrics(self):
        """Coletar métricas do sistema"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        self.cpu_usage.append(cpu_percent)
        
        # Memória
        memory = psutil.virtual_memory()
        self.memory_usage.append(memory.percent)
        
        # Disco
        disk = psutil.disk_usage('/')
        
        # Rede
        network = psutil.net_io_counters()
        
        # Processos
        process_count = len(psutil.pids())
        
        # Log métricas críticas
        if cpu_percent > self.alert_thresholds['cpu_high']:
            self.logger.warning(f"CPU alta: {cpu_percent}%")
            
        if memory.percent > self.alert_thresholds['memory_high']:
            self.logger.warning(f"Memória alta: {memory.percent}%")
            
    def _check_alerts(self):
        """Verificar e gerar alertas"""
        current_time = datetime.now()
        
        # CPU alto
        if self.cpu_usage and self.cpu_usage[-1] > self.alert_thresholds['cpu_high']:
            self._add_alert('cpu_high', f"CPU em {self.cpu_usage[-1]:.1f}%", 'warning')
            
        # Memória alta
        if self.memory_usage and self.memory_usage[-1] > self.alert_thresholds['memory_high']:
            self._add_alert('memory_high', f"Memória em {self.memory_usage[-1]:.1f}%", 'warning')
            
        # Taxa de erro alta
        if self.total_requests > 0:
            error_rate = (self.total_errors / self.total_requests) * 100
            if error_rate > self.alert_thresholds['error_rate_high']:
                self._add_alert('error_rate_high', f"Taxa de erro: {error_rate:.1f}%", 'critical')
                
    def _add_alert(self, alert_type, message, severity):
        """Adicionar alerta"""
        alert = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        
        # Evitar alertas duplicados recentes
        recent_alerts = [a for a in self.alerts if a['type'] == alert_type and 
                        datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(minutes=5)]
        
        if not recent_alerts:
            self.alerts.append(alert)
            self.logger.warning(f"Alerta {severity}: {message}")
            
            # Manter apenas últimos 50 alertas
            if len(self.alerts) > 50:
                self.alerts = self.alerts[-50:]
                
    def _emit_metrics(self):
        """Emitir métricas via WebSocket"""
        try:
            metrics = self.get_current_metrics()
            self.socketio.emit('performance_metrics', metrics, room='admin')
        except Exception as e:
            self.logger.error(f"Erro ao emitir métricas: {e}")
            
    def record_request(self, response_time=None, error=False):
        """Registrar requisição"""
        self.total_requests += 1
        
        if error:
            self.total_errors += 1
            
        if response_time:
            self.response_times.append(response_time)
            
    def get_current_metrics(self):
        """Obter métricas atuais"""
        uptime = datetime.now() - self.uptime_start
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': self.cpu_usage[-1] if self.cpu_usage else 0,
                'memory_percent': self.memory_usage[-1] if self.memory_usage else 0,
                'disk_usage': psutil.disk_usage('/').percent,
                'uptime_seconds': uptime.total_seconds()
            },
            'application': {
                'active_connections': self.active_connections,
                'total_requests': self.total_requests,
                'total_errors': self.total_errors,
                'error_rate': (self.total_errors / self.total_requests * 100) if self.total_requests > 0 else 0,
                'avg_response_time': sum(self.response_times) / len(self.response_times) if self.response_times else 0
            },
            'alerts': self.alerts[-10:],  # Últimos 10 alertas
            'health_status': self._get_health_status()
        }
        
    def _get_health_status(self):
        """Determinar status de saúde"""
        if not self.cpu_usage or not self.memory_usage:
            return 'unknown'
            
        cpu_ok = self.cpu_usage[-1] < self.alert_thresholds['cpu_high']
        memory_ok = self.memory_usage[-1] < self.alert_thresholds['memory_high']
        
        error_rate = (self.total_errors / self.total_requests * 100) if self.total_requests > 0 else 0
        error_ok = error_rate < self.alert_thresholds['error_rate_high']
        
        if cpu_ok and memory_ok and error_ok:
            return 'healthy'
        elif not cpu_ok or not memory_ok:
            return 'warning'
        else:
            return 'critical'
            
    def set_active_connections(self, count):
        """Definir número de conexões ativas"""
        self.active_connections = count

class DatabaseOptimizer:
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger(__name__)
        
    def optimize_database(self):
        """Otimizar banco de dados"""
        try:
            # Vacuum SQLite
            self.db.session.execute('VACUUM')
            
            # Analisar tabelas
            self.db.session.execute('ANALYZE')
            
            # Commit mudanças
            self.db.session.commit()
            
            self.logger.info("Banco de dados otimizado")
            
        except Exception as e:
            self.logger.error(f"Erro ao otimizar banco: {e}")
            self.db.session.rollback()
            
    def cleanup_old_data(self):
        """Limpar dados antigos"""
        try:
            from ..main import Message, Screenshot, LiveSession
            
            # Limpar mensagens antigas (7 dias)
            cutoff_date = datetime.now() - timedelta(days=7)
            old_messages = Message.query.filter(Message.created_at < cutoff_date).delete()
            
            # Limpar screenshots antigos (7 dias)
            old_screenshots = Screenshot.query.filter(Screenshot.created_at < cutoff_date).delete()
            
            # Limpar sessões antigas (24 horas)
            session_cutoff = datetime.now() - timedelta(hours=24)
            old_sessions = LiveSession.query.filter(
                LiveSession.created_at < session_cutoff,
                LiveSession.active == False
            ).delete()
            
            self.db.session.commit()
            
            self.logger.info(f"Limpeza concluída: {old_messages} mensagens, {old_screenshots} screenshots, {old_sessions} sessões")
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza: {e}")
            self.db.session.rollback()

class ConnectionManager:
    def __init__(self):
        self.connections = {}
        self.connection_count = 0
        self.max_connections = int(os.getenv('MAX_CONCURRENT_USERS', 5000))
        self.logger = logging.getLogger(__name__)
        
    def add_connection(self, sid, user_info=None):
        """Adicionar conexão"""
        if self.connection_count >= self.max_connections:
            self.logger.warning(f"Limite de conexões atingido: {self.connection_count}")
            return False
            
        self.connections[sid] = {
            'connected_at': datetime.now(),
            'user_info': user_info or {},
            'last_activity': datetime.now()
        }
        self.connection_count += 1
        
        self.logger.info(f"Conexão adicionada: {sid} (Total: {self.connection_count})")
        return True
        
    def remove_connection(self, sid):
        """Remover conexão"""
        if sid in self.connections:
            del self.connections[sid]
            self.connection_count -= 1
            self.logger.info(f"Conexão removida: {sid} (Total: {self.connection_count})")
            
    def update_activity(self, sid):
        """Atualizar atividade da conexão"""
        if sid in self.connections:
            self.connections[sid]['last_activity'] = datetime.now()
            
    def cleanup_inactive_connections(self):
        """Limpar conexões inativas"""
        cutoff_time = datetime.now() - timedelta(minutes=30)
        inactive_sids = []
        
        for sid, info in self.connections.items():
            if info['last_activity'] < cutoff_time:
                inactive_sids.append(sid)
                
        for sid in inactive_sids:
            self.remove_connection(sid)
            
        if inactive_sids:
            self.logger.info(f"Removidas {len(inactive_sids)} conexões inativas")
            
    def get_connection_stats(self):
        """Obter estatísticas de conexões"""
        return {
            'total_connections': self.connection_count,
            'max_connections': self.max_connections,
            'utilization_percent': (self.connection_count / self.max_connections) * 100
        }

# Instâncias globais
performance_monitor = PerformanceMonitor()
connection_manager = ConnectionManager()

def init_monitoring(app, socketio, db):
    """Inicializar sistema de monitoramento"""
    global performance_monitor
    
    performance_monitor.app = app
    performance_monitor.socketio = socketio
    performance_monitor.start_monitoring()
    
    # Configurar limpeza automática
    db_optimizer = DatabaseOptimizer(db)
    
    import schedule
    schedule.every(6).hours.do(db_optimizer.cleanup_old_data)
    schedule.every(12).hours.do(db_optimizer.optimize_database)
    schedule.every(30).minutes.do(connection_manager.cleanup_inactive_connections)
    
    return performance_monitor, connection_manager


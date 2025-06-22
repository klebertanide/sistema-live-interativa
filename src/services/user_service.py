"""
Serviço para gerenciar sessões de usuários
CORRIGIDO - Importação correta do SQLAlchemy
"""

from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

# Importar a instância global do SQLAlchemy
db = SQLAlchemy()

class UserService:
    
    @staticmethod
    def register_user_session(session_id, user_agent, ip_address):
        """Registrar nova sessão de usuário"""
        try:
            from src.models.user_session import UserSession
            
            # Verificar se já existe
            existing = UserSession.query.filter_by(session_id=session_id).first()
            
            if existing:
                # Atualizar última atividade
                existing.last_activity = datetime.utcnow()
                existing.user_agent = user_agent
                existing.ip_address = ip_address
            else:
                # Criar nova sessão
                user_session = UserSession(
                    session_id=session_id,
                    user_agent=user_agent,
                    ip_address=ip_address
                )
                db.session.add(user_session)
            
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"❌ Erro ao registrar sessão: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def remove_user_session(session_id):
        """Remover sessão de usuário"""
        try:
            from src.models.user_session import UserSession
            
            user_session = UserSession.query.filter_by(session_id=session_id).first()
            if user_session:
                db.session.delete(user_session)
                db.session.commit()
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao remover sessão: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_online_users_count():
        """Obter contagem de usuários online"""
        try:
            from src.models.user_session import UserSession
            
            # Considerar usuários ativos nos últimos 5 minutos
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            
            count = UserSession.query.filter(
                UserSession.last_activity >= cutoff_time
            ).count()
            
            return count
            
        except Exception as e:
            print(f"❌ Erro ao contar usuários: {e}")
            return 0
    
    @staticmethod
    def cleanup_old_sessions():
        """Limpar sessões antigas (mais de 1 hora)"""
        try:
            from src.models.user_session import UserSession
            
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            
            old_sessions = UserSession.query.filter(
                UserSession.last_activity < cutoff_time
            ).all()
            
            for session in old_sessions:
                db.session.delete(session)
            
            db.session.commit()
            
            print(f"🧹 Limpeza: {len(old_sessions)} sessões antigas removidas")
            return len(old_sessions)
            
        except Exception as e:
            print(f"❌ Erro na limpeza de sessões: {e}")
            db.session.rollback()
            return 0


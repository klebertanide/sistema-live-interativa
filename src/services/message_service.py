"""
Serviço para gerenciar mensagens dos usuários
CORRIGIDO - Importação correta do SQLAlchemy
"""

from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

# Importar a instância global do SQLAlchemy
db = SQLAlchemy()

class MessageService:
    
    @staticmethod
    def create_message(name, content):
        """Criar nova mensagem"""
        try:
            from src.models.message import Message
            
            message = Message(
                name=name.strip(),
                content=content.strip(),
                displayed=False
            )
            
            db.session.add(message)
            db.session.commit()
            
            print(f"💬 Mensagem criada: {name} - {content[:50]}...")
            return message
            
        except Exception as e:
            print(f"❌ Erro ao criar mensagem: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_next_message():
        """Obter próxima mensagem para exibição"""
        try:
            from src.models.message import Message
            
            message = Message.query.filter_by(displayed=False).order_by(Message.created_at).first()
            return message
            
        except Exception as e:
            print(f"❌ Erro ao buscar mensagem: {e}")
            return None
    
    @staticmethod
    def mark_as_displayed(message_id):
        """Marcar mensagem como exibida"""
        try:
            from src.models.message import Message
            
            message = Message.query.get(message_id)
            if message:
                message.displayed = True
                message.displayed_at = datetime.utcnow()
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erro ao marcar mensagem: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_recent_messages(limit=50):
        """Obter mensagens recentes"""
        try:
            from src.models.message import Message
            
            messages = Message.query.order_by(Message.created_at.desc()).limit(limit).all()
            return messages
            
        except Exception as e:
            print(f"❌ Erro ao buscar mensagens recentes: {e}")
            return []
    
    @staticmethod
    def cleanup_old_messages(days=7):
        """Limpar mensagens antigas"""
        try:
            from src.models.message import Message
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            old_messages = Message.query.filter(
                Message.created_at < cutoff_date,
                Message.displayed == True
            ).all()
            
            for message in old_messages:
                db.session.delete(message)
            
            db.session.commit()
            
            print(f"🧹 Limpeza: {len(old_messages)} mensagens antigas removidas")
            return len(old_messages)
            
        except Exception as e:
            print(f"❌ Erro na limpeza de mensagens: {e}")
            db.session.rollback()
            return 0


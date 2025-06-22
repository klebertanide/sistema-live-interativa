"""
Sistema de Enquetes Inteligentes com GPT
Gera enquetes polêmicas/engraçadas baseadas nas transcrições do Whisper
"""

import logging
import threading
import time
import requests
import json
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class IntelligentPollService:
    def __init__(self, app, db, socketio, whisper_service):
        self.app = app
        self.db = db
        self.socketio = socketio
        self.whisper_service = whisper_service
        self.is_running = False
        self.thread = None
        
        # Configurações
        self.poll_interval = 8 * 60  # 8 minutos em segundos
        self.openai_api_key = "sk-proj-YOUR_API_KEY_HERE"  # Configurar no .env
        
        # Templates de enquetes criativas para fallback
        self.creative_templates = [
            {
                "keywords": ["engraçado", "rindo", "hilário", "comédia"],
                "question": "Qual o nível de comédia neste momento?",
                "options": ["Rindo até chorar 😂", "Comédia pura 🤣"]
            },
            {
                "keywords": ["polêmico", "controverso", "debate", "discussão"],
                "question": "Essa opinião é:",
                "options": ["Totalmente polêmica 🔥", "Controversa mas real 💯"]
            },
            {
                "keywords": ["incrível", "impressionante", "surreal"],
                "question": "Como vocês estão reagindo a isso?",
                "options": ["Mente explodindo 🤯", "Impressionado demais 😱"]
            },
            {
                "keywords": ["game", "jogo", "jogando"],
                "question": "Qual a vibe do jogo agora?",
                "options": ["Épico total 🎮", "Gameplay insana 🔥"]
            },
            {
                "keywords": ["música", "som", "beat"],
                "question": "Essa música está:",
                "options": ["Viciante demais 🎵", "Hit garantido 🎶"]
            }
        ]
        
        logger.info("📊 IntelligentPollService inicializado")
    
    def start(self):
        """Iniciar serviço de enquetes"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._poll_generation_loop, daemon=True)
            self.thread.start()
            logger.info("📊 Serviço de enquetes inteligentes iniciado")
    
    def stop(self):
        """Parar serviço de enquetes"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("📊 Serviço de enquetes inteligentes parado")
    
    def _poll_generation_loop(self):
        """Loop principal de geração de enquetes"""
        logger.info("📊 Iniciando loop de geração de enquetes")
        
        while self.is_running:
            try:
                # Aguardar intervalo
                time.sleep(self.poll_interval)
                
                if not self.is_running:
                    break
                
                # Buscar transcrições recentes
                transcriptions = self.whisper_service.get_recent_transcriptions(minutes=8)
                
                if len(transcriptions) >= 3:  # Mínimo 3 transcrições
                    logger.info(f"📊 Gerando enquete baseada em {len(transcriptions)} transcrições")
                    
                    # Gerar enquete
                    poll_data = self._generate_poll(transcriptions)
                    
                    if poll_data:
                        # Criar enquete no banco
                        self._create_poll_in_database(poll_data)
                else:
                    logger.info("📊 Aguardando mais transcrições para gerar enquete")
                
            except Exception as e:
                logger.error(f"❌ Erro no loop de enquetes: {e}")
                time.sleep(60)  # Aguardar 1 minuto em caso de erro
    
    def _generate_poll(self, transcriptions):
        """Gerar enquete baseada nas transcrições"""
        try:
            # Tentar usar GPT primeiro
            if self.openai_api_key and self.openai_api_key != "sk-proj-YOUR_API_KEY_HERE":
                poll_data = self._generate_poll_with_gpt(transcriptions)
                if poll_data:
                    return poll_data
            
            # Fallback: usar templates criativos
            logger.info("📊 Usando enquete criativa de fallback")
            return self._generate_creative_fallback_poll(transcriptions)
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar enquete: {e}")
            return None
    
    def _generate_poll_with_gpt(self, transcriptions):
        """Gerar enquete usando GPT"""
        try:
            # Combinar transcrições
            context = " ".join(transcriptions)
            
            # Prompt criativo para GPT
            prompt = f"""
            Baseado nesta conversa de live: "{context}"
            
            Crie uma enquete POLÊMICA e ENGRAÇADA com:
            1. Uma pergunta provocativa sobre o que foi dito
            2. Exatamente 2 opções de resposta criativas
            
            Seja autêntico, use gírias brasileiras e seja divertido!
            
            Responda APENAS em JSON:
            {{
                "question": "pergunta aqui",
                "option_a": "primeira opção",
                "option_b": "segunda opção"
            }}
            """
            
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': 'Você é um criador de enquetes polêmicas e engraçadas para lives brasileiras.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 200,
                'temperature': 0.9
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Tentar parsear JSON
                try:
                    poll_data = json.loads(content)
                    if 'question' in poll_data and 'option_a' in poll_data and 'option_b' in poll_data:
                        logger.info(f"📊 Enquete GPT criada: {poll_data['question']}")
                        return poll_data
                except json.JSONDecodeError:
                    pass
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao usar GPT: {e}")
            return None
    
    def _generate_creative_fallback_poll(self, transcriptions):
        """Gerar enquete criativa usando templates"""
        try:
            # Combinar todas as transcrições
            full_text = " ".join(transcriptions).lower()
            
            # Encontrar template mais relevante
            best_template = None
            max_matches = 0
            
            for template in self.creative_templates:
                matches = sum(1 for keyword in template["keywords"] if keyword in full_text)
                if matches > max_matches:
                    max_matches = matches
                    best_template = template
            
            # Se não encontrou matches, usar template aleatório
            if not best_template:
                best_template = random.choice(self.creative_templates)
            
            # Criar enquete baseada no template
            poll_data = {
                "question": best_template["question"],
                "option_a": best_template["options"][0],
                "option_b": best_template["options"][1]
            }
            
            logger.info(f"📊 Enquete criativa criada: {poll_data['question']}")
            return poll_data
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar enquete criativa: {e}")
            return None
    
    def _create_poll_in_database(self, poll_data):
        """Criar enquete no banco de dados"""
        try:
            with self.app.app_context():
                from main import Poll
                
                # Desativar enquetes antigas
                old_polls = Poll.query.filter_by(active=True).all()
                for old_poll in old_polls:
                    old_poll.active = False
                
                # Criar nova enquete
                poll = Poll(
                    question=poll_data['question'],
                    option_a=poll_data['option_a'],
                    option_b=poll_data['option_b'],
                    active=True,
                    created_at=datetime.now()
                )
                
                self.db.session.add(poll)
                self.db.session.commit()
                
                logger.info(f"📊 Enquete criada no banco: {poll.question}")
                
                # Emitir via WebSocket
                if self.socketio:
                    self.socketio.emit('new_poll', poll.to_dict())
                
                return poll
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar enquete no banco: {e}")
            return None

# Funções de inicialização
def init_intelligent_poll_service(app, db, socketio, whisper_service):
    """Inicializar serviço de enquetes inteligentes"""
    return IntelligentPollService(app, db, socketio, whisper_service)

def get_intelligent_poll_service():
    """Obter instância do serviço de enquetes"""
    # Esta função será implementada no main.py
    pass


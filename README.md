# 🎬 Sistema de Live Interativa - Big Brother Moído

Sistema de live streaming interativo com funcionalidades avançadas de chat, enquetes e overlays para OBS.

## 🚀 Funcionalidades

- **Live Streaming Interativo**: Sistema completo de chat em tempo real
- **Enquetes Inteligentes**: Sistema de votação com análise de sentimentos
- **Overlays para OBS**: Integração direta com OBS Studio
- **Painel Administrativo**: Controle total da live
- **Processamento de Áudio**: Integração com Whisper para transcrição
- **Interface Responsiva**: Compatível com desktop e mobile

## 🛠️ Tecnologias

- **Backend**: Flask + SocketIO
- **Frontend**: HTML5, CSS3, JavaScript
- **Banco de Dados**: SQLAlchemy
- **WebSocket**: Para comunicação em tempo real
- **IA**: OpenAI Whisper para processamento de áudio

## 📦 Instalação Local

### Pré-requisitos
- Python 3.8+
- pip

### Passos

1. **Clone o repositório**
```bash
git clone <seu-repositorio>
cd <nome-do-projeto>
```

2. **Crie um ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Execute a aplicação**
```bash
python src/main.py
```

5. **Acesse o sistema**
- Página Principal: http://localhost:8081
- Painel Admin: http://localhost:8081/admin
- Overlays OBS: http://localhost:8081/overlay

## 🌐 Deploy

Este projeto está configurado para deploy automático no Render.com.

### Variáveis de Ambiente

Certifique-se de configurar as seguintes variáveis no seu serviço de hospedagem:

```
FLASK_ENV=production
PORT=10000
LOG_LEVEL=INFO
```

## 📁 Estrutura do Projeto

```
├── src/
│   ├── main.py              # Arquivo principal da aplicação
│   ├── templates/           # Templates HTML
│   ├── static/             # Arquivos estáticos (CSS, JS, imagens)
│   ├── models/             # Modelos do banco de dados
│   ├── services/           # Serviços e lógica de negócio
│   └── utils/              # Utilitários
├── static/                 # Arquivos estáticos adicionais
├── requirements.txt        # Dependências Python
├── Procfile               # Configuração para deploy
└── README.md              # Este arquivo
```

## 🎯 Como Usar

1. **Iniciar Live**: Acesse o painel admin e configure sua live
2. **Chat Interativo**: Os usuários podem participar do chat em tempo real
3. **Enquetes**: Crie enquetes e veja os resultados em tempo real
4. **OBS Integration**: Use os overlays fornecidos no OBS Studio

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte e dúvidas, abra uma issue no repositório do GitHub.


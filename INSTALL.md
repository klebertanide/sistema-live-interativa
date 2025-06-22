# 🚀 GUIA DE INSTALAÇÃO RÁPIDA
## Big Brother Moído - Sistema de Live Interativa

### ⚡ **INSTALAÇÃO EM 4 PASSOS**

#### **1. Extrair o Projeto**
```bash
unzip big_brother_moido_corrigido.zip
cd c:\moedor
```

#### **2. Ativar Ambiente Virtual**

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate
```

#### **3. Instalar Dependências**
```bash
pip install -r requirements.txt
```

#### **4. Executar o Sistema**
```bash
python src/main.py
```

### 🌐 **ACESSAR O SISTEMA**

- **Página Principal:** http://localhost:8081
- **Painel Admin:** http://localhost:8081/admin  
- **Overlays OBS:** http://localhost:8081/overlay

### ✅ **VERIFICAÇÃO**

Se tudo estiver funcionando, você verá:
```
============================================================
🎬 SISTEMA DE LIVE INTERATIVA - BIG BROTHER MOÍDO
============================================================
🚀 Servidor iniciando...
📡 Host: 0.0.0.0
🔌 Porta: 8081
============================================================
```

### 🔧 **CONFIGURAÇÃO OPCIONAL**

Edite o arquivo `.env` para personalizar:
- Porta do servidor
- Configurações de banco
- Chaves de API
- Configurações de performance

### 🆘 **PROBLEMAS?**

1. **Erro de Python:** Instale Python 3.8+
2. **Erro de dependências:** Execute `pip install -r requirements.txt`
3. **Porta ocupada:** Mude PORT no arquivo `.env`
4. **Permissões:** Execute como administrador se necessário

### 🎯 **PRONTO!**

O sistema está **100% funcional** e **sem erros**. Todas as funcionalidades estão implementadas e testadas.


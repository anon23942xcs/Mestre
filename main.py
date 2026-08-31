import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import google.generativeai as genai
from dotenv import load_dotenv

# ============================================
# 1. CARREGAR CONFIGURAÇÕES
# ============================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("⚠️  AVISO: GEMINI_API_KEY não encontrada no arquivo .env")
    print("⚠️  Configure a chave antes de chamar a IA ou deixe a aplicação em modo de espera.")
    MODELO = None
else:
    genai.configure(api_key=API_KEY)
    MODELO = genai.GenerativeModel("gemini-1.5-flash")

ARQUIVO_ESTADO = Path(__file__).with_name("estado_salvo.json")

# ============================================
# 2. MODELOS DE DADOS (Pydantic)
# ============================================

class Atributos(BaseModel):
    forca: int = 5
    destreza: int = 5
    inteligencia: int = 5
    carisma: int = 5

class Jogador(BaseModel):
    nome: str
    idade: int
    genero: str
    aparencia: str
    historico: str
    atributos: Atributos = Atributos()
    inventario: List[str] = []
    pv: int = 20
    pv_max: int = 20

class NPC(BaseModel):
    id: str
    nome: str
    raca: str
    aparencia: str
    humor: str
    relacao: int = 0
    segredos: List[str] = []
    ultima_interacao: str = ""

class Estado(BaseModel):
    local: str
    regiao: str = "Reino de Valdris"
    hora: str = "manhã"
    clima: str = "normal"
    eventos_ativos: List[str] = []
    npc_ativos: List[NPC] = []
    memorias_recentes: List[str] = []
    memorias_importantes: List[str] = []

class Campanha(BaseModel):
    arco_principal: str = "Em aberto"
    progresso: int = 0
    vilao: Dict[str, str] = {}
    proximos_eventos: List[str] = []

class EstadoCompleto(BaseModel):
    mundo: str = "Fantasia Medieval - Alderan, Reino de Valdris"
    jogador: Jogador
    estado: Estado
    campanha: Campanha = Campanha()
    data_criacao: str = Field(default_factory=lambda: datetime.now().isoformat())
    ultima_atualizacao: str = Field(default_factory=lambda: datetime.now().isoformat())

# ============================================
# 3. MODELOS DE REQUISIÇÃO
# ============================================

class CriarPersonagemRequest(BaseModel):
    nome: str
    idade: int
    genero: str
    aparencia: str
    historico: str

class AcaoRequest(BaseModel):
    mensagem: str
    estado: Optional[Dict[str, Any]] = None

# ============================================
# 4. FUNÇÕES DE ESTADO
# ============================================

def carregar_estado() -> Optional[Dict[str, Any]]:
    if ARQUIVO_ESTADO.exists():
        with ARQUIVO_ESTADO.open("r", encoding="utf-8") as f:
            return json.load(f)
    return None

def salvar_estado(estado: Dict[str, Any]):
    with ARQUIVO_ESTADO.open("w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)

def criar_estado_inicial(dados: CriarPersonagemRequest) -> Dict[str, Any]:
    return {
        "mundo": "Fantasia Medieval - Alderan, Reino de Valdris",
        "jogador": {
            "nome": dados.nome,
            "idade": dados.idade,
            "genero": dados.genero,
            "aparencia": dados.aparencia,
            "historico": dados.historico,
            "atributos": {"forca": 5, "destreza": 5, "inteligencia": 5, "carisma": 5},
            "inventario": ["roupas rasgadas"],
            "pv": 20,
            "pv_max": 20
        },
        "estado": {
            "local": "Taverna do Cão Caído - Alderan",
            "regiao": "Reino de Valdris",
            "hora": "manhã",
            "clima": "nublado",
            "eventos_ativos": [],
            "npc_ativos": [
                {
                    "id": "npc_001",
                    "nome": "Estalajadeira",
                    "raca": "humano",
                    "aparencia": "mulher robusta, avental manchado, cabelo preso",
                    "humor": "indiferente",
                    "relacao": 0,
                    "segredos": [],
                    "ultima_interacao": "observa o novo cliente"
                }
            ],
            "memorias_recentes": [],
            "memorias_importantes": []
        },
        "campanha": {
            "arco_principal": "Em busca de vingança",
            "progresso": 0,
            "vilao": {"nome": "Desconhecido", "objetivo": "Desconhecido"},
            "proximos_eventos": []
        },
        "data_criacao": datetime.now().isoformat(),
        "ultima_atualizacao": datetime.now().isoformat()
    }

# ============================================
# 5. FUNÇÕES DA IA
# ============================================

def gerar_resposta(estado: Dict[str, Any], mensagem_usuario: str) -> str:
    if not API_KEY or MODELO is None:
        return "⚠️ Ainda não há uma chave de API configurada. Coloque sua GEMINI_API_KEY no arquivo .env para ativar a IA."

    try:
        prompt = f"""
[INSTRUÇÕES DO MESTRE]
- Você é o Mestre de RPG. Narra a história, controla os NPCs e o mundo.
- NUNCA controle o personagem do jogador.
- NPCs têm personalidades próprias e podem discordar.
- Introduza conflitos quando a história estiver calma.
- Limite a resposta a 4 parágrafos.
- Seja descritivo, mostre emoções através de ações e diálogos.

[ESTADO DO MUNDO]
Mundo: {estado['mundo']}

[JOGADOR]
Nome: {estado['jogador']['nome']}
Idade: {estado['jogador']['idade']}
Aparência: {estado['jogador']['aparencia']}
Histórico: {estado['jogador']['historico']}
Atributos: Força {estado['jogador']['atributos']['forca']}, Destreza {estado['jogador']['atributos']['destreza']}, Inteligência {estado['jogador']['atributos']['inteligencia']}, Carisma {estado['jogador']['atributos']['carisma']}
Inventário: {', '.join(estado['jogador']['inventario']) if estado['jogador']['inventario'] else 'Nenhum'}
PV: {estado['jogador']['pv']}/{estado['jogador']['pv_max']}

[LOCAL]
{estado['estado']['local']} - {estado['estado']['hora']}
Clima: {estado['estado']['clima']}

[NPCs PRESENTES]
"""
        for npc in estado['estado']['npc_ativos']:
            prompt += f"- {npc['nome']} ({npc['raca']}): {npc['aparencia']} - Humor: {npc['humor']}, Relação: {npc['relacao']}/10\n"

        prompt += f"""
[EVENTOS ATIVOS]
{', '.join(estado['estado']['eventos_ativos']) if estado['estado']['eventos_ativos'] else 'Nenhum evento ativo'}

[MEMÓRIAS RECENTES]
{', '.join(estado['estado']['memorias_recentes']) if estado['estado']['memorias_recentes'] else 'A história está começando'}

[MEMÓRIAS IMPORTANTES]
{', '.join(estado['estado']['memorias_importantes']) if estado['estado']['memorias_importantes'] else 'Nenhuma memória importante ainda'}

[ARCO PRINCIPAL]
{estado['campanha']['arco_principal']} - Progresso: {estado['campanha']['progresso']}%

[MENSAGEM DO JOGADOR]
"{mensagem_usuario}"

[RESPOSTA DO MESTRE]
Escreva a narração em prosa, mantendo a imersão e a coerência. Não controle o jogador.
"""

        resposta = MODELO.generate_content(prompt)
        texto = resposta.text
        if "```" in texto:
            texto = texto.split("```")[0].strip()
        return texto
    except Exception as e:
        print(f"❌ Erro na IA: {e}")
        return f"[Erro ao gerar resposta. Verifique a chave da API. Detalhes: {e}]"

def atualizar_estado(estado: Dict[str, Any], mensagem_usuario: str, resposta_ia: str) -> Dict[str, Any]:
    if len(estado['estado']['memorias_recentes']) >= 5:
        estado['estado']['memorias_recentes'].pop(0)
    estado['estado']['memorias_recentes'].append(f"Jogador: {mensagem_usuario[:50]}...")
    estado['ultima_atualizacao'] = datetime.now().isoformat()
    return estado

# ============================================
# 6. API (FastAPI)
# ============================================

app = FastAPI(title="Mestre", version="1.0")

@app.get("/")
async def raiz():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mestre - RPG com IA</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 0 auto; padding: 20px; background: #1a1a2e; color: #eee; }
            .chat { background: #16213e; padding: 20px; border-radius: 10px; height: 400px; overflow-y: auto; margin-bottom: 20px; }
            .msg-user { background: #0f3460; padding: 10px; margin: 5px 0; border-radius: 5px; text-align: right; }
            .msg-ia { background: #1a1a2e; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 3px solid #e94560; }
            input, button, textarea { padding: 10px; font-size: 16px; border: none; border-radius: 5px; }
            input { flex: 1; background: #0f3460; color: white; }
            button { background: #e94560; color: white; cursor: pointer; margin-left: 10px; }
            .form-row { display: flex; }
            .status { margin-top: 10px; padding: 10px; background: #0f3460; border-radius: 5px; font-size: 12px; }
            .login-form { background: #16213e; padding: 20px; border-radius: 10px; }
            .login-form input, .login-form textarea { width: 100%; margin-bottom: 5px; background: #0f3460; color: white; border: 1px solid #1a1a2e; }
            .login-form textarea { height: 60px; }
            h1 { color: #e94560; }
        </style>
    </head>
    <body>
        <h1>🎲 Mestre</h1>
        <p><i>Motor de RPG com IA - Interface de Teste</i></p>
        
        <div id="personagem-area">
            <h3>📝 Criar Personagem</h3>
            <div class="login-form">
                <input type="text" id="nome" placeholder="Nome">
                <input type="number" id="idade" placeholder="Idade">
                <input type="text" id="genero" placeholder="Gênero">
                <input type="text" id="aparencia" placeholder="Aparência">
                <textarea id="historico" placeholder="Histórico do personagem"></textarea>
                <button onclick="criarPersonagem()" style="width:100%;">🌟 Iniciar Aventura</button>
            </div>
        </div>
        
        <div id="chat-area" style="display:none;">
            <div class="chat" id="chat"></div>
            <div class="form-row">
                <input type="text" id="mensagem" placeholder="O que você faz?" onkeypress="if(event.key==='Enter') enviarMensagem()">
                <button onclick="enviarMensagem()">Enviar</button>
            </div>
            <div class="status" id="status">Aguardando ação...</div>
        </div>
        
        <script>
            let estadoAtual = null;
            
            async function criarPersonagem() {
                const dados = {
                    nome: document.getElementById('nome').value || 'Aventureiro',
                    idade: parseInt(document.getElementById('idade').value) || 20,
                    genero: document.getElementById('genero').value || 'Indefinido',
                    aparencia: document.getElementById('aparencia').value || 'Viajante comum',
                    historico: document.getElementById('historico').value || 'Um viajante em busca de aventuras'
                };
                
                const resp = await fetch('/iniciar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(dados)
                });
                
                estadoAtual = await resp.json();
                document.getElementById('personagem-area').style.display = 'none';
                document.getElementById('chat-area').style.display = 'block';
                document.getElementById('status').innerHTML = '✅ Personagem criado! Envie sua primeira ação.';
                
                const chat = document.getElementById('chat');
                chat.innerHTML = '<div class="msg-ia">🎲 Bem-vindo a Alderan, viajante. O que você deseja fazer?</div>';
            }
            
            async function enviarMensagem() {
                const input = document.getElementById('mensagem');
                const msg = input.value.trim();
                if (!msg || !estadoAtual) return;
                
                input.value = '';
                
                const chat = document.getElementById('chat');
                chat.innerHTML += `<div class="msg-user">🗡️ ${msg}</div>`;
                chat.scrollTop = chat.scrollHeight;
                
                document.getElementById('status').innerHTML = '⏳ O Mestre está pensando...';
                
                try {
                    const resp = await fetch('/acao', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ mensagem: msg, estado: estadoAtual })
                    });
                    
                    const dados = await resp.json();
                    estadoAtual = dados.estado;
                    
                    chat.innerHTML += `<div class="msg-ia">📖 ${dados.resposta}</div>`;
                    chat.scrollTop = chat.scrollHeight;
                    
                    document.getElementById('status').innerHTML = `📍 ${dados.estado.estado.local} - ${dados.estado.estado.hora}`;
                } catch (e) {
                    document.getElementById('status').innerHTML = '❌ Erro: ' + e.message;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

@app.post("/iniciar")
async def iniciar_campanha(dados: CriarPersonagemRequest):
    estado = criar_estado_inicial(dados)
    salvar_estado(estado)
    return estado

@app.post("/acao")
async def processar_acao(requisicao: AcaoRequest):
    mensagem = requisicao.mensagem
    estado = requisicao.estado

    if not mensagem:
        raise HTTPException(status_code=400, detail="Mensagem obrigatória")

    if not estado:
        estado = carregar_estado()
        if not estado:
            raise HTTPException(status_code=400, detail="Nenhuma campanha ativa. Use /iniciar primeiro.")

    resposta = gerar_resposta(estado, mensagem)
    estado = atualizar_estado(estado, mensagem, resposta)
    salvar_estado(estado)

    return {"resposta": resposta, "estado": estado}

@app.get("/estado")
async def obter_estado():
    estado = carregar_estado()
    if not estado:
        raise HTTPException(status_code=404, detail="Nenhuma campanha ativa")
    return estado

@app.delete("/reiniciar")
async def reiniciar():
    if os.path.exists(ARQUIVO_ESTADO):
        os.remove(ARQUIVO_ESTADO)
    return {"mensagem": "Campanha reiniciada"}

# ============================================
# 7. EXECUÇÃO
# ============================================

if __name__ == "__main__":
    import uvicorn
    print("🎲 Mestre - Servidor Iniciado")
    print("🌐 http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
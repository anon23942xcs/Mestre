import os
import json
from typing import Dict, Any
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("⚠️  AVISO: GEMINI_API_KEY não encontrada no arquivo .env")

genai.configure(api_key=API_KEY or "chave_falsa_para_teste")
MODELO = genai.GenerativeModel("gemini-1.5-flash")

def gerar_resposta(estado: Dict[str, Any], mensagem_usuario: str) -> str:
    """Gera a resposta do narrador com base no estado e na mensagem do jogador"""
    
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
    
    try:
        resposta = MODELO.generate_content(prompt)
        texto = resposta.text
        if "```" in texto:
            texto = texto.split("```")[0].strip()
        return texto
    except Exception as e:
        print(f"❌ Erro na IA: {e}")
        return f"[Erro ao gerar resposta. Verifique a chave da API. Detalhes: {e}]"

def atualizar_estado(estado: Dict[str, Any], mensagem_usuario: str, resposta_ia: str) -> Dict[str, Any]:
    """Atualiza o estado com base na interação (versão simplificada)"""
    
    if len(estado['estado']['memorias_recentes']) >= 5:
        estado['estado']['memorias_recentes'].pop(0)
    estado['estado']['memorias_recentes'].append(f"Jogador: {mensagem_usuario[:50]}...")
    
    estado['ultima_atualizacao'] = datetime.now().isoformat()
    return estado

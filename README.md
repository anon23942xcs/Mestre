# Mestre - motor de RPG com IA

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate  # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edite o .env e coloque sua GEMINI_API_KEY
uvicorn app.main:app --reload
```

Abra `http://localhost:8000`. Testes locais (sem chamar a IA): `pytest`.

## Onde o projeto está

Ainda é um **protótipo jogável** do Modo Mestre: uma campanha de um jogador,
pipeline de IA + dados + estado em arquivos JSON, e uma UI de teste. Não há
login, banco, pagamento nem Modo Janitor.

O que já funciona de ponta a ponta:

- criar/retomar/apagar campanhas (`data/{id}.json`)
- turno: Intérprete → dados (se preciso) → Gerente (patch de estado) → Narrador
- compilação de memórias a cada N turnos
- o servidor é a fonte de verdade (o cliente não reenvia PV/inventário)

## Estrutura

```
app/
  config.py              .env, modelo Gemini, limites de memória
  main.py                FastAPI, / e /saude
  models/                estado do jogo, payloads da API, resultado de teste
  prompts/               system prompt + preencher() seguro
  services/
    ia_client.py         única camada Gemini
    interprete.py        Passo 1
    gerente.py           Passo 2 (aplica patch)
    narrador.py          Passo 3
    compilador.py        Passo 0 a cada N turnos
    dados.py             1d20 + atributo
    pipeline.py          orquestra o turno
    estado_inicial.py    cena inicial (taverna)
    formatadores.py      texto injetado nos prompts
  storage/repositorio.py arquivos JSON + lock por campanha
  routers/campanha.py    HTTP
  static/index.html      interface de teste
data/                    um .json por campanha (gitignorado)
tests/                   dados, patch, persistência, prompts (sem Gemini)
```

## Riscos de arquitetura (escalabilidade)

**Estes problemas não afetam MVP, mas aparecerão com crescimento:**

- **Pipeline**: `app/services/pipeline.py` orquestra hoje 5 passos. Com >7-8 passos novos, vai precisar refatoração (factory pattern ou state machine).
- **Armazenamento**: JSON em disco funciona até ~100 campanhas. Depois: Postgres + Redis cache.
- **Estado**: Hoje Estado tem ~5 listas. Evitar adicionar mais sem revisar modelo de persistência.
- **Validação em Pydantic**: Está correto. Manter assim (reduz "lixo" nos services).

## O que ainda não está resolvido

- **Autenticação.** Quem tem o `campanha_id` acessa a campanha.
- **Banco de dados.** JSON em disco não escala nem lista campanhas por usuário.
- **Rate limiting** das 50 mensagens/dia do Modo Janitor.
- **Modo Janitor.** Não implementado.
- **Histórico de chat completo.** Só a última narração e um FIFO de memórias recentes.

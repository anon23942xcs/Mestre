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
- catálogo canônico editável de personagens, locais, raças, itens e mais;
  cada ficha é persistida separadamente, com texto, atributos, imagem, tags
  e relações por ID com outras fichas
- o mesmo patch do Gerente pode atualizar fichas e relações da Wiki sem criar
  uma chamada adicional à IA por turno
- NPCs presentes e ausentes: quem deixa a cena permanece salvo, com sua
  localização e memória da relação, mas só os presentes são enviados à IA
- fichas extensas de jogador em Markdown são preservadas e organizadas por
  seção localmente, sem uma IA resumir ou alterar seu conteúdo
- cada mundo tem cenário, personalidade do Mestre, primeira mensagem e
  diálogos de exemplo, configuráveis ao criar a campanha

## Fichas e presença

O botão **Catálogo** dentro de uma campanha cria e edita as fichas manuais do
mundo. Elas são a fonte de verdade separada do estado dinâmico da partida.

As operações de presença também estão disponíveis pela API:

- `POST /campanhas/{id}/npcs/{npc_id}/sair` com `{ "local_ausente": "..." }`
- `POST /campanhas/{id}/npcs/{npc_id}/voltar`

O Gerente pode executar essas mudanças automaticamente em um turno. NPCs
ausentes não são incluídos na montagem de contexto do Gerente ou Narrador,
evitando o reenvio desnecessário de fichas.

## Ficha do jogador e configuração do mundo

Cole uma ficha completa no campo próprio ao criar o personagem. O texto fonte
é mantido intacto em `ficha_completa`; títulos Markdown como `## REGRAS` ou
`## HABILIDADES` também são separados automaticamente em `ficha_estruturada`
para dar contexto legível ao Narrador. Esse processo é local e determinístico:
não consome tokens nem altera o que foi escrito.

Na seção **Configurar mundo**, o criador pode definir os quatro blocos comuns
a plataformas de RP: cenário, personalidade do Mestre, primeira mensagem e
diálogos de exemplo. Há valores padrão se os campos forem deixados vazios.

## Wiki canônica e patch automático

As fichas ficam em `data/wiki/{campanha_id}/{ficha_id}.json`, separadas do
estado dinâmico da campanha. Uma ficha pode referenciar outras por relações,
por exemplo `{"contem_itens": ["item_espada"]}`. O Gerente inclui um
`patch_wiki` opcional na sua mesma resposta JSON para atualizar fatos e relações
persistentes; uma relação removida nunca apaga a ficha de destino.

## Estrutura

```
app/
  config.py              .env, modelo Gemini, limites de memória
  main.py                FastAPI, / e /saude
  models/                estado, ficha da Wiki, payloads e resultado de teste
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
    fichas_jogador.py    organização local de fichas Markdown
    wiki_gerente.py      aplicação defensiva de patch da Wiki
  storage/               campanha e fichas da Wiki em JSON atômico
  routers/               campanhas e Wiki HTTP
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

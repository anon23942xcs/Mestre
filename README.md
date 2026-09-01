# Mestre 0.8.0 - motor de RPG com IA

## Versão atual

**0.8.0** — Adiciona mundos canônicos como moldes: cada campanha recebe uma
cópia independente das fichas e da configuração do mundo escolhido.

O projeto usa versionamento semântico: `MAIOR.MENOR.CORREÇÃO`. Recursos novos
compatíveis elevam a versão menor; correções elevam a versão de correção;
mudanças incompatíveis elevam a maior.

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

- criar, retomar e apagar campanhas (`data/{id}.json`) a partir de um mundo e
  de um personagem reutilizáveis
- fluxo dinâmico na Home (`home.html`) para iniciar ou continuar campanhas
  diretamente a partir do card do mundo com seletor "Interpretando como",
  pré-seleção inteligente (personagem mais recente ou da campanha existente do mundo)
  e exclusão de campanhas sem recarregar a página
- melhorias visuais nos cards da Home com padding ampliado, elevação e sombras no hover,
  bordas arredondadas e hierarquia tipográfica reforçada
- criar, editar e apagar personagens separados das campanhas
  (`data/personagens/{id}.json`)
- criar, editar e apagar mundos canônicos (`data/mundos/{id}.json`) e suas
  fichas-base
- home em galeria de mundos e campanhas, com links diretos para jogar, editar ou abrir
  o mundo/campanha na Wiki
- turno: Intérprete → dados (se preciso) → Gerente (patch de estado) → Narrador
- compilação de memórias a cada N turnos
- o servidor é a fonte de verdade (o cliente não reenvia PV/inventário)
- Wiki por mundo e por campanha com sidebar colapsável por categoria, contadores
  dinâmicos `(N)`, listagem rápida e painel de perfil/detalhe rico com imagem,
  texto formatado, campos estruturados, tags e relações entre fichas
- o mesmo patch do Gerente pode atualizar fichas e relações da Wiki sem criar
  uma chamada adicional à IA por turno
- NPCs presentes e ausentes: quem deixa a cena permanece salvo, com sua
  localização e memória da relação, mas só os presentes são enviados à IA
- fichas extensas de jogador em Markdown são preservadas e organizadas por
  seção localmente, sem uma IA resumir ou alterar seu conteúdo
- cada mundo define cenário, personalidade do Mestre, primeira mensagem,
  diálogos de exemplo e sistema de regras para as campanhas que nascerem dele
- modo opcional de narrativa pura: sem dados, PV, testes ou rolagens no
  processamento e no contexto enviado ao Narrador
- sistemas de regras plugáveis, com contrato genérico de resultado; hoje há os
  plugins `d20` (padrão), `d10` (pool oposto) e `nenhum` (narrativa pura)

## Mundos, campanhas, Wiki e presença

A home em `/` lista mundos e campanhas separadamente. Em `/mundos`, é possível
criar e editar os moldes de mundo; a Wiki canônica de um molde fica em
`/mundos/{mundo_id}/wiki`. O CRUD correspondente usa `/api/mundos` e as fichas
do molde estão em `/api/mundos/{mundo_id}/fichas`.

Uma nova campanha exige um mundo e um personagem. O mundo fornece a
configuração e suas fichas são copiadas de `mundo_{mundo_id}` para
`campanha_{campanha_id}`; são arquivos independentes, preservando os IDs. Por
isso, editar ou apagar um mundo nunca modifica campanhas existentes, e apagar
uma campanha limpa somente a sua cópia. Campanhas antigas, cujas fichas ainda
estão em `data/wiki/{campanha_id}/`, continuam legíveis.

Uma campanha nova não cria NPCs ou fichas automaticamente: ela começa com a
cena descrita na configuração do mundo e com a cópia das fichas do molde.

O início e a retomada de aventuras são feitos diretamente na galeria da Home:
ao selecionar o personagem no card do mundo ("Interpretando como"), a interface
identifica se já existe uma campanha para a dupla mundo + personagem e alterna
o botão entre "Continuar campanha" (levando a `/jogo?campanha_id={id}`) e
"Iniciar nova campanha" (criando a campanha e iniciando o jogo). O formulário
manual `/jogo?nova=1` continua disponível como alternativa. A campanha recebe
uma cópia inicial do personagem selecionado, portanto sua evolução, PV e
inventário não alteram o perfil nem outras campanhas. A Wiki da campanha fica
em `/campanhas/{id}/wiki`, com API em `/campanhas/{id}/catalogo`.

As operações de presença também estão disponíveis pela API:

- `POST /campanhas/{id}/npcs/{npc_id}/sair` com `{ "local_ausente": "..." }`
- `POST /campanhas/{id}/npcs/{npc_id}/voltar`

O Gerente pode executar essas mudanças automaticamente em um turno. NPCs
ausentes não são incluídos na montagem de contexto do Gerente ou Narrador,
evitando o reenvio desnecessário de fichas.

## Ficha do jogador e configuração do mundo

No catálogo **Meus personagens**, cada personagem pode ter uma ficha completa.
O texto fonte é mantido intacto em `ficha_completa`; títulos Markdown como
`## REGRAS` ou `## HABILIDADES` também são separados automaticamente em
`ficha_estruturada` quando a campanha começa, para dar contexto legível ao
Narrador. Esse processo é local e determinístico: não consome tokens nem
altera o que foi escrito.

Em **Mundos**, o criador define os blocos comuns: cenário, personalidade do
Mestre, primeira mensagem e diálogos de exemplo. Também define se o mundo usa
RPG e qual sistema de regras é usado. Ao desativar o sistema, campanhas novas
desse mundo tornam-se narrativa pura: ações não rolam testes e o Narrador não
recebe PV, HP, CDs, rolagens ou o bloco de resultado de dados.

## Sistemas de regras

O pipeline não conhece mais d20, atributos ou fórmulas de teste. Ele consulta
o registro em `app/systems/registro.py` pelo `sistema_id` da campanha, recebe
um `ResultadoTesteGenerico` e passa apenas o resumo narrativo ao Mestre.

`d20` mantém exatamente a regra anterior (1d20 + atributo versus dificuldade,
com críticos em 20 e 1) reutilizando `services/dados.py`. `d10` rola pools do
jogador e da oposição; cada d10 igual ou acima do limiar é um sucesso, e vence
quem tiver mais sucessos (empate é falha do jogador). A oposição usa
`max(1, (dificuldade - 6) // 2)`, limitada a 7 dados. O limiar e os pontos do
d10 são configuráveis no molde de mundo.
`nenhum` retorna um resultado vazio e serve à narrativa pura. Um novo sistema
só precisa implementar o contrato de `app/systems/base.py` e ser registrado,
sem reescrever o pipeline.

## Wiki copiada e patch automático

As fichas canônicas ficam em `data/wiki/mundo_{mundo_id}/{ficha_id}.json` e a
cópia da campanha em `data/wiki/campanha_{campanha_id}/{ficha_id}.json`.
Uma ficha pode referenciar outras por relações,
por exemplo `{"contem_itens": ["item_espada"]}`. O Gerente inclui um
`patch_wiki` opcional na sua mesma resposta JSON para atualizar fatos e relações
persistentes; uma relação removida nunca apaga a ficha de destino.

## Estrutura

```
app/
  config.py              .env, modelo Gemini, limites de memória
  main.py                FastAPI, páginas estáticas e /saude
  models/                estado, mundo, personagem, ficha da Wiki e payloads
  prompts/               system prompt + preencher() seguro
  services/
    ia_client.py         única camada Gemini
    interprete.py        Passo 1
    gerente.py           Passo 2 (aplica patch)
    narrador.py          Passo 3
    compilador.py        Passo 0 a cada N turnos
    dados.py             1d20 + atributo
    pipeline.py          orquestra o turno
    estado_inicial.py    estado inicial derivado da configuração do mundo
    formatadores.py      texto injetado nos prompts
    fichas_jogador.py    organização local de fichas Markdown
    wiki_gerente.py      aplicação defensiva de patch da Wiki
  storage/               campanhas, mundos, personagens e fichas em JSON atômico
  routers/               campanhas, mundos, personagens e Wiki HTTP
  static/
    home.html            galeria de campanhas (/)
    index.html           tela do jogo (/jogo)
    personagens.html     catálogo de personagens reutilizáveis
    mundos.html          CRUD dos moldes de mundo
    wiki.html            painel da Wiki por campanha
    ficha.html           detalhe e edição de uma ficha da Wiki
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

- **Autenticação.** Quem tem um ID acessa campanhas, mundos, personagens e
  fichas correspondentes.
- **Banco de dados.** JSON em disco não escala nem lista campanhas por usuário.
- **Rate limiting** das 50 mensagens/dia do Modo Janitor.
- **Modo Janitor.** Não implementado.
- **Histórico de chat completo.** Só a última narração e um FIFO de memórias recentes.

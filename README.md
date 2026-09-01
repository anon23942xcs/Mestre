# Mestre 0.10.0 - motor de RPG com IA

## Versão atual

**0.10.0** — Visual clean unificado (estilo Antigravity IDE), sidebar global compartilhada,
foto do personagem do jogador, ficha completa e editável por campanha com isolamento atômico,
nome e foto do Mestre (= foto do mundo) configuráveis por mundo, edição direta de mundo na Wiki,
e consolidação de pontos de acesso no jogo.

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
- compilação de memórias a cada N turnos, com sincronização canônica da Wiki
- o servidor é a fonte de verdade (o cliente não reenvia PV/inventário)
- Wiki por mundo e por campanha com sidebar colapsável por categoria, contadores
  dinâmicos `(N)`, listagem rápida e painel de perfil/detalhe rico com imagem,
  texto formatado, campos estruturados, tags e relações entre fichas
- o mesmo patch do Gerente pode atualizar fichas, relações da Wiki e o estado
  do jogador (poderes adquiridos, itens, rank) sem chamada adicional à IA
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
- **histórico de chat completo** persistido em `historico_chat` no JSON da
  campanha, com edição de qualquer mensagem (jogador ou Mestre), deleção em
  cascata (apaga a mensagem e todas as subsequentes), regeneração da última
  resposta do Mestre, e indicador visual de digitação animado
- **sincronização canônica manual** via botão "⚡ Sincronizar Wiki" ou
  endpoint `POST /campanhas/{id}/sincronizar_wiki`: analisa os acontecimentos
  recentes e atualiza fichas da Wiki, jogador e memórias de longo prazo
- **foto do personagem e ficha completa editável em campanha**: suporte a campo `imagem`
  no perfil do personagem e no Jogador da campanha; modal rico com visualização de todos
  os atributos, inventário, PV e ficha estruturada, permitindo edição direta via
  `PUT /campanhas/{id}/jogador` com persistência atômica sem alterar o molde original
- **nome e foto do Mestre por mundo**: campos `nome_mestre` e `imagem_mestre` configuráveis
  em `ConfiguracaoMundo`, onde a imagem é também a capa do mundo na Home/lista de mundos e
  o avatar do Mestre no chat da sessão
- **edição de mundo integrada e sem retorno**: botão "⚙️ Editar Configuração do Mundo"
  acessível diretamente na visualização da Wiki do mundo (`/mundos/{id}/wiki`)
- **design clean e sidebar global unificada**: componente compartilhado (`shared.css` e
  `sidebar.js`) no estilo Antigravity IDE, com sub-navegação na Wiki em duas colunas sem conflitos,
  e consolidação de pontos de acesso únicos para Ficha e Wiki no jogo

## Histórico de chat e edição de mensagens

Toda mensagem trocada entre jogador e Mestre é salva sequencialmente em
`estado.historico_chat`. As operações disponíveis:

- `PUT /campanhas/{id}/mensagens/{msg_id}` — edita o conteúdo de qualquer
  mensagem (jogador ou Mestre). Se for a última do Mestre, sincroniza com
  `ultima_narracao`.
- `DELETE /campanhas/{id}/mensagens/{msg_id}` — apaga a mensagem e **todas as
  mensagens posteriores** (cascata). Recalcula `turno` e `ultima_narracao`.
- `POST /campanhas/{id}/regenerar` — remove a última resposta do Mestre e
  reprocessa o turno com a última ação do jogador.

O histórico é podado automaticamente quando excede `LIMITE_HISTORICO_CHAT`
(padrão: 200 mensagens). A primeira mensagem (abertura do mundo) é sempre
preservada; mensagens antigas já foram condensadas pelo compilador em
`memorias_importantes`.

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

O Gerente agora também recebe a lista de IDs e títulos das fichas da Wiki no
prompt, permitindo que ele referencie as fichas corretas ao aplicar mudanças
drásticas (mortes, destruição de locais, absorção de poderes).

O compilador (`compilar_e_sincronizar_wiki`) vai além do patch por turno:
analisa o histórico recente completo e pode criar fichas novas, atualizar
campos e conteúdo de fichas existentes, e registrar evolução do jogador
(novos poderes, mudança de rank, itens). É acionado automaticamente a cada
N turnos e manualmente pelo botão "⚡ Sincronizar Wiki".

## Estrutura

```
app/
  config.py              .env, modelo Gemini, limites de memória e chat
  main.py                FastAPI, páginas estáticas e /saude
  models/                estado, mundo, personagem, ficha da Wiki e payloads
  prompts/               system prompt + preencher() seguro
  services/
    ia_client.py         única camada Gemini
    interprete.py        Passo 1
    gerente.py           Passo 2 (aplica patch de NPCs, Wiki e jogador)
    narrador.py          Passo 3
    compilador.py        Passo 0 a cada N turnos + sincronização canônica
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
    index.html           tela do jogo (/jogo) — chat moderno com edição/cascata
    personagens.html     catálogo de personagens reutilizáveis
    mundos.html          CRUD dos moldes de mundo
    wiki.html            painel da Wiki por campanha
    ficha.html           detalhe e edição de uma ficha da Wiki
data/                    um .json por campanha (gitignorado)
tests/                   dados, patch, persistência, prompts (sem Gemini)
```

## Riscos de arquitetura (escalabilidade)

**Estes problemas não afetam MVP, mas aparecerão com crescimento:**

- **Pipeline**: `app/services/pipeline.py` orquestra hoje 5-6 passos (Intérprete,
  Dados, Gerente, Narrador, Histórico, Compilador periódico). Com >7-8 passos
  novos, vai precisar refatoração (factory pattern ou state machine).
- **Armazenamento**: JSON em disco funciona até ~100 campanhas. Depois:
  Postgres + Redis cache. A listagem já foi otimizada para leitura parcial
  (4 KB por arquivo em vez de parse completo), mitigando o gargalo imediato.
- **Estado**: `historico_chat` cresce a cada turno, mas é podado
  automaticamente em `LIMITE_HISTORICO_CHAT` (padrão: 200 mensagens).
  Mensagens antigas já foram condensadas em `memorias_importantes` pelo
  compilador antes de serem perdidas. `jogador.historico` e
  `jogador.ficha_completa` crescem por concatenação de strings em
  `jogador_atualizado` — migrar para `List[str]` quando a ficha for
  reestruturada.
- **Validação em Pydantic**: Está correto. Manter assim (reduz "lixo" nos
  services).

## Correções na 0.9.0

- **Double-save removido**: `compilador.compilar_e_sincronizar_wiki()` não
  salva mais internamente — quem persiste é sempre o router/caller. Antes,
  turnos com compilação gravavam o estado duas vezes no disco.
- **Lógica hardcoded removida**: `compilador.py` e `narrador.py` não
  referenciam mais personagens específicos (ex: "Olive") por nome. Toda
  mudança de presença de NPCs é tratada pelo gerente via `npcs_saem_de_cena`.
- **Narrador respeita mortes**: o prompt do Narrador agora tem instrução
  explícita para nunca dar voz a NPCs mortos ou devorados conforme as
  memórias canônicas.
- **Backfill corrigido**: campanhas antigas sem `historico_chat` são
  preenchidas com `nome_mestre = "Mestre"` em vez de "Olive".
- **Listagem otimizada**: `repositorio.listar()` lê apenas 4 KB por arquivo
  (regex sobre cabeçalho) em vez de parsear o JSON inteiro.

## Correções na 0.9.1

- **Prompts neutros e genéricos**: todos os prompts de IA (`compilador.py`,
  `gerente.py` e `narrador.py`) tiveram seus exemplos substituídos por
  placeholders agnósticos ao mundo/campanha, evitando contaminação em mundos novos.
- **Remoção de regra hardcoded de cenário**: eliminada a condicional
  específica para o cenário "Karvane" em `estado_inicial.py`.
- **Interface e templates neutros**: placeholders em `index.html` foram
  neutralizados e constantes residuais de avatar removidas.
- **Desacoplamento de `data/`**: pasta `data/` incluída no `.gitignore` e
  desindexada do repositório git (`git rm -r --cached data`), impedindo
  o versionamento de dados de teste ou campanhas locais.

## O que ainda não está resolvido

- **Autenticação.** Quem tem um ID acessa campanhas, mundos, personagens e
  fichas correspondentes.
- **Banco de dados.** JSON em disco não escala nem lista campanhas por usuário.
- **Rate limiting** das 50 mensagens/dia do Modo Free.
- **Modo Free.** Não implementado.


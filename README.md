# Mestre 0.7.0 - motor de RPG com IA

## Versão atual

**0.7.0** — Adiciona personagens reutilizáveis, separados das campanhas, e
remove a ficha padrão criada automaticamente em toda nova campanha.

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

- criar, retomar e apagar campanhas (`data/{id}.json`), escolhendo um
  personagem reutilizável
- criar, editar e apagar personagens separados das campanhas
  (`data/personagens/{id}.json`)
- home em galeria de campanhas, com links reais para jogar ou abrir o mundo
  de cada campanha em outra aba
- turno: Intérprete → dados (se preciso) → Gerente (patch de estado) → Narrador
- compilação de memórias a cada N turnos
- o servidor é a fonte de verdade (o cliente não reenvia PV/inventário)
- catálogo canônico editável de personagens, locais, raças, itens e mais;
  cada ficha é persistida separadamente, com texto, atributos, imagem, tags
  e relações por ID com outras fichas, além de páginas próprias para listar e
  consultar cada ficha
- o mesmo patch do Gerente pode atualizar fichas e relações da Wiki sem criar
  uma chamada adicional à IA por turno
- NPCs presentes e ausentes: quem deixa a cena permanece salvo, com sua
  localização e memória da relação, mas só os presentes são enviados à IA
- fichas extensas de jogador em Markdown são preservadas e organizadas por
  seção localmente, sem uma IA resumir ou alterar seu conteúdo
- cada mundo tem cenário, personalidade do Mestre, primeira mensagem e
  diálogos de exemplo, configuráveis ao criar a campanha
- modo opcional de narrativa pura: sem dados, PV, testes ou rolagens no
  processamento e no contexto enviado ao Narrador
- sistemas de regras plugáveis, com contrato genérico de resultado; hoje há os
  plugins `d20` (padrão), `d10` (pool oposto) e `nenhum` (narrativa pura)

## Fichas, Wiki e presença

A home em `/` lista as campanhas em cartões e também leva a
`/personagens`, onde os personagens do jogador podem ser criados, editados,
apagados e reutilizados. `/jogo?nova=1` sempre abre o formulário limpo de uma
nova campanha; `/jogo?campanha_id={id}` abre uma campanha específica. Cada
campanha recebe uma cópia inicial do personagem selecionado, portanto sua
evolução, PV e inventário não alteram o perfil nem outras campanhas. A Wiki
de uma campanha fica em `/campanhas/{id}/wiki`: ela separa as nove categorias
de ficha e permite criar fichas. Cada cartão leva, por um link real, à página
da ficha em `/campanhas/{id}/wiki/{ficha_id}`, onde é possível consultar e
editar seu conteúdo. Links para relações levam às fichas relacionadas.

As fichas manuais do mundo continuam sendo a fonte de verdade separada do
estado dinâmico da partida e começam vazias em uma nova campanha. A API expõe
o catálogo completo em
`GET /campanhas/{id}/catalogo` e uma ficha em
`GET /campanhas/{id}/catalogo/{ficha_id}`; criação, edição e remoção continuam
em `POST`, `PUT` e `DELETE` no mesmo recurso.

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

Na seção **Configurar mundo**, o criador pode definir os quatro blocos comuns
a plataformas de RP: cenário, personalidade do Mestre, primeira mensagem e
diálogos de exemplo. Há valores padrão se os campos forem deixados vazios.

O mesmo painel inclui **Usar sistema de RPG**. Ele vem ativado por padrão e
preserva o modo tradicional de dados/PV. Ao desativá-lo, a campanha torna-se
narrativa pura: ações não rolam testes e o Narrador não recebe PV, HP, CDs,
rolagens ou o bloco de resultado de dados.

## Sistemas de regras

O pipeline não conhece mais d20, atributos ou fórmulas de teste. Ele consulta
o registro em `app/systems/registro.py` pelo `sistema_id` da campanha, recebe
um `ResultadoTesteGenerico` e passa apenas o resumo narrativo ao Mestre.

`d20` mantém exatamente a regra anterior (1d20 + atributo versus dificuldade,
com críticos em 20 e 1) reutilizando `services/dados.py`. `d10` rola pools do
jogador e da oposição; cada d10 igual ou acima do limiar é um sucesso, e vence
quem tiver mais sucessos (empate é falha do jogador). A oposição usa
`max(1, (dificuldade - 6) // 2)`, limitada a 7 dados. O limiar é configurável
na criação da campanha (5 fácil, 6 normal, 7 difícil, 8 muito difícil).
`nenhum` retorna um resultado vazio e serve à narrativa pura. Um novo sistema
só precisa implementar o contrato de `app/systems/base.py` e ser registrado,
sem reescrever o pipeline.

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
  main.py                FastAPI, páginas estáticas e /saude
  models/                estado, personagem, ficha da Wiki, payloads e resultado de teste
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
  storage/               campanhas, personagens e fichas da Wiki em JSON atômico
  routers/               campanhas, personagens e Wiki HTTP
  static/
    home.html            galeria de campanhas (/)
    index.html           tela do jogo (/jogo)
    personagens.html     catálogo de personagens reutilizáveis
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

- **Autenticação.** Quem tem o `campanha_id` acessa a campanha, sua Wiki e suas
  fichas.
- **Banco de dados.** JSON em disco não escala nem lista campanhas por usuário.
- **Rate limiting** das 50 mensagens/dia do Modo Janitor.
- **Modo Janitor.** Não implementado.
- **Histórico de chat completo.** Só a última narração e um FIFO de memórias recentes.

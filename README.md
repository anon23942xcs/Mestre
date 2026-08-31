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

Abra `http://localhost:8000`.

## O que mudou em relação à primeira versão

- **Modelo do Gemini corrigido.** `gemini-1.5-flash` foi desativado pela Google
  e retornava erro 404 em qualquer chamada. Trocado por `gemini-2.5-flash`,
  configurável via `GEMINI_MODEL` no `.env` para não precisar mexer no código
  na próxima vez que a Google aposentar um modelo.

- **Pipeline de 3 passos implementado de verdade.** Antes só existia o
  Narrador; NPCs, eventos e progresso da campanha nunca eram atualizados por
  IA. Agora existem `app/services/interprete.py` (Passo 1),
  `app/services/gerente.py` (Passo 2, aplica um patch estruturado no estado)
  e `app/services/narrador.py` (Passo 3), orquestrados por
  `app/services/pipeline.py`.

- **Compilador de memórias implementado.** `app/services/compilador.py` roda
  a cada `TURNOS_POR_COMPILACAO` turnos (padrão 10) e destila
  `memorias_recentes` em `memorias_importantes`, em vez do FIFO que só
  descartava sem resumir nada.

- **Sistema de dados real.** `app/services/dados.py` rola 1d20 + atributo
  contra uma dificuldade, em Python, fora do alcance do modelo de linguagem.
  O Narrador recebe o resultado já decidido e narra em cima dele, em vez de
  a IA decidir sozinha se o jogador teve sucesso (o mesmo problema que o
  Modo Janitor tem, de nunca dizer não).

- **Estado do lado do servidor é a fonte única de verdade.** O cliente não
  manda mais o estado inteiro de volta a cada ação, só a mensagem e o
  `campanha_id`. Isso fecha a brecha de o jogador editar `pv`, `atributos`
  ou `inventario` direto no navegador antes de reenviar.

- **Uma campanha por arquivo.** Trocado o único `estado_salvo.json` global
  (que fazia duas campanhas simultâneas se sobrescreverem) por um arquivo
  por `campanha_id` em `data/`. Ver `app/storage/repositorio.py`.

- **Erros técnicos separados da narrativa.** Antes, um erro de API virava
  texto de "narração" exibido ao jogador. Agora `RespostaAcao.erro` é um
  campo separado.

- **Código duplicado removido.** `ia_service.py` e a lógica de IA embutida em
  `main.py` eram quase idênticas e uma delas nunca era importada. Agora só
  existe `app/services/ia_client.py`.

## Estrutura

```
app/
  config.py           configurações (.env, nomes de modelo, limites)
  main.py             cria o FastAPI app e registra as rotas
  models/
    estado.py          Jogador, NPC, Estado, Campanha, EstadoCompleto
    requests.py         payloads de entrada/saída da API
  services/
    ia_client.py         única camada que fala com o Gemini
    interprete.py         Passo 1
    gerente.py            Passo 2
    narrador.py           Passo 3
    compilador.py         Passo 0 (a cada N turnos)
    dados.py               rolagem de dados / testes
    pipeline.py             orquestra os passos acima
  storage/
    repositorio.py        carregar/salvar/deletar campanhas em disco
  routers/
    campanha.py           rotas HTTP
  static/
    index.html              interface de teste
data/                    um .json por campanha (ignorado no git)
```

## O que ainda não está resolvido (próximos passos sugeridos)

- **Autenticação.** Hoje qualquer pessoa com o `campanha_id` acessa a
  campanha. Para o Modo Mestre pago, isso precisa de login e associação de
  campanhas a um usuário.
- **Banco de dados.** Armazenamento em arquivo JSON funciona para
  protótipo, mas não escala para muitos usuários simultâneos nem permite
  consultas (ex: listar campanhas de um usuário). A camada
  `storage/repositorio.py` foi desenhada para essa troca ser isolada do
  resto do sistema quando chegar a hora.
- **Rate limiting.** O limite de 50 mensagens/dia do Modo Janitor citado na
  especificação ainda não tem enforcement em código.
- **Modo Janitor.** Só o Modo Mestre foi implementado até aqui, já que era o
  que tinha código-base para partir.
- **Testes automatizados.** Não há testes ainda. Como cada serviço agora é
  uma função isolada e testável (interprete, gerente, narrador, compilador,
  dados), dá para escrever testes unitários mockando `ia_client.gerar_json`
  e `gerar_texto`.

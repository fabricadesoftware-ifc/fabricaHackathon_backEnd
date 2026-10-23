# API privada (cadastro, inscrição, "meus dados" e avaliação)

Base: `/api/`. Autenticação por JWT: `Authorization: Bearer <access>` (obtido em `POST /api/token/`).
Erros de validação voltam como `400` com o formato `{"campo": ["mensagem"]}` (ou `{"campo": "mensagem"}`), sempre em português.
Sem token: `401`. Perfil sem permissão: `403`.

## Perfis (`tipoUser`)

| Perfil | Pode |
|---|---|
| `PARTICIPANTE` | Todo cadastro nasce assim. Inscreve e gerencia a própria equipe; vê só as próprias equipes/projetos. |
| `AVALIADOR` | Lança notas nas edições em que está vinculado (`AvaliadorEdicao`). Vê só as próprias notas. |
| `PROFESSOR` | Lê todas as equipes, projetos, integrantes e notas. **Não escreve nada.** |
| `ADMIN` | Gerencia tudo (exceto o que está bloqueado em edição `FINALIZADO`). Aprova/recusa solicitações de perfil. |

Ninguém além do admin altera o `tipoUser` (inclusive o próprio) via `PATCH /api/users/{id}/` → `400`.

## Status da edição

`INSCRICAO → EM_ANDAMENTO → AVALIACAO → FINALIZADO`. Só avança, um passo por vez (vale também para admin).
`PATCH /api/edicoes/{id}/ {"status": "..."}` fora da ordem → `400 {"status": "Transição inválida: ..."}`.
Edição nova só pode ser criada em `INSCRICAO`.

Quando `FINALIZADO`: edição, equipes, projetos, participantes e notas ficam **somente leitura** (qualquer escrita, até do admin, devolve `403`).

---

## Cadastro e solicitação de perfil

### `POST /api/auth/registro/` — público (limite anônimo `120/min`)

Corpo:
```json
{ "email": "ana@ex.com", "password": "Senha-forte-123", "first_name": "Ana", "last_name": "Silva",
  "username": "ana (opcional; padrão = e-mail)", "perfil_solicitado": "AVALIADOR | PROFESSOR (opcional)" }
```
Resposta `201`: `{ "id", "username", "first_name", "last_name", "email" }`. A conta é sempre `PARTICIPANTE`.
Se `perfil_solicitado` vier, cria uma solicitação `PENDENTE`; o perfil só muda quando um admin aprovar.
Erros `400`: e-mail já cadastrado (`email`), senha fraca (`password`, validators do Django), `perfil_solicitado` fora de `AVALIADOR`/`PROFESSOR`.

### `GET /api/solicitacoes-perfil/` — só ADMIN
Lista paginada. Filtros: `?status=PENDENTE|APROVADA|RECUSADA`, `?usuario=<id>` (status inválido → `400`).
Item: `id, usuario, usuario_email, usuario_nome, perfil_solicitado, status, criada_em, decidida_em, decidida_por, decidida_por_email`.

### `POST /api/solicitacoes-perfil/{id}/aprovar/` e `.../recusar/` — só ADMIN
Sem corpo. `200` devolve a solicitação atualizada. Aprovar altera o `tipoUser` do usuário. Solicitação já decidida → `400 {"status": "Esta solicitação já foi decidida."}`.
O mesmo painel existe no Django admin (`/admin/`, "Solicitações de perfil": lista filtrável + ações em massa de aprovar/recusar).

---

## Inscrição de equipe — `PARTICIPANTE`

Criar a equipe, trocar o nome e mexer nos membros só funcionam com a edição em `INSCRICAO`. Tema, descrição, link e logo do projeto (e o nome do projeto) também podem ser alterados com a edição `EM_ANDAMENTO`. As alterações são do **criador** da equipe (outros integrantes recebem `403`; quem não é da equipe recebe `404`).

### `POST /api/inscricoes/`
Cria `Equipe` + `Projeto` + integrantes em uma única transação (qualquer erro desfaz tudo; edição travada com `select_for_update` para respeitar `maximo_equipes` em concorrência).
```json
{ "edicao": 1, "nome_equipe": "Alfa",
  "projeto": { "nome_projeto": "App" },   // só o nome é obrigatório
  // opcionais, podem ser preenchidos depois: "tema": 3, "projeto.descricao_projeto", "projeto.link_deploy_projeto"
  "membros": ["colega1@ex.com", "colega2@ex.com"] }
```
`membros` = e-mails dos **demais** integrantes (o criador entra automaticamente e conta no mín./máx.).
Resposta `201`: equipe no formato de `GET /api/me/equipes/` (abaixo).

Erros `400` (por campo):
- `edicao`: inscrições fechadas; limite de equipes atingido; você já está em outra equipe da edição.
- `tema` (opcional): não pertence à edição.

O `link_deploy_projeto` também é preenchido automaticamente com o link de hospedagem informado na pré-avaliação (quando não é um endereço local).
- `nome_equipe`: já existe na edição.
- `membros` (lista de mensagens, uma por e-mail problemático): e-mail não cadastrado; usuário sem perfil de Participante; já está em outra equipe da edição; e-mail repetido; seu próprio e-mail; mínimo/máximo de participantes da edição.
- `projeto`, `nome_equipe`, ... : campos obrigatórios/ inválidos.

### `PATCH /api/inscricoes/{equipe_id}/` — criador
Parcial: `nome_equipe`, `tema`, `projeto: {nome_projeto, descricao_projeto, link_deploy_projeto}`. Devolve a equipe.

### `POST /api/inscricoes/{equipe_id}/membros/` — criador
`{"membros": ["novo@ex.com"]}`. Mesmas regras de e-mail; respeita o máximo. Devolve a equipe.

### `DELETE /api/inscricoes/{equipe_id}/membros/{usuario_id}/` — criador
Remove um integrante (não o criador; não pode ficar abaixo do mínimo). Devolve a equipe.

### `POST /api/inscricoes/{equipe_id}/logo/` e `DELETE /api/inscricoes/{equipe_id}/logo/` — criador
`POST` com `multipart/form-data` e o campo `logo_projeto` (JPEG, PNG ou WebP, até 5 MB) envia ou troca a logo do projeto; `DELETE` remove. Só o criador, com a edição em `INSCRICAO` ou `EM_ANDAMENTO` (`400` fora disso). Devolve a equipe no formato de `GET /api/me/equipes/`. Arquivo ausente ou inválido → `400 {"logo_projeto": ...}`.

### `POST /api/inscricoes/{equipe_id}/sair/` — integrante não criador
`204`. Não pode deixar a equipe abaixo do mínimo (`400`); o criador deve excluir a equipe (`403`).

### `DELETE /api/inscricoes/{equipe_id}/` — criador
Exclui equipe, projeto e vínculos. `204`.

---

## Meus dados

### `GET /api/me/` — qualquer autenticado
`{ id, username, first_name, last_name, email, tipoUser, foto_perfil, solicitacao_perfil: {id, perfil_solicitado, status} | null }`

### `PATCH /api/me/` — qualquer autenticado
Edita o **próprio** perfil: `first_name`, `last_name` e `foto_perfil` (JSON; ou `multipart/form-data` para enviar a foto; `null` remove). `username`, `email` e `tipoUser` são ignorados (o e-mail é o login). Foto JPEG/PNG/WebP até 5 MB (`400` se inválida). Devolve o mesmo formato de `GET /api/me/`.

### `GET /api/me/equipes/` — PARTICIPANTE (só as suas) · PROFESSOR/ADMIN (todas, somente leitura) · AVALIADOR `403`
Lista sem paginação:
```json
[{ "id": 1, "nome_equipe": "Alfa", "edicao": 1, "edicao_status": "INSCRICAO", "tema_id": 3, "tema": "Educação",
   "criador": 7, "sou_criador": true,
   "membros": [{ "id": 7, "username": "...", "first_name": "...", "last_name": "...", "email": "..." }],
   "projeto": { "id": 1, "nome_projeto": "...", "descricao_projeto": "...", "link_deploy_projeto": null,
                "logo_projeto": null, "edicao": 1, "edicao_status": "INSCRICAO",
                "equipe": {"id": 1, "nome_equipe": "Alfa"}, "nota_final": null } }]
```
`nota_final` só vem preenchida (string com 2 casas) quando a edição está `FINALIZADO`.

### `GET /api/me/projetos/` — mesmas regras de visibilidade
Lista de projetos (formato `projeto` acima).

### `GET /api/me/avaliacoes/` — AVALIADOR (demais `403`)
Um item por projeto das edições em que o avaliador está vinculado:
```json
[{ "edicao": 1, "edicao_nome": "...", "edicao_status": "AVALIACAO", "avaliacao_aberta": true, "avaliador_id": 4,
   "projeto": { "id": 9, "nome_projeto": "...", "descricao_projeto": "...", "link_deploy_projeto": null, "equipe": "Alfa" },
   "total_criterios": 3,
   "criterios_avaliados": [{ "criterio_id": 1, "criterio": "Inovação", "nota_id": 12, "nota": "8.00" }],
   "criterios_pendentes": [{ "criterio_id": 2, "criterio": "Usabilidade" }],
   "concluido": false }]
```

---

## Avaliação (notas)

- Lançar/alterar/remover nota só com a edição em `AVALIACAO` (`400 {"projeto": ...}`); em `FINALIZADO` → `403`.
- O avaliador é **sempre o usuário autenticado** (vínculo `AvaliadorEdicao` da edição do projeto); o campo `avaliador` é somente leitura. Sem vínculo → `400 {"avaliador": ...}`. Enviar `avaliador` de outra pessoa → `403`.
- Critério deve ser da edição do projeto; `nota` entre 0 e 10 (`400` fora disso).
- Mesmo avaliador + projeto + critério repetido → `400` ("Este critério já foi avaliado ...").

### `POST /api/notas/` — AVALIADOR
`{"projeto": 9, "criterio": 1, "nota": "8.50", "comentario_nota": "opcional"}` → `201` `{id, nota, comentario_nota, projeto, criterio, avaliador}`.

### `POST /api/notas/lote/` — AVALIADOR
`{"projeto": 9, "notas": [{"criterio": 1, "nota": "8.5"}, {"criterio": 2, "nota": "7"}]}` (atômico) → `201` lista de notas.

### `PATCH /api/notas/{id}/`, `DELETE /api/notas/{id}/` — dono da nota
`avaliador` não muda. Notas de outros avaliadores não aparecem (`404`).

### `GET /api/notas/`
ADMIN/PROFESSOR veem todas; AVALIADOR só as próprias; PARTICIPANTE recebe lista vazia.

### Nota final
`notaFinal_projeto` é calculada automaticamente (somente leitura na API): média das médias de cada avaliador vinculado à edição.
Só existe quando **todos** os avaliadores vinculados avaliaram **todos** os critérios da edição; senão fica `null`.
Publicamente (e em `/api/me/...`) só aparece com a edição `FINALIZADO`.

### `GET /api/edicoes/{id}/ranking/` — público
`403` antes de `FINALIZADO`. Devolve **todas** as equipes com nota (sem limite de top-N), em ordem decrescente; empates dividem a posição (1, 1, 3, ...).

---

## Outras mudanças de comportamento
- `GET /api/participantes-equipe/`: ADMIN/PROFESSOR veem tudo; demais perfis só os integrantes das próprias equipes.
- `POST /api/equipes/` (admin) valida `maximo_equipes` e coerência de tema/projeto com a edição.
- `Equipe` ganhou o campo `criador` (nulo em equipes antigas).

---

## Pré-avaliação (vale 10% da nota final)

Formulário preenchido pela equipe em "Meus projetos". **Nota final = 90% da média dos avaliadores + 10% da nota da pré-avaliação** (0 a 10). Equipe que não responde fica com 0 nos 10%.

### Liberação e prazo (admin)
Na edição (`PATCH /api/edicoes/{id}/`, admin): `pre_avaliacao_liberada` (bool) e `prazo_pre_avaliacao` (data/hora ISO, ex.: 1h antes da avaliação). O formulário só aceita respostas quando **a edição está EM_ANDAMENTO, foi liberado e o prazo não passou**. Fora disso: `403` com o motivo. Respostas fora do prazo não existem (nota 0).

### `GET /api/me/projetos/{projeto_id}/pre-avaliacao/`
Membros da equipe, administrador, professor e avaliadores da edição (somente leitura para estes). Outros: `403`.

```json
{
  "projeto": 12, "edicao": 4, "aberta": true, "motivo_fechada": "", "liberada": true,
  "prazo": "2026-10-21T14:00:00-03:00", "preenchida": false,
  "integrantes": [{ "id": 3, "nome": "Ana" }, { "id": 5, "nome": "Beto" }],
  "opcoes": {
    "organizacao_metodo": [{ "valor": "KANBAN", "rotulo": "Kanban" }],
    "hospedagem_plataforma": [{ "valor": "FABROKU", "rotulo": "Fabroku" }],
    "banco_plataforma": [{ "valor": "FABROKU_POSTGRES", "rotulo": "PostgreSQL do Fabroku" }],
    "minimo_caracteres_textos": 30
  },
  "responsabilidades": [], "organizacao_metodo": "", "organizacao_link": "",
  "problema_entendido": "", "problema_explicacao": "", "maior_dificuldade": "", "proximos_passos": "",
  "arquivo_rfs_rnfs": null, "arquitetura_arquivo": null, "arquitetura_link": "",
  "hospedagem_plataforma": "", "hospedagem_link": "", "hospedagem_justificativa": "",
  "banco_plataforma": "", "banco_justificativa": "",
  "nota": "0.00", "detalhe_pontuacao": {}, "atualizada_em": null
}
```

### `PATCH /api/me/projetos/{projeto_id}/pre-avaliacao/` (também `PUT`; sempre parcial)
Somente **membros da equipe**. Aceita `application/json` ou `multipart/form-data` (necessário para enviar arquivos; nesse caso mande `responsabilidades` como string JSON). Pode salvar por partes: a pontuação é recalculada a cada gravação e devolvida na resposta (`nota`, `detalhe_pontuacao`).

| Campo | Regra |
|---|---|
| `responsabilidades` | lista `[{ "user": id, "area": "back" }]`; só integrantes da equipe, sem repetir, `area` de 1 a 60 caracteres |
| `organizacao_metodo` | `KANBAN`, `LISTA`, `CONVERSA`, `OUTRO` |
| `organizacao_link`, `arquitetura_link`, `hospedagem_link` | URL `http`/`https` |
| `problema_entendido`, `problema_explicacao`, `maior_dificuldade`, `proximos_passos`, `hospedagem_justificativa`, `banco_justificativa` | texto; só pontua com no mínimo 30 caracteres |
| `arquivo_rfs_rnfs` (obrigatório para pontuar o item), `arquitetura_arquivo` | arquivo até 10 MB: pdf, doc, docx, md, txt, png, jpg, jpeg, webp |
| `hospedagem_plataforma` | `FABROKU`, `OUTRA`, `LOCAL` |
| `banco_plataforma` | `FABROKU_POSTGRES`, `SUPABASE`, `NEON`, `RENDER`, `OUTRO`, `LOCAL` |

`nota` e `detalhe_pontuacao` são somente leitura. Erros: `400` por campo; `403` se não for membro ou se o formulário estiver fechado.

### Pontuação automática (0–10)
5 seções de 2 pontos; os itens de uma seção dividem os pontos igualmente.

| Seção | Itens |
|---|---|
| 1. Equipe e organização | área de **todos** os integrantes (1,0); método de organização (1,0) |
| 2. Entendimento do problema | 4 respostas de texto (0,5 cada, mínimo de 30 caracteres) |
| 3. Arquivos de arquitetura | arquivo de RFs/RNFs (1,0); arquivo **ou** link de arquitetura (1,0) |
| 4. Aplicação hospedada | onde + link (1,0); justificativa (1,0) |
| 5. Banco de dados | onde (1,0); justificativa (1,0) |

- Respondeu/entregou = 100% do item; em branco = 0%.
- **Local = 50% do item "onde/link"**: plataforma `LOCAL` ou link com `localhost`, `127.0.0.1`, IP de rede interna (10.x, 172.16–31.x, 192.168.x) ou nome interno (`.local`, `.internal`, sem domínio). Vale para a aplicação e para o banco. As justificativas não perdem pontos.
- Sem o arquivo de RFs/RNFs: 0 só naquele item; o resto não é afetado.
- `detalhe_pontuacao` traz seções, itens, pontos e o motivo de cada um (ex.: "aplicação local (50%)").

## Painel do administrador (`/api/painel/`, somente ADMIN)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/painel/edicoes/` | Todas as edições com contadores |
| GET | `/api/painel/edicoes/{id}/` | Resumo: dados, contagens, critérios, temas, avaliadores e progresso |
| GET | `/api/painel/edicoes/{id}/equipes/` | Equipes com membros, projeto, pré-avaliação e nota final |
| GET | `/api/painel/edicoes/{id}/resultados/` | Médias por critério/avaliador, pré-avaliação, nota final e posição (visível ao admin antes de FINALIZADO) |
| GET | `/api/painel/edicoes/{id}/avaliadores/` | Todos os usuários AVALIADOR com flag `vinculado` |
| POST | `/api/painel/edicoes/{id}/avaliadores/` | `{"user": id}` vincula avaliador |
| DELETE | `/api/painel/edicoes/{id}/avaliadores/{user_id}/` | Desvincula (400 se já lançou notas) |

Status, pré-avaliação (`pre_avaliacao_liberada`, `prazo_pre_avaliacao`) e demais dados seguem em `PATCH /api/edicoes/{id}/`.

## Link de convite da equipe

O mínimo de participantes **não** é exigido na inscrição (vale ao fechar as inscrições; o painel admin marca `abaixo_do_minimo`). Só o máximo barra.

- `MinhaEquipe` ganha `link_convite` (só o criador: `id, token, url`), `minimo_participantes` e `maximo_participantes`.
- `POST /api/inscricoes/{id}/link-convite/` gera (ou troca) o link reutilizável da equipe; `DELETE` desativa. Só o criador, em INSCRICAO.
- `GET /api/convites/{token}/` (público) → `valido, motivo, equipe, edicao, criador`.
- `POST /api/convites/{token}/aceitar/` (Participante logado) entra na equipe (só em INSCRICAO e se houver vaga).
- `FRONTEND_URL` (env) monta a URL do link (`FRONTEND_URL/convite/<token>`).
- `membros` na inscrição segue aceitando só e-mails de contas já cadastradas.

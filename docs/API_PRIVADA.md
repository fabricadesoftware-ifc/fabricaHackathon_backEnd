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

Só funciona com a edição em `INSCRICAO`. As alterações são do **criador** da equipe (outros integrantes recebem `403`; quem não é da equipe recebe `404`).

### `POST /api/inscricoes/`
Cria `Equipe` + `Projeto` + integrantes em uma única transação (qualquer erro desfaz tudo; edição travada com `select_for_update` para respeitar `maximo_equipes` em concorrência).
```json
{ "edicao": 1, "nome_equipe": "Alfa", "tema": 3,
  "projeto": { "nome_projeto": "App", "descricao_projeto": "...", "link_deploy_projeto": "https://... (opcional)" },
  "membros": ["colega1@ex.com", "colega2@ex.com"] }
```
`membros` = e-mails dos **demais** integrantes (o criador entra automaticamente e conta no mín./máx.).
Resposta `201`: equipe no formato de `GET /api/me/equipes/` (abaixo).

Erros `400` (por campo):
- `edicao`: inscrições fechadas; limite de equipes atingido; você já está em outra equipe da edição.
- `tema`: não pertence à edição.
- `nome_equipe`: já existe na edição.
- `membros` (lista de mensagens, uma por e-mail problemático): e-mail não cadastrado; usuário sem perfil de Participante; já está em outra equipe da edição; e-mail repetido; seu próprio e-mail; mínimo/máximo de participantes da edição.
- `projeto`, `nome_equipe`, ... : campos obrigatórios/ inválidos.

### `PATCH /api/inscricoes/{equipe_id}/` — criador
Parcial: `nome_equipe`, `tema`, `projeto: {nome_projeto, descricao_projeto, link_deploy_projeto}`. Devolve a equipe.

### `POST /api/inscricoes/{equipe_id}/membros/` — criador
`{"membros": ["novo@ex.com"]}`. Mesmas regras de e-mail; respeita o máximo. Devolve a equipe.

### `DELETE /api/inscricoes/{equipe_id}/membros/{usuario_id}/` — criador
Remove um integrante (não o criador; não pode ficar abaixo do mínimo). Devolve a equipe.

### `POST /api/inscricoes/{equipe_id}/sair/` — integrante não criador
`204`. Não pode deixar a equipe abaixo do mínimo (`400`); o criador deve excluir a equipe (`403`).

### `DELETE /api/inscricoes/{equipe_id}/` — criador
Exclui equipe, projeto e vínculos. `204`.

---

## Meus dados

### `GET /api/me/` — qualquer autenticado
`{ id, username, first_name, last_name, email, tipoUser, foto_perfil, solicitacao_perfil: {id, perfil_solicitado, status} | null }`

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

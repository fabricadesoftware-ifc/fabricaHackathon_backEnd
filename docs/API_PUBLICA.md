# API pública de leitura

Endpoints de **leitura sem login** para as telas públicas do front (Home, Edições, Edição `/:id` e Explorar).
Base: `/api/`. Nenhum desses endpoints devolve participantes, usuários ou e-mails.

## Regras gerais

- `GET`, `HEAD` e `OPTIONS` são públicos em: `edicoes`, `tipos-edicao`, `apoiadores`, `temas`, `criterios`, `projetos` e `equipes`.
- `POST`/`PUT`/`PATCH`/`DELETE` nesses recursos exigem token JWT de administrador (sem token: `401`; outro perfil: `403`).
- Continuam privados (`401` sem token): `users`, `participantes-equipe`, `avaliadores`, `notas`.
- **Paginação** em todas as listas: `{ "count", "next", "previous", "results" }`, 8 itens por página. Use `?page=2` e `?page_size=` (máximo 100).
- **Nota final:** `nota_final` é `null` enquanto a edição não estiver `FINALIZADO`. Valor vem como string com 2 casas (`"9.50"`).
- **Filtro inválido:** devolve `400` com a mensagem do campo (ex.: `{"ano": "Informe um número inteiro."}`); filtro válido sem resultado devolve lista vazia. Nunca `500`.
- **Limite:** usuários anônimos têm limite de requisições (padrão `120/min`, variável `ANON_THROTTLE_RATE`). Acima disso, `429`.
- **CORS:** origens liberadas via `CORS_ALLOWED_ORIGINS` (padrão `http://localhost:3000,http://localhost:5173`).
- **Imagem:** ainda não existe campo de imagem (fica para a issue #35).

### Mapeamento para o mock do front

| Front | API |
|---|---|
| `id`, `title`, `description` | `id`, `nome`, `descricao` |
| `status` / `statusLabel` | `status` (`INSCRICAO`, `EM_ANDAMENTO`, `AVALIACAO`, `FINALIZADO`) / `status_label` |
| `startDate`, `endDate` | `data_inicio`, `data_fim` |
| `teamsCounter` | `total_equipes` |
| `manager` | `responsavel` |
| `location` | `local` |
| `tags` (Critérios) | `criterios` |
| `sponsor` | `apoiadores` |
| `teams` | `equipes` |

---

## `GET /api/edicoes/`

Lista de edições.

| Parâmetro | Descrição |
|---|---|
| `status` | `INSCRICAO`, `EM_ANDAMENTO`, `AVALIACAO` ou `FINALIZADO` |
| `ano` | ano (inteiro) |
| `tipo_edicao` | id do tipo de edição |
| `search` | busca no nome |
| `ordering` | `data_inicio`, `-data_inicio`, `nome` (também `ano`). Padrão: `-data_inicio` |
| `page`, `page_size` | paginação |

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "nome": "Hackathon Inovação 2024",
      "ano": 2024,
      "status": "INSCRICAO",
      "status_label": "Inscrição",
      "data_inicio": "2024-05-01",
      "data_fim": "2024-05-04",
      "local": "Campus Videira - IFC",
      "responsavel": "Fábrica de Software",
      "tipo_edicao": "Híbrido",
      "total_equipes": 2
    }
  ]
}
```

## `GET /api/edicoes/{id}/`

Detalhe completo, para montar a página da edição com **uma chamada**: tudo da lista mais
`descricao`, `minimo_participantes`, `maximo_participantes`, `maximo_equipes`, `apoiadores`, `criterios`, `temas` e `equipes`.

```json
{
  "id": 4,
  "nome": "Hackathon Finalizado 2022",
  "ano": 2022,
  "status": "FINALIZADO",
  "status_label": "Finalizado",
  "data_inicio": "2022-09-15",
  "data_fim": "2022-09-18",
  "local": "Campus Videira - IFC",
  "responsavel": "Fábrica de Software",
  "tipo_edicao": "Híbrido",
  "total_equipes": 1,
  "descricao": "Edição de exemplo no status FINALIZADO.",
  "minimo_participantes": 3,
  "maximo_participantes": 5,
  "maximo_equipes": 20,
  "apoiadores": [{ "id": 1, "nome": "TechCorp", "tipo": "ouro" }],
  "criterios": [{ "id": 7, "nome": "Inovação" }],
  "temas": [{ "id": 9, "descricao_tema": "Educação" }],
  "equipes": [
    {
      "id": 12,
      "nome_equipe": "Os Compiladores",
      "edicao": 4,
      "tema": "Educação",
      "projeto": {
        "id": 12,
        "nome_projeto": "Estuda Fácil",
        "descricao_projeto": "Reforço escolar com gamificação.",
        "link_deploy_projeto": "https://estudafacil.example.com",
        "nota_final": "9.40"
      }
    }
  ]
}
```

## `GET /api/edicoes/{id}/ranking/`

Ranking de projetos por `nota_final` (maior primeiro). Empates dividem a posição (1, 2, 2, 4). Projetos sem nota ficam de fora. Resposta é uma lista simples (sem paginação).

- Edição `FINALIZADO`: `200`.
- Qualquer outro status: `403` com `{"detail": "O ranking só fica disponível quando a edição está finalizada."}`.
- Edição inexistente: `404`.

```json
[
  { "posicao": 1, "projeto_id": 12, "projeto": "Estuda Fácil", "equipe": "Os Compiladores", "nota_final": "9.40" },
  { "posicao": 1, "projeto_id": 13, "projeto": "Posto Online", "equipe": "Debug Team", "nota_final": "9.40" },
  { "posicao": 3, "projeto_id": 14, "projeto": "Poupa Já", "equipe": "Stack Overflowers", "nota_final": "8.20" }
]
```

## `GET /api/equipes/` e `GET /api/equipes/{id}/`

| Parâmetro | Descrição |
|---|---|
| `edicao` | id da edição |
| `search` | busca no nome da equipe |
| `ordering` | `nome_equipe`, `-nome_equipe`, `id` |
| `page`, `page_size` | paginação |

```json
{
  "id": 12,
  "nome_equipe": "Os Compiladores",
  "edicao": 4,
  "tema": "Educação",
  "projeto": {
    "id": 12,
    "nome_projeto": "Estuda Fácil",
    "descricao_projeto": "Reforço escolar com gamificação.",
    "link_deploy_projeto": "https://estudafacil.example.com",
    "nota_final": "9.40"
  }
}
```

## `GET /api/projetos/` e `GET /api/projetos/{id}/`

| Parâmetro | Descrição |
|---|---|
| `edicao` | id da edição |
| `search` | busca no nome do projeto |
| `ordering` | `nome_projeto`, `-nome_projeto`, `id` |
| `page`, `page_size` | paginação |

```json
{
  "id": 12,
  "nome_projeto": "Estuda Fácil",
  "descricao_projeto": "Reforço escolar com gamificação.",
  "link_deploy_projeto": "https://estudafacil.example.com",
  "edicao": 4,
  "nome_equipe": "Os Compiladores",
  "nota_final": "9.40"
}
```

`nome_equipe` é `null` se o projeto ainda não tem equipe.

## `GET /api/apoiadores/`

```json
{ "count": 1, "next": null, "previous": null, "results": [{ "id": 1, "nome": "TechCorp", "tipo": "ouro" }] }
```

## `GET /api/criterios/`, `GET /api/temas/`, `GET /api/tipos-edicao/`

```json
{ "count": 1, "next": null, "previous": null, "results": [{ "id": 7, "nome": "Inovação", "edicao": 4 }] }
```

- `criterios`: `id`, `nome`, `edicao`.
- `temas`: `id`, `descricao_tema`, `edicao`; aceita `?edicao_id=`.
- `tipos-edicao`: `id`, `nome`.

## Dados de exemplo

`pdm run populate` cria (de forma idempotente) uma edição em cada status, com equipes, projetos, apoiadores e critérios.

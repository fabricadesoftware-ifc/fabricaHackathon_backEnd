# Deploy no Fabroku

Arquivos: `Procfile` (web + release com `migrate`), `requirements.txt` (gerado do PDM) e `.python-version`.

## Atualizar dependências
Depois de mudar o `pyproject.toml`: `pdm export --no-hashes --prod -o requirements.txt` e commite.

## Variáveis de ambiente (painel do app)
| Variável | Valor |
|---|---|
| `SECRET_KEY` | chave nova (`python -c "import secrets; print(secrets.token_urlsafe(64))"`) |
| `DEBUG` | `False` |
| `DATABASE_URL` | fornecida ao anexar o serviço PostgreSQL |
| `ALLOWED_HOSTS` | domínio do app, ex.: `meuapp.fabricadesoftware.ifc.edu.br` |
| `CORS_ALLOWED_ORIGINS` | URL(s) do front, separadas por vírgula |
| `CSRF_TRUSTED_ORIGINS` | `https://` do app e do front |
| `CLOUDINARY_URL` | `cloudinary://API_KEY:API_SECRET@CLOUD_NAME` (só no painel, nunca no git) |

## Passos
1. Criar o app no painel apontando para este repositório, branch `main` (ou `dev`), e anexar um serviço PostgreSQL.
2. Definir as variáveis acima.
3. Fazer o deploy (o `release` roda `migrate` sozinho).
4. Criar o administrador: `fabroku run createsuperuser`.
5. Conferir `GET /api/health/` → `{"status": "ok"}`.

# fabricaHackathon_backEnd

## Imagens

Capa da edição (`imagem_capa`), logo de apoiador (`logo_apoiador`), logo do projeto (`logo_projeto`) e foto de perfil (`foto_perfil`) são armazenadas no **Cloudinary** e a API devolve a **URL absoluta** (ou `null` quando não há imagem). Em produção (Fabroku) o disco do container é descartável, por isso as imagens não ficam no servidor.

### Configuração (`CLOUDINARY_URL`)

1. No painel do Cloudinary, abra **Console > Settings > API Keys** (ou o *Dashboard*, em *API Environment variable*) e copie a variável de ambiente da API, no formato `cloudinary://API_KEY:API_SECRET@CLOUD_NAME`.
2. No Fabroku, crie a variável de ambiente `CLOUDINARY_URL` com esse valor nas configurações do app e reinicie o app.
3. Nunca versione esse valor. O `.env.example` traz apenas um exemplo falso.

Sem `CLOUDINARY_URL` (desenvolvimento e testes) o projeto usa o sistema de arquivos (`media/`, ignorado pelo git), sem nenhum erro. Os testes usam armazenamento em memória e não acessam a rede.

### Formatos e limites

- Formatos: JPEG, PNG e WebP (verificado pelo conteúdo do arquivo, não pela extensão).
- Tamanho máximo: 5 MB (constante `IMAGEM_TAMANHO_MAXIMO` em `core/hackathon/validations/imagem_validation.py`).
- Tipo ou tamanho inválido devolve `400` com a mensagem no campo da imagem.
- Ao substituir ou remover uma imagem, a anterior é apagada do storage (falha ao apagar é registrada em log e não derruba a requisição).

### Permissões

- Administrador altera `imagem_capa`, `logo_apoiador` e `logo_projeto`.
- Cada usuário altera a própria `foto_perfil` (administrador altera a de qualquer um). `foto_perfil` aparece apenas nos endpoints autenticados de `users`, nunca em respostas públicas.

### Exemplos

Upload (`multipart/form-data`, em `POST`, `PUT` ou `PATCH`):

```bash
curl -X PATCH https://SEU_HOST/api/edicoes/1/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "imagem_capa=@capa.png"
```

Remover a imagem (envie `null` em JSON):

```bash
curl -X PATCH https://SEU_HOST/api/edicoes/1/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"imagem_capa": null}'
```

Miniaturas e transformações ficam por conta do front, via parâmetros na URL do Cloudinary.

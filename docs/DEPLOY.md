# Deploy: Render + Neon

O SIGE é um projeto Django com templates: telas e regras sobem juntas, num único
serviço. A aplicação roda no **Render** (Web Service) e o banco no **Neon**
(Postgres gratuito, 1 GB, sem expiração).

> O Postgres grátis do Render expira em 30 dias, por isso o banco fica no Neon.
> Netlify (só sites estáticos/JS) e MongoDB (não relacional) não servem.

## Como o projeto se comporta

| Variável | Local (notebook) | Produção (Render) |
|---|---|---|
| `DJANGO_DEBUG` | `1` (padrão) | `0` |
| `DJANGO_SECRET_KEY` | gerada a cada execução | gerada pelo Render |
| `DATABASE_URL` | ausente → SQLite | URL do Neon (com SSL) |
| `RENDER_EXTERNAL_HOSTNAME` | ausente | definida pelo Render; libera o domínio em `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` |

Com `DJANGO_DEBUG=0`, o `settings.py` ativa: arquivos estáticos comprimidos pelo
WhiteNoise, redirecionamento para HTTPS, cookies seguros e HSTS.

Arquivos de deploy:

- `build.sh`: instala dependências, roda `collectstatic` e `migrate`.
- `render.yaml`: blueprint do serviço (plano Free, região Virginia, branch `main`).
- `.python-version`: Python 3.14.

## 1. Banco no Neon

1. neon.com → **Sign up** com o GitHub.
2. **Create project**: nome `sige-murilos`, região **AWS US East (N. Virginia)**.
3. **Connect** → desmarque **Connection pooling** → copie a URL (`postgresql://...neon.tech/neondb...`).
4. A URL contém a senha do banco: não coloque no GitHub.

## 2. Tabelas e administrador (uma vez, do notebook)

```bash
export DATABASE_URL='URL_DO_NEON'
python manage.py migrate
python manage.py createsuperuser
unset DATABASE_URL
```

## 3. Serviço no Render

1. dashboard.render.com → entre com o GitHub e autorize o repositório **SIGE-Murilos**.
2. **New → Blueprint** → escolha o repositório. O Render lê o `render.yaml`.
3. Informe `DATABASE_URL` com a URL do Neon.
4. **Deploy Blueprint**. Nos **Logs**, o final deve mostrar `collectstatic`, `migrate` e o `gunicorn` iniciando.

Sem Blueprint (**New → Web Service**):

| Campo | Valor |
|---|---|
| Language | Python 3 |
| Branch | `main` |
| Region | Virginia (US East) |
| Build Command | `./build.sh` |
| Start Command | `gunicorn config.wsgi:application --workers 2 --timeout 60` |
| Instance Type | Free |

Variáveis: `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY` (**Generate**) e `DATABASE_URL`.

## 4. Fluxo de publicação

branch → pull request → `dev` → `main` → o Render publica sozinho.

## Plano grátis: limitação

O serviço adormece após 15 min sem acesso; o primeiro acesso depois disso leva
até 1 min. Contorno: um job no cron-job.org acessando `/conta/entrar/` a cada
14 min no horário da pizzaria. Para uso diário no balcão, o ideal é o plano
pago mais barato do Render (o Neon continua grátis).

## Backup semanal

```bash
export DATABASE_URL='URL_DO_NEON'
python manage.py dumpdata --exclude contenttypes --exclude auth.permission --indent 2 > ~/backup-sige-$(date +%F).json
unset DATABASE_URL
```

Guarde o arquivo fora do notebook.

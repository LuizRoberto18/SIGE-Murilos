# Deploy e banco de dados do SIGE Murilo's — roteiro para a apresentação

Resumo para explicar **onde o sistema roda, por que foi escolhido assim, como está
configurado, o que ganhamos e quais são os limites**. No fim há perguntas prováveis com
respostas curtas. O passo a passo técnico está em [DEPLOY.md](DEPLOY.md).

---

## 1. Em uma frase

O SIGE roda no **Render** (aplicação Django) e guarda os dados num **PostgreSQL gerenciado
do Neon**. Os dois estão no plano gratuito, e cada merge na `main` publica o sistema sozinho.

## 2. Arquitetura

```
 Navegador (balcão, celular)
        │  HTTPS
        ▼
 ┌──────────────────────────────── Render (Virginia, EUA) ─┐
 │  Gunicorn (servidor WSGI, 2 workers)                     │
 │    └─ Django 6 (telas + regras de negócio)               │
 │  WhiteNoise (entrega CSS, JS, fontes e ícones)           │
 └──────────────────────────────────────────┬──────────────┘
                                            │ SSL (sslmode=require)
                                            ▼
 ┌───────────────────────────── Neon (Ohio, EUA) ──────────┐
 │  PostgreSQL 18 · banco "neondb" · 1 GB                   │
 └─────────────────────────────────────────────────────────┘

 GitHub: branch → pull request → dev → main ──(push)──▶ Render faz o deploy
```

- **Um único serviço** para telas e regras: o SIGE é Django com templates, renderizado no
  servidor. Não existe um "front" separado para hospedar em outro lugar.
- **Banco separado da aplicação**, num serviço especializado em banco.

## 3. Por que essas escolhas

### Por que o Render para a aplicação

| Critério | Render |
|---|---|
| Roda Python/Django de forma nativa | Sim (usa o Python 3.14 indicado em `.python-version`) |
| Custo para começar | Plano gratuito |
| Deploy automático | Sim, a cada push na `main` do GitHub |
| HTTPS | Certificado automático no domínio `*.onrender.com` |
| Configuração como código | `render.yaml` (Blueprint) e `build.sh` versionados no repositório |

### Por que o Neon para o banco (e não outro)

| Opção | Por que **não** foi usada |
|---|---|
| **SQLite no próprio Render** | O disco do Render no plano gratuito é **efêmero**: a cada deploy ou reinício, o arquivo do banco seria apagado. Perderíamos todos os dados. |
| **Postgres gratuito do Render** | **Expira 30 dias** após a criação; depois disso é preciso pagar, senão os dados são apagados. |
| **MongoDB Atlas** | O SIGE é **relacional**: ingredientes, fichas técnicas, vendas e movimentações se ligam por chaves, com migrações e transações (a confirmação de planilha é atômica). Trocar para um banco de documentos exigiria reescrever a camada de dados sem ganho. |
| **Netlify** (para a aplicação) | Hospeda sites estáticos e funções em JavaScript; o Django não roda lá. |

**Neon:** PostgreSQL de verdade (o mesmo que o Django suporta oficialmente), gratuito,
**sem prazo de expiração**, com 1 GB de armazenamento, conexão com SSL e recuperação de pontos
recentes pelo painel.

### Por que PostgreSQL

- É o banco relacional mais completo suportado pelo Django: integridade referencial,
  transações, tipos decimais exatos para dinheiro e quantidades.
- As mesmas **migrações** do projeto criam as tabelas: não houve adaptação de código.
- Escala bem além do volume de uma pizzaria.

## 4. Como está configurado

### Ambientes: o mesmo código, comportamento por variável

| Variável | No notebook (desenvolvimento) | No Render (produção) |
|---|---|---|
| `DATABASE_URL` | ausente → usa **SQLite** local | URL do Neon → usa **PostgreSQL** com SSL |
| `DJANGO_DEBUG` | `1` (mensagens de erro detalhadas) | `0` (erros escondidos do usuário) |
| `DJANGO_SECRET_KEY` | gerada a cada execução | gerada pelo Render e guardada no painel |
| `RENDER_EXTERNAL_HOSTNAME` | ausente | definida pelo Render; libera o domínio no Django |

Nenhuma senha fica no código ou no GitHub: tudo que é segredo está nas variáveis de ambiente
do Render.

### Arquivos de deploy (no repositório)

| Arquivo | Função |
|---|---|
| `requirements.txt` | Dependências, incluindo `gunicorn`, `whitenoise`, `psycopg` e `dj-database-url` |
| `build.sh` | Executado a cada deploy: instala dependências, junta os estáticos (`collectstatic`) e aplica as migrações (`migrate`) |
| `render.yaml` | Serviço `sige-murilos`, plano Free, região Virginia, branch `main`, comando de início e verificação de saúde em `/conta/entrar/` |
| `.python-version` | Fixa o Python 3.14 |
| `config/settings.py` | Lê as variáveis acima e liga as proteções de produção |

### O que acontece num deploy

1. Merge na `main` → o GitHub avisa o Render.
2. **Build:** `pip install` → `collectstatic` → `migrate` (se houver tabela nova, é criada aqui).
3. **Início:** `gunicorn config.wsgi:application --workers 2 --timeout 60`.
4. **Verificação de saúde:** o Render acessa `/conta/entrar/` e só troca para a versão nova se
   ela responder. Se o build falhar, a versão anterior continua no ar.

### Segurança em produção (`DJANGO_DEBUG=0`)

- **HTTPS obrigatório:** acesso por `http` é redirecionado (301) para `https`.
- **HSTS** de 30 dias: o navegador passa a recusar a versão sem criptografia.
- **Cookies de sessão e CSRF** só trafegam por HTTPS.
- **Hosts permitidos** e **origens confiáveis para CSRF** limitados ao domínio do Render.
- **Conexão com o banco** sempre com SSL.
- **Sem cadastro público:** usuários são criados pelo administrador (`createsuperuser`/admin).

### Desempenho

- **WhiteNoise** comprime os arquivos estáticos e coloca um hash no nome
  (`style.2b0b834bd4ac.css`), o que permite cache longo no navegador.
- **Conexões persistentes** com o banco (`conn_max_age=600`, com verificação de saúde),
  evitando abrir uma conexão nova a cada página.

## 5. Vantagens

- **Custo zero** para homologar e apresentar.
- **Deploy contínuo:** o fluxo de branches que o projeto já usa (PR → `dev` → `main`)
  publica sozinho; não há passo manual de servidor.
- **Infraestrutura como código:** quem clonar o repositório tem tudo para recriar o serviço.
- **Mesmo banco do desenvolvimento ao uso real:** PostgreSQL, com as mesmas migrações.
- **Dados não expiram** e ficam fora do servidor da aplicação (reinício não perde nada).
- **Segredos fora do código** e **HTTPS** por padrão.

## 6. Limitações (e como lidar)

| Limitação | Impacto | Como contornar |
|---|---|---|
| Render gratuito **adormece após 15 min** sem acesso | O primeiro acesso depois disso leva **até ~1 min** | Para uso diário: plano pago mais barato do Render (não adormece). Contorno grátis: um agendador (ex.: cron-job.org) acessando a cada 14 min no horário da pizzaria |
| Render gratuito: **750 horas/mês** e recursos pequenos de CPU/memória | Suficiente para uma pizzaria, sem folga para picos grandes | Subir de plano quando o uso crescer |
| Neon gratuito: **1 GB** e o banco **suspende quando ocioso** | Primeira consulta após ociosidade fica um pouco mais lenta | 1 GB comporta anos de registros de uma pizzaria; plano pago se passar disso |
| **Regiões diferentes** (app em Virginia, banco em Ohio) | Poucos milissegundos a mais por consulta | Aceitável; pode ser alinhado recriando um dos serviços na mesma região |
| **Sem garantia de disponibilidade** (SLA) nos planos gratuitos | Pode haver indisponibilidade ocasional | Planos pagos para operação crítica |
| **Backup** depende de rotina | A recuperação do Neon cobre só um período recente | `dumpdata` semanal para um arquivo guardado fora do notebook (comando no `DEPLOY.md`) |
| Domínio `*.onrender.com` | Endereço genérico | Domínio próprio pode ser ligado no Render |

## 7. Perguntas prováveis

**Por que não deixaram o SQLite, que já funcionava?**
Porque no Render gratuito o disco é apagado a cada deploy ou reinício. O SQLite continua no
desenvolvimento local; em produção o banco precisa ficar fora do servidor.

**Por que não o Postgres do próprio Render, que seria mais simples?**
O gratuito expira em 30 dias e os dados são apagados se não houver pagamento. O Neon gratuito
não expira.

**Por que não MongoDB, que também é gratuito?**
Os dados do SIGE são relacionais e dependem de transações e migrações do Django. MongoDB exigiria
reescrever a camada de dados e perder garantias como a confirmação atômica da planilha.

**Por que não separar front e back (ex.: Netlify + API)?**
O SIGE é renderizado no servidor; não há front separado. Separar exigiria reescrever o sistema
como API + aplicação JavaScript, sem benefício para o uso atual.

**Como vocês publicam uma nova versão?**
Pull request para a `dev`, depois `dev` → `main`. O Render detecta o push, roda o build
(`pip install`, `collectstatic`, `migrate`) e só troca a versão se a nova responder na
verificação de saúde. Os testes rodam antes, na máquina de quem abre o pull request.

**E se um deploy quebrar?**
O Render mantém a versão anterior no ar quando o build falha, e é possível voltar para um
deploy anterior pelo painel (rollback).

**Onde ficam as senhas?**
Nas variáveis de ambiente do Render. O repositório só tem um `.env.example` sem valores reais.

**Os dados estão seguros?**
Tráfego com HTTPS do navegador ao Render e SSL do Render ao Neon; cookies seguros; acesso só
para usuários cadastrados pelo administrador; backup semanal com `dumpdata`.

**Por que o sistema demorou para abrir na primeira vez?**
Limitação do plano gratuito: o serviço adormece sem acesso. Em uso real, o plano pago resolve.

**Quanto custa colocar em uso real?**
Hoje R$ 0. Para uso diário sem espera, só a aplicação precisa ir para o plano pago do Render;
o banco no Neon pode continuar gratuito enquanto couber em 1 GB.

**Como o sistema está validado antes de ir para o ar?**
Antes de cada merge rodam `manage.py check`, a suíte de testes automatizados (112 testes) e o
`ruff`. O deploy foi simulado localmente com as configurações de produção (HTTPS, estáticos,
conexão SSL com o Neon) antes da primeira publicação.

## 8. Números para citar

| Item | Valor |
|---|---|
| Endereço | `https://sige-murilos.onrender.com` |
| Aplicação | Django 6.0.10 · Python 3.14 · Gunicorn 27 (2 workers) |
| Banco | PostgreSQL 18 no Neon · 1 GB · SSL obrigatório |
| Regiões | App: Virginia (EUA) · Banco: Ohio (EUA) |
| Tempo de deploy | ~1 a 5 minutos |
| Testes automatizados | 112 |
| Custo atual | R$ 0 |

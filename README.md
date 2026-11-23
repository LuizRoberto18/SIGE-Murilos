# SIGE Murilo's

Fundação funcional do sistema de gestão de estoque da Pizzaria Murilo's, implementada com Python 3.14, Django 6.0.10, templates, Bootstrap 5, SQLite e views baseadas em funções.

## Estrutura

- `config/`: configurações e roteamento principal.
- `apps/accounts/`: usuário por e-mail e autenticação.
- `apps/core/`: dashboard.
- `apps/ingredientes/`: cadastro, estoque de ingredientes e modelo XLSX.
- `apps/pizzas/`: pizzas e fichas técnicas.
- `templates/` e `static/`: interface.
- `docs/escopo_inicial.md`: limites desta etapa.

## Instalação

Requer Python 3.14 e Git. No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Configure `DJANGO_SECRET_KEY` no ambiente. Em desenvolvimento, uma chave local descartável é usada se a variável estiver ausente. Para desativar o modo de depuração, defina `DJANGO_DEBUG=0` e uma chave própria. `.env.example` documenta as variáveis; o projeto lê variáveis do ambiente e não carrega `.env` automaticamente.

SQLite é o padrão local. A opção `DB_ENGINE=postgresql` prepara a configuração de conexão futura; nesse caso, será preciso instalar `psycopg` e definir as variáveis `DB_*`.

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Validação

```powershell
python manage.py check
python manage.py test
ruff check .
```

## URLs

| Caminho | Função |
| --- | --- |
| `/` | Dashboard |
| `/conta/entrar/` | Login |
| `/conta/sair/` | Logout via POST |
| `/ingredientes/` | Lista de ingredientes ativos |
| `/ingredientes/novo/` | Cadastro de ingrediente |
| `/ingredientes/importar/` | Download e conferência do modelo XLSX |
| `/ingredientes/importar/modelo/` | Download do modelo XLSX |
| `/ingredientes/<id>/editar/` | Edição de ingrediente |
| `/pizzas/` | Lista de pizzas ativas |
| `/pizzas/nova/` | Cadastro de pizza |
| `/pizzas/<id>/editar/` | Edição de pizza |
| `/pizzas/<id>/ficha-tecnica/` | Ficha técnica |
| `/admin/` | Django Admin |

O primeiro usuário é criado com `createsuperuser`. Não há cadastro público. As páginas internas exigem login.

## Modelo de planilha do estoque

Na tela `/ingredientes/importar/`, usuários autenticados podem baixar o modelo XLSX com as colunas `ingrediente`, `unidade`, `quantidade` e `custo_unitario`. A unidade deve ser G, ML ou UN; informe quantidade e custo unitário nas unidades base. O formulário aceita o próprio modelo e planilhas com o mesmo cabeçalho, até 2 MB. Nesta etapa o envio apenas reconhece o formato: não grava o arquivo nem altera o estoque. Validação de linhas, prévia e confirmação da atualização pertencem às próximas etapas.

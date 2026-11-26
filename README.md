# SIGE Murilo's

Fundação funcional do sistema de gestão de estoque da Pizzaria Murilo's, implementada com Python 3.14, Django 6.0.10, templates, Bootstrap 5, SQLite e views baseadas em funções.

## Estrutura

- `config/`: configurações e roteamento principal.
- `apps/accounts/`: usuário por e-mail e autenticação.
- `apps/core/`: dashboard.
- `apps/ingredientes/`: cadastro, planilhas e atualização do estoque.
- `apps/pizzas/`: pizzas e fichas técnicas.
- `apps/vendas/`: períodos de vendas, pedidos e pizzas vendidas (HU08 e HU09).
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
| `/ingredientes/importar/` | Download do modelo e prévia de XLSX ou CSV |
| `/ingredientes/importar/modelo/` | Download do modelo XLSX |
| `/ingredientes/importar/confirmar/` | Confirmação de compra ou contagem via POST |
| `/ingredientes/importar/<id>/` | Resultado e registro da importação |
| `/ingredientes/<id>/editar/` | Edição de ingrediente |
| `/pizzas/` | Lista de pizzas ativas |
| `/pizzas/nova/` | Cadastro de pizza |
| `/pizzas/<id>/editar/` | Edição de pizza |
| `/pizzas/<id>/ficha-tecnica/` | Ficha técnica |
| `/vendas/` | Lista de períodos de vendas |
| `/vendas/novo/` | Registro de período |
| `/vendas/<id>/editar/` | Edição de período |
| `/vendas/<id>/pizzas/` | Pizzas vendidas no período |
| `/admin/` | Django Admin |

O primeiro usuário é criado com `createsuperuser`. Não há cadastro público. As páginas internas exigem login.

## Modelo de planilha do estoque

Na tela `/ingredientes/importar/`, usuários autenticados podem baixar o modelo XLSX com as colunas `ingrediente`, `unidade`, `quantidade` e `custo_unitario`. O envio aceita XLSX e CSV de até 2 MB, com as colunas obrigatórias em qualquer ordem. CSV pode usar vírgula ou ponto e vírgula como separador, com codificação UTF-8 ou Windows-1252.

A prévia identifica linhas com quantidade ou custo inválidos, ingredientes novos e unidades incompatíveis com o cadastro. Aceita G, ML, UN, KG e L: KG é convertido em G e L em ML. A quantidade é multiplicada por 1.000 e o custo unitário por KG ou L é dividido por 1.000, com arredondamento para quatro casas decimais. A planilha pode ter até 5.000 linhas preenchidas. Gerar a prévia não altera o estoque.

Quando todas as linhas são válidas, escolha **compra** ou **contagem** e confirme. Compra soma a quantidade ao saldo e calcula o custo médio ponderado pelos saldos e custos anteriores e pela entrada. Se o saldo anterior for zero ou negativo, o custo da entrada é usado; uma compra de quantidade zero mantém o custo existente. Contagem substitui saldo e custo pelos valores informados. A confirmação é atômica e registra usuário, arquivo, tipo e valores antes/depois por ingrediente. Repetir o POST não aplica novamente a operação; reenviar os mesmos dados e tipo também é bloqueado, salvo quando o usuário marca expressamente que deseja registrar outra operação idêntica. O arquivo enviado não é armazenado. Para usar a nova tabela de importações, execute `python manage.py migrate`.

## Períodos de vendas

Em `/vendas/`, usuários autenticados podem listar, cadastrar e corrigir períodos. Cada registro informa o tipo (dia, semana ou mês), as datas inicial e final, e o número inteiro de pedidos, que pode ser zero. As datas delimitam o intervalo informado; o tipo identifica sua granularidade. O sistema rejeita datas invertidas e qualquer sobreposição com outro registro, inclusive quando os tipos diferem ou os intervalos compartilham uma data de borda. A edição mantém essa validação e permite corrigir o próprio registro. A migration da HU08 é aplicada com `python manage.py migrate`.

Em cada período, a tela **Pizzas vendidas** permite adicionar mais de um tipo de pizza, corrigir quantidades e remover itens. A quantidade de cada pizza deve ser um inteiro não negativo. Somente pizzas ativas com ao menos um ingrediente na ficha técnica podem ser selecionadas; duplicatas no mesmo período são rejeitadas. Os itens são gravados em uma transação e a migration da HU09 é aplicada com `python manage.py migrate`.

Esta etapa registra as quantidades por pizza, sem calcular receita, consumo ou baixar ingredientes do estoque. Esses cálculos e movimentações pertencem às próximas histórias.

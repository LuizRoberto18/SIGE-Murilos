# Escopo inicial

Esta etapa entrega autenticação por e-mail, dashboard de estoque, cadastro e edição de ingredientes e pizzas, ficha técnica, administração, o modelo XLSX da HU05 e a prévia de planilhas da HU06. Todas as views próprias são funções. O estoque negativo é permitido no banco para uma futura baixa automática; o cadastro manual inicial exige valor não negativo. A quantidade da ficha usa a unidade base do ingrediente.

O dashboard mostra somente dados existentes. Pizza sem itens de ficha aparece como pendente. Não há exclusão pelo painel operacional; os relacionamentos da ficha são protegidos contra exclusão. A tela de planilha permite baixar o modelo e pré-visualizar XLSX ou CSV. Linhas inválidas são identificadas, KG/L são convertidos para G/ML, e ingredientes novos são sinalizados. O envio não persiste o arquivo nem altera o estoque.

## Próximas etapas

Os models `Importacao`, `ItemImportacao`, `RegistroVenda`, `ItemVenda`, `Movimentacao` e `Configuracao` ficam reservados para sprints futuras. A confirmação e aplicação de importações pertencem à HU07. Também ficam fora desta entrega pedidos, vendas, baixa automática, histórico, sugestões de compra, métricas de margem, relatórios avançados, API, notificações, integrações e implantação em produção.

O TAP citado no pedido não estava presente no diretório. Esta implementação segue o escopo descrito na solicitação.

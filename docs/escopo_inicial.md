# Escopo inicial

Esta etapa entrega autenticação por e-mail, dashboard de estoque, cadastro e edição de ingredientes e pizzas, ficha técnica, administração, o modelo XLSX da HU05, a prévia da HU06 e a confirmação de importações da HU07. Todas as views próprias são funções. O estoque negativo é permitido no banco para uma futura baixa automática; o cadastro manual inicial exige valor não negativo. A quantidade da ficha usa a unidade base do ingrediente.

O dashboard mostra somente dados existentes. Pizza sem itens de ficha aparece como pendente. Não há exclusão pelo painel operacional; os relacionamentos da ficha são protegidos contra exclusão. A tela de planilha permite baixar o modelo e pré-visualizar XLSX ou CSV. Linhas inválidas são identificadas, KG/L são convertidos para G/ML, e ingredientes novos são sinalizados. A prévia não altera o estoque; a confirmação aplica compra ou contagem e registra a importação com valores anteriores e posteriores. O mesmo envio não é reaplicado e conteúdo idêntico exige confirmação expressa de repetição. O arquivo enviado não é armazenado.

## Próximas etapas

Os models `Importacao` e `ItemImportacao` registram as atualizações confirmadas. `RegistroVenda`, `ItemVenda`, `Movimentacao` e `Configuracao` ficam reservados para sprints futuras. O histórico geral de movimentações da HU11, pedidos, vendas, baixa automática, sugestões de compra, métricas de margem, relatórios avançados, API, notificações, integrações e implantação em produção continuam fora desta entrega.

O TAP citado no pedido não estava presente no diretório. Esta implementação segue o escopo descrito na solicitação.

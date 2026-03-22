# Documentação da API - Sistema de Orçamento

Esta documentação descreve todos os endpoints disponíveis na API REST do sistema de emissão de orçamentos.

**URL Base:** `http://localhost:8000/api/`

## Autenticação

Todos os endpoints requerem autenticação. A API utiliza autenticação por sessão do Django REST Framework.

Para autenticar, você precisa fazer login primeiro através dos endpoints de autenticação abaixo.

## Endpoints de Autenticação

### Login

Realiza autenticação do usuário e cria uma sessão.

**Endpoint:** `POST /api/auth/login/`

**Autenticação:** ❌ Não requerida

**Corpo da Requisição:**
```json
{
  "email": "admin@example.com",
  "password": "admin123"
}
```

**Resposta de Sucesso (200):**
```json
{
  "mensagem": "Login realizado com sucesso",
  "usuario": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "first_name": "",
    "last_name": "",
    "is_staff": true,
    "date_joined": "2024-01-15T10:30:00Z"
  }
}
```

**Respostas de Erro:**

- `400 Bad Request`: Dados inválidos (campos obrigatórios faltando)
- `401 Unauthorized`: Credenciais inválidas ou usuário inativo

**Exemplo de Requisição:**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'
```

### Logout

Realiza logout do usuário autenticado, encerrando a sessão.

**Endpoint:** `POST /api/auth/logout/`

**Autenticação:** ✅ Requerida

**Resposta de Sucesso (200):**
```json
{
  "mensagem": "Logout realizado com sucesso"
}
```

**Respostas de Erro:**

- `403 Forbidden`: Usuário não autenticado

**Exemplo de Requisição:**
```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Cookie: sessionid=..."
```

### Obter Usuário Atual

Retorna informações do usuário autenticado.

**Endpoint:** `GET /api/auth/user/`

**Autenticação:** ✅ Requerida

**Resposta de Sucesso (200):**
```json
{
  "id": 1,
  "username": "admin@example.com",
  "email": "admin@example.com",
  "nome_exibicao": "Admin",
  "first_name": "",
  "last_name": "",
  "is_staff": true,
  "is_active": true,
  "date_joined": "2024-01-15T10:30:00Z"
}
```

**Respostas de Erro:**

- `403 Forbidden`: Usuário não autenticado

**Exemplo de Requisição:**
```bash
curl -X GET http://localhost:8000/api/auth/user/ \
  -H "Cookie: sessionid=..."
```

### Usuários do sistema (CRUD — apenas staff)

- `GET /api/usuarios/` — lista paginada
- `POST /api/usuarios/` — cria usuário (`email`, `password`, `first_name`, `last_name`, `is_staff`, `is_active`)
- `GET/PATCH/PUT /api/usuarios/{id}/`
- `DELETE /api/usuarios/{id}/` — desativa o usuário (`is_active=False`)

Requer sessão autenticada e `is_staff=True`.

## Endpoints do Dashboard

### Resumo do Dashboard

Retorna os dados para exibição na tela inicial (Dashboard): contadores e orçamentos recentes.

**Endpoint:** `GET /api/dashboard/resumo/`

**Autenticação:** ✅ Requerida

**Resposta de Sucesso (200):**
```json
{
  "total_orcamentos": 15,
  "rascunhos": 3,
  "enviados": 5,
  "total_clientes": 42,
  "orcamentos_recentes": [
    {
      "id": 1,
      "numero": "ORC-001",
      "ativo": true,
      "cliente": 1,
      "cliente_nome": "Cliente Exemplo Ltda",
      "cliente_cnpj_cpf": "12.345.678/0001-90",
      "descricao": "Manutenção preventiva",
      "status": "enviado",
      "data_criacao": "2024-01-15T10:30:00Z",
      "data_validade": "2024-02-15",
      "valor_total": "1500.00",
      "condicoes_pagamento": "À vista",
      "prazo_entrega": "15 dias",
      "observacoes": null,
      "usuario_criacao": 1,
      "usuario_criacao_nome": "admin",
      "itens": []
    }
  ]
}
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| total_orcamentos | integer | Total de orçamentos cadastrados |
| rascunhos | integer | Quantidade de orçamentos em rascunho |
| enviados | integer | Quantidade de orçamentos enviados |
| total_clientes | integer | Total de clientes ativos |
| orcamentos_recentes | array | Lista dos 10 orçamentos mais recentes (mesmo formato da listagem de orçamentos) |

**Exemplo de Requisição:**
```bash
curl -X GET http://localhost:8000/api/dashboard/resumo/ \
  -H "Cookie: sessionid=..."
```

## Endpoints de Configurações da Empresa

### Obter Configurações da Empresa

Retorna as configurações da empresa emissora de OS.

**Endpoint:** `GET /api/configuracoes-empresa/`

**Autenticação:** ✅ Requerida

**Resposta de Sucesso (200):**
```json
{
  "id": 1,
  "razao_social": "Empresa Exemplo Ltda",
  "nome_fantasia": "Exemplo",
  "cnpj": "12.345.678/0001-90",
  "inscricao_estadual": "123.456.789.012",
  "inscricao_municipal": "987654",
  "endereco": "Rua Exemplo",
  "numero": "123",
  "complemento": "Sala 45",
  "bairro": "Centro",
  "cidade": "São Paulo",
  "estado": "SP",
  "cep": "01234-567",
  "telefone": "(11) 1234-5678",
  "celular": "(11) 98765-4321",
  "email": "contato@exemplo.com",
  "website": "https://www.exemplo.com",
  "logomarca": "/media/configuracoes/logo.png",
  "logomarca_url": "http://localhost:8000/media/configuracoes/logo.png",
  "logo_dimensoes_maximas": {
    "largura_cm": 2.5,
    "altura_cm": 2.5
  },
  "texto_rodape": "Condições de pagamento: ...",
  "observacoes_padrao": "Observações padrão para os orçamentos",
  "data_criacao": "2024-01-15T10:30:00Z",
  "data_atualizacao": "2024-01-15T10:30:00Z"
}
```

### Criar/Atualizar Configurações da Empresa

Cria ou atualiza as configurações da empresa. Como é um singleton, sempre atualiza a mesma instância.

**Endpoint:** `POST /api/configuracoes-empresa/` (criar/atualizar)
**Endpoint:** `PUT /api/configuracoes-empresa/1/` (atualizar completo)
**Endpoint:** `PATCH /api/configuracoes-empresa/1/` (atualizar parcial)

**Autenticação:** ✅ Requerida

**Corpo da Requisição:**
```json
{
  "razao_social": "Empresa Exemplo Ltda",
  "nome_fantasia": "Exemplo",
  "cnpj": "12.345.678/0001-90",
  "inscricao_estadual": "123.456.789.012",
  "endereco": "Rua Exemplo, 123",
  "cidade": "São Paulo",
  "estado": "SP",
  "cep": "01234-567",
  "telefone": "(11) 1234-5678",
  "email": "contato@exemplo.com",
  "texto_rodape": "Condições de pagamento: À vista com 5% de desconto ou parcelado em até 3x sem juros.",
  "observacoes_padrao": "Orçamento válido por 30 dias."
}
```

**Nota:** Para upload de logomarca, use `multipart/form-data` e envie o arquivo no campo `logomarca`.

**Dimensões da Logomarca (`logo_dimensoes_maximas`):**

O objeto `logo_dimensoes_maximas` retorna o tamanho máximo da logo no PDF do orçamento (em centímetros). O frontend deve usar esses valores ao exibir o preview da imagem importada, permitindo que o usuário ajuste (diminuir ou aumentar) para otimizar a visualização antes do envio.

| Campo       | Tipo    | Descrição                    | Valor padrão |
|-------------|---------|------------------------------|--------------|
| largura_cm  | number  | Largura máxima em cm         | 2.5          |
| altura_cm   | number  | Altura máxima em cm          | 2.5          |

A logo é exibida no canto superior esquerdo do PDF do orçamento. No frontend, ao importar a imagem, exiba o tamanho máximo (2,5 cm x 2,5 cm) e permita que o usuário redimensione para se adequar ao espaço.

**Resposta de Sucesso (200):** Retorna as configurações atualizadas.

**Nota:** Não é possível deletar as configurações da empresa (método DELETE retorna erro 405).

## Endpoints de Clientes

### Listar Clientes

Retorna uma lista paginada de todos os clientes cadastrados.

**Endpoint:** `GET /api/clientes/`

**Parâmetros de Query (opcionais):**
- `cnpj_cpf` (string): Filtra por CNPJ/CPF (busca parcial)
- `razao_social` (string): Filtra por razão social (busca parcial)
- `page` (integer): Número da página (padrão: 1)

**Resposta de Sucesso (200):**
```json
{
  "count": 10,
  "next": "http://localhost:8000/api/clientes/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "cnpj_cpf": "12345678000190",
      "tipo_documento": "CNPJ",
      "razao_social": "Empresa Exemplo Ltda",
      "nome_fantasia": "Exemplo",
      "telefone": "(11) 1234-5678",
      "endereco": "Rua Exemplo, 123",
      "cep": "01234567",
      "cidade": "São Paulo",
      "estado": "SP",
      "data_cadastro": "2024-01-15T10:30:00Z",
      "usuario_cadastro": 1,
      "usuario_cadastro_nome": "admin",
      "data_ultima_alteracao": "2024-01-15T10:30:00Z",
      "usuario_ultima_alteracao": null,
      "usuario_ultima_alteracao_nome": null,
      "ativo": true
    }
  ]
}
```

### Obter Detalhes de um Cliente

Retorna os detalhes de um cliente específico.

**Endpoint:** `GET /api/clientes/{id}/`

**Resposta de Sucesso (200):**
```json
{
  "id": 1,
  "cnpj_cpf": "12345678000190",
  "tipo_documento": "CNPJ",
  "razao_social": "Empresa Exemplo Ltda",
  "nome_fantasia": "Exemplo",
  "telefone": "(11) 1234-5678",
  "endereco": "Rua Exemplo, 123",
  "cep": "01234567",
  "cidade": "São Paulo",
  "estado": "SP",
  "data_cadastro": "2024-01-15T10:30:00Z",
  "usuario_cadastro": 1,
  "usuario_cadastro_nome": "admin",
  "data_ultima_alteracao": "2024-01-15T10:30:00Z",
  "usuario_ultima_alteracao": null,
  "usuario_ultima_alteracao_nome": null,
  "ativo": true
}
```


**Campos Obrigatórios:**
- `cnpj_cpf`: CNPJ ou CPF (sem formatação)
- `tipo_documento`: "CNPJ" ou "CPF"
- `razao_social`: Razão social da empresa ou nome completo

**Campos Opcionais:**
- `nome_fantasia`: Nome fantasia
- `telefone`: Telefone de contato
- `endereco`: Endereço completo
- `cep`: CEP
- `cidade`: Cidade
- `estado`: Estado (sigla de 2 letras)

**Resposta de Sucesso (201):**
```json
{
  "id": 1,
  "cnpj_cpf": "12345678000190",
  "tipo_documento": "CNPJ",
  "razao_social": "Empresa Exemplo Ltda",
  "nome_fantasia": "Exemplo",
  "telefone": "(11) 1234-5678",
  "endereco": "Rua Exemplo, 123",
  "cep": "01234567",
  "cidade": "São Paulo",
  "estado": "SP",
  "data_cadastro": "2024-01-15T10:30:00Z",
  "usuario_cadastro": 1,
  "usuario_cadastro_nome": "admin",
  "data_ultima_alteracao": "2024-01-15T10:30:00Z",
  "usuario_ultima_alteracao": null,
  "usuario_ultima_alteracao_nome": null
}
```

### Atualizar Cliente

Atualiza um cliente existente.

**Endpoint:** `PUT /api/clientes/{id}/` (atualização completa)
**Endpoint:** `PATCH /api/clientes/{id}/` (atualização parcial)

**Corpo da Requisição (PATCH exemplo):**
```json
{
  "telefone": "(11) 9876-5432"
}
```

**Resposta de Sucesso (200):** Retorna o objeto cliente atualizado.

### Deletar Cliente

Remove um cliente do sistema.

**Endpoint:** `DELETE /api/clientes/{id}/`

**Resposta de Sucesso (200):**
```json
{
  "mensagem": "Cliente marcado como inativo com sucesso"
}
```

**Nota:** O sistema utiliza soft delete. Ao deletar um cliente, ele é marcado como inativo (`ativo: false`) ao invés de ser removido permanentemente do banco de dados. Isso preserva o histórico e permite recuperar o cliente se necessário. Clientes inativos não aparecem nas listagens por padrão, mas podem ser incluídos usando o parâmetro `?incluir_inativos=true`.

### Consultar CNPJ na SEFAZ

Consulta dados de uma empresa na ReceitaWS (API pública) baseado no CNPJ.

**Endpoint:** `GET /api/clientes/consultar_cnpj/`

**Parâmetros de Query:**
- `cnpj` (string, obrigatório): CNPJ a ser consultado (apenas números, 14 dígitos)

**Exemplo de Requisição:**
```
GET /api/clientes/consultar_cnpj/?cnpj=12345678000190
```

**Resposta de Sucesso (200):**
```json
{
  "cnpj_cpf": "12345678000190",
  "tipo_documento": "CNPJ",
  "razao_social": "Empresa Exemplo Ltda",
  "nome_fantasia": "Exemplo",
  "telefone": "(11) 1234-5678",
  "endereco": "Rua Exemplo, 123",
  "cep": "01234567",
  "cidade": "São Paulo",
  "estado": "SP"
}
```

**Resposta de Erro (400):**
```json
{
  "erro": "CNPJ deve conter 14 dígitos"
}
```

**Resposta de Erro (500):**
```json
{
  "erro": "Erro ao consultar CNPJ: [mensagem de erro]"
}
```

## Endpoints de Orçamentos

### Listar Orçamentos

Retorna uma lista paginada de todos os orçamentos.

**Endpoint:** `GET /api/orcamentos/`

**Parâmetros de Query (opcionais):**
- `status` (string): Filtra por status (rascunho, enviado, aprovado, rejeitado, vencido, cancelado)
- `incluir_excluidos` (string): Se `true`, inclui orçamentos marcados como excluídos (soft delete)
- `excluidos_apenas` (string): Se `true`, retorna apenas orçamentos excluídos (listagem separada)
- `page` (integer): Número da página (padrão: 1)

**Nota sobre soft delete:** Por padrão, a listagem retorna apenas orçamentos ativos. Orçamentos excluídos não são removidos do banco; use `incluir_excluidos=true` para listar todos ou `excluidos_apenas=true` para a listagem de excluídos.

**Resposta de Sucesso (200):**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "numero": "ORC-001",
      "ativo": true,
      "cliente": 1,
      "cliente_nome": "Empresa Exemplo Ltda",
      "cliente_cnpj_cpf": "12345678000190",
      "descricao": "Serviços de manutenção e reparo",
      "status": "rascunho",
      "data_criacao": "2024-01-15T10:30:00Z",
      "data_validade": "2024-02-15",
      "subtotal": "500.00",
      "desconto": "0.00",
      "desconto_tipo": "valor",
      "valor_desconto_calculado": "0.00",
      "acrescimo": "0.00",
      "acrescimo_tipo": "valor",
      "valor_acrescimo_calculado": "0.00",
      "valor_total": "500.00",
      "condicoes_pagamento": "À vista ou parcelado em 3x",
      "prazo_entrega": "15 dias úteis",
      "observacoes": "",
      "usuario_criacao": 1,
      "usuario_criacao_nome": "vendedor",
      "itens": []
    }
  ]
}
```

### Obter Detalhes de um Orçamento

Retorna os detalhes de um orçamento específico, incluindo seus itens.

**Endpoint:** `GET /api/orcamentos/{id}/`

**Resposta de Sucesso (200):**
```json
{
  "id": 1,
  "numero": "ORC-001",
  "ativo": true,
  "cliente": 1,
  "cliente_nome": "Empresa Exemplo Ltda",
  "cliente_cnpj_cpf": "12345678000190",
  "descricao": "Serviços de manutenção e reparo",
  "status": "rascunho",
  "data_criacao": "2024-01-15T10:30:00Z",
  "data_validade": "2024-02-15",
  "subtotal": "500.00",
  "desconto": "0.00",
  "desconto_tipo": "valor",
  "valor_desconto_calculado": "0.00",
  "acrescimo": "0.00",
  "acrescimo_tipo": "valor",
  "valor_acrescimo_calculado": "0.00",
  "valor_total": "500.00",
  "condicoes_pagamento": "À vista ou parcelado em 3x",
  "prazo_entrega": "15 dias úteis",
  "observacoes": "",
  "usuario_criacao": 1,
  "usuario_criacao_nome": "vendedor",
  "itens": [
    {
      "id": 1,
      "orcamento": 1,
      "tipo": "servico",
      "descricao": "Mão de obra",
      "quantidade": 2,
      "valor_unitario": "250.00",
      "valor_total": "500.00"
    }
  ]
}
```

### Criar Orçamento

Cria um novo orçamento. É possível criar o orçamento já com itens (peças e serviços) no mesmo payload.

**Endpoint:** `POST /api/orcamentos/`

**Corpo da Requisição (sem itens):**
```json
{
  "cliente": 1,
  "descricao": "Serviços de manutenção e reparo",
  "status": "rascunho",
  "data_validade": "2024-02-15",
  "desconto": "0",
  "desconto_tipo": "valor",
  "acrescimo": "0",
  "acrescimo_tipo": "valor",
  "condicoes_pagamento": "À vista ou parcelado em 3x",
  "prazo_entrega": "15 dias úteis",
  "observacoes": "Orçamento válido por 30 dias"
}
```

**Corpo da Requisição (com itens e desconto):**
```json
{
  "cliente": 1,
  "descricao": "Serviços de manutenção e reparo",
  "status": "rascunho",
  "data_validade": "2024-02-15",
  "desconto": "10",
  "desconto_tipo": "percentual",
  "acrescimo": "0",
  "acrescimo_tipo": "valor",
  "condicoes_pagamento": "À vista ou parcelado em 3x",
  "prazo_entrega": "15 dias úteis",
  "observacoes": "Orçamento válido por 30 dias",
  "itens": [
    {
      "tipo": "servico",
      "descricao": "Mão de obra",
      "quantidade": 2,
      "valor_unitario": "250.00"
    },
    {
      "tipo": "peca",
      "descricao": "Peça X",
      "quantidade": 1,
      "valor_unitario": "100.00"
    }
  ]
}
```

**Campos Obrigatórios:**
- `cliente`: ID do cliente (ForeignKey)

**Campos Gerados Automaticamente:**
- `numero`: Número sequencial do orçamento (formato: ORC-001, ORC-002, etc.) - gerado automaticamente

**Campos Opcionais:**
- `descricao`: Descrição geral dos serviços (opcional; os itens já descrevem o orçamento)
- `status`: Status do orçamento (padrão: "rascunho")
- `data_validade`: Data de validade do orçamento (formato: YYYY-MM-DD)
- `desconto`: Valor do desconto (decimal, padrão: 0)
- `desconto_tipo`: Tipo do desconto - `"valor"` (valor fixo em R$) ou `"percentual"` (padrão: "valor")
- `acrescimo`: Valor do acréscimo (decimal, padrão: 0)
- `acrescimo_tipo`: Tipo do acréscimo - `"valor"` (valor fixo em R$) ou `"percentual"` (padrão: "valor")
- `condicoes_pagamento`: Condições de pagamento
- `prazo_entrega`: Prazo de entrega/execução
- `observacoes`: Observações adicionais
- `itens`: Array de itens do orçamento (opcional)

**Desconto e Acréscimo:**
O valor total do orçamento é calculado da seguinte forma:
1. **Subtotal** = soma dos itens
2. **Desconto** = se `desconto_tipo` = "valor": subtrair o valor fixo; se "percentual": subtrair X% do subtotal
3. **Acréscimo** = se `acrescimo_tipo` = "valor": somar o valor fixo; se "percentual": somar X% do valor após desconto
4. **Valor Total** = (Subtotal - Desconto) + Acréscimo

A API retorna também `subtotal`, `valor_desconto_calculado` e `valor_acrescimo_calculado` (em R$) para exibição.

**Campos dos Itens (quando incluídos):**
- `tipo`: Tipo do item - `"peca"` ou `"servico"` (obrigatório)
- `descricao`: Descrição do item (obrigatório)
- `quantidade`: Quantidade (obrigatório, inteiro positivo)
- `valor_unitario`: Valor unitário (obrigatório, decimal)

**Status Válidos:**
- `rascunho` (padrão)
- `enviado`
- `aprovado`
- `rejeitado`
- `vencido`
- `cancelado`

**Resposta de Sucesso (201):** Retorna o objeto orçamento criado com todos os campos, incluindo `data_criacao`, `usuario_criacao`, `subtotal`, `valor_desconto_calculado`, `valor_acrescimo_calculado`, `valor_total` e `itens` (se fornecidos). O `valor_total` é calculado automaticamente considerando itens, desconto e acréscimo.

### Atualizar Orçamento

Atualiza um orçamento existente. Permite atualizar qualquer campo, incluindo `desconto`, `desconto_tipo`, `acrescimo` e `acrescimo_tipo`. O `valor_total` é recalculado automaticamente ao salvar.

**Endpoint:** `PUT /api/orcamentos/{id}/` (atualização completa)
**Endpoint:** `PATCH /api/orcamentos/{id}/` (atualização parcial)

**Resposta de Sucesso (200):** Retorna o objeto orçamento atualizado.

### Deletar Orçamento (Soft Delete)

Marca o orçamento como excluído (soft delete). O registro permanece no banco e pode ser consultado usando `incluir_excluidos=true` ou `excluidos_apenas=true` na listagem.

**Endpoint:** `DELETE /api/orcamentos/{id}/`

**Resposta de Sucesso (200):**
```json
{
  "mensagem": "Orçamento marcado como excluído com sucesso"
}
```

### Adicionar Item ao Orçamento

Adiciona um item (peça ou serviço) a um orçamento específico.

**Endpoint:** `POST /api/orcamentos/{id}/adicionar_item/`

**Corpo da Requisição:**
```json
{
  "tipo": "servico",
  "descricao": "Mão de obra",
  "quantidade": 2,
  "valor_unitario": "250.00"
}
```

**Campos Obrigatórios:**
- `tipo`: Tipo do item - `"peca"` ou `"servico"`
- `descricao`: Descrição do item
- `quantidade`: Quantidade (inteiro positivo)
- `valor_unitario`: Valor unitário (decimal)

**Resposta de Sucesso (201):**
```json
{
  "id": 1,
  "orcamento": 1,
  "tipo": "servico",
  "descricao": "Mão de obra",
  "quantidade": 2,
  "valor_unitario": "250.00",
  "valor_total": "500.00"
}
```

**Nota:** O valor total do orçamento é recalculado automaticamente após adicionar o item.

### Atualizar Status do Orçamento

Atualiza apenas o status de um orçamento.

**Endpoint:** `PATCH /api/orcamentos/{id}/atualizar_status/`

**Corpo da Requisição:**
```json
{
  "status": "enviado"
}
```

**Status Válidos:**
- `rascunho`
- `enviado`
- `aprovado`
- `rejeitado`
- `vencido`
- `cancelado`

**Resposta de Sucesso (200):** Retorna o objeto orçamento atualizado.

**Resposta de Erro (400):**
```json
{
  "erro": "Status inválido"
}
```

### Gerar Orçamento em PDF

Gera um arquivo PDF do orçamento com todas as informações.

**Endpoint:** `GET /api/orcamentos/{id}/gerar_pdf/`

**Autenticação:** ✅ Requerida

**Resposta de Sucesso (200):**
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="{numero} - {razao_social_cliente}.pdf"` (ex: `ORC-005 - GOOGLE BRASIL INTERNET LTDA.pdf`)
- Retorna arquivo PDF para download

**Conteúdo do PDF:**
- Cabeçalho com logomarca e dados da empresa
- Título "ORÇAMENTO"
- Informações do orçamento (número, data de criação, validade, status)
- Dados completos do cliente
- Descrição dos serviços
- Tabela com todos os itens (tipo, descrição, quantidade, valores)
- Resumo de valores: subtotal, desconto (se houver), acréscimo (se houver) e valor total
- Condições de pagamento (se informado)
- Prazo de entrega (se informado)
- Observações (se houver)
- Rodapé com data/hora de geração

**Exemplo de Uso:**
```
GET /api/orcamentos/1/gerar_pdf/
```

O navegador fará o download do arquivo PDF automaticamente.

## Endpoints de Itens de Orçamento

### Listar Itens de Orçamento

Retorna uma lista paginada de todos os itens de orçamento.

**Endpoint:** `GET /api/itens-orcamento/`

**Resposta de Sucesso (200):** Lista paginada de itens de orçamento.

### Obter Detalhes de um Item de Orçamento

Retorna os detalhes de um item de orçamento específico.

**Endpoint:** `GET /api/itens-orcamento/{id}/`

**Resposta de Sucesso (200):**
```json
{
  "id": 1,
  "orcamento": 1,
  "tipo": "servico",
  "descricao": "Mão de obra",
  "quantidade": 2,
  "valor_unitario": "250.00",
  "valor_total": "500.00"
}
```

### Criar Item de Orçamento

Cria um novo item de orçamento.

**Endpoint:** `POST /api/itens-orcamento/`

**Corpo da Requisição:**
```json
{
  "orcamento": 1,
  "tipo": "servico",
  "descricao": "Mão de obra",
  "quantidade": 2,
  "valor_unitario": "250.00"
}
```

**Campos Obrigatórios:**
- `orcamento`: ID do orçamento
- `tipo`: Tipo do item - `"peca"` ou `"servico"`
- `descricao`: Descrição do item
- `quantidade`: Quantidade (inteiro positivo)
- `valor_unitario`: Valor unitário (decimal)

**Resposta de Sucesso (201):** Retorna o objeto item de orçamento criado.

### Atualizar Item de Orçamento

Atualiza um item de orçamento existente.

**Endpoint:** `PUT /api/itens-orcamento/{id}/` (atualização completa)
**Endpoint:** `PATCH /api/itens-orcamento/{id}/` (atualização parcial)

**Resposta de Sucesso (200):** Retorna o objeto item de orçamento atualizado.

### Deletar Item de Orçamento

Remove um item de orçamento do sistema.

**Endpoint:** `DELETE /api/itens-orcamento/{id}/`

**Resposta de Sucesso (204):** Sem conteúdo.

## Códigos de Status HTTP

- `200 OK`: Requisição bem-sucedida
- `201 Created`: Recurso criado com sucesso
- `204 No Content`: Recurso deletado com sucesso
- `400 Bad Request`: Erro na requisição (dados inválidos)
- `401 Unauthorized`: Não autenticado
- `403 Forbidden`: Sem permissão
- `404 Not Found`: Recurso não encontrado
- `500 Internal Server Error`: Erro interno do servidor

## Paginação

Todos os endpoints de listagem retornam resultados paginados com 20 itens por página.

**Estrutura da Resposta Paginada:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/clientes/?page=2",
  "previous": null,
  "results": [...]
}
```

**Parâmetros:**
- `count`: Total de itens
- `next`: URL da próxima página (null se não houver)
- `previous`: URL da página anterior (null se não houver)
- `results`: Array com os resultados da página atual

## Exemplos de Uso

### Fluxo Completo: Login, Criar Cliente e Orçamento

1. **Fazer Login:**
```bash
POST /api/auth/login/
{
  "username": "admin",
  "password": "admin123"
}
```

2. **Consultar CNPJ:**
```bash
GET /api/clientes/consultar_cnpj/?cnpj=12345678000190
```

3. **Criar Cliente com os dados retornados:**
```bash
POST /api/clientes/
{
  "cnpj_cpf": "12345678000190",
  "tipo_documento": "CNPJ",
  "razao_social": "Empresa Exemplo Ltda",
  ...
}
```

4. **Criar Orçamento (com itens):**
```bash
POST /api/orcamentos/
{
  "cliente": 1,
  "descricao": "Serviços de manutenção e reparo",
  "status": "rascunho",
  "data_validade": "2024-02-15",
  "condicoes_pagamento": "À vista ou parcelado em 3x",
  "prazo_entrega": "15 dias úteis",
  "itens": [
    {
      "tipo": "servico",
      "descricao": "Mão de obra",
      "quantidade": 2,
      "valor_unitario": "250.00"
    },
    {
      "tipo": "peca",
      "descricao": "Peça X",
      "quantidade": 1,
      "valor_unitario": "100.00"
    }
  ]
}
```

**Nota:** O número do orçamento (formato: ORC-001, ORC-002, etc.) é gerado automaticamente de forma sequencial. Não é necessário informar o campo `numero` na criação.

5. **Atualizar Status:**
```bash
PATCH /api/orcamentos/1/atualizar_status/
{
  "status": "enviado"
}
```

6. **Gerar PDF do Orçamento:**
```bash
GET /api/orcamentos/1/gerar_pdf/
```

## Notas Importantes

1. **Autenticação:** Todos os endpoints requerem autenticação, exceto o endpoint de login. Faça login primeiro usando `POST /api/auth/login/` para obter uma sessão. Use o cookie de sessão retornado nas requisições subsequentes.

2. **Validação de CNPJ:** O endpoint de consulta CNPJ utiliza a API pública ReceitaWS, que pode ter limitações de rate limit.

3. **Relacionamentos:** 
   - Um Orçamento deve ter um Cliente associado
   - Um Item de Orçamento deve ter um Orçamento associado
   - Não é possível deletar um Cliente que possui Orçamentos

4. **Soft Delete de Orçamentos:** Ao excluir um orçamento, ele é marcado como inativo (campo `ativo=false`) e não removido do banco. A listagem padrão retorna apenas orçamentos ativos. Use `excluidos_apenas=true` para listar os orçamentos excluídos em uma listagem separada.

5. **Campos de Auditoria:** Os campos `usuario_cadastro` e `usuario_ultima_alteracao` são preenchidos automaticamente pelo sistema.

6. **Formatação de Datas:** Todas as datas são retornadas no formato ISO 8601 (UTC).

---

## Guia para o Frontend - Soft Delete de Orçamentos

Esta seção resume as alterações relacionadas ao soft delete de orçamentos para orientar os ajustes no frontend.

### Resumo do Comportamento

- **Excluir** um orçamento não o remove do banco; ele passa a ficar "excluído" (campo `ativo: false`).
- A **listagem principal** exibe apenas orçamentos ativos.
- Os orçamentos excluídos devem ser exibidos em uma **listagem separada** (aba, página ou seção dedicada).

### Mudanças nos Endpoints

#### 1. Listar Orçamentos `GET /api/orcamentos/`

| Parâmetro          | Tipo   | Descrição                                                         |
|--------------------|--------|-------------------------------------------------------------------|
| `status`           | string | (existente) Filtra por status                                     |
| `incluir_excluidos`| string | `"true"` = inclui ativos e excluídos na mesma lista               |
| `excluidos_apenas` | string | `"true"` = retorna **apenas** orçamentos excluídos (listagem separada) |

**Uso recomendado:**
- Lista principal: `GET /api/orcamentos/` (sem parâmetros extras)
- Lista de excluídos: `GET /api/orcamentos/?excluidos_apenas=true`
- Combinar com status: `GET /api/orcamentos/?excluidos_apenas=true&status=rascunho`

#### 2. Deletar Orçamento `DELETE /api/orcamentos/{id}/`

- **Antes:** retornava `204 No Content`
- **Agora:** retorna `200 OK` com corpo:

```json
{
  "mensagem": "Orçamento marcado como excluído com sucesso"
}
```

**Ajuste no frontend:** tratar resposta `200` com a mensagem em vez de `204`. O orçamento some da lista principal e passa a aparecer na listagem de excluídos.

#### 3. Resposta dos Endpoints - Novo Campo `ativo`

Todos os orçamentos retornados (listagem, detalhe, criar, atualizar) passam a incluir o campo:

| Campo   | Tipo    | Descrição                                      |
|---------|---------|------------------------------------------------|
| `ativo` | boolean | `true` = orçamento ativo, `false` = excluído   |

**Exemplo:**
```json
{
  "id": 1,
  "numero": "ORC-001",
  "ativo": true,
  "cliente": 1,
  ...
}
```

### Checklist de Implementação Frontend

- [ ] Listagem principal: chamar `GET /api/orcamentos/` sem `incluir_excluidos` nem `excluidos_apenas`
- [ ] Criar seção/aba "Orçamentos Excluídos" que chama `GET /api/orcamentos/?excluidos_apenas=true`
- [ ] Ao excluir: tratar `DELETE` como sucesso com `200` e mensagem; remover item da lista principal e opcionalmente mostrar na lista de excluídos
- [ ] Incluir o campo `ativo` nos tipos/interfaces de orçamento
- [ ] Dashboard: `total_orcamentos`, `rascunhos`, `enviados` e `orcamentos_recentes` consideram apenas orçamentos ativos (sem alteração necessária no frontend)

---

## Integração Frontend - Listagem de Orçamentos (Troubleshooting)

Esta seção descreve exatamente como a API envia os dados para ajudar na integração e depuração.

### Endpoint

```
GET /api/orcamentos/
```

**URL completa (desenvolvimento):** `http://localhost:8000/api/orcamentos/`

### Autenticação

- **Obrigatória.** Sem autenticação, a API retorna `403 Forbidden`.
- A API usa **SessionAuthentication** — a requisição deve enviar cookies de sessão.
- O frontend precisa fazer login primeiro (`POST /api/auth/login/`) e enviar `credentials: 'include'` em todas as requisições subsequentes.

**Exemplo (fetch):**
```javascript
fetch('http://localhost:8000/api/orcamentos/', {
  method: 'GET',
  credentials: 'include',  // IMPORTANTE: envia cookies
  headers: { 'Content-Type': 'application/json' }
})
```

**Exemplo (axios):**
```javascript
axios.get('/api/orcamentos/', { withCredentials: true })
```

### Estrutura da Resposta (200 OK)

A listagem é **paginada**. Os orçamentos vêm dentro de `results`:

```json
{
  "count": 10,
  "next": "http://localhost:8000/api/orcamentos/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "numero": "ORC-001",
      "ativo": true,
      "cliente": 1,
      "cliente_nome": "Empresa Exemplo Ltda",
      "cliente_cnpj_cpf": "12345678000190",
      "descricao": "Serviços de manutenção",
      "status": "rascunho",
      "data_criacao": "2024-01-15T10:30:00Z",
      "data_validade": "2024-02-15",
      "subtotal": "500.00",
      "desconto": "0.00",
      "desconto_tipo": "valor",
      "valor_desconto_calculado": "0.00",
      "acrescimo": "0.00",
      "acrescimo_tipo": "valor",
      "valor_acrescimo_calculado": "0.00",
      "valor_total": "500.00",
      "condicoes_pagamento": "À vista",
      "prazo_entrega": "15 dias",
      "observacoes": null,
      "usuario_criacao": 1,
      "usuario_criacao_nome": "admin",
      "itens": []
    }
  ]
}
```

**Pontos importantes:**
- Os dados da lista ficam em `response.results` (ou `response.data.results` com axios).
- `count` = total de orçamentos na consulta (considerando paginação).
- `next` e `previous` = URLs para próxima/anterior página, ou `null` quando não houver.
- Paginação padrão: 20 itens por página (`PAGE_SIZE`).

### Respostas de Erro

| Status | Corpo                       | Causa provável                                      |
|--------|-----------------------------|-----------------------------------------------------|
| 403    | `{"detail":"As credenciais de autenticação não foram fornecidas."}` | Não autenticado — cookies não enviados ou sessão inválida |
| 403    | `{"detail":"Você não tem permissão para executar essa ação."}`     | Usuário sem permissão                               |

### Campos que Podem Ser Null

- `cliente_nome`, `cliente_cnpj_cpf`: `null` se o cliente foi removido (caso raro)
- `usuario_criacao_nome`: `null` se o usuário de criação foi removido
- `descricao`, `data_validade`, `condicoes_pagamento`, `prazo_entrega`, `observacoes`: podem ser `null`

### Verificação Rápida

1. O frontend chama `GET /api/orcamentos/` com `credentials: 'include'` (ou `withCredentials: true`)?
2. O usuário está logado? A sessão está válida?
3. A listagem usa `response.results` (ou `response.data.results`) para exibir os orçamentos?
4. A URL base está correta? (ex.: `http://localhost:8000` para a API em desenvolvimento)


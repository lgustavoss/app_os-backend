# Mudanças na API - Soft Delete de Clientes

## 📋 Resumo

Implementado **soft delete** para clientes. Agora, ao deletar um cliente, ele é marcado como inativo ao invés de ser removido permanentemente do sistema.

---

## 🔄 Mudanças no Endpoint de Deletar Cliente

### Antes
- **Endpoint:** `DELETE /api/clientes/{id}/`
- **Status de Resposta:** `204 No Content` (sem corpo)
- **Comportamento:** Cliente era removido permanentemente do banco

### Agora
- **Endpoint:** `DELETE /api/clientes/{id}/` (mesmo endpoint)
- **Status de Resposta:** `200 OK` (com corpo JSON)
- **Comportamento:** Cliente é marcado como inativo (`ativo: false`)

**Resposta de Sucesso (200):**
```json
{
  "mensagem": "Cliente marcado como inativo com sucesso"
}
```

**⚠️ IMPORTANTE:** Ajustar o tratamento de resposta no frontend:
- Não esperar mais status `204`
- Esperar status `200` com mensagem de sucesso
- O cliente ainda existe no banco, apenas está inativo

---

## 📊 Novo Campo no Modelo de Cliente

Todos os endpoints que retornam dados de cliente agora incluem o campo `ativo`:

```json
{
  "id": 1,
  "cnpj_cpf": "12345678000190",
  "tipo_documento": "CNPJ",
  "razao_social": "Empresa Exemplo Ltda",
  // ... outros campos ...
  "ativo": true  // ← NOVO CAMPO
}
```

**Tipo:** `boolean`  
**Valor padrão:** `true` (cliente ativo)  
**Read-only:** Sim (não pode ser editado diretamente via API)

---

## 🔍 Mudanças na Listagem de Clientes

### Comportamento Padrão
- **Endpoint:** `GET /api/clientes/`
- **Comportamento:** Retorna **apenas clientes ativos** por padrão
- Clientes inativos (`ativo: false`) **não aparecem** na listagem

### Incluir Clientes Inativos
- **Endpoint:** `GET /api/clientes/?incluir_inativos=true`
- **Comportamento:** Retorna **todos os clientes** (ativos e inativos)

**Parâmetro de Query:**
- `incluir_inativos` (string, opcional)
  - `"true"` = inclui clientes inativos
  - Omitido ou qualquer outro valor = apenas clientes ativos

**Exemplo:**
```javascript
// Listar apenas clientes ativos (padrão)
GET /api/clientes/

// Listar todos os clientes (incluindo inativos)
GET /api/clientes/?incluir_inativos=true
```

---

## 🎯 Impacto no Frontend

### 1. Tratamento de Deleção
```javascript
// ANTES
deleteCliente(id) {
  await fetch(`/api/clientes/${id}/`, {
    method: 'DELETE'
  });
  // Esperava status 204
}

// AGORA
deleteCliente(id) {
  const response = await fetch(`/api/clientes/${id}/`, {
    method: 'DELETE'
  });
  const data = await response.json();
  // Status 200 com mensagem: { "mensagem": "Cliente marcado como inativo..." }
}
```

### 2. Exibição de Clientes
- **Listagem padrão:** Mostra apenas clientes ativos
- **Filtro opcional:** Adicionar opção para mostrar clientes inativos
- **Indicador visual:** Considerar mostrar badge/indicador para clientes inativos quando incluídos

### 3. Validação ao Criar Cliente
- Se tentar criar cliente com CNPJ que já existe **mesmo que inativo**, ainda dará erro de duplicado
- O campo `ativo` não precisa ser enviado no POST (é sempre `true` para novos clientes)

### 4. Atualização de Estado
Após deletar um cliente:
- Remover da lista atual (já que não aparece mais na listagem padrão)
- OU manter na lista se estiver usando `incluir_inativos=true` e atualizar o campo `ativo: false`

---

## 📝 Exemplo de Implementação Sugerida

```javascript
// Componente de Listagem
const [incluirInativos, setIncluirInativos] = useState(false);

const fetchClientes = async () => {
  const url = incluirInativos 
    ? '/api/clientes/?incluir_inativos=true'
    : '/api/clientes/';
  
  const response = await fetch(url);
  const data = await response.json();
  return data.results;
};

// Função de Deletar
const handleDelete = async (clienteId) => {
  try {
    const response = await fetch(`/api/clientes/${clienteId}/`, {
      method: 'DELETE',
      credentials: 'include'
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log(data.mensagem); // "Cliente marcado como inativo com sucesso"
      // Atualizar lista
      await fetchClientes();
    }
  } catch (error) {
    console.error('Erro ao deletar cliente:', error);
  }
};

// Renderização com indicador
{clientes.map(cliente => (
  <div key={cliente.id}>
    <span>{cliente.razao_social}</span>
    {!cliente.ativo && <Badge>Inativo</Badge>}
  </div>
))}
```

---

## ✅ Checklist para o Frontend

- [ ] Atualizar tratamento de resposta do DELETE (200 ao invés de 204)
- [ ] Adicionar campo `ativo` no tipo/interface de Cliente
- [ ] Ajustar listagem para considerar apenas clientes ativos por padrão
- [ ] (Opcional) Adicionar filtro para incluir clientes inativos
- [ ] (Opcional) Adicionar indicador visual para clientes inativos
- [ ] Testar fluxo completo de criação → listagem → deleção → listagem

---

## 🔗 Documentação Completa

Para mais detalhes, consulte: [API.md](API.md) - Seção "Endpoints de Clientes"


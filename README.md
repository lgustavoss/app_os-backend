# app_os-backend

Backend do sistema de emissão de orçamentos, desenvolvido em Python com Django REST Framework (DRF).

## Índice

- [Tecnologias](#tecnologias)
- [Funcionalidades](#funcionalidades)
- [Instalação](#instalação)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Endpoints da API](#endpoints-da-api)
- [Desenvolvimento Local](#desenvolvimento-local)
- [Testes](#testes)

## Tecnologias

- Python 3.11
- Django 4.2
- Django REST Framework
- PostgreSQL 15
- Docker & Docker Compose

## Funcionalidades

- **Clientes:** CRUD completo, consulta CNPJ na SEFAZ, soft delete
- **Orçamentos:** CRUD completo, itens (peças/serviços), controle de status, soft delete
- **Itens de Orçamento:** CRUD com cálculo automático de valores
- **Dashboard:** Resumo com contadores e orçamentos recentes
- **Autenticação:** Login/Logout por sessão
- **Geração de PDF:** Orçamentos em PDF
- **Configurações:** Dados da empresa para emissão de documentos

## Instalação

### Pré-requisitos

- Docker e Docker Compose instalados

### Passos

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/lgustavoss/opp_os-backend.git
   cd opp_os-backend
   ```

2. **Crie o arquivo `.env`** a partir do exemplo:
   ```bash
   cp .env.example .env
   ```
   Edite `.env` conforme necessário.

3. **Construa e inicie os containers:**
   ```bash
   docker-compose build
   docker-compose up -d
   ```

4. **Execute as migrações:**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. **Crie um superusuário:**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. **Acesse a API:** http://localhost:8000/api/

### Script helper (Linux/Mac)

O projeto inclui `docker-run.sh` para facilitar operações:

| Comando | Descrição |
|---------|-----------|
| `./docker-run.sh build` | Construir imagens |
| `./docker-run.sh start` | Iniciar containers |
| `./docker-run.sh stop` | Parar containers |
| `./docker-run.sh restart` | Reiniciar containers |
| `./docker-run.sh migrate` | Executar migrações |
| `./docker-run.sh createsuperuser` | Criar superusuário |
| `./docker-run.sh shell` | Abrir shell no container |

## Estrutura do Projeto

```
├── config/              # Configurações Django
├── autenticacao/        # App de autenticação (login/logout)
├── configuracoes/       # App de configurações da empresa
├── clientes/            # App de clientes
├── ordens_servico/      # App de orçamentos e itens
├── dashboard/           # App do dashboard
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── API.md               # Documentação completa da API
└── manage.py
```

## Endpoints da API

### Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/auth/login/` | Login |
| POST | `/api/auth/logout/` | Logout |
| GET | `/api/auth/user/` | Usuário autenticado |

### Dashboard

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/dashboard/resumo/` | Resumo (contadores e orçamentos recentes) |

### Clientes

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/clientes/` | Listar (ativa: `incluir_inativos=true`) |
| GET | `/api/clientes/{id}/` | Detalhes |
| POST | `/api/clientes/` | Criar |
| PUT/PATCH | `/api/clientes/{id}/` | Atualizar |
| DELETE | `/api/clientes/{id}/` | Soft delete |
| GET | `/api/clientes/consultar_cnpj/?cnpj=` | Consulta CNPJ SEFAZ |

### Orçamentos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/orcamentos/` | Listar (ativas: `incluir_excluidos`, `excluidos_apenas`) |
| GET | `/api/orcamentos/{id}/` | Detalhes |
| POST | `/api/orcamentos/` | Criar |
| PUT/PATCH | `/api/orcamentos/{id}/` | Atualizar |
| DELETE | `/api/orcamentos/{id}/` | Soft delete |
| POST | `/api/orcamentos/{id}/adicionar_item/` | Adicionar item |
| PATCH | `/api/orcamentos/{id}/atualizar_status/` | Atualizar status |
| GET | `/api/orcamentos/{id}/gerar_pdf/` | Gerar PDF |

### Itens de Orçamento

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/itens-orcamento/` | Listar |
| GET | `/api/itens-orcamento/{id}/` | Detalhes |
| POST | `/api/itens-orcamento/` | Criar |
| PUT/PATCH | `/api/itens-orcamento/{id}/` | Atualizar |
| DELETE | `/api/itens-orcamento/{id}/` | Remover |

> **Documentação completa:** consulte [API.md](API.md)

## Desenvolvimento Local (sem Docker)

1. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure PostgreSQL e o arquivo `.env`.

4. Execute migrações e crie o superusuário:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. Inicie o servidor:
   ```bash
   python manage.py runserver
   ```

## Testes

```bash
# Todos os testes
docker-compose exec web python manage.py test

# Por app
docker-compose exec web python manage.py test clientes
docker-compose exec web python manage.py test ordens_servico

# Com verbosidade
docker-compose exec web python manage.py test --verbosity=2
```

## Licença

Projeto privado.

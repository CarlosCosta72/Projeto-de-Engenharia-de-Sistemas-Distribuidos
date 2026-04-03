# Projeto-de-Engenharia-de-Sistemas-Distribuidos

## IA como Pool (Não Dependência Síncrona)

- Este repositório tem como objetivo: provar que a geração de desafios por IA pode ser desacoplada do fluxo crítico, operando como pool assíncrono com fallback para banco estático.

### Escopo

- Geração assíncrona de pool de desafios (GPT-4o-mini ou similar)
- Geração de perguntas sobre conteúdo de vídeo do anunciante (IA de Retenção)
- Motor consome do pool em tempo real. Se pool esgota, fallback para banco estático
- Teste de operação com IA indisponível (resiliência)

### Integrantes

- Arthur Vieira
- Augusto Miguel
- Carlos Eduardo
- Igor Wanderley
- Joás Gomes
- Kalil Teotonio

## Instruções de Execução

### Pré-requisitos

- Docker e Docker Compose instalados
- Chave da API do Google Gemini (GEMINI_API_KEY)

### Configuração

1. Clone o repositório:
   ```
   git clone https://github.com/CarlosCosta72/Projeto-de-Engenharia-de-Sistemas-Distribuidos.git
   cd Projeto-de-Engenharia-de-Sistemas-Distribuidos
   ```

2. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
   ```
   POSTGRES_DB=desafiar_db
   POSTGRES_USER=desafiar_user
   POSTGRES_PASSWORD=desafiar_password
   GEMINI_API_KEY=sua_chave_aqui
   ```

### Execução

1. Construa e inicie os serviços com Docker Compose:
   ```
   docker-compose up --build
   ```

   Isso iniciará:
   - Banco de dados PostgreSQL
   - Redis (para pool de desafios e broker do Celery)
   - API Django (porta 8000)
   - Worker Celery

2. Acesse a aplicação em: http://localhost:8000

3. Para acessar o admin do Django, use as credenciais:
   - Usuário: admin
   - Senha: admin

### Testes de Carga

Para executar testes de carga com Locust:

1. Instale o Locust (se não estiver usando Docker):
   ```
   pip install locust
   ```

2. Execute os testes:
   ```
   locust -f locustfile.py
   ```

3. Acesse a interface web do Locust em: http://localhost:8089

### Parada dos Serviços

Para parar os serviços:
```
docker-compose down
```

# ADR-05: Implementação de Circuit Breaker para a API da LLM

## Status
- [ ] Proposto
- [x] **Aceito**
- [ ] Descontinuado

**Data**: 29-03-2026  
**Autor**: @kalil-teotonio  
**Revisor**: @igor-wanderley
**Implementado em**: 28-03-2026  

---

## 🎯 Contexto

O preenchimento do pool de desafios **depende de uma API externa de IA** (OpenAI GPT-4o-mini, Google Gemini, etc).

**Problemas observados:**
- APIs externas são **pontos únicos de falha**
- Podem sofrer:
  - Timeouts (5-10 segundos)
  - Indisponibilidade total (500, 503 errors)
  - Degradação de performance
- Se API cai, worker **trava indefinidamente** aguardando resposta
- Fila de tarefas **acumula** sem poder processar
- Sistema como um todo fica **comprometido**

**Impacto:**
- Usuários não conseguem mais utilizar o sistema (sem novo pool de desafios)
- Redis fila cresce indefinidamente
- Workers "pendurados" esperando resposta

**Requisitos:**
- Sistema deve ser **resiliente** a falhas de IA
- Deve detectar problema rapidamente (não esperar 30+ segundos)
- Deve **degradar graciosamente** com fallback

---

## ✨ Decisão

**Implementar padrão Circuit Breaker para encapsular TODAS as requisições feitas à IA.**

### Como funciona:

```
┌─────────────────────────────────────────────────┐
│          CIRCUIT BREAKER STATE MACHINE           │
├─────────────────────────────────────────────────┤
│                                                 │
│  [CLOSED] (normal operation)                   │
│     ├─ Requisições passam normalmente          │
│     ├─ Monitora taxa de erro                   │
│     └─ Se erro_rate > threshold → OPEN         │
│                                                 │
│  [OPEN] (falhas detectadas)                    │
│     ├─ Rejeita requisições imediatamente       │
│     ├─ Sem tentar IA                           │
│     ├─ Usa fallback automático (banco estático)│
│     └─ Espera timeout → HALF_OPEN              │
│                                                 │
│  [HALF_OPEN] (testando recuperação)            │
│     ├─ Permite poucas requisições de teste     │
│     ├─ Se sucesso → CLOSED                     │
│     └─ Se falha → OPEN (reinicia timeout)      │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 📊 Análise de Alternativas

### Alternativa 1: Sem Proteção (Status Quo)
**Pros:**
- Simples, uma requisição por vez
- Sem lógica adicional

**Contras:**
- Vulnerável a cascata de falhas 
- Worker trava aguardando IA
- Fila acumula indefinidamente
- UX degradada indefinidamente

**Rejeitada**: Não viável para production

---

### Alternativa 2: Simple Timeout + Retry
**Pros:**
- Mais simples que circuit breaker
- Evita travamentos indefinidos

**Contras:**
- Ainda sobrecarrega IA já fraca
- Retry indefinido agrava problema
- Sem feedback de "IA está down"
- Sem transição para fallback automático

**Rejeitada**: Reativa ao invés de proativa

---

### Alternativa 3: Bulkhead Isolation (threads separados)
**Pros:**
- Isola falhas em threads separados
- Evita bloquear workers globalmente

**Contras:**
- Em Python (GIL) não funciona bem
- Mais complexo que circuit breaker
- Requer custom thread pooling

**Rejeitada**: Não é padrão de indústria

---

### Alternativa 4: Circuit Breaker Pattern ✅ **ESCOLHIDA**
**Pros:**
- **Padrão estabelecido** na indústria
- Detecta falhas **rapidamente**
- **Falha rápido** (não espera timeout)
- **Recuperação automática** (half-open)
- **Observabilidade** clara (3 estados)
- **Fallback automático** integrado

**Contras:**
- Complexidade adicional
- Requer tuning de thresholds
- Debugging mais desafiador

**Justificativa:**
- Melhor resiliência sistêmica
- Experiência do usuário não é bloqueada
- Reduz carga em IA durante degradação

---

## 📈 Consequências

### ✅ Positivas (Benefícios)

1. **Resiliência Sistêmica**
   - Falhas de IA não travamtodo o sistema
   - Sistema continua respondendo
   - Usuários continuam vendo desafios

2. **Detecção Rápida**
   - Não espera 30+ segundos para timeout
   - Detecta padrão de erros em 10-20 requisições
   - Transição imediata para fallback

3. **Graceful Degradation**
   - Com circuit OPEN: serve desafios estáticos
   - Usuário ainda tem experiência do sistema
   - Qualidade reduzida mas funcional

4. **Recuperação Automática**
   - Half-open permite auto-healing
   - Quando IA se recupera, circuit fecha
   - Sem intervenção manual

5. **Observabilidade**
   - Fácil monitorar estado do circuit
   - Alertas quando circuit abre
   - Métricas de disponibilidade

### ⚠️ Negativas (Trade-offs)

1. **Perda Temporária do Valor Core (Degradação de UX)**
   - Quando o disjuntor está no estado OPEN, o sistema faz o fallback e serve perguntas genéricas do banco estático (PostgreSQL).
   Isso significa que, temporariamente, a plataforma perde sua principal proposta de valor, que é a geração de perguntas com contexto direto sobre o vídeo assistido.

2. **Complexidade de Calibração (Tuning)**
   - Definir os limites corretos para a máquina de estados (ex: quantos erros disparam o estado OPEN, ou qual o tempo exato do timeout para o HALF_OPEN) exige testes rigorosos. Se o limite for muito sensível, o disjuntor abrirá sem necessidade; se for muito tolerante, o sistema travará antes de reagir.

3. **Falsos Positivos em Picos de Tráfego**
   - Oscilações rápidas de rede ou rate limits momentâneos da API da LLM podem acionar o Circuit Breaker prematuramente, degradando a experiência de vários usuários por um erro que duraria apenas poucos segundos.

---

## 📊 Comportamento Esperado

### Cenário 1: LLM API Normal

```
Time  Event                        Circuit   Decisão
─────────────────────────────────────────────────────────
0:00  Requisição 1 OK             CLOSED    Chamar IA
0:02  Requisição 2 OK             CLOSED    Chamar IA
0:04  Requisição 3 OK             CLOSED    Chamar IA
...
(continuando normal)
```

**Resultado**: Desafios com contexto, experiência ideal ✅

---

### Cenário 2: LLM API Começa a Falhar

```
Time  Event                        Circuit   Decisão
─────────────────────────────────────────────────────────
1:00  Requisição 1 OK             CLOSED    Chamar IA
1:02  Requisição 2 ERRO           CLOSED    Chamar IA (1 erro registrado)
1:04  Requisição 3 ERRO           CLOSED    Chamar IA (2 erros)
1:06  Requisição 4 ERRO           CLOSED    Chamar IA (3 erros, taxa 75%)
1:08  Requisição 5 ERRO           OPEN      ← Threshold atingido!
1:09  Requisição 6 (call)         OPEN      Fallback imediato
1:10  Requisição 7 (call)         OPEN      Fallback imediato
(circuit permanece aberto por 60s)
2:08  Tentativa de recuperação     HALF_OPEN Testar 1 requisição
2:10  (Teste falha)               OPEN      Reiniciar timeout
2:12  Requisição 8 (call)         OPEN      Fallback imediato
...
```

**Resultado**: Degradação graceful, sem travamento ⚠️

---

### Cenário 3: LLM API Recupera

```
Time  Event                        Circuit   Decisão
─────────────────────────────────────────────────────────
3:00  Circuit OPEN por 60s elapsed HALF_OPEN Abrir para teste
3:01  Requisição teste OK          HALF_OPEN Sucesso! → Fechar
3:02  Circuit CLOSED              CLOSED    Voltando ao normal
3:03  Requisição 1 OK             CLOSED    Chamar IA
3:04  Requisição 2 OK             CLOSED    Chamar IA
...
```

**Resultado**: Auto-recovery, sem intervenção ✅

---

## 📋 Monitoramento

### Métricas Recomendadas

- `circuit_breaker_state`: Estado atual (CLOSED=0, OPEN=1, HALF_OPEN=2)
- `circuit_breaker_calls_total`: Contagem de requisições por status (success, failure, fallback)
- `circuit_breaker_error_rate`: Percentual de erros
- `fallback_served_count`: Quantas vezes fallback foi ativado
- `circuit_recovery_time`: Tempo até transição de OPEN → recuperação

### Alertas Críticos

- 🔴 Circuit OPEN por > 5 minutos consecutivos
- 🔴 Error rate > 50%
- 🟡 Padrão de abertura/fechamento cíclico (instabilidade)
- 🟡 Fallback ativado múltiplas vezes em curto período

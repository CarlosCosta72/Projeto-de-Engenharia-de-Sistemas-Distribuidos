# ADR-001: Usar Google Gemini 2.5 Flash ao invés de OpenAI GPT-4

## Status
- [ ] Proposto
- [x] **Aceito**
- [ ] Descontinuado

**Data**: 27-03-2026  
**Autor**: @carlos-eduardo 
**Revisor**: @augusto-miguel  
**Implementado em**: 26-03-2026  

---

## 🎯 Contexto

O projeto precisa processar transcrição de áudio de vídeos do YouTube em tempo real.

**Desafios iniciais:**
- Latência de resposta crítica para UX (usuário aguardando resultado)
- Necessidade de qualidade adequada mas não perfeita (contexto educacional)
- Time pequeno, apenas 6 pessoas

**Estado anterior:**
- Nenhuma integração de IA ainda implementada
- Avaliação inicial: GPT-4 vs Gemini vs Whisper API

**Pressões e restrições:**
- Latência máxima permitida: ~5-10 segundos por transcrição
- Confiabilidade: Disponibilidade mínima 99%

---

## ✨ Decisão

**Usar Google Gemini 2.5 Flash como modelo primário para transcrição de áudio e geração de desafios, ao invés de OpenAI GPT-4o.**

Razão simplificada: melhor equilíbrio entre latência, custo e qualidade para nosso caso de uso educacional.

---

## 📊 Análise de Alternativas

### Alternativa 1: OpenAI GPT-4o
**Pros:**
- Melhor qualidade geral de transcrição
- API bem documentada
- Suporte a multimodal completo
- Comunidade maior

**Contras:**
- Latência média: ~2-3 segundos (P99: ~5s)
- Requer API key separada
- Rate limits mais apertados

**Impacto de latência**: ~2-3s (aceitável, mas subótimo)  
**Qualidade**: Excelente (scores >95%)

---

### Alternativa 2: AWS Transcribe
**Pros:**
- Especializado em transcrição (não é LLM genérico)
- Integração com AWS ecosystem
- Funcionalidades enterprise (segurança, compliance)

**Contras:**
- Não gera _desafios_ educacionais, apenas transcrição
- Precisaríamos de 2° modelo para geração de conteúdo
- Setup inicial complexo

**Impacto de latência**: ~1-2s (bom)  
**Qualidade**: Boa para transcrição, necessário outro modelo para desafios

---

### Alternativa 3: Google Gemini 2.5 Flash ✅ **ESCOLHIDA**
**Pros:**
- Latência reduzida: ~1-1.5s (P99: ~3s)
- Modelo multimodal (áudio + vídeo)
- JSON mode nativo (sem parsing)
- Melhor performance em problemas estruturados

**Contras:**
- Qualidade um pouco inferior em contextos específicos
- API relativamente nova
- Documentação em rápida evolução
- Menor comunidade comparado a OpenAI
 
**Impacto de latência**: ~1-1.5s (excelente)  
**Qualidade**: Boa para educação (~85-90%)

---

## 📊 Benchmarks e Testes

### Performance Comparativa

| Métrica | GPT-4o | Gemini 2.5 Flash | Whisper |
|---------|--------|-----------------|---------|
| **Latência (P50)** | 2.1s | 1.2s ⭐ | 0.8s |
| **Latência (P99)** | 5.2s | 3.1s ⭐ | 1.5s |
| **Qualidade transcrição** | 98% | 92% ⭐ | 94% |
| **Gera desafios?** | Sim | Sim ⭐ | Não |
| **JSON mode** | Parse LLM | Nativo ⭐ | N/A |

*Whisper só faz transcrição, precisaríamos 2º modelo para desafios

### Testes Realizados (Q1 2025)

1. **Teste de Latência** (50 vídeos)
   ```
   GPT-4: média 2.3s, desvio 0.8s
   Gemini: média 1.1s, desvio 0.3s ⭐
   Vencedor: Gemini (47% mais rápido)
   ```

2. **Teste de Qualidade** (10 vídeos, scoring manual)
   ```
   GPT-4: score 4.2/5.0
   Gemini: score 3.8/5.0 ⭐
   Diferença: Gemini perde em contexto específico (~95% ok)
   ```

3. **Teste de JSON** (100 requisições)
   ```
   GPT-4: 15% erros de parsing
   Gemini: 0% erros (JSON mode) ⭐
   Vencedor: Gemini (confiabilidade estruturada)
   ```

---
## 📈 Consequências

### ✅ Positivas (Benefícios)

1. **Performance Otimizada**
   - Latência reduzida em 47% comparado a GPT-4o (1.1s vs 2.3s)
   - P99 aceitável (3.1s vs 5.2s no GPT-4o)
   - Experiência do usuário não é prejudicada

2. **Qualidade Adequada para Educação**
   - Score de 3.8/5.0 é suficiente para contexto educacional
   - 95% das transcrições são corretas (bom para gerar desafios)
   - Erros não comprometem significantemente a experiência

3. **Confiabilidade Estruturada**
   - JSON mode nativo elimina erros de parsing (0% vs 15% no GPT-4)
   - Desafios são sempre estruturalmente válidos
   - Sem necessidade de fallback por erro de formato

4. **Escalabilidade**
   - Resposta mais rápida permite mais usuários simultâneos
   - Latência reduzida reduz timeouts
   - Sistema pode suportar mais requisições em paralelo

5. **Custo Reduzido**
   - Gemini 2.5 Flash é mais barato que GPT-4o (~50% menos)
   - Menos overhead operacional
   - Budget de IA otimizado para startup

### ⚠️ Negativas (Trade-offs)

<!-- ADICIONAR TRADE-OFFS-->


---

## 📋 Checklist de Revisão

- [x] Problema está claramente descrito?
- [x] Decisão é específica e acionável?
- [x] Alternativas foram consideradas?
- [ ] Tradeoffs foram explicados honestamente?
- [x] Impacto em segurança foi avaliado? (APIs são HTTPS)
- [x] Impacto em performance foi estimado? (1-1.5s)
- [x] Riscos foram identificados e mitigados? (fallback em erros)
- [x] Documentação foi estruturada? (README atualizado)


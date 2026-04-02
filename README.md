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

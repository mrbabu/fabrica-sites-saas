# Playbook DFY v1
## Fábrica de Sites IA

## 1. Objetivo
Transformar geração de sites em processo comercial repetível.

## 2. Oferta DFY

**Problema resolvido:** negócio local aparece no Google Maps mas perde
oportunidade por não ter presença digital profissional. O cliente não
compra IA — compra presença digital pronta pra gerar oportunidades.

**Entrega:** site responsivo, copy comercial, SEO básico, integração
WhatsApp, configuração visual, publicação.

**Prazo:** alvo de 48-72h da coleta de dados até apresentação (referência
do plano de negócio original) — não é garantia contratual até validado em
campo.

**Modelo recorrente:** mensalidade recorrente.

**Hipótese de preço:** R$149/mês como referência interna de teste — não
apresentado como preço definitivo até validação comercial (ver seção 7).

### Não incluso inicialmente
Dashboard do cliente, upload self-service, gestão de conteúdo pelo
cliente, área administrativa SaaS — bloqueado até o gate da seção 8.

## 3. Estratégia de validação
Não existe nicho vencedor definido. Teste horizontal por segmentos.
Referência: `docs/nichos_validacao.md`.

## 4. Processo operacional DFY

```
Lead Google Maps
        |
        v
Análise da empresa (não tem site; site ruim; concorrentes melhores
posicionados; Google Meu Negócio sem conversão — demo só se houver
justificativa real de oportunidade)
        |
        v
Coleta de dados reais (nome, WhatsApp, localização — obrigatórios;
logo/fotos — opcional)
        |
        v
gerar_demo_dfy.py
        |
        v
Revisão humana
        |
        v
Apresentação
        |
        v
Follow-up (docs/fase2_scripts_whatsapp.md)
        |
        v
Registro dos resultados (docs/nichos_validacao.md)
```

## 5. Guardrails comerciais e técnicos

Nunca:
- inventar depoimentos;
- inventar avaliações de clientes;
- inventar telefone, WhatsApp ou e-mail;
- criar redes sociais inexistentes;
- publicar sem revisão humana.

Dados factuais do negócio devem vir do cliente ou de fontes confirmadas.

(Garantido em código por `backend/agent_construtor.py` — commit `ca96493`.)

## 6. Prospecção
Referência: `docs/fase2_scripts_whatsapp.md` — fonte oficial de abordagem,
mensagens, follow-up e regras de contato. Não duplicar aqui.

## 7. Métricas

**Métrica norte:** clientes pagantes por segmento testado. Não otimizar
só quantidade de leads, respostas ou demos — o objetivo é descobrir onde
existe disposição real de compra.

- leads encontrados = indicador operacional;
- respostas = indicador intermediário;
- demos = indicador de interesse;
- vendas pagantes = validação real.

**Comercial:** leads, contatos, respostas, reuniões, vendas.

**Produto:** tempo de geração, custo de IA, ajustes solicitados.

**Mercado:** conversão por segmento, ticket aceito, CAC — ver
`docs/nichos_validacao.md`.

## 8. Critério para evolução SaaS

Somente após:
- 15-20 vendas DFY;
- processo repetível;
- entendimento das dores reais;
- identificação de segmento(s) vencedor(es) via `docs/nichos_validacao.md`.

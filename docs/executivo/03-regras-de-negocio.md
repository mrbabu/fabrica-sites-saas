# 03 — Regras de Negócio Implementadas

> Toda regra abaixo foi confirmada lendo o código de fato (auditoria de 2026-07-24). Formato por regra: Objetivo, Onde está (arquivo/função), Como funciona, Quem usa, Impacto, Risco se falhar/for violada.

## 1. Preço único, fonte de verdade

- **Objetivo:** nunca ter dois lugares com preços diferentes pro mesmo produto.
- **Onde está:** `vendas-config.json.pricing.base` (o dado real) + `backend/routers/hunter.py::_preco_base()`/`_vendas_config()` (leitura, com `lru_cache`).
- **Como funciona:** o Hunter lê o preço do mesmo arquivo que a landing usa, em vez de ter um valor duplicado no Python. Se o arquivo não existir no container, a falha é alta e visível (`FileNotFoundError`), não silenciosa.
- **Quem usa:** `vendas.html` (client-side) e o template de oferta do Hunter (`TEMPLATE_OFERTA`).
- **Impacto:** alto — é a base de qualquer conversa comercial.
- **Risco se violada:** dois preços diferentes circulando (um na landing, outro numa mensagem de WhatsApp) — quebra de confiança na negociação.

## 2. Domínio próprio como opcional, não incluso

- **Objetivo:** não prometer no marketing algo que o plano base não cobre.
- **Onde está:** `vendas-config.json.pricing.opcionais` (item "Domínio próprio"), FAQ correspondente no mesmo arquivo.
- **Como funciona:** o plano base publica num endereço padrão; domínio `.com.br` é contratado à parte, sem preço fixo ainda decidido.
- **Quem usa:** landing (`vendas.html`).
- **Impacto:** médio — evita expectativa errada na venda.
- **Risco se violada:** cliente cobra "onde está meu domínio" depois de fechar, gerando atrito e retrabalho.

## 3. Garantia "sem letra miúda"

- **Objetivo:** reduzir a fricção de decidir comprar.
- **Onde está:** `vendas-config.json.pricing.garantia`.
- **Como funciona:** texto estático afirmando que dá pra começar só com o plano base, sem precisar contratar nenhum opcional.
- **Quem usa:** landing.
- **Impacto:** médio (conversão).
- **Risco se violada:** nenhum risco técnico — é só copy; o risco é comercial, se a operação não cumprir a promessa na prática.

## 4. Pipeline de status do lead (Hunter = CRM)

- **Objetivo:** rastrear onde cada lead prospectado está no funil comercial.
- **Onde está:** `backend/models_db.py::HunterLead.status`, valores geridos por `backend/repository.py`, UI em `/hunter/leads` (`backend/routers/hunter.py`).
- **Como funciona:** 6 estados — `pendente → contatado → respondeu → demo_enviada → cliente → descartado`. O avanço é **sempre manual**, via dropdown na UI que faz `POST /hunter/leads/{id}/status`. Nada no sistema avança um lead sozinho.
- **Quem usa:** o operador, na tela `/hunter/leads`.
- **Impacto:** alto — é literalmente o CRM da operação hoje.
- **Risco se violada/quebrada:** se o status não refletir a realidade (esquecimento de atualizar), o operador perde controle de quem já foi abordado e reaborda ou ignora leads por engano.

## 5. Trava de oferta por status

- **Objetivo:** impedir que a mensagem de oferta (mais "vendedora") seja enviada antes do primeiro contato ter sido respondido.
- **Onde está:** `backend/routers/hunter.py::STATUS_LIBERA_OFERTA = {"respondeu", "demo_enviada", "cliente"}`.
- **Como funciona:** o botão "Oferta" na tela `/hunter/leads` só fica clicável (não-desabilitado) quando o status do lead já é um dos três acima; antes disso, aparece cinza com tooltip explicando por quê.
- **Quem usa:** operador, na mesma tela do item 4.
- **Impacto:** médio — evita erro humano de sequência.
- **Risco se violada:** sem a trava, um operador apressado poderia mandar a oferta comercial completa pra alguém que nunca respondeu o primeiro "oi", o que soa invasivo e queima a abordagem.

## 6. Template de primeiro contato

- **Objetivo:** abordagem inicial padronizada, de baixa pressão, que não soa como spam comercial.
- **Onde está:** `backend/routers/hunter.py::TEMPLATE_ABORDAGEM` / `_mensagem()`.
- **Como funciona:** string com placeholders (`{nome}`, `{local}`, `{nicho_lower}`) — texto pronto pra copiar e colar manualmente no WhatsApp.
- **Quem usa:** botão "1º contato" em `/hunter` e `/hunter/leads`.
- **Impacto:** médio — padroniza a qualidade da primeira mensagem, independente de quem está operando.
- **Risco se violada:** inconsistência de tom entre diferentes pessoas abordando leads.

## 7. Template de oferta pós-resposta

- **Objetivo:** converter interesse demonstrado numa proposta comercial concreta.
- **Onde está:** `backend/routers/hunter.py::TEMPLATE_OFERTA` / `_mensagem_oferta()`.
- **Como funciona:** usa o preço dinâmico (regra 1) e os benefícios reais do plano base — não é gerado por IA, é template estático.
- **Quem usa:** botão "Oferta", condicionado pela regra 5.
- **Impacto:** médio-alto — é o momento em que a conversa vira proposta.
- **Risco se violada:** ver regra 5 (a trava é o que evita o uso indevido).

## 8. Nunca disparo automático de WhatsApp

- **Objetivo:** evitar banimento do número pela Meta por envio em massa sem opt-in explícito — risco citado como guardrail central desde o `ROADMAP.md`.
- **Onde está:** confirmado ausente em todo o código revisado — `hunter.py` (templates só geram texto pra copiar), `backend/agents/vendedor.py` (mock de envio, nunca chama API real), `backend/routers/whatsapp_inbound.py` (só recebe e grava, nunca responde sozinho).
- **Como funciona:** toda "mensagem sugerida" em qualquer parte do sistema é texto estático que um humano decide se envia, quando envia, e envia manualmente.
- **Quem usa:** todo o sistema — é uma regra transversal, não de um módulo específico.
- **Impacto:** crítico.
- **Risco se violada:** perda do número de WhatsApp comercial (banimento), que hoje é o canal de vendas inteiro da operação.

## 9. Nunca automatizar venda antes do gate de 15-20 clientes fechados

- **Objetivo:** não treinar/confiar um agente automatizado de vendas com um roteiro nunca validado com cliente real.
- **Onde está:** guardrail do `ROADMAP.md`, respeitado em `backend/agents/vendedor.py` (toda função de envio é mock).
- **Como funciona:** o agente Vendedor tem lógica real de scoring/mensagem, mas nenhuma chamada HTTP de verdade sai dele hoje.
- **Quem usa:** `AgenteVendedor` (ainda não plugado em produção real).
- **Impacto:** alto — é uma proteção deliberada contra escalar um processo não testado.
- **Risco se violada:** vender mal, em escala, com um script que nunca foi validado por um humano numa negociação real.

## 10. Nunca fabricar depoimento, contato ou rede social no site gerado

- **Objetivo:** garantir que todo site gerado pela IA seja honesto — nenhum dado inventado aparece pro cliente final do cliente.
- **Onde está:** `backend/agent_construtor.py::_preencher_fallbacks()` (zera `email`/`social`/`testimonials` sempre, independente do que o modelo de IA tenha retornado), documentado também em `backend/schema_validator.py`.
- **Como funciona:** é um guardrail determinístico, não uma instrução de prompt que a IA pode ou não seguir — o código força esses campos vazios depois da geração.
- **Quem usa:** todo site gerado via `AgenteConstrutor`.
- **Impacto:** alto — é o que garante que o produto nunca entregue uma mentira pro cliente final (ex.: um depoimento que ninguém deu).
- **Risco se violada:** cliente descoberto com informação falsa no próprio site, prejuízo de reputação direto pro negócio dele e indireto pra Fábrica de Sites.

## 11. Sessão de login interno curta (15 minutos)

- **Objetivo:** limitar a janela de exposição da ferramenta interna (Hunter, Site Constructor, Biblioteca de Demos).
- **Onde está:** `backend/auth_demo.py::SESSAO_DURACAO_SEGUNDOS = 900`; comparação de credencial via `hmac.compare_digest` (defesa contra timing attack).
- **Como funciona:** qualquer requisição pras rotas internas (`/demo`, `/demo/lista`, `/hunter`, `/demo/preview`) checa a sessão e redireciona pro login se expirou.
- **Quem usa:** todas as rotas internas.
- **Impacto:** médio.
- **Risco se violada/mal calibrada:** 15 minutos pode ser curto pra um fluxo de geração de demo mais longo (o próprio formulário já documentou timeout de geração de 30-60s) — risco é de fricção operacional, não de segurança.

## 12. Conciliação de pagamento estrita (PIX)

- **Objetivo:** só liberar acesso ao site quando o pagamento estiver **de fato** confirmado, nunca por suposição.
- **Onde está:** `backend/agents/financeiro.py::conciliar()`.
- **Como funciona:** exige status "aprovado" **e** valor batendo (tolerância de 1 centavo); qualquer valor a maior cai em revisão manual em vez de aprovar automaticamente.
- **Quem usa:** `AgenteFinanceiro` — **ainda sem webhook de gateway real plugado em produção**, é lógica pronta esperando integração.
- **Impacto:** alto, quando ativado.
- **Risco se violada:** liberar um site sem pagamento real de fato ter entrado.

## 13. Deduplicação de leads do Hunter

- **Objetivo:** não abordar a mesma empresa duas vezes como se fosse um lead novo.
- **Onde está:** `backend/repository.py::_lead_hunter_existente()`.
- **Como funciona:** checa por `place_id` (preferencial, vem do Google Places) ou, na ausência dele, por `(nome_empresa, cidade)`.
- **Quem usa:** `salvar_leads_hunter()`, chamado toda vez que uma busca nova é feita.
- **Impacto:** médio — evita parecer desorganizado com um lead que já foi contatado.
- **Risco se violada:** reabordagem duplicada, ou pior, dois operadores diferentes abordando o mesmo lead com mensagens diferentes.

---

**Regras que existem só como especificação, ainda sem código** (não confundir com as acima): cobrança recorrente automática (`docs/fluxo_financeiro_recorrencia.md`), pipeline inteligente de seleção de imagem (`docs/pipeline_imagens_inteligente.md`), evolução comercial do Hunter com scoring avançado (`docs/hunter_online_spec.md` — mas atenção: a spec descreve como "futuro" um pipeline de status que **já existe e está em produção**, ver regra 4 acima; a spec não foi atualizada).

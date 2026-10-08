# Chatbot de Empreendimentos

Chatbot imobiliário de terminal (consulta de empreendimentos, simulação de financiamento,
fluxo de pagamento) + **visualizador interativo**: o cliente vê a fachada do prédio, clica na
janela do apartamento e entra num tour 360° daquela unidade, com a vista do andar.

```bash
python main.py                    # chatbot (opção 4 abre o visualizador)
# ou só o visualizador:
cd visualizador && python -m http.server 8000   # http://localhost:8000
```

Links diretos (para o chatbot, WhatsApp, anúncios):

| URL | Efeito |
|---|---|
| `/?unidade=T1-502` | abre a fachada com o apto 502 selecionado |
| `/?unidade=T1-502&tour=1` | entra direto no tour 360° do apto 502 |
| `/?debug=1` | modo calibração: clique no panorama para ver `pitch`/`yaw` dos hotspots |

> O material em `visualizador/midia` é **sintético**, gerado por `ferramentas/gerar_demo.py`
> só para o protótipo funcionar. Substitua pelos renders reais seguindo o pipeline abaixo.

## Estrutura

```
producao/                     entradas do pipeline (não vão para o site)
  mascara_fachada.png           passe de ID: uma cor sólida por unidade
  cores_mascara.csv             cor -> código da unidade
  tabela_vendas.csv             tabela do comercial (preço, status, tipologia…)
ferramentas/
  gerar_unidades.py             máscara + cores + tabela -> visualizador/dados/unidades.json
  gerar_demo.py                 gera o material de demonstração
visualizador/                 site estático (pode ir para qualquer hospedagem)
  dados/empreendimento.json     configuração: tipologias, cômodos, hotspots, faixas de vista, contato
  dados/unidades.json           gerado — não editar à mão
  midia/fachada.jpg
  midia/panoramas/{tipologia}-{comodo}-{faixa}.jpg
visualizador.py               integração com o chatbot (servidor local + abrir navegador)
```

## Pipeline de produção do material real

1. **Modelagem (SketchUp/Revit)** — fachada completa e um interior decorado **por tipologia**.
2. **Fachada** (D5 / Enscape / V-Ray), numa câmera fixa:
   - `fachada.jpg` (recomendado 4K–8K) → `visualizador/midia/fachada.jpg`;
   - na **mesma câmera e resolução**, um passe de *Object/Material ID* **sem antialiasing**,
     com um material de cor sólida por janela/varanda de unidade → `producao/mascara_fachada.png`;
   - liste cada cor e a unidade correspondente em `producao/cores_mascara.csv`.
   - Pós-produção com IA (Magnific, etc.) só no `fachada.jpg` — **nunca** na máscara, e sem
     reenquadrar ou redimensionar, senão as áreas clicáveis desalinham.
3. **Panoramas 360°** equiretangulares 2:1 (8192×4096 ideal; 4096×2048 já é bom na web),
   um por cômodo, com a câmera na altura do olho (~1,55 m).
   - **Vista real por andar**: fotografe panoramas 360° de drone no terreno em cada faixa de
     altura e use como fundo (HDRI/backplate) das janelas. Renderize cada cômodo uma vez por
     faixa: `A-sala-baixo.jpg`, `A-sala-medio.jpg`, `A-sala-alto.jpg`.
   - Sem vista por faixa? Remova o `{faixa}` do caminho em `empreendimento.json`.
   - Se usar IA no 360°, converta para cubemap, trate as faces e reconverta (senão quebra a emenda).
4. **Tabela de vendas** → `producao/tabela_vendas.csv` (status: `disponivel`, `reservado`, `vendido`).
5. Rode `python ferramentas/gerar_unidades.py` — ele avisa se faltar unidade na máscara ou
   na tabela. Rode de novo **sempre que o status/preço mudar**.
6. Edite `visualizador/dados/empreendimento.json`: nome, tipologias, cômodos, textos do memorial
   descritivo nos hotspots, faixas de vista e o WhatsApp do plantão (`contato.whatsapp`, só dígitos
   com DDI, ex.: `5511999999999`). Para posicionar hotspots, abra com `?debug=1&unidade=...&tour=1`,
   clique no ponto e copie `pitch`/`yaw`.

## Cuidados comerciais

- O tour é por **tipologia**; a vista é por **faixa de andares**. O aviso legal no rodapé deixa
  isso claro — mantenha-o.
- Planta, metragem e acabamentos dos renders devem bater com o memorial e o projeto aprovado.

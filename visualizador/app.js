// Visualizador de empreendimento: fachada clicável -> ficha da unidade -> tour 360° (Pannellum).
// Dados: dados/empreendimento.json (configuração, tipologias, tour) e
//        dados/unidades.json (gerado por ferramentas/gerar_unidades.py).

const STATUS = { disponivel: "Disponível", reservado: "Reservado", vendido: "Vendido" };
const SVG_NS = "http://www.w3.org/2000/svg";
const params = new URLSearchParams(location.search);
const DEBUG = params.get("debug") === "1";

const estado = {
  config: null,
  unidades: [],
  porCodigo: new Map(),
  selecionada: null,
  statusVisiveis: new Set(Object.keys(STATUS)),
  tipologia: "",
  viewer: null,
};

const $ = (id) => document.getElementById(id);
const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });

async function carregar() {
  const [config, dados] = await Promise.all([
    fetch("dados/empreendimento.json").then((r) => r.json()),
    fetch("dados/unidades.json").then((r) => r.json()),
  ]);
  estado.config = config;
  estado.unidades = dados.unidades;
  dados.unidades.forEach((u) => estado.porCodigo.set(u.unidade, u));

  document.title = `${config.nome} · Escolha seu apartamento`;
  $("nome-empreendimento").textContent = config.nome;
  $("subtitulo").textContent = config.subtitulo || config.endereco || "";
  $("aviso-legal").textContent = config.aviso_legal || "";
  $("fachada-img").src = config.fachada;

  for (const [id, tip] of Object.entries(config.tipologias)) {
    $("filtro-tipologia").add(new Option(tip.nome, id));
  }

  desenharFachada(dados.imagem);
  atualizarResumo();
  ligarEventos();

  const inicial = params.get("unidade");
  if (inicial && estado.porCodigo.has(inicial.toUpperCase())) {
    selecionar(estado.porCodigo.get(inicial.toUpperCase()));
    if (params.get("tour") === "1") abrirTour();
  }
}

// ------------------------------------------------------------------ fachada

function desenharFachada({ largura, altura }) {
  const svg = $("fachada-svg");
  svg.setAttribute("viewBox", `0 0 ${largura} ${altura}`);
  for (const u of estado.unidades) {
    const poly = document.createElementNS(SVG_NS, "polygon");
    poly.setAttribute("points", u.poligono.map((p) => p.join(",")).join(" "));
    poly.setAttribute("class", `unidade ${u.status}`);
    poly.setAttribute("tabindex", "0");
    poly.setAttribute("role", "button");
    poly.setAttribute("aria-label", `${rotuloUnidade(u)}, ${STATUS[u.status]}`);
    poly.dataset.unidade = u.unidade;
    u.elemento = poly;
    svg.appendChild(poly);
  }
}

function rotuloUnidade(u) {
  const torre = estado.config.torres?.[u.torre] || u.torre;
  return `${torre} · Apto ${u.andar}${String(u.final).padStart(2, "0")}`;
}

function faixaDoAndar(andar) {
  return estado.config.faixas_vista.find((f) => andar >= f.de && andar <= f.ate) || estado.config.faixas_vista[0];
}

function aplicarFiltros() {
  for (const u of estado.unidades) {
    const visivel = estado.statusVisiveis.has(u.status) && (!estado.tipologia || u.tipologia === estado.tipologia);
    u.elemento.classList.toggle("apagada", !visivel);
  }
}

function atualizarResumo() {
  const contagem = { disponivel: 0, reservado: 0, vendido: 0 };
  estado.unidades.forEach((u) => contagem[u.status]++);
  $("resumo").innerHTML = Object.entries(contagem)
    .map(([s, n]) => `<div><strong>${n}</strong><span>${STATUS[s].toLowerCase()}s</span></div>`)
    .join("");
}

function mostrarTooltip(u, evento) {
  const tip = $("tooltip");
  const caixa = $("fachada").getBoundingClientRect();
  const tipologia = estado.config.tipologias[u.tipologia];
  tip.innerHTML = `<strong>Apto ${u.andar}${String(u.final).padStart(2, "0")}</strong> · ${tipologia?.quartos ?? ""} quartos · ${u.area_privativa} m² · ${STATUS[u.status]}`;
  tip.style.left = `${evento.clientX - caixa.left}px`;
  tip.style.top = `${evento.clientY - caixa.top}px`;
  tip.hidden = false;
}

// ------------------------------------------------------------------ painel da unidade

function selecionar(u) {
  estado.selecionada?.elemento.classList.remove("selecionada");
  estado.selecionada = u;
  u.elemento.classList.add("selecionada");

  const tip = estado.config.tipologias[u.tipologia];
  const faixa = faixaDoAndar(u.andar);
  $("painel-vazio").hidden = true;
  $("painel-unidade").hidden = false;
  $("u-local").textContent = `${estado.config.torres?.[u.torre] || u.torre} · ${u.andar}º andar · final ${String(u.final).padStart(2, "0")}`;
  $("u-titulo").textContent = `Apartamento ${u.andar}${String(u.final).padStart(2, "0")}`;
  $("u-status").textContent = STATUS[u.status];
  $("u-status").className = `selo ${u.status}`;
  $("u-tipologia").textContent = tip?.nome || u.tipologia;
  $("u-area").textContent = `${u.area_privativa.toLocaleString("pt-BR")} m²`;
  $("u-vagas").textContent = tip?.vagas ?? "—";
  $("u-vista").textContent = faixa.nome;
  $("u-preco").textContent = u.status === "vendido" ? "Unidade vendida" : moeda.format(u.preco);

  $("btn-similares").hidden = u.status === "disponivel";
  const contato = estado.config.contato || {};
  const interesse = $("btn-interesse");
  interesse.hidden = !contato.whatsapp;
  if (contato.whatsapp) {
    const texto = (contato.mensagem || "")
      .replace("{unidade}", rotuloUnidade(u))
      .replace("{tipologia}", tip?.nome || u.tipologia)
      .replace("{empreendimento}", estado.config.nome);
    interesse.href = `https://wa.me/${contato.whatsapp}?text=${encodeURIComponent(texto)}`;
  }
  $("resultado-simulacao").innerHTML = "";

  const url = new URL(location.href);
  url.searchParams.set("unidade", u.unidade);
  url.searchParams.delete("tour");
  history.replaceState(null, "", url);
}

function realcarSimilares() {
  const u = estado.selecionada;
  const similares = estado.unidades.filter((x) => x.tipologia === u.tipologia && x.status === "disponivel");
  similares.forEach((x) => {
    x.elemento.classList.remove("apagada", "realce");
    void x.elemento.getBoundingClientRect(); // reinicia a animação
    x.elemento.classList.add("realce");
  });
  if (!similares.length) alert("No momento não há outras unidades disponíveis desta tipologia.");
}

// Mesma regra do chatbot (financiamento.py): parcela até X% da renda, tabela Price.
function simular(renda, entrada, fgts) {
  const f = estado.config.financiamento;
  const i = f.taxa_anual / 12;
  const n = f.prazo_anos * 12;
  const parcela = f.comprometimento_renda * renda;
  const financiavel = i === 0 ? parcela * n : (parcela * (1 - (1 + i) ** -n)) / i;
  return { parcela, financiavel, poderCompra: financiavel + entrada + fgts };
}

// ------------------------------------------------------------------ tour 360°

function abrirTour() {
  const u = estado.selecionada;
  const tip = estado.config.tipologias[u.tipologia];
  if (!tip?.comodos?.length) {
    alert("O tour desta tipologia ainda não foi publicado.");
    return;
  }
  const faixa = faixaDoAndar(u.andar);
  const nomes = Object.fromEntries(tip.comodos.map((c) => [c.id, c.nome]));
  const cenas = {};
  for (const c of tip.comodos) {
    cenas[c.id] = {
      title: c.nome,
      panorama: c.panorama.replace("{faixa}", faixa.id),
      yaw: c.yaw_inicial ?? 0,
      pitch: c.pitch_inicial ?? 0,
      hfov: 100,
      hotSpots: c.hotspots.map((h) => {
        const texto = h.tipo === "comodo" ? `Ir para ${nomes[h.destino] || h.texto}`
          : h.tipo === "vista" ? `${h.texto}. Vista simulada do ${faixa.nome}.` : h.texto;
        return {
          pitch: h.pitch,
          yaw: h.yaw,
          type: h.tipo === "comodo" ? "scene" : "info",
          sceneId: h.tipo === "comodo" ? h.destino : undefined,
          cssClass: `hs-${h.tipo}`,
          createTooltipFunc: (div) => {
            const span = document.createElement("span");
            span.textContent = texto;
            div.appendChild(span);
            div.setAttribute("title", texto);
          },
        };
      }),
    };
  }

  $("tour-titulo").textContent = `${rotuloUnidade(u)} · ${tip.nome}`;
  $("tour-sub").textContent = `Vista: ${faixa.nome}`;
  const nav = $("tour-comodos");
  nav.innerHTML = "";
  for (const c of tip.comodos) {
    const b = document.createElement("button");
    b.className = "chip";
    b.textContent = c.nome;
    b.dataset.cena = c.id;
    b.addEventListener("click", () => estado.viewer.loadScene(c.id));
    nav.appendChild(b);
  }

  $("tour").hidden = false;
  estado.viewer = pannellum.viewer("panorama", {
    default: { firstScene: tip.comodos[0].id, sceneFadeDuration: 700, autoLoad: true, compass: false },
    scenes: cenas,
    hotSpotDebug: DEBUG,
  });
  const marcarCena = () => {
    const atual = estado.viewer.getScene();
    nav.querySelectorAll("button").forEach((b) => b.classList.toggle("ativo", b.dataset.cena === atual));
  };
  estado.viewer.on("scenechange", () => setTimeout(marcarCena));
  marcarCena();

  if (DEBUG) {
    $("debug-coords").hidden = false;
    $("debug-coords").textContent = "Modo calibração: clique para ver pitch/yaw";
    $("panorama").addEventListener("mouseup", (e) => {
      const [pitch, yaw] = estado.viewer.mouseEventToCoords(e);
      $("debug-coords").textContent = `cena: ${estado.viewer.getScene()}  "pitch": ${pitch.toFixed(1)}, "yaw": ${yaw.toFixed(1)}`;
    });
  }

  const url = new URL(location.href);
  url.searchParams.set("tour", "1");
  history.replaceState(null, "", url);
  $("btn-fechar-tour").focus();
}

function fecharTour() {
  estado.viewer?.destroy();
  estado.viewer = null;
  $("tour").hidden = true;
  const url = new URL(location.href);
  url.searchParams.delete("tour");
  history.replaceState(null, "", url);
  estado.selecionada?.elemento.focus();
}

// ------------------------------------------------------------------ eventos

function ligarEventos() {
  const svg = $("fachada-svg");
  const unidadeDoEvento = (e) => estado.porCodigo.get(e.target.dataset?.unidade);

  svg.addEventListener("mousemove", (e) => {
    const u = unidadeDoEvento(e);
    if (u && !u.elemento.classList.contains("apagada")) mostrarTooltip(u, e);
    else $("tooltip").hidden = true;
  });
  svg.addEventListener("mouseleave", () => ($("tooltip").hidden = true));
  svg.addEventListener("click", (e) => {
    const u = unidadeDoEvento(e);
    if (u && !u.elemento.classList.contains("apagada")) selecionar(u);
  });
  svg.addEventListener("keydown", (e) => {
    const u = unidadeDoEvento(e);
    if (u && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      selecionar(u);
    }
  });

  document.querySelectorAll(".chip[data-status]").forEach((chip) =>
    chip.addEventListener("click", () => {
      const s = chip.dataset.status;
      if (estado.statusVisiveis.has(s)) estado.statusVisiveis.delete(s);
      else estado.statusVisiveis.add(s);
      chip.classList.toggle("ativo", estado.statusVisiveis.has(s));
      aplicarFiltros();
    })
  );
  $("filtro-tipologia").addEventListener("change", (e) => {
    estado.tipologia = e.target.value;
    aplicarFiltros();
  });

  $("btn-tour").addEventListener("click", abrirTour);
  $("btn-similares").addEventListener("click", realcarSimilares);
  $("btn-fechar-tour").addEventListener("click", fecharTour);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !$("tour").hidden) fecharTour();
  });

  $("form-simulacao").addEventListener("submit", (e) => {
    e.preventDefault();
    const dados = new FormData(e.target);
    const r = simular(+dados.get("renda"), +dados.get("entrada"), +dados.get("fgts"));
    const u = estado.selecionada;
    const diferenca = r.poderCompra - u.preco;
    $("resultado-simulacao").innerHTML = `
      <p>Parcela máxima: <strong>${moeda.format(r.parcela)}</strong>/mês<br>
      Valor financiável: <strong>${moeda.format(r.financiavel)}</strong><br>
      Poder de compra: <strong>${moeda.format(r.poderCompra)}</strong></p>
      ${u.status === "vendido" ? "" : diferenca >= 0
        ? `<p class="ok">Esta unidade cabe no seu orçamento.</p>`
        : `<p class="falta">Faltam ${moeda.format(-diferenca)} para esta unidade. Fale com o corretor sobre o fluxo de pagamento da entrada.</p>`}
      <p class="sutil">Simulação estimada, sujeita à análise de crédito.</p>`;
  });
}

carregar().catch((erro) => {
  console.error(erro);
  $("nome-empreendimento").textContent = "Não foi possível carregar os dados do empreendimento.";
  $("subtitulo").textContent = "Abra pelo servidor local (python -m http.server), não direto pelo arquivo.";
});

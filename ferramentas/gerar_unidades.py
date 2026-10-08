"""
Gera visualizador/dados/unidades.json a partir do material de produção:

  - mascara_fachada.png : passe de ID (Object/Material ID) renderizado na MESMA câmera
                          e resolução da fachada, SEM antialiasing, uma cor sólida por unidade.
  - cores_mascara.csv   : cor,unidade   (ex.: #3a5aa0,T1-1502) — definido pelo artista 3D.
  - tabela_vendas.csv   : unidade,torre,andar,final,tipologia,area_privativa,preco,status
                          — mantida pelo comercial; rode este script de novo a cada atualização.

Uso:
  python ferramentas/gerar_unidades.py
  python ferramentas/gerar_unidades.py --mascara outra.png --tabela outra.csv
"""
import argparse
import csv
import json
import os

import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS_VALIDOS = {"disponivel", "reservado", "vendido"}


def hex_para_int(cor):
    cor = cor.strip().lstrip("#")
    return int(cor, 16)


def casco_convexo(pontos):
    """Monotone chain. pontos: lista de (x, y). Retorna o casco em ordem anti-horária."""
    pontos = sorted(set(pontos))
    if len(pontos) <= 2:
        return pontos

    def cruz(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    inferior, superior = [], []
    for p in pontos:
        while len(inferior) >= 2 and cruz(inferior[-2], inferior[-1], p) <= 0:
            inferior.pop()
        inferior.append(p)
    for p in reversed(pontos):
        while len(superior) >= 2 and cruz(superior[-2], superior[-1], p) <= 0:
            superior.pop()
        superior.append(p)
    return inferior[:-1] + superior[:-1]


def simplificar(poligono, tolerancia=1.5):
    """Remove vértices quase colineares (o casco de um quadrilátero rasterizado tem dezenas)."""
    pts = list(poligono)
    mudou = True
    while mudou and len(pts) > 3:
        mudou = False
        for i in range(len(pts)):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
            base = ((c[0] - a[0]) ** 2 + (c[1] - a[1]) ** 2) ** 0.5 or 1
            dist = abs((c[0] - a[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (c[1] - a[1])) / base
            if dist < tolerancia:
                pts.pop(i)
                mudou = True
                break
    return pts


def poligono_da_regiao(ys, xs):
    """Usa só os extremos de cada linha da região para montar o casco (rápido em imagens 8K)."""
    ordem = np.argsort(ys, kind="stable")
    ys, xs = ys[ordem], xs[ordem]
    linhas, inicio = np.unique(ys, return_index=True)
    minimos = np.minimum.reduceat(xs, inicio)
    maximos = np.maximum.reduceat(xs, inicio)
    pontos = []
    for y, x0, x1 in zip(linhas.tolist(), minimos.tolist(), maximos.tolist()):
        pontos += [(x0, y), (x1 + 1, y), (x0, y + 1), (x1 + 1, y + 1)]
    return [[int(x), int(y)] for x, y in simplificar(casco_convexo(pontos))]


def ler_tabela(caminho):
    unidades = {}
    with open(caminho, newline="", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            status = linha["status"].strip().lower()
            if status not in STATUS_VALIDOS:
                raise ValueError(f"Status inválido '{status}' na unidade {linha['unidade']}")
            unidades[linha["unidade"].strip()] = {
                "unidade": linha["unidade"].strip(),
                "torre": linha["torre"].strip(),
                "andar": int(linha["andar"]),
                "final": int(linha["final"]),
                "tipologia": linha["tipologia"].strip(),
                "area_privativa": float(linha["area_privativa"]),
                "preco": float(linha["preco"]),
                "status": status,
            }
    return unidades


def gerar(mascara, cores, tabela, saida):
    img = np.asarray(Image.open(mascara).convert("RGB")).astype(np.int32)
    altura, largura = img.shape[:2]
    empacotado = (img[..., 0] << 16) | (img[..., 1] << 8) | img[..., 2]

    cor_para_unidade = {}
    with open(cores, newline="", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            cor_para_unidade[hex_para_int(linha["cor"])] = linha["unidade"].strip()

    dados_vendas = ler_tabela(tabela)

    resultado = []
    for cor, unidade in cor_para_unidade.items():
        ys, xs = np.nonzero(empacotado == cor)
        if len(ys) == 0:
            print(f"AVISO: cor #{cor:06x} ({unidade}) não aparece na máscara.")
            continue
        if unidade not in dados_vendas:
            print(f"AVISO: {unidade} está na máscara mas não na tabela de vendas — ignorada.")
            continue
        registro = dict(dados_vendas[unidade])
        registro["poligono"] = poligono_da_regiao(ys, xs)
        resultado.append(registro)

    sem_poligono = set(dados_vendas) - {u["unidade"] for u in resultado}
    for unidade in sorted(sem_poligono):
        print(f"AVISO: {unidade} está na tabela mas não tem janela na máscara.")

    conhecidas = np.isin(empacotado, list(cor_para_unidade) + [0])
    desconhecidos = int((~conhecidas).sum())
    if desconhecidos > 0.001 * largura * altura:
        print(f"AVISO: {desconhecidos} pixels com cores fora de cores_mascara.csv "
              "(máscara renderizada com antialiasing?).")

    resultado.sort(key=lambda u: (u["torre"], -u["andar"], u["final"]))
    with open(saida, "w", encoding="utf-8") as f:
        json.dump({"imagem": {"largura": largura, "altura": altura}, "unidades": resultado},
                  f, ensure_ascii=False, indent=1)
    print(f"{len(resultado)} unidades gravadas em {os.path.relpath(saida, RAIZ)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mascara", default=os.path.join(RAIZ, "producao", "mascara_fachada.png"))
    parser.add_argument("--cores", default=os.path.join(RAIZ, "producao", "cores_mascara.csv"))
    parser.add_argument("--tabela", default=os.path.join(RAIZ, "producao", "tabela_vendas.csv"))
    parser.add_argument("--saida", default=os.path.join(RAIZ, "visualizador", "dados", "unidades.json"))
    args = parser.parse_args()
    gerar(args.mascara, args.cores, args.tabela, args.saida)

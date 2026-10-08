"""
Gera o material de DEMONSTRAÇÃO do visualizador (fachada, máscara de janelas,
tabela de vendas, panoramas 360° e visualizador/dados/empreendimento.json).

Tudo aqui é sintético, só para o protótipo funcionar. Em produção, troque por:
  - fachada.jpg e mascara_fachada.png  -> render do SketchUp/D5 (still + passe de ID)
  - panoramas                           -> panoramas 360° equiretangulares do D5/Enscape
  - tabela_vendas.csv                   -> tabela real do comercial

Uso: python ferramentas/gerar_demo.py
"""
import csv
import json
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gerar_unidades import gerar as gerar_unidades  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(RAIZ, "visualizador")
PRODUCAO = os.path.join(RAIZ, "producao")

TORRE = "T1"
ANDARES = 12
FINAIS = 4
TIPOLOGIA_POR_FINAL = {1: "A", 2: "B", 3: "B", 4: "A"}
FAIXAS = [
    {"id": "baixo", "nome": "1º ao 4º andar", "de": 1, "ate": 4},
    {"id": "medio", "nome": "5º ao 8º andar", "de": 5, "ate": 8},
    {"id": "alto", "nome": "9º ao 12º andar", "de": 9, "ate": 12},
]
PE_DIREITO_TERREO = 4.5
ALTURA_ANDAR = 2.9
ALTURA_OLHO = 1.55


def codigo(andar, final):
    return f"{TORRE}-{andar}{final:02d}"


def cor_mascara(andar, final):
    return (20 + andar * 17, 30 + final * 50, 160)


def altura_olho(andar):
    return PE_DIREITO_TERREO + (andar - 1) * ALTURA_ANDAR + ALTURA_OLHO


# --------------------------------------------------------------------------- fachada

LARG, ALT = 1600, 1800
X0, CELULA = 330, 235
Y_ANDARES, H_ANDAR = 220, 105
Y_TERREO = Y_ANDARES + ANDARES * H_ANDAR
Y_CHAO = Y_TERREO + 170


def y_andar(andar):
    return Y_ANDARES + (ANDARES - andar) * H_ANDAR


def coeficientes_perspectiva(destino, origem):
    a, b = [], []
    for (x, y), (X, Y) in zip(destino, origem):
        a.append([x, y, 1, 0, 0, 0, -X * x, -X * y])
        b.append(X)
        a.append([0, 0, 0, x, y, 1, -Y * x, -Y * y])
        b.append(Y)
    return np.linalg.solve(np.array(a, float), np.array(b, float)).tolist()


def gerar_fachada(rng):
    v = np.linspace(0, 1, ALT)[:, None, None]
    ceu = (1 - v) * np.array([118, 164, 214]) + v * np.array([232, 238, 242])
    base = Image.fromarray(np.broadcast_to(ceu, (ALT, LARG, 3)).astype(np.uint8))
    img = base.convert("RGBA")
    d = ImageDraw.Draw(img)
    mascara = Image.new("RGB", (LARG, ALT), (0, 0, 0))
    dm = ImageDraw.Draw(mascara)

    # prédios do entorno
    for x, w, h, c in [(20, 260, 760, (176, 188, 200)), (1330, 250, 640, (170, 182, 196)),
                       (180, 170, 520, (190, 198, 208)), (1240, 120, 860, (184, 194, 206))]:
        d.rectangle([x, Y_CHAO - h, x + w, Y_CHAO], fill=c)
        for yy in range(Y_CHAO - h + 20, Y_CHAO - 20, 34):
            for xx in range(x + 14, x + w - 20, 30):
                d.rectangle([xx, yy, xx + 14, yy + 18], fill=tuple(int(k * 0.9) for k in c))

    x1 = X0 + FINAIS * CELULA
    # coroamento
    d.rectangle([X0 + 40, 120, x1 - 40, Y_ANDARES], fill=(214, 208, 198))
    d.rectangle([X0 + 40, 120, x1 - 40, 140], fill=(186, 178, 166))
    d.rectangle([X0 - 10, Y_ANDARES - 18, x1 + 10, Y_ANDARES], fill=(238, 235, 228))
    # corpo
    d.rectangle([X0, Y_ANDARES, x1, Y_TERREO], fill=(222, 217, 207))

    for andar in range(1, ANDARES + 1):
        yt = y_andar(andar)
        for final in range(1, FINAIS + 1):
            xc = X0 + (final - 1) * CELULA
            jx0, jy0, jx1, jy1 = xc + 18, yt + 10, xc + CELULA - 18, yt + 90
            acesa = rng.random() < 0.22
            topo = np.array([255, 222, 168] if acesa else [96, 128, 156])
            fundo = np.array([226, 168, 104] if acesa else [52, 72, 94])
            for yy in range(jy0, jy1):
                t = (yy - jy0) / (jy1 - jy0)
                d.line([jx0, yy, jx1, yy], fill=tuple(int(k) for k in (1 - t) * topo + t * fundo))
            # reflexo diagonal
            camada = Image.new("RGBA", img.size, (0, 0, 0, 0))
            dc = ImageDraw.Draw(camada)
            off = rng.randint(0, 90)
            dc.polygon([(jx0 + off, jy0), (jx0 + off + 40, jy0), (jx0 + off - 30, jy1), (jx0 + off - 70, jy1)],
                       fill=(255, 255, 255, 38))
            img = Image.alpha_composite(img, camada)
            d = ImageDraw.Draw(img)
            # caixilhos
            for k in (1, 2):
                xx = jx0 + k * (jx1 - jx0) // 3
                d.line([xx, jy0, xx, jy1], fill=(58, 62, 66), width=3)
            d.rectangle([jx0, jy0, jx1, jy1], outline=(58, 62, 66), width=3)
            # guarda-corpo de vidro da varanda
            camada = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(camada).rectangle([jx0 - 6, yt + 58, jx1 + 6, jy1], fill=(210, 230, 236, 70))
            img = Image.alpha_composite(img, camada)
            d = ImageDraw.Draw(img)
            d.line([jx0 - 6, yt + 58, jx1 + 6, yt + 58], fill=(70, 74, 78), width=3)
            dm.rectangle([jx0 - 6, jy0, jx1 + 6, jy1], fill=cor_mascara(andar, final))
        # laje
        d.rectangle([X0 - 8, yt + 92, x1 + 8, yt + H_ANDAR], fill=(244, 242, 236))
        d.line([X0 - 8, yt + H_ANDAR, x1 + 8, yt + H_ANDAR], fill=(170, 164, 154), width=2)
    for final in range(FINAIS + 1):
        xc = X0 + final * CELULA
        d.rectangle([xc - 6, Y_ANDARES, xc + 6, Y_TERREO], fill=(204, 198, 188))

    # térreo
    d.rectangle([X0 + 30, Y_TERREO, x1 - 30, Y_CHAO], fill=(54, 62, 70))
    for xx in range(X0 + 30, x1 - 30, 94):
        d.rectangle([xx, Y_TERREO, xx + 14, Y_CHAO], fill=(196, 190, 180))
    d.rectangle([X0 + 330, Y_TERREO + 30, X0 + 610, Y_TERREO + 44], fill=(232, 228, 220))
    # chão, paisagismo
    d.rectangle([0, Y_CHAO, LARG, ALT], fill=(176, 172, 164))
    d.rectangle([0, Y_CHAO + 40, LARG, Y_CHAO + 64], fill=(112, 142, 92))
    for x, r in [(260, 90), (390, 70), (1230, 95), (1360, 75), (120, 80), (1490, 85)]:
        d.ellipse([x - r, Y_CHAO - 2 * r + 30, x + r, Y_CHAO + 30], fill=(64, 98, 66))
        d.ellipse([x - r + 18, Y_CHAO - 2 * r + 40, x + r - 30, Y_CHAO], fill=(84, 122, 80))

    # leve perspectiva de baixo para cima (como uma câmera real a nível do pedestre)
    destino = [(0, 0), (LARG, 0), (LARG, ALT), (0, ALT)]
    origem = [(-140, 0), (LARG + 100, 30), (LARG, ALT), (0, ALT)]
    coef = coeficientes_perspectiva(destino, origem)
    fachada = img.convert("RGB").transform((LARG, ALT), Image.PERSPECTIVE, coef, Image.BICUBIC,
                                           fillcolor=(118, 164, 214))
    mascara = mascara.transform((LARG, ALT), Image.PERSPECTIVE, coef, Image.NEAREST, fillcolor=(0, 0, 0))
    fachada.save(os.path.join(WEB, "midia", "fachada.jpg"), quality=86)
    mascara.save(os.path.join(PRODUCAO, "mascara_fachada.png"))

    with open(os.path.join(PRODUCAO, "cores_mascara.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cor", "unidade"])
        for andar in range(1, ANDARES + 1):
            for final in range(1, FINAIS + 1):
                w.writerow(["#%02x%02x%02x" % cor_mascara(andar, final), codigo(andar, final)])


def gerar_tabela(rng, tipologias):
    with open(os.path.join(PRODUCAO, "tabela_vendas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["unidade", "torre", "andar", "final", "tipologia", "area_privativa", "preco", "status"])
        for andar in range(1, ANDARES + 1):
            for final in range(1, FINAIS + 1):
                tip = TIPOLOGIA_POR_FINAL[final]
                preco = tipologias[tip]["preco_base"] * (1 + 0.009 * (andar - 1))
                status = rng.choices(["disponivel", "reservado", "vendido"], [0.55, 0.15, 0.30])[0]
                w.writerow([codigo(andar, final), TORRE, andar, final, tip,
                            tipologias[tip]["area_privativa"], round(preco, -3), status])


# --------------------------------------------------------------------------- panoramas


def ruido(x):
    return np.abs(np.modf(np.sin(x * 12.9898 + 78.233) * 43758.5453)[0])


def direcoes(largura, altura):
    u = (np.arange(largura, dtype=np.float32) + 0.5) / largura
    v = (np.arange(altura, dtype=np.float32) + 0.5) / altura
    lon, lat = np.meshgrid((u - 0.5) * 2 * np.pi, (0.5 - v) * np.pi)
    cl = np.cos(lat)
    return np.stack([cl * np.sin(lon), np.sin(lat), cl * np.cos(lon)], axis=-1)


def vista(D, olho):
    """Céu + mar + camadas de prédios; quanto mais alto o andar, mais livre a vista."""
    el = np.arcsin(np.clip(D[:, 1], -1, 1))
    az = np.arctan2(D[:, 0], D[:, 2]) + np.pi
    t = np.sqrt(np.clip(el / (np.pi / 2), 0, 1))[:, None]
    ceu_horizonte = np.array([228, 236, 242], np.float32)
    cor = (1 - t) * ceu_horizonte + t * np.array([88, 146, 212], np.float32)
    mar = el < 0
    cor[mar] = [64, 118, 148]
    serra = el < 0.03 + 0.018 * np.sin(2.3 * az + 1) + 0.008 * np.sin(7.1 * az)
    cor[serra & ~mar] = [132, 152, 170]
    for dist, hmin, hmax, ang, base in [(900, 20, 80, 0.05, (150, 160, 172)), (400, 15, 60, 0.07, (168, 164, 160)),
                                        (180, 10, 45, 0.11, (188, 178, 166)), (70, 8, 30, 0.2, (200, 190, 176))]:
        chao = np.arctan2(-olho, dist)
        cor[el < chao] = np.array([96, 120, 92]) * (0.8 + dist / 4500) + ceu_horizonte * (dist / 2500)
        idx = np.floor(az / ang)
        h = hmin + (hmax - hmin) * ruido(idx + dist)
        h = np.where(ruido(idx * 3.1 + dist) < 0.15, 0, h)
        topo = np.arctan2(h - olho, dist)
        predio = (el < topo) & (el >= chao)
        f1 = np.modf(az / ang * 6)[0]
        f2 = np.modf((el - chao) * dist / 3.0)[0]
        janela = (f1 > 0.25) & (f1 < 0.75) & (f2 > 0.3) & (f2 < 0.75)
        tom = (0.88 + 0.2 * ruido(idx + 7))[:, None] * np.array(base, np.float32)
        tom = np.where(janela[:, None], tom * 0.78, tom)
        nevoa = min(dist / 1500, 0.6)
        cor[predio] = (tom * (1 - nevoa) + ceu_horizonte * nevoa)[predio]
    cor[el < np.arctan2(-olho, 20)] = [92, 128, 86]
    return cor


PAREDES = {"esquerda": (0, -1), "direita": (0, 1), "fundo": (2, -1), "frente": (2, 1)}


def renderizar_comodo(comodo, olho, largura=2048):
    w, d, h = comodo["dim"]
    cam = np.array(comodo["camera"], np.float32)
    L = int(largura * 1.5)
    D = direcoes(L, L // 2).reshape(-1, 3)
    limites = np.array([w, h, d], np.float32)

    with np.errstate(divide="ignore", invalid="ignore"):
        T = np.where(D > 1e-6, (limites - cam) / D, np.where(D < -1e-6, -cam / D, np.inf))
    eixo = T.argmin(1)
    t = T.min(1)
    P = cam + D * t[:, None]
    sinal = np.sign(D[np.arange(len(D)), eixo])
    normal = np.zeros_like(D)
    normal[np.arange(len(D)), eixo] = -sinal

    cor = np.zeros_like(D)
    piso = (eixo == 1) & (sinal < 0)
    teto = (eixo == 1) & (sinal > 0)
    parede = eixo != 1

    if comodo["piso"] == "madeira":
        tabua = np.floor(P[:, 0] / 0.19)
        cor[piso] = (np.array([170, 128, 92]) * (0.82 + 0.3 * ruido(tabua + np.floor(P[:, 2] / 1.4 + tabua * 0.5)))[:, None])[piso]
        cor[piso & (np.modf(P[:, 0] / 0.19)[0] < 0.035)] = [110, 80, 58]
    else:
        cor[piso] = [214, 210, 202]
        junta = (np.modf(P[:, 0] / 0.9)[0] < 0.005) | (np.modf(P[:, 2] / 0.9)[0] < 0.005)
        cor[piso & junta] = [178, 174, 168]
    cor[teto] = [246, 245, 242]
    cor[parede] = comodo["cor_parede"]
    cor[parede & (P[:, 1] < 0.1)] = [240, 239, 234]

    # oclusão ambiente falsa nos cantos: na face a menor distância é 0, a segunda é a borda mais próxima
    distancias = np.stack([P[:, 0], w - P[:, 0], P[:, 1], h - P[:, 1], P[:, 2], d - P[:, 2]])
    sombra = 1 - 0.2 * np.exp(-np.partition(distancias, 1, axis=0)[1] / 0.25)
    luz = np.array([0.2, 0.6, 1.0], np.float32)
    luz /= np.linalg.norm(luz)
    sombra *= 0.72 + 0.28 * np.clip(normal @ luz, 0, 1)
    sombra *= 0.85 + 0.15 * (P[:, 2] / d)

    vidro = np.zeros(len(D), bool)
    for ab in comodo["aberturas"]:
        ax, lado = PAREDES[ab["parede"]]
        na_parede = (eixo == ax) & (sinal == lado)
        u = P[:, 2] if ax == 0 else P[:, 0]
        (u0, u1), (y0, y1) = ab["u"], ab["y"]
        dentro = na_parede & (u >= u0) & (u <= u1) & (P[:, 1] >= y0) & (P[:, 1] <= y1)
        moldura = 0.06
        miolo = dentro & (u >= u0 + moldura) & (u <= u1 - moldura) & (P[:, 1] <= y1 - moldura) & \
            ((P[:, 1] >= y0 + moldura) | (y0 == 0))
        if ab["tipo"] == "porta":
            cor[dentro] = [236, 234, 229]
            cor[miolo] = [150, 112, 78]
        else:
            cor[dentro] = [70, 72, 76]
            vidro |= miolo
            if ab["tipo"] == "varanda":
                meio = (u0 + u1) / 2
                cor[dentro & (np.abs(u - meio) < 0.03)] = [70, 72, 76]
    if vidro.any():
        cor_vista = vista(D[vidro], olho)
        for ab in comodo["aberturas"]:
            if ab["tipo"] == "varanda":
                gc = P[vidro, 1] < 1.05
                cor_vista[gc] = cor_vista[gc] * 0.82 + np.array([196, 216, 222]) * 0.18
                cor_vista[np.abs(P[vidro, 1] - 1.05) < 0.025] = [70, 72, 76]
        cor[vidro] = cor_vista
        sombra[vidro] = 1

    for movel in comodo["moveis"]:
        mn = np.array(movel["min"], np.float32)
        mx = np.array(movel["max"], np.float32)
        with np.errstate(divide="ignore", invalid="ignore"):
            t1 = (mn - cam) / D
            t2 = (mx - cam) / D
        tn = np.nan_to_num(np.minimum(t1, t2), nan=-np.inf)
        tf = np.nan_to_num(np.maximum(t1, t2), nan=np.inf)
        perto = tn.max(1)
        acerto = (perto > 0) & (perto < tf.min(1)) & (perto < t)
        if mn[1] <= 0.01 and mx[1] - mn[1] > 0.05:
            sob = piso & (P[:, 0] > mn[0] - 0.1) & (P[:, 0] < mx[0] + 0.1) & \
                (P[:, 2] > mn[2] - 0.1) & (P[:, 2] < mx[2] + 0.1)
            sombra[sob] *= 0.72
        if not acerto.any():
            continue
        ax_m = tn.argmax(1)[acerto]
        n = np.zeros((acerto.sum(), 3), np.float32)
        n[np.arange(len(ax_m)), ax_m] = -np.sign(D[acerto][np.arange(len(ax_m)), ax_m])
        t[acerto] = perto[acerto]
        cor[acerto] = movel["cor"]
        sombra[acerto] = (0.62 + 0.38 * np.clip(n @ luz, 0, 1)) * 0.95

    final = np.clip(cor * sombra[:, None], 0, 255).astype(np.uint8).reshape(L // 2, L, 3)
    return Image.fromarray(final).resize((largura, largura // 2), Image.LANCZOS)


def angulos(cam, ponto):
    vx, vy, vz = (ponto[i] - cam[i] for i in range(3))
    return {"pitch": round(math.degrees(math.atan2(vy, math.hypot(vx, vz))), 1),
            "yaw": round(math.degrees(math.atan2(vx, vz)), 1)}


def comodos_da_tipologia(dims):
    (sw, sd), (cw, cd), (qw, qd) = dims
    H = 2.7
    sala = {
        "id": "sala", "nome": "Sala e varanda", "dim": (sw, sd, H), "camera": (sw / 2, ALTURA_OLHO, sd * 0.55),
        "piso": "porcelanato", "cor_parede": [214, 206, 194],
        "aberturas": [
            {"parede": "frente", "tipo": "varanda", "u": (0.15 * sw, 0.85 * sw), "y": (0, 2.3)},
            {"parede": "esquerda", "tipo": "porta", "u": (sd * 0.2, sd * 0.2 + 0.85), "y": (0, 2.1), "destino": "cozinha"},
            {"parede": "direita", "tipo": "porta", "u": (sd * 0.25, sd * 0.25 + 0.85), "y": (0, 2.1), "destino": "suite"},
        ],
        "moveis": [
            {"min": (0.2 * sw, 0, 0.9), "max": (0.8 * sw, 0.012, sd * 0.5), "cor": (204, 194, 174)},
            {"min": (0.22 * sw, 0, 0.08), "max": (0.78 * sw, 0.42, 0.95), "cor": (118, 122, 128)},
            {"min": (0.22 * sw, 0, 0.08), "max": (0.78 * sw, 0.86, 0.3), "cor": (112, 116, 122)},
            {"min": (0.22 * sw, 0, 0.08), "max": (0.22 * sw + 0.18, 0.62, 0.95), "cor": (112, 116, 122)},
            {"min": (0.78 * sw - 0.18, 0, 0.08), "max": (0.78 * sw, 0.62, 0.95), "cor": (112, 116, 122)},
            {"min": (0.4 * sw, 0, 1.2), "max": (0.6 * sw, 0.38, 1.7), "cor": (112, 82, 58)},
            {"min": (0.25, 0, sd - 0.6), "max": (0.6, 0.5, sd - 0.25), "cor": (88, 88, 90)},
            {"min": (0.2, 0.5, sd - 0.65), "max": (0.65, 1.45, sd - 0.2), "cor": (68, 108, 70)},
        ],
        "infos": [
            {"ponto": (sw / 2 + 0.7, 0, sd * 0.55 - 1.1), "texto": "Piso em porcelanato 90×90 acetinado"},
            {"ponto": (sw / 2, 1.6, sd), "vista": True,
             "texto": "Porta de correr em alumínio, vidro laminado e guarda-corpo em vidro"},
        ],
    }
    cozinha = {
        "id": "cozinha", "nome": "Cozinha", "dim": (cw, cd, H), "camera": (cw / 2, ALTURA_OLHO, cd * 0.62),
        "piso": "porcelanato", "cor_parede": [232, 230, 226],
        "aberturas": [
            {"parede": "frente", "tipo": "janela", "u": (0.3 * cw, 0.7 * cw), "y": (1.1, 2.1)},
            {"parede": "direita", "tipo": "porta", "u": (cd * 0.3, cd * 0.3 + 0.85), "y": (0, 2.1), "destino": "sala"},
        ],
        "moveis": [
            {"min": (0.05, 0, 0), "max": (cw - 0.85, 0.88, 0.6), "cor": (236, 234, 230)},
            {"min": (0.03, 0.88, 0), "max": (cw - 0.83, 0.92, 0.62), "cor": (62, 64, 68)},
            {"min": (0.05, 1.5, 0), "max": (cw - 0.85, 2.25, 0.35), "cor": (222, 216, 206)},
            {"min": (cw - 0.8, 0, 0), "max": (cw - 0.05, 1.85, 0.7), "cor": (200, 202, 206)},
        ],
        "infos": [
            {"ponto": ((cw - 0.85) / 2, 0.92, 0.3), "texto": "Bancada em quartzo cinza com cuba em inox"},
            {"ponto": (cw / 2, 1.6, cd), "vista": True, "texto": "Janela de alumínio com vidro"},
        ],
    }
    suite = {
        "id": "suite", "nome": "Suíte", "dim": (qw, qd, H), "camera": (qw / 2, ALTURA_OLHO, qd * 0.74),
        "piso": "madeira", "cor_parede": [200, 208, 196],
        "aberturas": [
            {"parede": "frente", "tipo": "janela", "u": (0.2 * qw, 0.8 * qw), "y": (0.5, 2.2)},
            {"parede": "esquerda", "tipo": "porta", "u": (qd * 0.55, qd * 0.55 + 0.85), "y": (0, 2.1), "destino": "sala"},
        ],
        "moveis": [
            {"min": (qw / 2 - 0.8, 0, 0.05), "max": (qw / 2 + 0.8, 0.45, 2.05), "cor": (236, 233, 227)},
            {"min": (qw / 2 - 1.0, 0, 0), "max": (qw / 2 + 1.0, 1.15, 0.08), "cor": (150, 120, 95)},
            {"min": (qw / 2 - 0.7, 0.45, 0.15), "max": (qw / 2 - 0.05, 0.6, 0.5), "cor": (248, 247, 244)},
            {"min": (qw / 2 + 0.05, 0.45, 0.15), "max": (qw / 2 + 0.7, 0.6, 0.5), "cor": (248, 247, 244)},
            {"min": (qw / 2 - 0.82, 0.44, 1.4), "max": (qw / 2 + 0.82, 0.48, 1.95), "cor": (118, 130, 152)},
            {"min": (qw / 2 - 1.5, 0, 0.05), "max": (qw / 2 - 1.05, 0.5, 0.45), "cor": (150, 120, 95)},
            {"min": (qw / 2 + 1.05, 0, 0.05), "max": (qw / 2 + 1.5, 0.5, 0.45), "cor": (150, 120, 95)},
        ],
        "infos": [
            {"ponto": (qw / 2 + 0.9, 0, qd * 0.74 - 0.5), "texto": "Piso vinílico amadeirado"},
            {"ponto": (qw / 2, 1.5, qd), "vista": True, "texto": "Janela com persiana integrada"},
        ],
    }
    return [sala, cozinha, suite]


def gerar_panoramas_e_config(tipologias):
    nomes_comodos = {"sala": "Sala", "cozinha": "Cozinha", "suite": "Suíte"}
    config_tip = {}
    for tip, dados in tipologias.items():
        comodos = comodos_da_tipologia(dados["dims"])
        lista = []
        for c in comodos:
            for faixa in FAIXAS:
                andar_medio = (faixa["de"] + faixa["ate"]) / 2
                arquivo = f"{tip}-{c['id']}-{faixa['id']}.jpg"
                renderizar_comodo(c, altura_olho(andar_medio)).save(
                    os.path.join(WEB, "midia", "panoramas", arquivo), quality=82)
                print("panorama", arquivo)
            hotspots = []
            for ab in c["aberturas"]:
                if "destino" not in ab:
                    continue
                ax, lado = PAREDES[ab["parede"]]
                u = sum(ab["u"]) / 2
                limite = c["dim"][0] if ax == 0 else c["dim"][1]
                pos = 0 if lado < 0 else limite
                ponto = (pos, 1.05, u) if ax == 0 else (u, 1.05, pos)
                hotspots.append({"tipo": "comodo", "destino": ab["destino"],
                                 "texto": nomes_comodos[ab["destino"]], **angulos(c["camera"], ponto)})
            for info in c["infos"]:
                hotspots.append({"tipo": "vista" if info.get("vista") else "info", "texto": info["texto"],
                                 **angulos(c["camera"], info["ponto"])})
            lista.append({"id": c["id"], "nome": c["nome"],
                          "panorama": f"midia/panoramas/{tip}-{c['id']}-{{faixa}}.jpg",
                          "yaw_inicial": 0, "pitch_inicial": -8, "hotspots": hotspots})
        config_tip[tip] = {k: dados[k] for k in ("nome", "quartos", "suites", "vagas", "area_privativa")}
        config_tip[tip]["comodos"] = lista

    config = {
        "nome": "Residencial Mirante",
        "subtitulo": "Empreendimento de demonstração",
        "endereco": "Endereço do empreendimento",
        "torres": {TORRE: "Torre Única"},
        "fachada": "midia/fachada.jpg",
        "contato": {"whatsapp": "",
                    "mensagem": "Olá! Tenho interesse na unidade {unidade} ({tipologia}) do {empreendimento}."},
        "financiamento": {"taxa_anual": 0.11, "prazo_anos": 30, "comprometimento_renda": 0.3},
        "faixas_vista": FAIXAS,
        "tipologias": config_tip,
        "aviso_legal": "Imagens meramente ilustrativas. Mobiliário e decoração não fazem parte do contrato. "
                       "Vista simulada por faixa de andares. Valores sujeitos a alteração sem aviso prévio.",
    }
    with open(os.path.join(WEB, "dados", "empreendimento.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


TIPOLOGIAS = {
    "A": {"nome": "Tipo A · 3 quartos (1 suíte)", "quartos": 3, "suites": 1, "vagas": 2, "area_privativa": 92.0,
          "preco_base": 780000, "dims": ((5.2, 4.4), (3.2, 3.0), (3.8, 3.5))},
    "B": {"nome": "Tipo B · 2 quartos (1 suíte)", "quartos": 2, "suites": 1, "vagas": 1, "area_privativa": 68.0,
          "preco_base": 560000, "dims": ((4.2, 3.8), (2.8, 2.7), (3.3, 3.1))},
}

if __name__ == "__main__":
    rng = random.Random(42)
    gerar_fachada(rng)
    gerar_tabela(rng, TIPOLOGIAS)
    gerar_panoramas_e_config(TIPOLOGIAS)
    gerar_unidades(os.path.join(PRODUCAO, "mascara_fachada.png"), os.path.join(PRODUCAO, "cores_mascara.csv"),
                   os.path.join(PRODUCAO, "tabela_vendas.csv"), os.path.join(WEB, "dados", "unidades.json"))

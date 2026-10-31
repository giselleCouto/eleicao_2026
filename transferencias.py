#!/usr/bin/env python3
"""
Estima para onde foi cada grupo de eleitores entre dois turnos (ou entre duas eleições),
a partir dos arquivos de ./dados gerados por extrair_presidente.py.

O voto é secreto: não existe dado individual de quem votou em quem. O método é inferência
ecológica — compara milhares de seções e estima a fração de cada grupo de origem que foi para
cada destino. Como o resultado depende das escolhas do modelo, rodamos seis variantes:
  - restrição: (a) cada fração entre 0 e 1, destino por destino; (b) cada linha somando 100%
    (cada eleitor de origem vai para exatamente um destino);
  - nível: o país inteiro, cada macrorregião ou cada estado (somando as contagens).
Todas passam por um ajuste proporcional iterativo (IPF) para bater com os votos contados.
Depois conferimos cada variante contra limites que os boletins garantem sem modelo (por exemplo,
quantos abstencionistas do 1º turno no mínimo votaram no 2º). O valor central é o da variante
mais desagregada que respeita esses limites (estado por estado, cada linha somando 100%); a faixa vai
do menor ao maior valor entre as variantes que respeitam os limites.

Grava em ./resultados:
  transferencia_<ano>_completa.csv          1º → 2º turno, todos os candidatos, com faixas
  transferencia_2022_2026_<turno>t.csv      de uma eleição para a outra, por município
  limites_secoes_<ano>.csv                  fatos que não dependem de modelo (quedas por seção)
  pisos_<ano>.csv                           mínimos garantidos pelos boletins, por grupo

Requer pandas, numpy e scipy.
"""
import os

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear

BASE = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(BASE, "dados")
OUT = os.path.join(BASE, "resultados")
os.makedirs(OUT, exist_ok=True)
LULA, PL = "V_13", "V_22"
REGIAO = {**{u: "N" for u in ["AC", "AM", "AP", "PA", "RO", "RR", "TO"]},
          **{u: "NE" for u in ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"]},
          **{u: "CO" for u in ["DF", "GO", "MS", "MT"]}, **{u: "SE" for u in ["ES", "MG", "RJ", "SP"]},
          **{u: "S" for u in ["PR", "RS", "SC"]}, "ZZ": "EXT"}
REFERENCIA = ("estado/linhas", "regiao/linhas", "estado/colunas", "regiao/colunas", "nacional/linhas", "nacional/colunas")
FICAM = ("Brancos", "Nulos", "Abstenção")   # categorias que existem nos dois turnos, além dos finalistas


def carregar(ano, turno):
    d = pd.read_csv(os.path.join(DADOS, f"presidente_{ano}_{turno}t_secoes.csv.gz"), sep=";",
                    dtype={"UF": str, "ZONA": str, "SECAO": str, "CD_MUNICIPIO": str, "LOCAL": str})
    c = pd.read_csv(os.path.join(DADOS, f"candidatos_{ano}_{turno}t.csv"), sep=";", dtype=str)
    nomes = dict(zip("V_" + c.NUMERO, c.NOME.str.title()))
    nomes[LULA] = "Lula"
    nomes[PL] = "Jair Bolsonaro" if ano == "2022" else "Flávio Bolsonaro"
    return d, nomes


def grupos(d, nomes, sufixo=""):
    """Contagens por unidade: cada candidato, brancos, nulos e abstenção."""
    vc = [c for c in d.columns if c.startswith("V_") and c.endswith(sufixo)]
    base = [c[: len(c) - len(sufixo)] if sufixo else c for c in vc]
    ordem = sorted(range(len(vc)), key=lambda i: (base[i] not in (LULA, PL), -d[vc[i]].sum()))
    G = pd.DataFrame({nomes[base[i]]: d[vc[i]] for i in ordem})
    G["Brancos"] = d["BRANCOS" + sufixo]
    G["Nulos"] = d["NULOS" + sufixo]
    G["Abstenção"] = d["APTOS" + sufixo] - d["COMPARECIMENTO" + sufixo]
    return G


# ---------------------------------------------------------------- estimadores
def gram(X, Y, w):
    sw = np.sqrt(w)[:, None]
    Xw, Yw = X * sw, Y * sw
    return Xw.T @ Xw, Xw.T @ Yw


def por_colunas(G, C):
    """Mínimos quadrados com cada coeficiente em [0, 1], destino por destino."""
    k = G.shape[0]
    R = np.linalg.cholesky(G + 1e-12 * np.trace(G) / k * np.eye(k)).T
    B = np.zeros((k, C.shape[1]))
    for j in range(C.shape[1]):
        B[:, j] = lsq_linear(R, np.linalg.solve(R.T, C[:, j]), bounds=(0, 1), method="bvls").x
    return B


def simplex(V):
    """Projeta cada linha de V no simplex (valores >= 0 somando 1)."""
    n, m = V.shape
    U = -np.sort(-V, axis=1)
    css = np.cumsum(U, axis=1) - 1
    idx = np.arange(1, m + 1)
    rho = (U - css / idx > 0).sum(axis=1)
    theta = css[np.arange(n), rho - 1] / rho
    return np.maximum(V - theta[:, None], 0)


def por_linhas(G, C, it=20000):
    """Mínimos quadrados com cada linha no simplex (gradiente projetado acelerado)."""
    k, m = C.shape
    L = 2 * np.linalg.eigvalsh(G).max()
    B = np.full((k, m), 1 / m)
    Z, t = B.copy(), 1.0
    for _ in range(it):
        Bn = simplex(Z - (2 * (G @ Z - C)) / L)
        tn = (1 + np.sqrt(1 + 4 * t * t)) / 2
        Z = Bn + (t - 1) / tn * (Bn - B)
        B, t = Bn, tn
    return B


def ipf(Bm, origem, destino, it=2000):
    o = np.asarray(origem, float)
    dd = np.asarray(destino, float) * o.sum() / np.sum(destino)
    N = Bm * o[:, None] + 1e-9
    for _ in range(it):
        N *= (o / N.sum(axis=1))[:, None]
        N *= (dd / N.sum(axis=0))[None, :]
    return N


def estimar(Go, Gd, w, niveis):
    """Roda as seis variantes. niveis = {'nacional': rótulos, 'regiao': ..., 'estado': ...}.
    Retorna dict nome_da_variante -> matriz de contagens (linhas = origem, colunas = destino)."""
    ao, ad = Go.sum(axis=1).values, Gd.sum(axis=1).values
    ok = (ao > 0) & (ad > 0)
    Xc, Yc = Go.values[ok], Gd.values[ok]
    X, Y, w = Xc / ao[ok][:, None], Yc / ad[ok][:, None], w[ok]
    res = {}
    for nivel, rot in niveis.items():
        rot = np.asarray(rot)[ok]
        for nome, f in (("colunas", por_colunas), ("linhas", por_linhas)):
            N = np.zeros((Go.shape[1], Gd.shape[1]))
            for g in np.unique(rot):
                m = rot == g
                if m.sum() < 30:       # unidades muito pequenas ficam de fora da estimativa
                    continue
                N += ipf(f(*gram(X[m], Y[m], w[m])), Xc[m].sum(axis=0), Yc[m].sum(axis=0))
            # ajusta ao total nacional (repõe as unidades puladas)
            N = ipf(N / np.maximum(N.sum(axis=1, keepdims=True), 1e-9), Xc.sum(axis=0), Yc.sum(axis=0))
            res[f"{nivel}/{nome}"] = pd.DataFrame(N, index=Go.columns, columns=Gd.columns)
    return res


def pisos(Go, Gd):
    """Mínimos garantidos sem modelo, somando seção a seção: para cada categoria que existe nos dois
    lados, quantos no mínimo saíram dela (max(0, antes − depois))."""
    return {c: float((Go[c] - Gd[c]).clip(lower=0).sum()) for c in Go.columns if c in Gd.columns}


def resumir(var, Go, piso):
    """Valor central (variante de referência que respeita os pisos) e faixa (mín.–máx. das que respeitam)."""
    n = Go.sum()
    P = {k: v.div(v.sum(axis=1), axis=0) for k, v in var.items()}
    respeita = {}
    for k, p in P.items():
        respeita[k] = all(not (n[c] > 0 and p.loc[c, c] > 1 - saiu / n[c] + 2e-4) for c, saiu in piso.items())
    validas = [k for k in P if respeita[k]]
    if len(validas) < 2:
        validas = list(P)
    A = np.array([P[k].values for k in validas])
    # Referência: a variante mais desagregada que respeita os pisos (fecha exatamente com os totais)
    ref = next((k for k in REFERENCIA if k in validas), validas[0])
    central = P[ref]
    idx, cols = central.index, central.columns
    lo = pd.DataFrame(A.min(axis=0), index=idx, columns=cols)
    hi = pd.DataFrame(A.max(axis=0), index=idx, columns=cols)
    linhas = []
    for o in idx:
        for dst in cols:
            linhas.append({"origem": o, "eleitores_origem": int(round(n[o])), "destino": dst,
                           "pct": central.loc[o, dst], "votos": central.loc[o, dst] * n[o],
                           "pct_min": lo.loc[o, dst], "pct_max": hi.loc[o, dst],
                           **{f"pct[{k}]": P[k].loc[o, dst] for k in validas}})
    t = pd.DataFrame(linhas)
    t.attrs["variantes_validas"] = validas
    t.attrs["referencia"] = ref
    return t


def entre_turnos(ano):
    d1, n1 = carregar(ano, 1)
    d2, n2 = carregar(ano, 2)
    k = ["UF", "ZONA", "SECAO"]
    j = d1.set_index(k).add_suffix("_1").join(d2.set_index(k).add_suffix("_2"), how="inner").reset_index()
    Go, Gd = grupos(j, n1, "_1"), grupos(j, n2, "_2")
    niveis = {"nacional": np.zeros(len(j), int), "regiao": j.UF.map(REGIAO).values, "estado": j.UF.values}
    var = estimar(Go, Gd, j.APTOS_2.values.astype(float), niveis)
    piso = pisos(Go, Gd)
    t = resumir(var, Go, piso)
    t.to_csv(os.path.join(OUT, f"transferencia_{ano}_completa.csv"), sep=";", index=False, decimal=",")
    with open(os.path.join(OUT, f"transferencia_{ano}_variantes_validas.txt"), "w") as f:
        f.write("referência: " + t.attrs["referencia"] + "\nrespeitam os pisos:\n" + "\n".join(t.attrs["variantes_validas"]) + "\n")

    # pisos: quem no mínimo saiu de cada categoria e quem no mínimo entrou em cada uma
    entrou = {c: float((Gd[c] - Go[c]).clip(lower=0).sum()) for c in piso}
    pd.DataFrame([{"grupo": c, "no_1o_turno": int(Go[c].sum()), "no_2o_turno": int(Gd[c].sum()),
                   "saiu_no_minimo": int(piso[c]), "entrou_no_minimo": int(entrou[c])} for c in piso]) \
        .to_csv(os.path.join(OUT, f"pisos_{ano}.csv"), sep=";", index=False, decimal=",")

    # fatos sem modelo: em quantas seções cada finalista perdeu votos entre os turnos
    lim = []
    for c, nome in ((LULA, n1[LULA]), (PL, n1[PL])):
        dv = j[c + "_2"] - j[c + "_1"]
        # Limite de Duncan-Davis: mínimo de eleitores que foram direto deste finalista para o outro
        direto = (j[c + "_1"] - j[c + "_2"] - (j.BRANCOS_2 + j.NULOS_2) - (j.APTOS_2 - j.COMPARECIMENTO_2)).clip(lower=0)
        estavel = (dv < 0) & (j.COMPARECIMENTO_2 >= j.COMPARECIMENTO_1)
        lim.append({"candidato": nome, "secoes": len(j), "secoes_com_queda": int((dv < 0).sum()),
                    "pct_secoes_com_queda": float((dv < 0).mean()), "soma_das_quedas": int(-dv[dv < 0].sum()),
                    "soma_dos_ganhos": int(dv[dv > 0].sum()), "variacao_total": int(dv.sum()),
                    "secoes_queda_com_comparecimento_igual_ou_maior": int(estavel.sum()),
                    "votos_perdidos_com_comparecimento_igual_ou_maior": int(-dv[estavel].sum()),
                    "troca_direta_minima_para_o_outro": int(direto.sum())})
    pd.DataFrame(lim).to_csv(os.path.join(OUT, f"limites_secoes_{ano}.csv"), sep=";", index=False, decimal=",")
    return t


def entre_eleicoes(turno):
    """2022 → 2026 por município (as seções mudam de uma eleição para a outra)."""
    def mun(ano):
        d, nomes = carregar(ano, turno)
        G = grupos(d, nomes)
        if turno == 1:  # candidatos com menos de 1% dos votos válidos viram "Demais candidatos"
            cand = [c for c in G.columns if c not in FICAM]
            val = G[cand].sum().sum()
            peq = [c for c in cand[2:] if G[c].sum() < 0.01 * val]
            G["Demais candidatos"] = G[peq].sum(axis=1)
            G = G.drop(columns=peq)
            G = G[[c for c in G.columns if c not in FICAM] + list(FICAM)]
        G["UF"], G["MUN"] = d.UF, d.CD_MUNICIPIO
        return G.groupby(["UF", "MUN"]).sum()
    a, b = mun("2022"), mun("2026")
    j = a.join(b, lsuffix="|22", rsuffix="|26", how="inner")
    Go = j[[c + ("|22" if c in b.columns else "") for c in a.columns]]
    Gd = j[[c + ("|26" if c in a.columns else "") for c in b.columns]]
    Go.columns, Gd.columns = list(a.columns), list(b.columns)
    ufs = np.array([u for u, _ in j.index])
    niveis = {"nacional": np.zeros(len(j), int), "regiao": np.array([REGIAO[u] for u in ufs]), "estado": ufs}
    var = estimar(Go, Gd, Gd.sum(axis=1).values.astype(float), niveis)
    t = resumir(var, Go, {})
    t.to_csv(os.path.join(OUT, f"transferencia_2022_2026_{turno}t.csv"), sep=";", index=False, decimal=",")
    return t


if __name__ == "__main__":
    for ano in ("2022", "2026"):
        print("entre turnos", ano, flush=True)
        entre_turnos(ano)
    for turno in (1, 2):
        print("entre eleições, turno", turno, flush=True)
        entre_eleicoes(turno)
    print("pronto")

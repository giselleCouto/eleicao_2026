#!/usr/bin/env python3
"""
Estima para onde foi cada grupo de eleitores entre dois turnos (ou entre duas eleições),
a partir dos arquivos de ./dados gerados por extrair_presidente.py.

O voto é secreto: não existe dado individual de quem votou em quem. O método é inferência
ecológica — compara milhares de seções e estima a fração de cada grupo de origem que foi para
cada destino:
  1. Regressão de Goodman com limites: para cada destino, mínimos quadrados ponderados pelos
     eleitores aptos, com cada fração restrita ao intervalo [0, 1].
  2. Ajuste proporcional iterativo (IPF): corrige a matriz para que cada linha some o total
     real do grupo de origem e cada coluna some o total real do destino.
  3. Intervalo de 90%: bootstrap por município (100 reamostragens).
  4. Robustez: a mesma estimativa feita estado por estado e somada.

Grava em ./resultados:
  transferencia_<ano>_completa.csv          1º → 2º turno, todos os candidatos, com intervalos
  transferencia_<ano>_por_estado.csv        a mesma matriz estimada estado por estado
  transferencia_2022_2026_<turno>t.csv      de uma eleição para a outra, por município
  limites_secoes_<ano>.csv                  fatos que não dependem de modelo (quedas por seção)

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
B = 100                       # reamostragens do bootstrap
SEMENTE = 2026
LULA, PL = "V_13", "V_22"


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


def gram(X, Y, w):
    sw = np.sqrt(w)[:, None]
    Xw, Yw = X * sw, Y * sw
    return Xw.T @ Xw, Xw.T @ Yw


def resolver(XtX, XtY):
    """Mínimos quadrados com cada coeficiente em [0, 1], via o problema reduzido (Cholesky)."""
    k = XtX.shape[0]
    R = np.linalg.cholesky(XtX + 1e-12 * np.trace(XtX) / k * np.eye(k)).T
    Bm = np.zeros((k, XtY.shape[1]))
    for j in range(XtY.shape[1]):
        c = np.linalg.solve(R.T, XtY[:, j])
        Bm[:, j] = lsq_linear(R, c, bounds=(0, 1), method="bvls").x
    return Bm


def ipf(Bm, origem, destino, it=1000):
    o = np.asarray(origem, float)
    dd = np.asarray(destino, float) * o.sum() / np.sum(destino)
    N = Bm * o[:, None] + 1e-9
    for _ in range(it):
        N *= (o / N.sum(axis=1))[:, None]
        N *= (dd / N.sum(0))[None, :]
    return N


def estimar(Go, Gd, w, municipio=None, uf=None):
    """Retorna (percentuais, votos, ic5, ic95, por_estado) — linhas = origem, colunas = destino."""
    ao, ad = Go.sum(axis=1).values, Gd.sum(axis=1).values
    ok = (ao > 0) & (ad > 0)
    Go, Gd, w = Go[ok], Gd[ok], w[ok]
    X, Y = Go.values / ao[ok][:, None], Gd.values / ad[ok][:, None]
    origem, destino = Go.sum().values, Gd.sum().values

    N = ipf(resolver(*gram(X, Y, w)), origem, destino)
    P = N / N.sum(1, keepdims=True)

    amostras = []
    if municipio is not None:
        mun = pd.factorize(municipio[ok])[0]
        rng = np.random.default_rng(SEMENTE)
        for _ in range(B):
            cont = np.bincount(rng.integers(0, mun.max() + 1, mun.max() + 1), minlength=mun.max() + 1)
            wb = w * cont[mun]
            m = wb > 0
            Nb = ipf(resolver(*gram(X[m], Y[m], wb[m])), (Go.values[m] * cont[mun][m][:, None]).sum(0),
                     (Gd.values[m] * cont[mun][m][:, None]).sum(0))
            amostras.append(Nb / Nb.sum(1, keepdims=True))
    A = np.array(amostras) if amostras else None

    por_estado = None
    if uf is not None:
        Ns = np.zeros_like(N)
        u = uf[ok]
        for e in np.unique(u):
            m = u == e
            if m.sum() < 50:
                continue
            Ns += ipf(resolver(*gram(X[m], Y[m], w[m])), Go.values[m].sum(0), Gd.values[m].sum(0))
        por_estado = Ns / Ns.sum(1, keepdims=True)

    idx, cols = list(Go.columns), list(Gd.columns)
    df = lambda M: pd.DataFrame(M, index=idx, columns=cols)
    return (df(P), df(N), df(np.percentile(A, 5, 0)) if A is not None else None,
            df(np.percentile(A, 95, 0)) if A is not None else None, df(por_estado) if por_estado is not None else None)


def tabela_longa(P, N, lo, hi, est, tamanho):
    linhas = []
    for o in P.index:
        for dst in P.columns:
            linhas.append({"origem": o, "eleitores_origem": int(round(tamanho[o])), "destino": dst,
                           "pct": P.loc[o, dst], "votos": N.loc[o, dst],
                           "ic90_min": lo.loc[o, dst] if lo is not None else np.nan,
                           "ic90_max": hi.loc[o, dst] if hi is not None else np.nan,
                           "pct_por_estado": est.loc[o, dst] if est is not None else np.nan})
    return pd.DataFrame(linhas)


def entre_turnos(ano):
    d1, n1 = carregar(ano, 1)
    d2, n2 = carregar(ano, 2)
    k = ["UF", "ZONA", "SECAO"]
    j = d1.set_index(k).add_suffix("_1").join(d2.set_index(k).add_suffix("_2"), how="inner").reset_index()
    Go, Gd = grupos(j, n1, "_1"), grupos(j, n2, "_2")
    P, N, lo, hi, est = estimar(Go, Gd, j.APTOS_2.values.astype(float),
                                municipio=(j.UF + "-" + j.CD_MUNICIPIO_1).values, uf=j.UF.values)
    t = tabela_longa(P, N, lo, hi, est, Go.sum())
    t.to_csv(os.path.join(OUT, f"transferencia_{ano}_completa.csv"), sep=";", index=False, decimal=",")

    # fatos sem modelo: em quantas seções cada finalista perdeu votos entre os turnos
    lim = []
    for c, nome in ((LULA, n1[LULA]), (PL, n1[PL])):
        dv = j[c + "_2"] - j[c + "_1"]
        # Limite de Duncan-Davis: mínimo de eleitores que foram direto deste finalista para o outro
        direto = (j[c + "_1"] - j[c + "_2"] - (j.BRANCOS_2 + j.NULOS_2) - (j.APTOS_2 - j.COMPARECIMENTO_2)).clip(lower=0)
        lim.append({"candidato": nome, "secoes": len(j), "secoes_com_queda": int((dv < 0).sum()),
                    "pct_secoes_com_queda": float((dv < 0).mean()), "soma_das_quedas": int(-dv[dv < 0].sum()),
                    "soma_dos_ganhos": int(dv[dv > 0].sum()), "variacao_total": int(dv.sum()),
                    "secoes_queda_com_comparecimento_igual_ou_maior": int(((dv < 0) &
                        (j.COMPARECIMENTO_2 >= j.COMPARECIMENTO_1)).sum()),
                    "votos_perdidos_com_comparecimento_igual_ou_maior": int(-dv[(dv < 0) &
                        (j.COMPARECIMENTO_2 >= j.COMPARECIMENTO_1)].sum()),
                    "troca_direta_minima_para_o_outro": int(direto.sum())})
    pd.DataFrame(lim).to_csv(os.path.join(OUT, f"limites_secoes_{ano}.csv"), sep=";", index=False, decimal=",")
    return t


def entre_eleicoes(turno):
    """2022 → 2026 por município (as seções mudam de uma eleição para a outra)."""
    def mun(ano):
        d, nomes = carregar(ano, turno)
        G = grupos(d, nomes)
        if turno == 1:  # candidatos com menos de 1% dos votos válidos viram "Demais candidatos"
            cand = [c for c in G.columns if c not in ("Brancos", "Nulos", "Abstenção")]
            val = G[cand].sum().sum()
            peq = [c for c in cand[2:] if G[c].sum() < 0.01 * val]
            G["Demais candidatos"] = G[peq].sum(axis=1)
            G = G.drop(columns=peq)
            G = G[[c for c in G.columns if c not in ("Brancos", "Nulos", "Abstenção")] + ["Brancos", "Nulos", "Abstenção"]]
        G["UF"], G["MUN"] = d.UF, d.CD_MUNICIPIO
        return G.groupby(["UF", "MUN"]).sum()
    a, b = mun("2022"), mun("2026")
    j = a.join(b, lsuffix="|22", rsuffix="|26", how="inner")
    Go = j[[c + ("|22" if c in b.columns else "") for c in a.columns]]
    Gd = j[[c + ("|26" if c in a.columns else "") for c in b.columns]]
    Go.columns, Gd.columns = list(a.columns), list(b.columns)
    w = Gd.sum(axis=1).values.astype(float)
    P, N, lo, hi, est = estimar(Go, Gd, w, municipio=np.array([f"{u}-{m}" for u, m in j.index]),
                                uf=np.array([u for u, _ in j.index]))
    t = tabela_longa(P, N, lo, hi, est, Go.sum())
    t.to_csv(os.path.join(OUT, f"transferencia_2022_2026_{turno}t.csv"), sep=";", index=False, decimal=",")
    return t


if __name__ == "__main__":
    for ano in ("2022", "2026"):
        print("entre turnos", ano)
        entre_turnos(ano)
    for turno in (1, 2):
        print("entre eleições, turno", turno)
        entre_eleicoes(turno)
    print("pronto")

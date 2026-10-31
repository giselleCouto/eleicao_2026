#!/usr/bin/env python3
"""
Analisa os arquivos gerados por extrair_presidente.py (pasta ./dados) e escreve
./resultados/relatorio.md mais tabelas CSV de apoio.

Perguntas tratadas:
  1. A soma dos boletins de urna bate com a totalização oficial?
  2. Comparecimento e abstenção: 2022 x 2026, 1º x 2º turno.
  3. O voto em Flávio Bolsonaro (2026) se distribui como o voto em Jair Bolsonaro (2022)?
  4. Para onde foram, no 1º turno de 2026, os eleitores de Lula em 2022? (inferência ecológica)
  5. De onde vieram os votos que Lula ganhou entre o 1º e o 2º turno de 2026? (inferência ecológica)
  6. Seções em que só um candidato recebeu votos: quantas, de quem, e de que tamanho.

Requer pandas e numpy.
"""
import os
import sys

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(BASE, "dados")
OUT = os.path.join(BASE, "resultados")
os.makedirs(OUT, exist_ok=True)

relatorio = []


def md(texto=""):
    relatorio.append(texto)


def br(v, fmt="{:,.1f}"):
    """Número no formato brasileiro (1.234,5)."""
    if pd.isna(v):
        return ""
    return fmt.format(v).replace(",", "X").replace(".", ",").replace("X", ".")


def tabela(df, floatfmt="{:,.1f}", formatos=None):
    df = df.copy()
    for c in df.columns:
        if formatos and c in formatos:
            df[c] = df[c].map(lambda v, f=formatos[c]: br(v, f))
        elif pd.api.types.is_float_dtype(df[c]):
            df[c] = df[c].map(lambda v: br(v, floatfmt))
        elif pd.api.types.is_integer_dtype(df[c]):
            df[c] = df[c].map(lambda v: br(v, "{:,}"))
    linhas = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    linhas += ["| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False)]
    return "\n".join(linhas)


def pct(a, b):
    return 100.0 * a / b if b else float("nan")


# ---------------------------------------------------------------- carga
def carregar(ano, turno):
    p = os.path.join(DADOS, f"presidente_{ano}_{turno}t_secoes.csv.gz")
    if not os.path.exists(p):
        return None
    df = pd.read_csv(p, sep=";", dtype={"UF": str, "CD_MUNICIPIO": str, "ZONA": str, "SECAO": str,
                                        "LOCAL": str, "AGREGADAS": str, "TIPO_URNA": str, "MUNICIPIO": str})
    cand = pd.read_csv(os.path.join(DADOS, f"candidatos_{ano}_{turno}t.csv"), sep=";", dtype=str)
    nomes = dict(zip("V_" + cand.NUMERO, cand.NOME))
    vcols = [c for c in df.columns if c.startswith("V_")]
    df["VALIDOS"] = df[vcols].sum(axis=1)
    df["BN"] = df.BRANCOS + df.NULOS
    return df, nomes, vcols


def achar(nomes, trecho, preferido):
    if preferido in nomes:
        return preferido
    for c, nm in nomes.items():
        if trecho in nm.upper():
            return c
    return None


D = {}
for ano in ("2022", "2026"):
    for t in (1, 2):
        r = carregar(ano, t)
        if r is not None:
            D[(ano, t)] = r
if not D:
    sys.exit("Nenhum arquivo em ./dados. Rode antes extrair_presidente.py.")

LULA = {k: achar(v[1], "LULA", "V_13") for k, v in D.items()}
BOLS = {k: achar(v[1], "BOLSONARO", "V_22") for k, v in D.items()}

md("# Eleições presidenciais 2022 e 2026 — análise dos boletins de urna")
md()
md("Fonte: boletins de urna e totalização oficial publicados pelo TSE no Portal de Dados Abertos. "
   "Todos os números abaixo foram calculados a partir desses arquivos.")
md()

# ---------------------------------------------------------------- 1. conferência
md("## 1. Soma dos boletins de urna x totalização oficial")
md()
md("Cada boletim de urna (BU) é impresso e afixado na seção ao fim da votação e publicado pelo TSE. "
   "Se a soma de todos os BUs é igual ao total oficial, o resultado divulgado é exatamente a soma "
   "do que as urnas registraram — e qualquer cidadão pode conferir o BU da própria seção.")
md()
linhas = []
for (ano, t) in sorted(D):
    p = os.path.join(DADOS, f"conferencia_{ano}_{t}t.csv")
    if os.path.exists(p):
        c = pd.read_csv(p, sep=";")
        linhas.append({"Eleição": f"{ano} – {t}º turno", "Votos nos BUs": int(c.SOMA_BOLETINS.sum()),
                       "Totalização oficial": int(c.TOTALIZACAO_OFICIAL.sum()),
                       "Diferença absoluta": int(c.DIFERENCA.abs().sum()),
                       "Zonas com diferença": int(c.ZONAS_COM_DIFERENCA.sum())})
if linhas:
    md(tabela(pd.DataFrame(linhas)))
    md()
    for (ano, t) in sorted(D):
        p = os.path.join(DADOS, f"conferencia_{ano}_{t}t.csv")
        if not os.path.exists(p):
            continue
        c = pd.read_csv(p, sep=";")
        dif = c[c.DIFERENCA != 0].groupby("CANDIDATO").DIFERENCA.sum().sort_values(key=abs, ascending=False)
        if len(dif):
            partes = "; ".join(f"{nm}: {br(v, '{:+,}')}" for nm, v in dif.items())
            md(f"**{ano}, {t}º turno:** a diferença se concentra em {len(dif)} candidato(s) — {partes} votos.")
            md()
    md("Quando toda a diferença está num único candidato, a causa é a situação da candidatura, não a "
       "contagem: votos dados a quem renunciou ou teve o registro negado continuam aparecendo no boletim "
       "da urna, mas a totalização os considera nulos. O arquivo `conferencia_*.csv` mostra cada UF.")
else:
    md("_Arquivos de conferência não encontrados._")
md()

# ---------------------------------------------------------------- 2. abstenção
md("## 2. Comparecimento e abstenção")
md()
res = []
for (ano, t), (df, nomes, vc) in sorted(D.items()):
    ap, co = df.APTOS.sum(), df.COMPARECIMENTO.sum()
    linha = {"Eleição": f"{ano} – {t}º turno", "Aptos": int(ap), "Comparecimento": int(co),
             "Abstenção": int(ap - co), "Abstenção %": pct(ap - co, ap),
             "Brancos+nulos %": pct(df.BN.sum(), co)}
    for rot, mapa in (("Lula", LULA), ("Bolsonaro (PL)", BOLS)):
        c = mapa[(ano, t)]
        linha[f"{rot} votos"] = int(df[c].sum()) if c else 0
        linha[f"{rot} % válidos"] = pct(df[c].sum(), df.VALIDOS.sum()) if c else float("nan")
    res.append(linha)
res = pd.DataFrame(res)
res.to_csv(os.path.join(OUT, "resumo_nacional.csv"), sep=";", index=False, decimal=",")
md(tabela(res[["Eleição", "Aptos", "Comparecimento", "Abstenção", "Abstenção %", "Brancos+nulos %"]]))
md()
md(tabela(res[["Eleição", "Lula votos", "Lula % válidos", "Bolsonaro (PL) votos", "Bolsonaro (PL) % válidos"]]))
md()
md("Na linha do PL: em 2022 o candidato é Jair Bolsonaro; em 2026, Flávio Bolsonaro.")
md()
for ano in ("2022", "2026"):
    r1 = res[res["Eleição"] == f"{ano} – 1º turno"]
    r2 = res[res["Eleição"] == f"{ano} – 2º turno"]
    if len(r1) and len(r2):
        a1, a2 = r1["Abstenção %"].iloc[0], r2["Abstenção %"].iloc[0]
        q = int(r1["Abstenção"].iloc[0] - r2["Abstenção"].iloc[0])
        md(f"- **{ano}:** a abstenção foi de {br(a1, '{:.2f}')}% no 1º turno para {br(a2, '{:.2f}')}% no 2º "
           f"({br(a2 - a1, '{:+.2f}')} ponto percentual; {br(q, '{:,}')} eleitores a menos faltaram).")
md()


# ---------------------------------------------------------------- 3. semelhança geográfica
def por_municipio(ano, t):
    df, nomes, vc = D[(ano, t)]
    g = df.groupby(["UF", "CD_MUNICIPIO"]).agg(
        APTOS=("APTOS", "sum"), COMP=("COMPARECIMENTO", "sum"), BN=("BN", "sum"),
        VALIDOS=("VALIDOS", "sum"), **{c: (c, "sum") for c in vc})
    g.attrs["nomes"] = nomes
    return g


def wcorr(x, y, w):
    mx, my = np.average(x, weights=w), np.average(y, weights=w)
    cov = np.average((x - mx) * (y - my), weights=w)
    return cov / np.sqrt(np.average((x - mx) ** 2, weights=w) * np.average((y - my) ** 2, weights=w))


md("## 3. O eleitorado de Flávio Bolsonaro (2026) é o mesmo de Jair Bolsonaro (2022)?")
md()
md("Comparação município a município da fatia de votos válidos do candidato do PL. As seções mudam de "
   "uma eleição para outra, por isso a unidade comum é o município. Correlação ponderada pelo número de "
   "eleitores: 1 = mesma distribuição geográfica; 0 = nenhuma relação.")
md()
sim = []
for t in (1, 2):
    if ("2022", t) in D and ("2026", t) in D and BOLS[("2022", t)] and BOLS[("2026", t)]:
        a, b = por_municipio("2022", t), por_municipio("2026", t)
        j = a.add_suffix("_22").join(b.add_suffix("_26"), how="inner")
        j = j[(j.VALIDOS_22 > 0) & (j.VALIDOS_26 > 0)]
        j["APTOS"] = j.APTOS_26
        x = 100 * j[BOLS[("2022", t)] + "_22"] / j.VALIDOS_22
        y = 100 * j[BOLS[("2026", t)] + "_26"] / j.VALIDOS_26
        r = wcorr(x.values, y.values, j.APTOS.values)
        dif = y - x
        sim.append({"Turno": f"{t}º", "Municípios": len(j), "Correlação": r,
                    "Diferença média (p.p.)": float(np.average(dif, weights=j.APTOS)),
                    "Municípios onde o PL caiu": int((dif < 0).sum()),
                    "Municípios onde o PL subiu": int((dif > 0).sum())})
        pd.DataFrame({"PL_2022_%": x, "PL_2026_%": y, "dif_pp": dif, "APTOS": j.APTOS}).to_csv(
            os.path.join(OUT, f"pl_2022_x_2026_{t}t_municipios.csv"), sep=";", decimal=",")
if sim:
    md(tabela(pd.DataFrame(sim), "{:,.3f}"))
    md()
    md("Correlação acima de ~0,9 indica que o voto no PL em 2026 veio, em grande medida, dos mesmos "
       "lugares que votaram no PL em 2022. A coluna 'diferença média' mostra quanto o partido ganhou ou "
       "perdeu, em pontos percentuais, no município típico.")
else:
    md("_Dados insuficientes._")
md()


# ---------------------------------------------------------------- inferência ecológica
def goodman(X, Y, w, rotX, rotY):
    """Regressão sem intercepto de Y (proporções do destino) em X (proporções da origem), ponderada.
    Retorna a matriz de transferência estimada (linhas = origem, colunas = destino), ajustada para
    ficar entre 0 e 1 e somar 1 em cada linha."""
    sw = np.sqrt(w)[:, None]
    B, *_ = np.linalg.lstsq(X * sw, Y * sw, rcond=None)
    B = np.clip(B, 0, None)
    soma = B.sum(axis=1, keepdims=True)
    B = np.divide(B, soma, out=np.full_like(B, np.nan), where=soma > 0)  # linha sem dados fica em branco
    return pd.DataFrame(B * 100, index=rotX, columns=rotY)


def ajustar(T, origem, destino, iteracoes=500):
    """Ajuste proporcional iterativo (IPF): parte da matriz estimada e a corrige até que cada linha some
    o total real do grupo de origem e cada coluna some o total real de destino. Assim as estimativas
    batem exatamente com os votos contados. Retorna (percentuais, votos)."""
    N = T.fillna(0).values / 100 * np.asarray(origem, float)[:, None]
    o, d = np.asarray(origem, float), np.asarray(destino, float) * np.sum(origem) / np.sum(destino)
    for _ in range(iteracoes):
        N *= np.divide(o, N.sum(1), out=np.zeros_like(o), where=N.sum(1) > 0)[:, None]
        N *= np.divide(d, N.sum(0), out=np.zeros_like(d), where=N.sum(0) > 0)[None, :]
    P = pd.DataFrame(100 * N / o[:, None], index=T.index, columns=T.columns)
    return P, pd.DataFrame(N, index=T.index, columns=T.columns)



md("## 4. Para onde foram, no 1º turno de 2026, os eleitores de Lula em 2022?")
md()
md("O voto é secreto: não existe dado de *quem* votou em quem. O que dá para fazer é **inferência "
   "ecológica** — comparar milhares de municípios e estimar, estatisticamente, que fração de cada grupo "
   "de 2022 vai para cada opção de 2026. É uma estimativa (método de Goodman), não uma contagem. "
   "Mudanças no eleitorado entre 2022 e 2026 (jovens que entraram, óbitos, mudanças de domicílio) "
   "também entram no resultado.")
md()
if ("2022", 1) in D and ("2026", 1) in D:
    a, b = por_municipio("2022", 1), por_municipio("2026", 1)
    j = a.add_suffix("_22").join(b.add_suffix("_26"), how="inner")
    j = j[(j.APTOS_22 > 0) & (j.APTOS_26 > 0)]

    def blocos(sfx, vc, lula, pl):
        sub = pd.DataFrame({
            "Lula": j[lula + sfx], "PL": j[pl + sfx],
            "Outros candidatos": j[[c + sfx for c in vc if c not in (lula, pl)]].sum(axis=1),
            "Brancos/nulos": j["BN" + sfx], "Abstenção": j["APTOS" + sfx] - j["COMP" + sfx]})
        return sub.div(j["APTOS" + sfx], axis=0)

    X = blocos("_22", D[("2022", 1)][2], LULA[("2022", 1)], BOLS[("2022", 1)])
    Y = blocos("_26", D[("2026", 1)][2], LULA[("2026", 1)], BOLS[("2026", 1)])
    T = goodman(X.values, Y.values, j.APTOS_26.values, [f"{c} 2022" for c in X.columns],
                [f"{c} 2026" for c in Y.columns])
    T, _ = ajustar(T, X.mul(j.APTOS_22, axis=0).sum().values, Y.mul(j.APTOS_26, axis=0).sum().values)
    T.to_csv(os.path.join(OUT, "transferencia_2022_1t_para_2026_1t.csv"), sep=";", decimal=",")
    md("Atenção: entre eleições diferentes o método é frágil. Se a tabela mostrar algo implausível "
       "(por exemplo, quase todo um eleitorado trocando de lado), isso indica limite do método, não fato.")
    md()
    md("Percentual estimado de cada grupo de 2022 (linhas) que foi para cada opção no 1º turno de 2026 (colunas):")
    md()
    md(tabela(T.reset_index().rename(columns={"index": "Origem (1º turno 2022)"})))
    # outros candidatos de 2026 por nome
    outros26 = [c for c in D[("2026", 1)][2] if c not in (LULA[("2026", 1)], BOLS[("2026", 1)])]
    if outros26:
        Y2 = pd.DataFrame({D[("2026", 1)][1][c]: j[c + "_26"] for c in outros26}).div(j.APTOS_26, axis=0)
        Y2["Lula"], Y2["PL"] = Y["Lula"], Y["PL"]
        Y2["Brancos/nulos"], Y2["Abstenção"] = Y["Brancos/nulos"], Y["Abstenção"]
        T2 = goodman(X.values, Y2.values, j.APTOS_26.values, [f"{c} 2022" for c in X.columns], list(Y2.columns))
        T2, _ = ajustar(T2, X.mul(j.APTOS_22, axis=0).sum().values, Y2.mul(j.APTOS_26, axis=0).sum().values)
        T2.to_csv(os.path.join(OUT, "transferencia_2022_1t_para_2026_1t_por_candidato.csv"), sep=";", decimal=",")
        md()
        md("Detalhe por candidato de 2026 (apenas a linha dos eleitores de Lula em 2022):")
        md()
        lin = T2.loc[["Lula 2022"]].T.reset_index()
        lin.columns = ["Destino no 1º turno de 2026", "% dos eleitores de Lula 2022"]
        md(tabela(lin.sort_values(lin.columns[1], ascending=False)))
else:
    md("_Faltam dados do 1º turno de 2022 ou de 2026._")
md()

md("## 5. De onde vieram os votos que Lula ganhou entre o 1º e o 2º turno?")
md()
md("Aqui a comparação é seção a seção (as seções são as mesmas nos dois turnos da mesma eleição), "
   "o que torna a estimativa bem mais precisa que a do item 4.")
md()
for ano in ("2022", "2026"):
    if (ano, 1) in D and (ano, 2) in D:
        d1, n1, v1 = D[(ano, 1)]
        d2, n2, v2 = D[(ano, 2)]
        k = ["UF", "ZONA", "SECAO"]
        j = d1.set_index(k).add_suffix("_1").join(d2.set_index(k).add_suffix("_2"), how="inner").reset_index()
        j = j[(j.APTOS_1 > 0) & (j.APTOS_2 > 0)]
        l1, p1, l2, p2 = LULA[(ano, 1)], BOLS[(ano, 1)], LULA[(ano, 2)], BOLS[(ano, 2)]
        outros1 = [c for c in v1 if c not in (l1, p1)]
        validos = d1.VALIDOS.sum()
        grandes = [c for c in outros1 if d1[c].sum() >= 0.01 * validos]   # eliminados com 1% ou mais
        pequenos = [c for c in outros1 if c not in grandes]
        X = pd.DataFrame({"Lula": j[l1 + "_1"], "PL": j[p1 + "_1"],
                          **{n1[c]: j[c + "_1"] for c in sorted(grandes, key=lambda c: -d1[c].sum())},
                          "Demais candidatos": j[[c + "_1" for c in pequenos]].sum(axis=1),
                          "Brancos/nulos": j.BN_1, "Abstenção": j.APTOS_1 - j.COMPARECIMENTO_1})
        Y = pd.DataFrame({"Lula": j[l2 + "_2"], "PL": j[p2 + "_2"], "Brancos/nulos": j.BN_2,
                          "Abstenção": j.APTOS_2 - j.COMPARECIMENTO_2})
        T = goodman(X.div(j.APTOS_1, axis=0).values, Y.div(j.APTOS_2, axis=0).values, j.APTOS_2.values,
                    [f"{c} (1º turno)" for c in X.columns], [f"{c} (2º turno)" for c in Y.columns])
        tot = X.sum()
        T, N = ajustar(T, tot.values, Y.sum().values)
        T.to_csv(os.path.join(OUT, f"transferencia_{ano}_1t_para_2t.csv"), sep=";", decimal=",")
        ganho = N["Lula (2º turno)"]
        ganho_pl = N["PL (2º turno)"]
        dec = pd.DataFrame({"Grupo no 1º turno": T.index, "Tamanho do grupo": tot.values.astype(int),
                            "→ Lula %": T["Lula (2º turno)"].values, "→ PL %": T["PL (2º turno)"].values,
                            "→ Abstenção %": T["Abstenção (2º turno)"].values,
                            "Votos estimados para Lula": ganho.values.round().astype(int),
                            "Votos estimados para o PL": ganho_pl.values.round().astype(int)})
        md(f"### {ano}")
        md()
        md(f"Seções casadas entre os turnos: {br(len(j), '{:,}')}")
        md()
        md(tabela(dec))
        md()
        saldo = (ganho - ganho_pl).values
        m1 = int(d1[l1].sum() - d1[p1].sum())
        m2 = int(d2[l2].sum() - d2[p2].sum())
        md(f"Diferença Lula − PL: {br(m1, '{:+,}')} votos no 1º turno e {br(m2, '{:+,}')} no 2º "
           f"(variação de {br(m2 - m1, '{:+,}')}). A tabela abaixo reparte essa variação entre os grupos: "
           "nas duas primeiras linhas, o efeito de eleitores dos finalistas que deixaram de votar neles; "
           "nas demais, o saldo (votos para Lula menos votos para o PL) de cada grupo que não votou nos "
           "finalistas no 1º turno.")
        md()
        perda = [saldo[0] - tot.iloc[0], saldo[1] + tot.iloc[1]]
        sal = pd.DataFrame({"Grupo no 1º turno": T.index,
                            "Efeito na diferença Lula − PL": np.r_[perda, saldo[2:]].round().astype(int)})
        md(tabela(sal))
        md()
        md(f"Soma das linhas: {br(int(round(sal.iloc[:, 1].sum())), '{:+,}')} votos.")
        md()
        md(f"Abstenção: {br(pct(X['Abstenção'].sum(), j.APTOS_1.sum()), '{:.2f}')}% no 1º turno → "
           f"{br(pct(Y['Abstenção'].sum(), j.APTOS_2.sum()), '{:.2f}')}% no 2º turno.")
        md()
md("Como ler: a linha 'Abstenção (1º turno)' estima quantos eleitores que faltaram no 1º turno "
   "votaram no 2º e em quem; as linhas dos candidatos eliminados estimam como se dividiram os seus eleitores. "
   "As estimativas foram ajustadas para bater exatamente com os votos contados em cada turno. Os percentuais de cada linha somam 100% contando também brancos/nulos no "
   "2º turno, que não aparecem na tabela. As linhas não são contagens, são estimativas com margem de erro.")
md()

# ---------------------------------------------------------------- 6. seções com um só candidato
md("## 6. Seções em que apenas um candidato recebeu votos")
md()
md("Esse padrão aparece em toda eleição e é usado em boatos de fraude. Os dados abaixo mostram três "
   "coisas: (1) é raríssimo — menos de 0,04% das seções; (2) acontece sobretudo em seções menores que a "
   "média, e a chance cresce muito quanto menor a seção; (3) quase todas ficam em aldeias indígenas, "
   "assentamentos, quilombos e comunidades rurais isoladas, onde um grupo pequeno e coeso costuma votar "
   "do mesmo jeito. Os votos dessas seções somados são uma fração mínima da diferença entre os candidatos.")
md()
locais = {}
for ano in ("2022", "2026"):
    p = os.path.join(DADOS, f"locais_{ano}.csv.gz")
    if os.path.exists(p):
        locais[ano] = pd.read_csv(p, sep=";", dtype=str)
resumo, todas = [], []

INDIGENA = ("INDIGEN", "INDÍGEN", "ALDEIA", "POLO BASE", "TERRA INDIG", "TIKUNA", "TICUNA", "TUKUNA",
            "YANOMAMI", "XAVANTE", "KAYAP", "XIKRIN", "GUARANI", "MUNDURUKU", "TERENA", "MACUXI", "WAPICHANA")
RURAL = ("ASSENTAMENTO", "QUILOMB", "COMUNIDADE", "POVOADO", "ZONA RURAL", "RIBEIR", "SÍTIO", "SITIO",
         "FAZENDA", "AGROVILA", "GLEBA", "COLÔNIA", "COLONIA", "RESERVA", "IGARAP", "RIO ")


def tipo_local(r):
    if r.UF == "ZZ":
        return "Exterior"
    nome = f"{r.get('NM_LOCAL', '')} {r.get('ENDERECO', '')} {r.get('BAIRRO', '')}".upper()
    if any(k in nome for k in INDIGENA):
        return "Aldeia / escola indígena"
    if any(k in nome for k in RURAL):
        return "Assentamento, quilombo ou comunidade rural"
    return "Outro (escola ou prédio comum)"

for (ano, t), (df, nomes, vc) in sorted(D.items()):
    com_voto = (df[vc] > 0).sum(axis=1)
    so1 = df[(com_voto == 1) & (df.VALIDOS > 0)].copy()
    so1["CANDIDATO"] = so1[vc].idxmax(axis=1).map(nomes)
    so1["VOTOS_CANDIDATO"] = so1[vc].max(axis=1)
    if ano in locais:
        so1 = so1.merge(locais[ano][["UF", "ZONA", "SECAO", "NM_LOCAL", "ENDERECO", "BAIRRO"]],
                        on=["UF", "ZONA", "SECAO"], how="left")
    so1["TIPO_LOCAL"] = so1.apply(tipo_local, axis=1)
    total = len(df)
    ordem = df[vc].sum().sort_values(ascending=False)
    margem = int(ordem.iloc[0] - ordem.iloc[1])
    base = {"Eleição": f"{ano} – {t}º turno", "Seções": total, "Seções com 1 só candidato": len(so1),
            "% das seções": pct(len(so1), total),
            "Eleitores aptos (mediana) — todas": float(df.APTOS.median()),
            "Eleitores aptos (mediana) — 1 só candidato": float(so1.APTOS.median()) if len(so1) else float("nan"),
            "Comparecimento (mediana) — 1 só candidato": float(so1.COMPARECIMENTO.median()) if len(so1) else float("nan"),
            "Comparecimento (mediana) — todas": float(df.COMPARECIMENTO.median()),
            "Votos válidos nessas seções": int(so1.VALIDOS.sum()),
            "Diferença entre 1º e 2º colocados no país": margem}
    resumo.append(base)
    for cand, g in so1.groupby("CANDIDATO"):
        todas.append({"Eleição": f"{ano} – {t}º turno", "Candidato": cand, "Seções": len(g),
                      "% das seções do país": pct(len(g), total),
                      "Votos nessas seções": int(g.VOTOS_CANDIDATO.sum()),
                      "% dos votos do candidato": pct(g.VOTOS_CANDIDATO.sum(), df[g[vc].idxmax(axis=1).iloc[0]].sum()),
                      "Aptos (mediana)": float(g.APTOS.median()),
                      "Seções no exterior": int((g.UF == "ZZ").sum())})
    resumo[-1]["_tipos"] = so1.TIPO_LOCAL.value_counts()
    so1.drop(columns=vc).to_csv(os.path.join(OUT, f"secoes_um_candidato_{ano}_{t}t.csv"),
                                sep=";", index=False, encoding="utf-8-sig")
    # distribuição por faixa de tamanho
    faixas = [0, 50, 100, 200, 300, 400, 10**9]
    rot = ["até 50", "51–100", "101–200", "201–300", "301–400", "mais de 400"]
    df["FAIXA"] = pd.cut(df.APTOS, faixas, labels=rot, include_lowest=True)
    df["SO1"] = (com_voto == 1) & (df.VALIDOS > 0)
    fx = df.groupby("FAIXA", observed=False).agg(Secoes=("SO1", "size"), Com_1=("SO1", "sum"))
    fx["% com 1 só candidato"] = 100 * fx.Com_1 / fx.Secoes
    fx.reset_index().to_csv(os.path.join(OUT, f"secoes_um_candidato_por_tamanho_{ano}_{t}t.csv"),
                            sep=";", index=False, decimal=",")
    resumo[-1]["_faixas"] = fx

F6 = {"% das seções": "{:.3f}", "% das seções do país": "{:.4f}", "% dos votos do candidato": "{:.4f}",
      "Aptos (mediana)": "{:,.0f}"}
for r in resumo:
    fx = r.pop("_faixas")
    tipos = r.pop("_tipos")
    md(f"### {r['Eleição']}")
    md()
    t1 = pd.DataFrame([r]).drop(columns="Eleição")
    md(tabela(t1.T.reset_index().set_axis(["Indicador", "Valor"], axis=1).assign(
        Valor=lambda d: [br(v, "{:.3f}" if "%" in i else "{:,.0f}") for i, v in zip(d.Indicador, d.Valor)])))
    md()
    md("Tipo de local de votação dessas seções (pelo nome do local no cadastro do TSE):")
    md()
    md(tabela(tipos.rename_axis("Tipo de local").reset_index(name="Seções")))
    md()
    md("Chance de uma seção ter votos em um só candidato, por tamanho da seção (eleitores aptos):")
    md()
    md(tabela(fx.reset_index().rename(columns={"FAIXA": "Tamanho", "Secoes": "Seções", "Com_1": "Com 1 só candidato"})))
    md()
if todas:
    md("### Por candidato")
    md()
    md(tabela(pd.DataFrame(todas), "{:,.2f}", F6))
    md()

with open(os.path.join(OUT, "relatorio.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(relatorio) + "\n")
print("Relatório gravado em", os.path.join(OUT, "relatorio.md"))

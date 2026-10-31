#!/usr/bin/env python3
"""
Analisa os arquivos gerados por extrair_presidente.py (pasta ./dados) e escreve
./resultados/relatorio.md mais tabelas CSV de apoio.

Perguntas tratadas:
  1. A soma dos boletins de urna bate com a totalização oficial?
  2. Resultado, abstenção, brancos e nulos nos quatro turnos; onde a abstenção caiu.
  3. O voto em Flávio Bolsonaro (2026) se distribui como o voto em Jair Bolsonaro (2022)?
  4. Entre o 1º e o 2º turno (2022 e 2026): o que os boletins mostram sem modelo e para onde
     foi cada grupo de eleitores do 1º turno (inferência ecológica, ver transferencias.py).
  5. De 2022 para 2026 (por município, estimativa mais frágil).
  6. Seções em que só um candidato recebeu votos: quantas, de quem, de que tamanho, onde,
     e se as mesmas seções já votavam assim em 2022.

Requer pandas, numpy e scipy.
"""
import os
import sys

import numpy as np
import pandas as pd

import transferencias as tr

BASE = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(BASE, "dados")
OUT = os.path.join(BASE, "resultados")
os.makedirs(OUT, exist_ok=True)

REGIOES = {"Norte": ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
           "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
           "Centro-Oeste": ["DF", "GO", "MS", "MT"], "Sudeste": ["ES", "MG", "RJ", "SP"],
           "Sul": ["PR", "RS", "SC"], "Exterior": ["ZZ"]}
REGIAO = {uf: r for r, ufs in REGIOES.items() for uf in ufs}

relatorio = []


def md(texto=""):
    relatorio.append(texto)


def br(v, fmt="{:,.1f}"):
    """Número no formato brasileiro (1.234,5)."""
    if pd.isna(v):
        return ""
    return fmt.format(v).replace(",", "X").replace(".", ",").replace("X", ".")


def mi(v, sinal=True):
    return br(v / 1e6, "{:+,.2f}" if sinal else "{:,.2f}") + " mi"


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
    nomes = dict(zip("V_" + cand.NUMERO, cand.NOME.str.title()))
    vcols = [c for c in df.columns if c.startswith("V_")]
    df["VALIDOS"] = df[vcols].sum(axis=1)
    df["BN"] = df.BRANCOS + df.NULOS
    return df, nomes, vcols


D = {}
for ano in ("2022", "2026"):
    for t in (1, 2):
        r = carregar(ano, t)
        if r is not None:
            D[(ano, t)] = r
if len(D) < 4:
    sys.exit("Faltam arquivos em ./dados. Rode antes extrair_presidente.py.")

LULA, PL = "V_13", "V_22"
NOME_PL = {"2022": "Jair Bolsonaro", "2026": "Flávio Bolsonaro"}
CHAVE = ["UF", "ZONA", "SECAO"]


def casar(ano):
    d1, d2 = D[(ano, 1)][0], D[(ano, 2)][0]
    return d1.set_index(CHAVE).add_suffix("_1").join(d2.set_index(CHAVE).add_suffix("_2"), how="inner").reset_index()


locais = {a: pd.read_csv(os.path.join(DADOS, f"locais_{a}.csv.gz"), sep=";", dtype=str).fillna("")
          for a in ("2022", "2026") if os.path.exists(os.path.join(DADOS, f"locais_{a}.csv.gz"))}

INDIGENA = ("INDIGEN", "INDÍGEN", "ALDEIA", "POLO BASE", "TERRA INDIG", "TIKUNA", "TICUNA", "TUKUNA",
            "YANOMAMI", "XAVANTE", "KAYAP", "XIKRIN", "GUARANI", "MUNDURUKU", "TERENA", "MACUXI", "WAPICHANA")
RURAL = ("ASSENTAMENTO", "QUILOMB", "COMUNIDADE", "POVOADO", "ZONA RURAL", "RIBEIR", "SÍTIO", "SITIO",
         "FAZENDA", "AGROVILA", "GLEBA", "COLÔNIA", "COLONIA", "RESERVA", "IGARAP", "RIO ")
T_IND, T_RUR, T_EXT, T_COM = ("Aldeia ou escola indígena", "Assentamento, quilombo ou comunidade rural",
                              "Exterior", "Escola ou prédio comum")


def tipo_local(r):
    if r.UF == "ZZ":
        return T_EXT
    nome = f"{r.get('NM_LOCAL', '')} {r.get('ENDERECO', '')} {r.get('BAIRRO', '')}".upper()
    if any(k in nome for k in INDIGENA):
        return T_IND
    if any(k in nome for k in RURAL):
        return T_RUR
    return T_COM


def com_local(df, ano):
    if ano not in locais:
        return df.assign(NM_LOCAL="", ENDERECO="", BAIRRO="")
    return df.merge(locais[ano][["UF", "ZONA", "SECAO", "NM_LOCAL", "ENDERECO", "BAIRRO"]], on=CHAVE, how="left") \
             .fillna({"NM_LOCAL": "", "ENDERECO": "", "BAIRRO": ""})


md("# Eleições presidenciais 2022 e 2026 — análise dos boletins de urna")
md()
md("Fonte: boletins de urna de presidente, totalização oficial e cadastro de locais de votação publicados "
   "pelo TSE no Portal de Dados Abertos. Todos os números foram calculados a partir desses arquivos. "
   "Nas seções 4.2, 4.3 e 5 há estimativas estatísticas: o voto é secreto e nenhum dado público diz em "
   "quem cada pessoa votou.")
md()

# ---------------------------------------------------------------- 1. conferência
md("## 1. A soma dos boletins de urna confere com a totalização oficial")
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
            partes = "; ".join(f"{nm.title()}: {br(v, '{:+,}')}" for nm, v in dif.items())
            md(f"**{ano}, {t}º turno:** toda a diferença está em {len(dif)} candidato — {partes} votos. "
               "Votos dados a quem renunciou ou teve o registro negado continuam no boletim da urna, mas a "
               "totalização os conta como nulos. Não é erro de contagem.")
            md()
md()

# ---------------------------------------------------------------- 2. resultado e abstenção
md("## 2. Resultado, abstenção, brancos e nulos nos quatro turnos")
md()
res = []
for (ano, t), (df, nomes, vc) in sorted(D.items()):
    ap, co = df.APTOS.sum(), df.COMPARECIMENTO.sum()
    res.append({"Eleição": f"{ano} – {t}º turno", "Aptos": int(ap), "Comparecimento": int(co),
                "Abstenção": int(ap - co), "Abstenção %": pct(ap - co, ap),
                "Brancos": int(df.BRANCOS.sum()), "Nulos": int(df.NULOS.sum()),
                "Brancos+nulos %": pct(df.BN.sum(), co),
                "Lula votos": int(df[LULA].sum()), "Lula % válidos": pct(df[LULA].sum(), df.VALIDOS.sum()),
                "PL votos": int(df[PL].sum()), "PL % válidos": pct(df[PL].sum(), df.VALIDOS.sum())})
res = pd.DataFrame(res)
res.to_csv(os.path.join(OUT, "resumo_nacional.csv"), sep=";", index=False, decimal=",")
md(tabela(res[["Eleição", "Aptos", "Comparecimento", "Abstenção", "Abstenção %", "Brancos", "Nulos", "Brancos+nulos %"]],
          formatos={"Abstenção %": "{:.2f}", "Brancos+nulos %": "{:.2f}"}))
md()
md(tabela(res[["Eleição", "Lula votos", "Lula % válidos", "PL votos", "PL % válidos"]],
          formatos={"Lula % válidos": "{:.2f}", "PL % válidos": "{:.2f}"}))
md()
md("Na coluna do PL: em 2022 o candidato é Jair Bolsonaro; em 2026, Flávio Bolsonaro.")
md()
md("Todos os candidatos do 1º turno (votos contados nos boletins de urna):")
md()
cand_rows = []
for ano in ("2026", "2022"):
    df, nomes, vc = D[(ano, 1)]
    tot = df[vc].sum().sort_values(ascending=False)
    for c, v in tot.items():
        nome = {LULA: "Lula", PL: NOME_PL[ano]}.get(c, nomes[c])
        cand_rows.append({"Ano": ano, "Candidato": nome, "Número": c[2:], "Votos": int(v),
                          "% dos válidos": pct(v, df.VALIDOS.sum())})
md(tabela(pd.DataFrame(cand_rows), formatos={"% dos válidos": "{:.2f}"}))
md()
md("Em 2026, os 5.246 votos de Leonardo Avalanche aparecem nos boletins, mas a totalização oficial os conta "
   "como nulos (ele renunciou antes da eleição); por isso os percentuais oficiais diferem na segunda casa decimal.")
md()
VAR = {}
for ano in ("2022", "2026"):
    r1 = res[res["Eleição"] == f"{ano} – 1º turno"].iloc[0]
    r2 = res[res["Eleição"] == f"{ano} – 2º turno"].iloc[0]
    VAR[ano] = {"pp": r2["Abstenção %"] - r1["Abstenção %"], "votantes": int(r2.Comparecimento - r1.Comparecimento),
                "bn": int((r2.Brancos + r2.Nulos) - (r1.Brancos + r1.Nulos)),
                "lula": int(r2["Lula votos"] - r1["Lula votos"]), "pl": int(r2["PL votos"] - r1["PL votos"]),
                "m1": int(r1["Lula votos"] - r1["PL votos"]), "m2": int(r2["Lula votos"] - r2["PL votos"])}
    v = VAR[ano]
    md(f"- **{ano}:** a abstenção foi de {br(r1['Abstenção %'], '{:.2f}')}% para {br(r2['Abstenção %'], '{:.2f}')}% "
       f"({br(v['pp'], '{:+.2f}')} ponto percentual): {br(v['votantes'], '{:,}')} eleitores a mais votaram no 2º turno. "
       f"Brancos e nulos variaram {br(v['bn'], '{:+,}')}.")
md()

md("Contexto: segundo dados do TSE divulgados pela imprensa (não recalculados aqui), a abstenção subiu do "
   "1º para o 2º turno em 2014 (de 19,39% para 21,1%) e em 2018 (de 20,33% para 21,3%). Em 2022 caiu pouco; "
   "em 2026 caiu bem mais, para o menor nível em um 2º turno presidencial desde 2006.")
md()
md("### 2.1 Onde a abstenção caiu")
md()
reg_rows = []
for ano in ("2022", "2026"):
    for t in (1, 2):
        df = D[(ano, t)][0]
        g = df.assign(REG=df.UF.map(REGIAO)).groupby("REG")[["APTOS", "COMPARECIMENTO"]].sum()
        for reg, x in g.iterrows():
            reg_rows.append({"ano": ano, "t": t, "Região": reg, "aptos": x.APTOS, "comp": x.COMPARECIMENTO})
rg = pd.DataFrame(reg_rows)
tab = []
for reg in REGIOES:
    linha = {"Região": reg}
    for ano in ("2022", "2026"):
        a = rg[(rg.ano == ano) & (rg["Região"] == reg)].set_index("t")
        linha[f"{ano}: variação (p.p.)"] = pct(a.aptos[2] - a.comp[2], a.aptos[2]) - pct(a.aptos[1] - a.comp[1], a.aptos[1])
        linha[f"{ano}: votantes a mais"] = int(a.comp[2] - a.comp[1])
    tab.append(linha)
tab = pd.DataFrame(tab)
tab.to_csv(os.path.join(OUT, "abstencao_por_regiao.csv"), sep=";", index=False, decimal=",")
md("Variação da abstenção do 1º para o 2º turno, por região:")
md()
md(tabela(tab, formatos={"2022: variação (p.p.)": "{:+.2f}", "2026: variação (p.p.)": "{:+.2f}"}))
md()

quint = []
for ano in ("2022", "2026"):
    d1, n1, vc1 = D[(ano, 1)]
    d2 = D[(ano, 2)][0]
    m1 = d1.groupby(["UF", "CD_MUNICIPIO"]).agg(A=("APTOS", "sum"), C=("COMPARECIMENTO", "sum"),
                                                 L=(LULA, "sum"), V=("VALIDOS", "sum"))
    m2 = d2.groupby(["UF", "CD_MUNICIPIO"]).agg(A2=("APTOS", "sum"), C2=("COMPARECIMENTO", "sum"))
    m = m1.join(m2)
    m = m[(m.A > 0) & (m.V > 0)]
    m["q"] = pd.qcut(m.L / m.V, 5, labels=["1 (Lula mais fraco)", "2", "3", "4", "5 (Lula mais forte)"])
    for q, g in m.groupby("q", observed=True):
        quint.append({"Ano": ano, "Grupo de municípios": q, "Municípios": len(g),
                      "Lula no 1º turno %": pct(g.L.sum(), g.V.sum()),
                      "Variação da abstenção (p.p.)": pct(g.A2.sum() - g.C2.sum(), g.A2.sum()) - pct(g.A.sum() - g.C.sum(), g.A.sum()),
                      "Votantes a mais": int(g.C2.sum() - g.C.sum())})
quint = pd.DataFrame(quint)
quint.to_csv(os.path.join(OUT, "abstencao_por_forca_de_lula.csv"), sep=";", index=False, decimal=",")
md("Municípios divididos em cinco grupos iguais pela votação de Lula no 1º turno do mesmo ano:")
md()
md(tabela(quint, formatos={"Variação da abstenção (p.p.)": "{:+.2f}"}))
md()
md("O que os dados mostram: em 2022 a queda da abstenção diminuía à medida que Lula era mais forte, "
   "chegava a zero no 4º grupo e virava alta só no grupo mais lulista. Em 2026 ela caiu em todos os grupos "
   "de municípios, um pouco menos nos redutos de Lula, e em todas as regiões menos o Norte (onde subiu nos "
   "dois anos). Em números absolutos, o Sudeste sozinho teve 1,6 milhão de votantes a mais. Os grupos mais "
   "lulistas são quase todos do Nordeste, então não dá para separar força de Lula e região. São variações "
   "líquidas: não mostram quantas pessoas faltaram num turno e votaram no outro. Os boletins mostram onde e "
   "quanto a abstenção caiu; não mostram por quê.")
md()


# ---------------------------------------------------------------- 3. semelhança geográfica
def por_municipio(ano, t):
    df, nomes, vc = D[(ano, t)]
    return df.groupby(["UF", "CD_MUNICIPIO"]).agg(APTOS=("APTOS", "sum"), VALIDOS=("VALIDOS", "sum"),
                                                  **{c: (c, "sum") for c in vc})


def wcorr(x, y, w):
    mx, my = np.average(x, weights=w), np.average(y, weights=w)
    cov = np.average((x - mx) * (y - my), weights=w)
    return cov / np.sqrt(np.average((x - mx) ** 2, weights=w) * np.average((y - my) ** 2, weights=w))


md("## 3. Flávio Bolsonaro (2026) teve votos nos mesmos lugares que Jair Bolsonaro (2022)")
md()
md("Comparação município a município da fatia de votos válidos do candidato do PL (as seções mudam de "
   "uma eleição para outra; o município é a unidade comum). Correlação ponderada pelo número de eleitores: "
   "1 = mesma distribuição geográfica; 0 = nenhuma relação.")
md()
sim = []
for t in (1, 2):
    a, b = por_municipio("2022", t), por_municipio("2026", t)
    j = a.add_suffix("_22").join(b.add_suffix("_26"), how="inner")
    j = j[(j.VALIDOS_22 > 0) & (j.VALIDOS_26 > 0)]
    x = 100 * j[PL + "_22"] / j.VALIDOS_22
    y = 100 * j[PL + "_26"] / j.VALIDOS_26
    dif = y - x
    sim.append({"Turno": f"{t}º", "Municípios": len(j), "Correlação": wcorr(x.values, y.values, j.APTOS_26.values),
                "Variação média do PL (p.p.)": float(np.average(dif, weights=j.APTOS_26)),
                "Municípios onde o PL subiu": int((dif > 0).sum()), "Municípios onde o PL caiu": int((dif < 0).sum())})
    pd.DataFrame({"PL_2022_%": x, "PL_2026_%": y, "dif_pp": dif, "APTOS": j.APTOS_26}).to_csv(
        os.path.join(OUT, f"pl_2022_x_2026_{t}t_municipios.csv"), sep=";", decimal=",")
md(tabela(pd.DataFrame(sim), formatos={"Correlação": "{:.3f}", "Variação média do PL (p.p.)": "{:+.2f}"}))
md()

# ---------------------------------------------------------------- 4. entre turnos
print("estimando transferências entre turnos...", flush=True)
TR = {ano: tr.entre_turnos(ano) for ano in ("2022", "2026")}


def resumo_transf(t):
    """Uma linha por grupo de origem: valor central e faixa (entre as seis variantes) para cada destino."""
    linhas = []
    for o, g in t.groupby("origem", sort=False):
        g = g.set_index("destino")
        linha = {"Grupo no 1º turno": o, "Eleitores": int(g.eleitores_origem.iloc[0])}
        for dst in g.index:
            linha[dst] = (g.loc[dst, "pct"], g.loc[dst, "pct_min"], g.loc[dst, "pct_max"])
        linhas.append(linha)
    return linhas


def celula(v):
    c, lo, hi = v
    if hi - lo < 0.02:
        return f"{br(100 * c, '{:.0f}')}%"
    return f"{br(100 * c, '{:.0f}')}% ({br(100 * lo, '{:.0f}')}–{br(100 * hi, '{:.0f}')})"


def efeitos(t, ano):
    """Efeito de cada grupo na diferença Lula − PL (votos para Lula menos votos para o PL vindos do
    grupo; nos finalistas, descontando os próprios votos do 1º turno). A soma é a variação real."""
    pl = NOME_PL[ano]
    variantes = [c for c in t.columns if c.startswith("pct[")]
    out = []
    for o, g in t.groupby("origem", sort=False):
        n = g.eleitores_origem.iloc[0]
        g = g.set_index("destino")

        def ef(col):
            e = (g.loc["Lula", col] - g.loc[pl, col]) * n
            return e - n if o == "Lula" else e + n if o == pl else e
        vals = {c: ef(c) for c in variantes}
        out.append({"Grupo no 1º turno": o, "central": ef("pct"), "min": min(vals.values()), "max": max(vals.values()), **vals})
    return pd.DataFrame(out)


def soma_faixa(e, grupos_):
    """Soma do efeito de vários grupos: central e faixa calculada variante por variante."""
    x = e[e["Grupo no 1º turno"].isin(grupos_)]
    var = [c for c in e.columns if c.startswith("pct[")]
    tot = [x[c].sum() for c in var]
    return x.central.sum(), min(tot), max(tot)


md("## 4. Do 1º para o 2º turno: para onde foi cada eleitor")
md()
md(f"Em 2026, Lula ganhou {br(VAR['2026']['lula'], '{:+,}')} votos do 1º para o 2º turno e Flávio "
   f"{br(VAR['2026']['pl'], '{:+,}')}. A diferença entre os dois foi de {br(VAR['2026']['m1'], '{:+,}')} "
   f"(Flávio à frente) para {br(VAR['2026']['m2'], '{:+,}')} (Lula à frente): uma virada de "
   f"{br(VAR['2026']['m2'] - VAR['2026']['m1'], '{:,}')} votos na diferença. Esse número não é o total de "
   "votos que Lula ganhou; é quanto a diferença entre os dois mudou.")
md()
md(f"Em 2022, para comparação, a diferença caiu de {br(VAR['2022']['m1'], '{:+,}')} para "
   f"{br(VAR['2022']['m2'], '{:+,}')}: Lula ganhou {br(VAR['2022']['lula'], '{:+,}')} votos e Bolsonaro "
   f"{br(VAR['2022']['pl'], '{:+,}')}.")
md()

md("### 4.1 O que os boletins mostram sem nenhum modelo")
md()
md("Primeiro, de onde vieram os votos novos dos finalistas, em conta exata: os eleitores dos candidatos "
   "eliminados, os votantes a mais e os brancos e nulos a menos somam o que Lula e o PL ganharam juntos. "
   "É uma identidade contábil (fecha sempre): ela mostra o tamanho de cada fonte, mas não diz quem foi para "
   "quem. Os boletins não exigem troca de lado entre eleitores de Flávio e de Lula para explicar a virada, "
   "nem a excluem.")
md()
md(tabela(pd.DataFrame([{"Ano": ano, "Votos dos eliminados no 1º turno": int(D[(ano, 1)][0][[c for c in D[(ano, 1)][2] if c not in (LULA, PL)]].sum().sum()),
                         "Votantes a mais no 2º turno": VAR[ano]["votantes"], "Brancos e nulos a menos": -VAR[ano]["bn"],
                         "Ganho de Lula": VAR[ano]["lula"], "Ganho do PL": VAR[ano]["pl"]} for ano in ("2022", "2026")])))
md()
md("As seções são as mesmas nos dois turnos de uma eleição. Se numa seção um candidato teve menos votos no "
   "2º turno do que no 1º, então pelo menos essa quantidade de eleitores que votaram nele no 1º turno não "
   "votou nele no 2º. Somando as seções, isso dá um mínimo garantido, que qualquer pessoa pode conferir nos "
   "boletins. O que os boletins não dizem é para onde esses eleitores foram: Lula, branco, nulo ou abstenção.")
md()
lim_rows = []
for ano in ("2022", "2026"):
    lim = pd.read_csv(os.path.join(OUT, f"limites_secoes_{ano}.csv"), sep=";", decimal=",")
    for r in lim.itertuples():
        lim_rows.append({"Eleição": ano, "Candidato": r.candidato,
                         "Seções em que perdeu votos": int(r.secoes_com_queda),
                         "% das seções": 100 * r.pct_secoes_com_queda,
                         "Votos perdidos nessas seções": int(r.soma_das_quedas),
                         "Seções com queda e comparecimento igual ou maior": int(r.secoes_queda_com_comparecimento_igual_ou_maior),
                         "Votos perdidos nelas": int(r.votos_perdidos_com_comparecimento_igual_ou_maior)})
lim_tab = pd.DataFrame(lim_rows)
j26 = casar("2026")
dPL, dL, dC = j26[PL + "_2"] - j26[PL + "_1"], j26[LULA + "_2"] - j26[LULA + "_1"], j26.COMPARECIMENTO_2 - j26.COMPARECIMENTO_1
estavel = (dPL < 0) & (dC >= 0)


def estrito(de, para):
    """Mínimo garantido de eleitores que foram de 'de' direto para 'para' (limites de Duncan-Davis)."""
    lim = j26[de + "_1"] - j26[de + "_2"] - (j26.BRANCOS_2 + j26.NULOS_2) - (j26.APTOS_2 - j26.COMPARECIMENTO_2)
    return int(lim.clip(lower=0).sum())


votos_estaveis = int(-dPL[estavel].sum())
md(tabela(lim_tab, formatos={"% das seções": "{:.1f}"}))
md()
md(f"Em 2026, Flávio teve menos votos no 2º turno em {br(int((dPL < 0).sum()), '{:,}')} seções "
   f"({br(pct(int((dPL < 0).sum()), len(j26)), '{:.1f}')}% das seções) "
   f"({br(int(-dPL[dPL < 0].sum()), '{:,}')} votos): pelo menos esse número de eleitores dele no 1º turno não "
   f"votou nele no 2º. Em {br(int(estavel.sum()), '{:,}')} dessas seções o comparecimento foi igual ou maior "
   f"({br(votos_estaveis, '{:,}')} votos perdidos, {br(pct(votos_estaveis, VAR['2026']['m2'] - VAR['2026']['m1']), '{:.1f}')}% "
   "da virada), mas isso não prova troca de voto: um eleitor de Flávio "
   "pode ter faltado e outro, que tinha faltado no 1º turno, ter ido votar em Lula. Pelos boletins, o mínimo "
   f"matematicamente comprovável de troca direta é de {br(estrito(PL, LULA), '{:,}')} votos de Flávio para Lula "
   f"e {br(estrito(LULA, PL), '{:,}')} de Lula para Flávio, no país inteiro: os boletins não conseguem medir "
   "troca de voto em nenhuma direção. Ela só poderia ser medida com pesquisa (painel ou boca de urna).")
md()
md("Isso não é novidade de 2026. Em 2022 aconteceu o espelho, e maior: quem perdeu votos em muitas seções "
   "foi Lula, o finalista que menos cresceu no 2º turno. É o comportamento comum de quem ganha menos votos "
   "novos entre os turnos.")
md()
md("Outros mínimos garantidos pelos boletins (somando, seção a seção, quanto cada grupo encolheu ou cresceu):")
md()
pis = []
for ano in ("2026", "2022"):
    p = pd.read_csv(os.path.join(OUT, f"pisos_{ano}.csv"), sep=";", decimal=",")
    for r in p.itertuples():
        pis.append({"Ano": ano, "Grupo": r.grupo, "1º turno": int(r.no_1o_turno), "2º turno": int(r.no_2o_turno),
                    "Saíram do grupo, no mínimo": int(r.saiu_no_minimo), "Entraram no grupo, no mínimo": int(r.entrou_no_minimo)})
md(tabela(pd.DataFrame(pis)))
md()
p26 = pd.read_csv(os.path.join(OUT, "pisos_2026.csv"), sep=";", decimal=",").set_index("grupo")
md(f"Por exemplo: em 2026, pelo menos {br(int(p26.loc['Abstenção', 'saiu_no_minimo']), '{:,}')} pessoas que se "
   f"abstiveram no 1º turno votaram no 2º ({br(pct(p26.loc['Abstenção', 'saiu_no_minimo'], p26.loc['Abstenção', 'no_1o_turno']), '{:.1f}')}% "
   "dos abstencionistas). Para onde foram os votos delas, os boletins não dizem.")
md()
md("Atenção: nas seções do Acre e do Amazonas com as maiores quedas de Flávio, o comparecimento despencou "
   "no 2º turno (abstenção maior no Norte), então lá a queda é sobretudo de eleitores que faltaram.")
md()
ex = com_local(j26[estavel & (dL > 0)].assign(QUEDA=-dPL[estavel & (dL > 0)]), "2026") \
    .sort_values("QUEDA", ascending=False).head(10)
ex_tab = pd.DataFrame({"UF": ex.UF, "Município": ex.MUNICIPIO_1.str.title(), "Zona": ex.ZONA, "Seção": ex.SECAO,
                       "Local": ex.NM_LOCAL.str.title(),
                       "Comparecimento 1º → 2º": [f"{a} → {b}" for a, b in zip(ex.COMPARECIMENTO_1, ex.COMPARECIMENTO_2)],
                       "Flávio 1º → 2º": [f"{a} → {b}" for a, b in zip(ex[PL + "_1"], ex[PL + "_2"])],
                       "Lula 1º → 2º": [f"{a} → {b}" for a, b in zip(ex[LULA + "_1"], ex[LULA + "_2"])]})
ex_tab.to_csv(os.path.join(OUT, "exemplos_queda_flavio_2026.csv"), sep=";", index=False, encoding="utf-8-sig")
md("**Como conferir com os próprios olhos.** Escolha uma seção da lista abaixo (comparecimento estável, "
   "Flávio caiu, Lula subiu) e abra o boletim de urna do 1º e do 2º turno dela no Portal de Resultados do "
   "TSE (resultados.tse.jus.br, opção de boletim de urna por UF, município, zona e seção) ou nos arquivos de "
   "boletim de urna do Portal de Dados Abertos do TSE — os mesmos usados aqui. O boletim também é afixado "
   "na porta da seção e pode ser conferido com o QR Code impresso nele. O que dá para verificar é a contagem "
   "de cada seção. Esses exemplos são forte indício de que parte dos eleitores de Flávio mudou de voto, mas "
   "não prova: o voto é secreto.")
md()
md(tabela(ex_tab))
md()

md("### 4.2 Para onde foi cada grupo do 1º turno (estimativa)")
md()
md("Método: inferência ecológica com todas as seções (regressão de Goodman, ajustada para bater exatamente "
   "com os votos contados). O resultado depende das escolhas do modelo, por isso rodamos seis variantes: "
   "com o país inteiro, por região e estado por estado; e com duas formas de restrição (cada fração entre "
   "0% e 100%, ou cada linha somando 100%). Conferimos cada variante contra os mínimos garantidos pelos "
   "boletins (tabela acima). O valor mostrado é o da variante estado por estado com linhas somando 100%, "
   "que respeita esses mínimos; entre parênteses, o menor e o maior valor entre as variantes que também os respeitam. Faixa larga = "
   "resultado incerto. Cada linha soma 100%. Os destinos são: Lula, PL, voto em branco, voto nulo e não "
   "foi votar.")
md()
for ano in ("2026", "2022"):
    linhas = resumo_transf(TR[ano])
    destinos = [k for k in linhas[0] if k not in ("Grupo no 1º turno", "Eleitores")]
    tab = pd.DataFrame([{"Grupo no 1º turno": l["Grupo no 1º turno"], "Eleitores": l["Eleitores"],
                         **{f"→ {d}": celula(l[d]) for d in destinos}} for l in linhas])
    md(f"**{ano}**")
    md()
    md(tabela(tab))
    md()

md("### 4.3 Quanto cada grupo pesou na mudança da diferença")
md()
md("Efeito na diferença Lula − PL (não é número de pessoas): votos para Lula menos votos para o PL vindos de "
   "cada grupo do 1º turno. Nos próprios finalistas, é o efeito de eleitores que não repetiram o voto. A coluna "
   "'Central' soma exatamente a variação real da diferença; a faixa mostra o quanto cada item muda entre as "
   "variantes que respeitam os mínimos dos boletins. A divisão entre abstenção, brancos e nulos é a parte menos precisa: os três andam juntos "
   "entre as seções. A soma dos três é robusta.")
md()
for ano in ("2026", "2022"):
    e = efeitos(TR[ano], ano)
    e["Faixa"] = [f"{mi(a)} a {mi(b)}" for a, b in zip(e["min"], e["max"])]
    e["Central"] = [mi(c) for c in e.central]
    e[["Grupo no 1º turno", "central", "min", "max"]].to_csv(os.path.join(OUT, f"efeito_na_diferenca_{ano}.csv"), sep=";", index=False, decimal=",")
    if ano == "2022":
        md("Em 2022, só duas das seis variantes respeitam os mínimos dos boletins, então as faixas desse ano são "
           "mais estreitas do que a incerteza real.")
        md()
    md(f"**{ano}** (variação real da diferença: {br(VAR[ano]['m2'] - VAR[ano]['m1'], '{:+,}')} votos)")
    md()
    md(tabela(e[["Grupo no 1º turno", "Central", "Faixa"]]))
    md()
    c3, lo3, hi3 = soma_faixa(e, ["Brancos", "Nulos", "Abstenção"])
    md(f"Soma de abstenção, brancos e nulos: {mi(c3)} (faixa {mi(lo3)} a {mi(hi3)}).")
    md()

md("### 4.4 O que mudou em relação à tabela anterior")
md()
md("Uma versão anterior desta análise mostrava só os quatro maiores saldos a favor de Lula em 2026, vindos de "
   "um modelo mais agregado (todos os eliminados juntos, brancos e nulos juntos). Esses quatro somavam 7,67 mi, "
   "mais do que a virada real, porque os grupos que favoreceram Flávio ficaram de fora. Todos os votos de "
   "todos os candidatos foram contados pelo TSE; a omissão foi só daquela tabela-resumo. A versão atual separa "
   "cada candidato e brancos de nulos, e respeita os mínimos garantidos pelos boletins:")
md()
e26 = efeitos(TR["2026"], "2026")
nomeados = ["Lula", "Flávio Bolsonaro", "Escritor Augusto Cury", "Renan Santos", "Ronaldo Caiado", "Zema",
            "Brancos", "Nulos", "Abstenção"]
demais = [g for g in e26["Grupo no 1º turno"] if g not in nomeados]
conc = [("Brancos e nulos", "+2,99 mi", ["Brancos", "Nulos"]), ("Abstenção", "+1,94 mi", ["Abstenção"]),
        ("Eleitores de Flávio que não repetiram o voto", "+1,59 mi (bruto)", ["Flávio Bolsonaro"]),
        ("Eleitores de Lula que não repetiram o voto", "não mostrado", ["Lula"]),
        ("Augusto Cury", "+1,15 mi", ["Escritor Augusto Cury"]), ("Renan Santos", "não mostrado", ["Renan Santos"]),
        ("Ronaldo Caiado", "não mostrado", ["Ronaldo Caiado"]), ("Zema", "não mostrado", ["Zema"]),
        ("Demais candidatos", "não mostrado", demais)]
linhas_c = []
for g, ant, gs in conc:
    c, lo, hi = soma_faixa(e26, gs)
    linhas_c.append({"Grupo": g, "Tabela anterior": ant, "Agora (central)": mi(c), "Faixa entre métodos": f"{mi(lo)} a {mi(hi)}"})
linhas_c.append({"Grupo": "Total", "Tabela anterior": "+7,67 mi", "Agora (central)": mi(e26.central.sum()), "Faixa entre métodos": ""})
pd.DataFrame(linhas_c).to_csv(os.path.join(OUT, "conciliacao_tabela_anterior.csv"), sep=";", index=False)
md(tabela(pd.DataFrame(linhas_c)))
md()
cf, lof, hif = soma_faixa(e26, ["Lula", "Flávio Bolsonaro"])
md(f"O '+1,59 mi' anterior era bruto (não descontava os eleitores de Lula que também não repetiram o voto) e "
   f"vinha do modelo agregado. Hoje, o efeito líquido das perdas dos dois finalistas é de {mi(cf)} "
   f"(faixa {mi(lof)} a {mi(hif)}).")
md()

# ---------------------------------------------------------------- 5. entre eleições
print("estimando transferências entre eleições...", flush=True)
E1, E2 = tr.entre_eleicoes(1), tr.entre_eleicoes(2)
md("## 5. De 2022 para 2026 (estimativa frágil)")
md()
md("Entre eleições diferentes as seções mudam, então a comparação é por município (cerca de 5.700) e o "
   "eleitorado também mudou (jovens que entraram, óbitos, mudanças de cidade). Os resultados variam muito "
   "conforme o método; só as linhas com faixa estreita merecem ser citadas.")
md()
for t, E in ((1, E1), (2, E2)):
    linhas = resumo_transf(E)
    destinos = [k for k in linhas[0] if k not in ("Grupo no 1º turno", "Eleitores")]
    tab = pd.DataFrame([{f"Grupo no {t}º turno de 2022": l["Grupo no 1º turno"], "Eleitores": l["Eleitores"],
                         **{f"→ {d}": celula(l[d]) for d in destinos}} for l in linhas[:2]])
    md(f"**{t}º turno de 2022 → {t}º turno de 2026** (só os finalistas, que têm faixas estreitas)")
    md()
    md(tabela(tab))
    md()

# ---------------------------------------------------------------- 6. seções com um só candidato
md("## 6. Seções em que apenas um candidato recebeu votos")
md()
resumo, por_cand, tipos_tab, faixas_tab = [], [], [], []
SO1 = {}
for (ano, t), (df, nomes, vc) in sorted(D.items()):
    nomes = {**nomes, PL: NOME_PL[ano], LULA: "Lula"}
    com_voto = (df[vc] > 0).sum(axis=1)
    m1 = (com_voto == 1) & (df.VALIDOS > 0)
    so1 = com_local(df[m1].copy(), ano)
    so1["CANDIDATO"] = so1[vc].idxmax(axis=1).map(nomes)
    so1["VOTOS_CANDIDATO"] = so1[vc].max(axis=1)
    so1["TIPO_LOCAL"] = so1.apply(tipo_local, axis=1)
    SO1[(ano, t)] = so1
    ordem = df[vc].sum().sort_values(ascending=False)
    rural = so1.TIPO_LOCAL.isin([T_IND, T_RUR]).mean() if len(so1) else np.nan
    resumo.append({"Eleição": f"{ano} – {t}º turno", "Seções com 1 só candidato": len(so1),
                   "% das seções": pct(len(so1), len(df)),
                   "Aptos, mediana (essas seções)": float(so1.APTOS.median()),
                   "Aptos, mediana (todas)": float(df.APTOS.median()),
                   "% em aldeias, assentamentos, quilombos ou comunidades rurais": 100 * rural,
                   "Votos nessas seções": int(so1.VALIDOS.sum()),
                   "Diferença entre os dois primeiros": int(ordem.iloc[0] - ordem.iloc[1])})
    for cand in ("Lula", NOME_PL[ano]):
        g = so1[so1.CANDIDATO == cand]
        col = LULA if cand == "Lula" else PL
        por_cand.append({"Eleição": f"{ano} – {t}º turno", "Candidato": cand, "Seções": len(g),
                         "% das seções do país": pct(len(g), len(df)), "Votos nessas seções": int(g.VOTOS_CANDIDATO.sum()),
                         "% dos votos do candidato": pct(g.VOTOS_CANDIDATO.sum(), df[col].sum()),
                         "Aptos, mediana": float(g.APTOS.median()) if len(g) else np.nan,
                         "Compareceram, mediana": float(g.COMPARECIMENTO.median()) if len(g) else np.nan,
                         "Em aldeias ou comunidades rurais": int(g.TIPO_LOCAL.isin([T_IND, T_RUR]).sum())})
    for k, v in so1.TIPO_LOCAL.value_counts().items():
        tipos_tab.append({"Eleição": f"{ano} – {t}º turno", "Tipo de local": k, "Seções": int(v)})
    faixas = [0, 50, 100, 200, 300, 400, 10**9]
    rot = ["até 50", "51 a 100", "101 a 200", "201 a 300", "301 a 400", "mais de 400"]
    fx = pd.DataFrame({"F": pd.cut(df.APTOS, faixas, labels=rot, include_lowest=True), "S": m1})
    for f, g in fx.groupby("F", observed=False):
        faixas_tab.append({"Eleição": f"{ano} – {t}º turno", "Eleitores aptos": f, "Seções": len(g),
                           "Com 1 só candidato": int(g.S.sum()), "%": pct(g.S.sum(), len(g))})
    so1.drop(columns=vc).to_csv(os.path.join(OUT, f"secoes_um_candidato_{ano}_{t}t.csv"),
                                sep=";", index=False, encoding="utf-8-sig")
pd.DataFrame(faixas_tab).to_csv(os.path.join(OUT, "secoes_um_candidato_por_tamanho.csv"), sep=";", index=False, decimal=",")
pd.DataFrame(por_cand).to_csv(os.path.join(OUT, "secoes_um_candidato_por_candidato.csv"), sep=";", index=False, decimal=",")

r26 = resumo[3]
s26 = SO1[("2026", 2)]
grandes = s26[s26.APTOS >= 300]
md("**Em resumo:** é raríssimo — de 0,008% a 0,031% das seções, conforme o turno. Acontece para os dois lados "
   "e nas duas eleições, muito mais para Lula. Entre "
   f"{br(min(r['% em aldeias, assentamentos, quilombos ou comunidades rurais'] for r in resumo), '{:.0f}')}% e "
   f"{br(max(r['% em aldeias, assentamentos, quilombos ou comunidades rurais'] for r in resumo), '{:.0f}')}% "
   "dessas seções ficam em aldeias indígenas, assentamentos, quilombos e comunidades rurais, onde um grupo "
   "pequeno e coeso tende a votar do mesmo jeito. São seções menores que a média. "
   f"No 2º turno de 2026, só {len(grandes)} delas tinham 300 eleitores ou mais: "
   f"{int((grandes.TIPO_LOCAL == T_IND).sum())} em aldeias ou escolas indígenas, "
   f"{int((grandes.UF == 'AM').sum())} no Amazonas.")
md()
lu = s26[s26.CANDIDATO == "Lula"].VOTOS_CANDIDATO.sum()
fl = s26[s26.CANDIDATO == NOME_PL["2026"]].VOTOS_CANDIDATO.sum()
md(f"No 2º turno de 2026, essas seções deram a Lula um saldo de {br(int(lu - fl), '{:,}')} votos, "
   f"{br(pct(lu - fl, VAR['2026']['m2']), '{:.2f}')}% da vantagem final de {br(VAR['2026']['m2'], '{:,}')}. "
   f"O fenômeno é estável: o 2º turno de 2022 teve mais seções assim ({len(SO1[('2022', 2)])}) do que o de "
   f"2026 ({len(s26)}).")
md()
md("A classificação do local é automática, pelo nome e endereço no cadastro do TSE, e conservadora. As "
   "seções que ficam de fora são principalmente presídios e unidades de internação (onde votam presos "
   "provisórios e adolescentes internados), embaixadas e consulados no exterior e algumas aldeias ou "
   "comunidades que a regra não reconheceu (por exemplo a escola Ingarikó em Uiramutã-RR e a aldeia "
   "guarani Karai Nhe'e Katu em Viamão-RS). Lendo os nomes um a um, a parcela em aldeias e comunidades "
   "rurais fica perto de 88% a 98%.")
md()
md(tabela(pd.DataFrame(resumo), formatos={"% das seções": "{:.3f}", "Aptos, mediana (essas seções)": "{:,.0f}",
                                          "Aptos, mediana (todas)": "{:,.0f}",
                                          "% em aldeias, assentamentos, quilombos ou comunidades rurais": "{:.0f}"}))
md()
md("### 6.1 Para cada candidato")
md()
md("As seções com 100% para o PL também ficam em comunidades rurais pequenas: em 2026, no interior do Pará "
   "e em colônias rurais do Rio Grande do Sul (Arroio do Padre e Cândido Godói, de colonização alemã). Em 2022, "
   "duas delas eram de Caracas votando em Bogotá, com pouquíssimos eleitores presentes.")
md()
md(tabela(pd.DataFrame(por_cand), formatos={"% das seções do país": "{:.4f}", "% dos votos do candidato": "{:.4f}",
                                            "Aptos, mediana": "{:,.0f}", "Compareceram, mediana": "{:,.0f}"}))
md()
ext = SO1[("2022", 2)]
ext = ext[(ext.UF == "ZZ") & (ext.CANDIDATO == NOME_PL["2022"])]
if len(ext):
    md(f"Em 2022, {len(ext)} das seções com 100% para Bolsonaro ficavam no exterior ("
       + ", ".join(f"{m.title()}: {c} eleitor(es) presente(s) de {a} aptos" for m, c, a in
                   zip(ext.MUNICIPIO, ext.COMPARECIMENTO, ext.APTOS))
       + "), por isso a mediana de aptos dele naquele turno é alta; a de quem compareceu é baixa.")
    md()
md("### 6.2 É um comportamento comum dessas seções?")
md()
# persistência: mesma seção e mesmo local em 2022
p22 = com_local(D[("2022", 2)][0], "2022")[CHAVE + [LULA, PL, "VALIDOS", "NM_LOCAL"]] \
    .rename(columns={LULA: "L22", PL: "P22", "VALIDOS": "V22", "NM_LOCAL": "LOC22"})
m = s26.merge(p22, on=CHAVE, how="inner")
m = m[m.NM_LOCAL.str.upper().str.strip() == m.LOC22.str.upper().str.strip()]
pers = []
for cand, col in (("Lula", "L22"), ("Flávio Bolsonaro", "P22")):
    g = m[m.CANDIDATO == cand]
    sh = g[col] / g.V22
    pers.append({"Candidato com 100% em 2026": cand, "Seções comparáveis com 2022": len(g),
                 "Deram 90%+ ao mesmo lado em 2022": int((sh >= 0.9).sum()),
                 "Deram 95%+": int((sh >= 0.95).sum()), "Deram 100%": int((sh >= 0.99999).sum()),
                 "Mediana em 2022 (%)": 100 * float(sh.median()) if len(g) else np.nan})
pers = pd.DataFrame(pers)
pers.to_csv(os.path.join(OUT, "secoes_um_candidato_persistencia.csv"), sep=";", index=False, decimal=",")
o1 = SO1[("2026", 1)].merge(s26[CHAVE], on=CHAVE)
md("Sim. Comparando a mesma seção (mesmo número e mesmo local de votação) no 2º turno de 2022:")
md()
md(tabela(pers, formatos={"Mediana em 2022 (%)": "{:.1f}"}))
md()
md(f"E {len(o1)} das {len(SO1[('2026', 1)])} seções com um só candidato no 1º turno de 2026 repetiram isso no 2º turno. "
   "Essas comunidades votam de forma quase unânime há pelo menos duas eleições.")
md()
quase = []
for ano in ("2022", "2026"):
    df = D[(ano, 2)][0]
    for cand, col in (("Lula", LULA), (NOME_PL[ano], PL)):
        sh = df[col] / df.VALIDOS
        for lim in (0.9, 0.95, 1.0):
            sel = df[(df.VALIDOS > 0) & (sh >= lim - 1e-12)]
            quase.append({"Ano": ano, "Candidato": cand, "Limite": "100%" if lim == 1.0 else f"{int(lim * 100)}% ou mais",
                          "Seções": len(sel), "% das seções": pct(len(sel), len(df)),
                          "UFs com mais seções": ", ".join(f"{u} {n}" for u, n in sel.UF.value_counts().head(4).items())})
quase = pd.DataFrame(quase)
quase.to_csv(os.path.join(OUT, "secoes_quase_unanimes.csv"), sep=";", index=False, decimal=",")
md("Seções quase unânimes no 2º turno existem para os dois lados — as de Lula concentradas no Nordeste e na "
   "Amazônia, as do PL no Sul (comunidades rurais do RS e de SC) e no Pará. De 2022 para 2026, as seções com "
   "90% ou mais para Lula diminuíram e as do PL aumentaram, embora a vantagem de Lula tenha crescido: a "
   "vitória maior de 2026 não veio de mais seções quase unânimes.")
md()
md(tabela(quase, formatos={"% das seções": "{:.3f}"}))
md()
md("### 6.3 Tamanho e tipo de local")
md()
md("Chance de uma seção ter votos em um só candidato, por número de eleitores aptos:")
md()
fxp = pd.DataFrame(faixas_tab).pivot(index="Eleitores aptos", columns="Eleição", values="%").reindex(
    ["até 50", "51 a 100", "101 a 200", "201 a 300", "301 a 400", "mais de 400"]).reset_index()
md(tabela(fxp, floatfmt="{:.2f}"))
md()
md("Tipo de local (pelo nome e endereço no cadastro do TSE; escolas indígenas com nome só no idioma local "
   "caem em 'escola ou prédio comum', então as aldeias estão subestimadas):")
md()
md(tabela(pd.DataFrame(tipos_tab).pivot(index="Tipo de local", columns="Eleição", values="Seções").fillna(0)
          .astype(int).reset_index()))
md()
md(f"As {len(grandes)} seções com 300 ou mais eleitores no 2º turno de 2026:")
md()
md(tabela(pd.DataFrame({"UF": grandes.UF, "Município": grandes.MUNICIPIO.str.title(), "Local": grandes.NM_LOCAL.str.title(),
                        "Tipo": grandes.TIPO_LOCAL, "Candidato": grandes.CANDIDATO, "Votos": grandes.VOTOS_CANDIDATO,
                        "Aptos": grandes.APTOS}).sort_values("Aptos", ascending=False)))
md()

with open(os.path.join(OUT, "relatorio.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(relatorio) + "\n")
print("Relatório gravado em", os.path.join(OUT, "relatorio.md"))

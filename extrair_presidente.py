#!/usr/bin/env python3
"""
Extrai do Portal de Dados Abertos do TSE os votos para PRESIDENTE, seção por seção,
das eleições de 2022 e 2026 (1º e 2º turnos), e confere a soma dos boletins de urna
com a totalização oficial por município/zona.

Uso (Windows):  py extrair_presidente.py
Uso (Mac/Linux): python3 extrair_presidente.py

Gera a pasta ./dados/ (ao lado do script) com arquivos pequenos, prontos para subir no GitHub:
  presidente_<ano>_<turno>t_secoes.csv.gz  -> uma linha por seção: aptos, comparecimento,
                                             abstenções, brancos, nulos e votos de cada candidato (V_<número>)
  candidatos_<ano>_<turno>t.csv            -> número e nome de cada candidato
  conferencia_<ano>_<turno>t.csv           -> soma dos boletins x totalização oficial, por UF e candidato
  locais_<ano>.csv.gz                      -> nome e endereço do local de votação de cada seção

Os arquivos grandes baixados do TSE (vários GB) ficam em ./dados/_downloads e são apagados
depois de processados. Use --manter para guardá-los.
Só usa a biblioteca padrão do Python 3.
"""
import csv
import gzip
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from collections import defaultdict

API = "https://dadosabertos.tse.jus.br/api/3/action/"
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "dados")
DL = os.path.join(OUT, "_downloads")
MANTER = "--manter" in sys.argv
ANOS = [a for a in ("2022", "2026") if not any(x.isdigit() for x in sys.argv[1:]) or a in sys.argv[1:]]

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))


def api(action, **params):
    url = API + action + "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)["result"]
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** (attempt + 1))


def recursos(ano, dataset_ids, busca, trecho_url):
    """Recursos do portal cujo link contém trecho_url e é da eleição do ano pedido."""
    def ok(r):
        u = r["url"].lower()
        return trecho_url in u and u.endswith(".zip") and (f"eleicoes{ano}" in u or f"_{ano}" in u)
    for ds in dataset_ids:
        try:
            achados = [r for r in api("package_show", id=ds)["resources"] if ok(r)]
            if achados:
                return list({r["url"]: r for r in achados}.values())
        except Exception:
            pass
    achados = []
    for pkg in api("package_search", q=busca, rows=50)["results"]:
        achados += [r for r in pkg["resources"] if ok(r)]
    return list({r["url"]: r for r in achados}.values())


def baixar(url):
    os.makedirs(DL, exist_ok=True)
    dest = os.path.join(DL, url.rsplit("/", 1)[-1])
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    for attempt in range(4):
        try:
            print(f"    baixando {url.rsplit('/', 1)[-1]}", flush=True)
            tmp = dest + ".part"
            with urllib.request.urlopen(url, timeout=600) as r, open(tmp, "wb") as f:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
            os.replace(tmp, dest)
            return dest
        except Exception as e:
            print(f"    falhou ({e}); tentando de novo...", flush=True)
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"Não foi possível baixar {url}")


def apagar(path):
    if not MANTER:
        try:
            os.remove(path)
        except OSError:
            pass


def linhas_csv(zip_path, filtro_nome=lambda n: True):
    with zipfile.ZipFile(zip_path) as z:
        for nome in z.namelist():
            if nome.lower().endswith(".csv") and filtro_nome(nome.lower()):
                with z.open(nome) as raw:
                    yield from csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1"), delimiter=";")


def n(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def eh_presidente(row):
    cargo = row.get("CD_CARGO_PERGUNTA") or row.get("CD_CARGO")
    nome = (row.get("DS_CARGO_PERGUNTA") or row.get("DS_CARGO") or "").strip().lower()
    return cargo == "1" or nome == "presidente"


def extrair_boletins(ano, turno):
    arqs = recursos(ano, [f"resultados-{ano}-boletim-de-urna"], f"boletim de urna {ano}", f"bweb_{turno}t")
    if not arqs:
        print(f"  !! Não encontrei os boletins de urna de {ano}, {turno}º turno. Pulando.")
        return None
    print(f"  {len(arqs)} arquivos de boletim de urna")
    secoes = {}
    votos = defaultdict(lambda: defaultdict(int))
    nomes = {}
    for r in sorted(arqs, key=lambda r: r["url"]):
        path = baixar(r["url"])
        for row in linhas_csv(path, lambda nm: "bweb" in nm):
            if row.get("NR_TURNO", str(turno)) != str(turno) or not eh_presidente(row):
                continue
            k = (row["SG_UF"], row["CD_MUNICIPIO"], row["NR_ZONA"], row["NR_SECAO"])
            if k not in secoes:
                secoes[k] = {
                    "UF": row["SG_UF"], "CD_MUNICIPIO": row["CD_MUNICIPIO"], "MUNICIPIO": row["NM_MUNICIPIO"],
                    "ZONA": row["NR_ZONA"], "SECAO": row["NR_SECAO"], "LOCAL": row.get("NR_LOCAL_VOTACAO", ""),
                    "APTOS": n(row.get("QT_APTOS")), "COMPARECIMENTO": n(row.get("QT_COMPARECIMENTO")),
                    "ABSTENCOES": n(row.get("QT_ABSTENCOES")), "BRANCOS": 0, "NULOS": 0,
                    "TIPO_URNA": row.get("DS_TIPO_URNA", ""), "AGREGADAS": row.get("DS_AGREGADAS", ""),
                }
            tipo = (row.get("DS_TIPO_VOTAVEL") or "").strip().lower()
            q = n(row.get("QT_VOTOS"))
            if tipo == "nominal":
                votos[k][row["NR_VOTAVEL"]] += q
                nomes[row["NR_VOTAVEL"]] = row["NM_VOTAVEL"]
            elif tipo == "branco":
                secoes[k]["BRANCOS"] += q
            elif tipo == "nulo":
                secoes[k]["NULOS"] += q
        apagar(path)

    nums = sorted(nomes, key=int)
    campos = list(next(iter(secoes.values())).keys()) + [f"V_{c}" for c in nums]
    destino = os.path.join(OUT, f"presidente_{ano}_{turno}t_secoes.csv.gz")
    with gzip.open(destino, "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(campos)
        for k, s in secoes.items():
            w.writerow(list(s.values()) + [votos[k].get(c, 0) for c in nums])
    with open(os.path.join(OUT, f"candidatos_{ano}_{turno}t.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["NUMERO", "NOME"])
        for c in nums:
            w.writerow([c, nomes[c]])
    print(f"  {len(secoes)} seções gravadas em {os.path.basename(destino)}")

    soma = defaultdict(int)
    for k, s in secoes.items():
        for c, q in votos[k].items():
            soma[(s["UF"], s["CD_MUNICIPIO"], s["ZONA"], c)] += q
    return soma, nomes


def conferir(ano, turno, soma_bu, nomes):
    """Compara a soma dos boletins com a totalização oficial (votacao_candidato_munzona)."""
    arqs = recursos(ano, [f"resultados-{ano}"], f"resultados {ano} votação candidato município zona",
                    "votacao_candidato_munzona")
    if not arqs:
        print("  (não encontrei a totalização por município/zona; conferência pulada)")
        return
    path = baixar(arqs[0]["url"])
    with zipfile.ZipFile(path) as z:
        tem_br = any(nm.lower().endswith("_br.csv") for nm in z.namelist())
    filtro = (lambda nm: nm.endswith("_br.csv")) if tem_br else (lambda nm: not nm.endswith("_br.csv"))
    oficial = defaultdict(int)
    for row in linhas_csv(path, filtro):
        if row.get("NR_TURNO") != str(turno) or not eh_presidente(row):
            continue
        q = n(row.get("QT_VOTOS_NOMINAIS") or row.get("QT_VOTOS_NOMINAIS_VALIDOS") or row.get("QT_VOTOS"))
        oficial[(row["SG_UF"], row["CD_MUNICIPIO"], row["NR_ZONA"], row["NR_CANDIDATO"])] += q
    if turno == 2:  # o mesmo arquivo traz os dois turnos
        apagar(path)

    por_uf = defaultdict(lambda: [0, 0, 0])   # (UF, candidato) -> [soma BU, oficial, zonas divergentes]
    for k in set(soma_bu) | set(oficial):
        uf, _, _, c = k
        a, b = soma_bu.get(k, 0), oficial.get(k, 0)
        t = por_uf[(uf, c)]
        t[0] += a
        t[1] += b
        t[2] += a != b
    with open(os.path.join(OUT, f"conferencia_{ano}_{turno}t.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["UF", "NUMERO", "CANDIDATO", "SOMA_BOLETINS", "TOTALIZACAO_OFICIAL", "DIFERENCA",
                    "ZONAS_COM_DIFERENCA"])
        for (uf, c), (a, b, d) in sorted(por_uf.items()):
            w.writerow([uf, c, nomes.get(c, ""), a, b, a - b, d])
    dif = sum(abs(a - b) for a, b, _ in por_uf.values())
    print(f"  conferência: diferença total entre boletins e totalização = {dif} votos")


def extrair_locais(ano):
    arqs = recursos(ano, [f"eleitorado-{ano}"], f"locais de votação {ano}", f"local_votacao_{ano}")
    if not arqs:
        print("  (não encontrei o cadastro de locais de votação)")
        return
    path = baixar(arqs[0]["url"])
    vistos = set()
    with gzip.open(os.path.join(OUT, f"locais_{ano}.csv.gz"), "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["UF", "CD_MUNICIPIO", "ZONA", "SECAO", "NR_LOCAL", "NM_LOCAL", "ENDERECO", "BAIRRO",
                    "LATITUDE", "LONGITUDE"])
        for row in linhas_csv(path, lambda nm: "local_votacao" in nm):
            k = (row.get("SG_UF"), row.get("NR_ZONA"), row.get("NR_SECAO"))
            if k in vistos:
                continue
            vistos.add(k)
            w.writerow([row.get("SG_UF"), row.get("CD_MUNICIPIO"), row.get("NR_ZONA"), row.get("NR_SECAO"),
                        row.get("NR_LOCAL_VOTACAO"), row.get("NM_LOCAL_VOTACAO"),
                        row.get("DS_ENDERECO") or row.get("DS_ENDERECO_LOCAL_VOTACAO", ""),
                        row.get("NM_BAIRRO", ""), row.get("NR_LATITUDE", ""), row.get("NR_LONGITUDE", "")])
    apagar(path)
    print(f"  {len(vistos)} seções no cadastro de locais")


def main():
    os.makedirs(OUT, exist_ok=True)
    for ano in ANOS:
        for turno in (1, 2):
            print(f"\n== {ano} – {turno}º turno ==", flush=True)
            r = extrair_boletins(ano, turno)
            if r:
                conferir(ano, turno, *r)
        print(f"\n== {ano} – locais de votação ==", flush=True)
        extrair_locais(ano)
    print(f"\nPronto. Arquivos em: {OUT}")
    print("Suba a pasta 'dados' (sem a subpasta _downloads) para o repositório no GitHub.")


if __name__ == "__main__":
    main()

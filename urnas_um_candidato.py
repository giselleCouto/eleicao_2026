#!/usr/bin/env python3
"""
Baixa os Boletins de Urna (2º turno 2026) do Portal de Dados Abertos do TSE e lista
as seções (urnas) em que apenas UM candidato recebeu votos nominais.

Uso:   py urnas_um_candidato.py ["C:\\pasta\\de\\saida"]
Saída: na pasta indicada (ou, sem argumento, na mesma pasta do script):
  - urnas_um_candidato.csv  -> uma linha por urna/cargo com 100% dos votos nominais para um candidato
  - resumo_municipios.csv    -> contagem dessas urnas por município
  - downloads/               -> arquivos originais do TSE (podem ser apagados depois)

Só usa a biblioteca padrão do Python 3 (nada para instalar).
"""
import csv
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
# Pasta de saída: 1º argumento da linha de comando, ou a própria pasta onde o script está salvo
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
DL = os.path.join(OUT, "downloads")

csv.field_size_limit(sys.maxsize)


def api(action, **params):
    url = API + action + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)["result"]


def find_resources(dataset_ids, search_query, url_part):
    """Procura recursos cujo link contenha url_part, tentando IDs conhecidos e depois a busca."""
    for ds in dataset_ids:
        try:
            res = [r for r in api("package_show", id=ds)["resources"] if url_part in r["url"]]
            if res:
                return res
        except Exception:
            pass
    found = []
    for pkg in api("package_search", q=search_query, rows=50)["results"]:
        found += [r for r in pkg["resources"] if url_part in r["url"]]
    return found


def download(url):
    os.makedirs(DL, exist_ok=True)
    dest = os.path.join(DL, url.rsplit("/", 1)[-1])
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    for attempt in range(4):
        try:
            print(f"  baixando {url}")
            tmp = dest + ".part"
            with urllib.request.urlopen(url, timeout=300) as r, open(tmp, "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            os.replace(tmp, dest)
            return dest
        except Exception as e:
            print(f"  falhou ({e}); tentando de novo...")
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"Não foi possível baixar {url}")


def iter_csv_rows(zip_path, name_part=""):
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            if name.lower().endswith(".csv") and name_part in name.lower():
                with z.open(name) as raw:
                    yield from csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1"), delimiter=";")


def to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def main():
    print("1/3  Localizando os Boletins de Urna do 2º turno no portal do TSE...")
    bu = find_resources(
        ["resultados-2026-boletim-de-urna", "resultados-2026-boletim-de-urna-2-turno"],
        "boletim de urna 2026", "bweb_2t",
    )
    bu = list({r["url"]: r for r in bu}.values())
    if not bu:
        sys.exit("Não encontrei os arquivos bweb_2t_*.zip. O TSE pode ainda não ter publicado.")
    print(f"     {len(bu)} arquivos encontrados.")

    # chave da seção+cargo -> dados
    secoes = {}
    votos = defaultdict(lambda: defaultdict(int))   # chave -> {candidato: votos}
    candidatos = defaultdict(set)                   # (UF, cargo) -> candidatos na disputa

    print("2/3  Baixando e processando...")
    for r in sorted(bu, key=lambda r: r["url"]):
        path = download(r["url"])
        for row in iter_csv_rows(path, "bweb"):
            if row.get("NR_TURNO") not in (None, "2"):
                continue
            cargo = row["DS_CARGO_PERGUNTA"]
            key = (row["SG_UF"], row["CD_MUNICIPIO"], row["NR_ZONA"], row["NR_SECAO"], cargo)
            if key not in secoes:
                secoes[key] = {
                    "UF": row["SG_UF"], "CD_MUNICIPIO_TSE": row["CD_MUNICIPIO"],
                    "MUNICIPIO": row["NM_MUNICIPIO"], "ZONA": row["NR_ZONA"],
                    "SECAO": row["NR_SECAO"], "NR_LOCAL_VOTACAO": row.get("NR_LOCAL_VOTACAO", ""),
                    "CARGO": cargo, "APTOS": to_int(row.get("QT_APTOS")),
                    "COMPARECIMENTO": to_int(row.get("QT_COMPARECIMENTO")),
                    "BRANCOS": 0, "NULOS": 0,
                    "NR_URNA": row.get("NR_URNA_EFETIVADA", ""),
                    "CODIGO_CARGA_URNA": row.get("CD_CARGA_1_URNA_EFETIVADA", ""),
                    "SECOES_AGREGADAS": row.get("DS_AGREGADAS", ""),
                }
            tipo = row.get("DS_TIPO_VOTAVEL", "").lower()
            q = to_int(row["QT_VOTOS"])
            if tipo == "nominal":
                votos[key][row["NM_VOTAVEL"]] += q
                candidatos[(row["SG_UF"], cargo)].add(row["NM_VOTAVEL"])
            elif tipo == "branco":
                secoes[key]["BRANCOS"] += q
            elif tipo == "nulo":
                secoes[key]["NULOS"] += q

    resultado = []
    for key, s in secoes.items():
        com_voto = {c: v for c, v in votos[key].items() if v > 0}
        if len(com_voto) == 1 and len(candidatos[(s["UF"], s["CARGO"])]) > 1:
            cand, v = next(iter(com_voto.items()))
            resultado.append({**s, "CANDIDATO_UNICO": cand, "VOTOS_CANDIDATO": v})

    print("3/3  Buscando nomes e endereços dos locais de votação...")
    locais = {}
    try:
        lv = find_resources(["eleitorado-2026"], "local de votação 2026", "local_votacao_2026")
        if lv:
            wanted = {(r["UF"], r["ZONA"], r["SECAO"]) for r in resultado}
            for row in iter_csv_rows(download(lv[0]["url"]), "local_votacao"):
                k = (row.get("SG_UF"), row.get("NR_ZONA"), row.get("NR_SECAO"))
                if k in wanted:
                    locais[k] = (row.get("NM_LOCAL_VOTACAO", ""),
                                 row.get("DS_ENDERECO", "") or row.get("DS_ENDERECO_LOCAL_VOTACAO", ""),
                                 row.get("NM_BAIRRO", ""))
    except Exception as e:
        print(f"     (não consegui os locais de votação: {e}; sigo sem eles)")
    for r in resultado:
        r["LOCAL_VOTACAO"], r["ENDERECO"], r["BAIRRO"] = locais.get((r["UF"], r["ZONA"], r["SECAO"]), ("", "", ""))

    os.makedirs(OUT, exist_ok=True)
    resultado.sort(key=lambda r: (r["CARGO"], r["UF"], r["MUNICIPIO"], int(r["ZONA"]), int(r["SECAO"])))
    campos = ["CARGO", "UF", "MUNICIPIO", "CD_MUNICIPIO_TSE", "ZONA", "SECAO", "LOCAL_VOTACAO",
              "ENDERECO", "BAIRRO", "CANDIDATO_UNICO", "VOTOS_CANDIDATO", "BRANCOS", "NULOS",
              "COMPARECIMENTO", "APTOS", "NR_URNA", "CODIGO_CARGA_URNA", "SECOES_AGREGADAS",
              "NR_LOCAL_VOTACAO"]
    with open(os.path.join(OUT, "urnas_um_candidato.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        w.writeheader()
        w.writerows(resultado)

    resumo = defaultdict(lambda: {"URNAS": 0, "VOTOS": 0})
    for r in resultado:
        g = resumo[(r["CARGO"], r["UF"], r["MUNICIPIO"], r["CD_MUNICIPIO_TSE"], r["CANDIDATO_UNICO"])]
        g["URNAS"] += 1
        g["VOTOS"] += r["VOTOS_CANDIDATO"]
    with open(os.path.join(OUT, "resumo_municipios.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["CARGO", "UF", "MUNICIPIO", "CD_MUNICIPIO_TSE", "CANDIDATO_UNICO", "URNAS", "VOTOS"])
        for k, g in sorted(resumo.items(), key=lambda kv: -kv[1]["URNAS"]):
            w.writerow([*k, g["URNAS"], g["VOTOS"]])

    print(f"\nPronto. {len(secoes)} urnas/cargos analisados; {len(resultado)} com votos para um único candidato.")
    print(f"Resultados em: {OUT}")


if __name__ == "__main__":
    main()

# eleicao_2026
Analise Urnas e votos vs comportamento eleitor

## Como usar

1. **No seu computador** (precisa de acesso ao site do TSE):
   `py extrair_presidente.py` (Windows) ou `python3 extrair_presidente.py` (Mac/Linux).
   Baixa os boletins de urna de presidente de 2022 e 2026 (vários GB, apagados depois de processados)
   e grava arquivos compactos em `dados/`.
2. Suba a pasta `dados/` (sem `dados/_downloads`) para este repositório.
3. `python3 analisar.py` gera `resultados/relatorio.md` e as tabelas de apoio (usa `transferencias.py`; requer pandas, numpy e scipy).

`urnas_um_candidato.py` é a versão anterior, só para o 2º turno de 2026.

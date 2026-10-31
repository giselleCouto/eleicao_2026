# Eleições presidenciais 2022 e 2026 — análise dos boletins de urna

Fonte: boletins de urna e totalização oficial publicados pelo TSE no Portal de Dados Abertos. Todos os números abaixo foram calculados a partir desses arquivos.

## 1. Soma dos boletins de urna x totalização oficial

Cada boletim de urna (BU) é impresso e afixado na seção ao fim da votação e publicado pelo TSE. Se a soma de todos os BUs é igual ao total oficial, o resultado divulgado é exatamente a soma do que as urnas registraram — e qualquer cidadão pode conferir o BU da própria seção.

| Eleição | Votos nos BUs | Totalização oficial | Diferença absoluta | Zonas com diferença |
|---|---|---|---|---|
| 2022 – 1º turno | 118.229.719 | 118.229.719 | 0 | 0 |
| 2022 – 2º turno | 118.552.353 | 118.552.353 | 0 | 0 |
| 2026 – 1º turno | 119.306.034 | 119.300.788 | 5.246 | 2.148 |
| 2026 – 2º turno | 124.082.273 | 124.082.273 | 0 | 0 |

Diferenças diferentes de zero, quando houver, costumam vir de seções com votação em cédula, urnas substituídas ou BUs recuperados depois; o arquivo `conferencia_*.csv` mostra onde estão.

## 2. Comparecimento e abstenção

| Eleição | Aptos | Comparecimento | Abstenção | Abstenção % | Brancos+nulos % |
|---|---|---|---|---|---|
| 2022 – 1º turno | 156.453.354 | 123.682.372 | 32.770.982 | 20,9 | 4,4 |
| 2022 – 2º turno | 156.453.354 | 124.252.796 | 32.200.558 | 20,6 | 4,6 |
| 2026 – 1º turno | 158.745.007 | 125.275.835 | 33.469.172 | 21,1 | 4,8 |
| 2026 – 2º turno | 158.744.977 | 128.236.074 | 30.508.903 | 19,2 | 3,2 |

| Eleição | Lula votos | Lula % válidos | Bolsonaro (PL) votos | Bolsonaro (PL) % válidos |
|---|---|---|---|---|
| 2022 – 1º turno | 57.259.504 | 48,4 | 51.072.345 | 43,2 |
| 2022 – 2º turno | 60.345.999 | 50,9 | 58.206.354 | 49,1 |
| 2026 – 1º turno | 53.879.538 | 45,2 | 56.104.503 | 47,0 |
| 2026 – 2º turno | 64.256.232 | 51,8 | 59.826.041 | 48,2 |

Na linha do PL: em 2022 o candidato é Jair Bolsonaro; em 2026, Flávio Bolsonaro.

## 3. O eleitorado de Flávio Bolsonaro (2026) é o mesmo de Jair Bolsonaro (2022)?

Comparação município a município da fatia de votos válidos do candidato do PL. As seções mudam de uma eleição para outra, por isso a unidade comum é o município. Correlação ponderada pelo número de eleitores: 1 = mesma distribuição geográfica; 0 = nenhuma relação.

| Turno | Municípios | Correlação | Diferença média (p.p.) | Municípios onde o PL caiu | Municípios onde o PL subiu |
|---|---|---|---|---|---|
| 1º | 5.706 | 0,984 | 3,929 | 149 | 5.557 |
| 2º | 5.707 | 0,984 | -0,604 | 1.298 | 4.409 |

Correlação acima de ~0,9 indica que o voto no PL em 2026 veio, em grande medida, dos mesmos lugares que votaram no PL em 2022. A coluna 'diferença média' mostra quanto o partido ganhou ou perdeu, em pontos percentuais, no município típico.

## 4. Para onde foram, no 1º turno de 2026, os eleitores de Lula em 2022?

O voto é secreto: não existe dado de *quem* votou em quem. O que dá para fazer é **inferência ecológica** — comparar milhares de municípios e estimar, estatisticamente, que fração de cada grupo de 2022 vai para cada opção de 2026. É uma estimativa (método de Goodman), não uma contagem. Mudanças no eleitorado entre 2022 e 2026 (jovens que entraram, óbitos, mudanças de domicílio) também entram no resultado.

Atenção: entre eleições diferentes o método é frágil. Se a tabela mostrar algo implausível (por exemplo, quase todo um eleitorado trocando de lado), isso indica limite do método, não fato.

Percentual estimado de cada grupo de 2022 (linhas) que foi para cada opção no 1º turno de 2026 (colunas):

| Origem (1º turno 2022) | Lula 2026 | PL 2026 | Outros candidatos 2026 | Brancos/nulos 2026 | Abstenção 2026 |
|---|---|---|---|---|---|
| Lula 2022 | 92,5 | 5,4 | 0,2 | 1,9 | 0,0 |
| PL 2022 | 0,0 | 95,3 | 4,7 | 0,0 | 0,0 |
| Outros candidatos 2022 | 21,6 | 0,0 | 49,0 | 3,3 | 26,1 |
| Brancos/nulos 2022 | 0,0 | 0,0 | 9,7 | 64,1 | 26,2 |
| Abstenção 2022 | 3,6 | 5,9 | 0,0 | 0,1 | 90,5 |

Detalhe por candidato de 2026 (apenas a linha dos eleitores de Lula em 2022):

| Destino no 1º turno de 2026 | % dos eleitores de Lula 2022 |
|---|---|
| Lula | 91,7 |
| PL | 5,4 |
| Brancos/nulos | 1,8 |
| ESCRITOR AUGUSTO CURY | 1,0 |
| RENAN SANTOS | 0,0 |
| HERTZ DIAS | 0,0 |
| EDMILSON COSTA | 0,0 |
| ZEMA | 0,0 |
| RUI COSTA PIMENTA | 0,0 |
| LEONARDO AVALANCHE | 0,0 |
| CLARIANA BARAO | 0,0 |
| SAMARA | 0,0 |
| RONALDO CAIADO | 0,0 |
| VETERINÁRIO WILSON GRASSI | 0,0 |
| Abstenção | 0,0 |

## 5. De onde vieram os votos que Lula ganhou entre o 1º e o 2º turno?

Aqui a comparação é seção a seção (as seções são as mesmas nos dois turnos da mesma eleição), o que torna a estimativa bem mais precisa que a do item 4.

### 2022

Seções casadas entre os turnos: 472.028

| Grupo no 1º turno | Tamanho do grupo | → Lula % | → PL % | → Abstenção % | Votos estimados para Lula | Votos estimados para o PL |
|---|---|---|---|---|---|---|
| Lula (1º turno) | 57.259.504 | 95,6 | 0,0 | 3,0 | 54.711.753 | 0 |
| PL (1º turno) | 51.072.345 | 0,0 | 99,8 | 0,2 | 0 | 50.951.572 |
| Outros candidatos (1º turno) | 9.897.870 | 43,3 | 38,6 | 1,9 | 4.286.153 | 3.820.222 |
| Brancos/nulos (1º turno) | 5.452.653 | 21,7 | 24,4 | 0,0 | 1.184.391 | 1.330.288 |
| Abstenção (1º turno) | 32.770.982 | 2,9 | 2,1 | 95,0 | 941.699 | 702.067 |

Abstenção: 20,95% no 1º turno → 20,58% no 2º turno.

### 2026

Seções casadas entre os turnos: 499.205

| Grupo no 1º turno | Tamanho do grupo | → Lula % | → PL % | → Abstenção % | Votos estimados para Lula | Votos estimados para o PL |
|---|---|---|---|---|---|---|
| Lula (1º turno) | 53.879.536 | 97,3 | 0,0 | 2,3 | 52.442.700 | 0 |
| PL (1º turno) | 56.104.503 | 0,0 | 96,7 | 2,7 | 0 | 54.244.766 |
| Outros candidatos (1º turno) | 9.321.993 | 44,7 | 43,9 | 0,0 | 4.169.346 | 4.094.465 |
| Brancos/nulos (1º turno) | 5.969.801 | 60,6 | 8,1 | 0,0 | 3.619.105 | 485.364 |
| Abstenção (1º turno) | 33.469.144 | 7,1 | 3,9 | 88,7 | 2.362.199 | 1.290.996 |

Abstenção: 21,08% no 1º turno → 19,22% no 2º turno.

Como ler: a linha 'Abstenção (1º turno)' estima quantos eleitores que faltaram no 1º turno votaram no 2º e em quem; a linha 'Outros candidatos' estima como se dividiram os eleitores dos candidatos eliminados. As linhas não são contagens, são estimativas com margem de erro.

## 6. Seções em que apenas um candidato recebeu votos

Esse padrão aparece em toda eleição e é usado em boatos de fraude. Os dados mostram que ele se concentra em seções muito pequenas — onde poucos eleitores, muitas vezes de uma mesma comunidade (aldeias, comunidades rurais isoladas, seções no exterior), tendem a votar do mesmo jeito.

### 2022 – 1º turno

| Seções | Seções com 1 só candidato | % das seções | Eleitores aptos (mediana) — todas | Eleitores aptos (mediana) — 1 só candidato | Comparecimento (mediana) — 1 só candidato | % dos votos válidos do país |
|---|---|---|---|---|---|---|
| 472.028 | 62 | 0,0 | 340,0 | 100,0 | 77,5 | 0,0 |

Chance de uma seção ter votos em um só candidato, por tamanho da seção (eleitores aptos):

| Tamanho | Seções | Com 1 só candidato | % com 1 só candidato |
|---|---|---|---|
| até 50 | 191 | 7 | 3,7 |
| 51–100 | 2.619 | 24 | 0,9 |
| 101–200 | 15.748 | 20 | 0,1 |
| 201–300 | 116.728 | 6 | 0,0 |
| 301–400 | 298.685 | 4 | 0,0 |
| mais de 400 | 38.057 | 1 | 0,0 |

### 2022 – 2º turno

| Seções | Seções com 1 só candidato | % das seções | Eleitores aptos (mediana) — todas | Eleitores aptos (mediana) — 1 só candidato | Comparecimento (mediana) — 1 só candidato | % dos votos válidos do país |
|---|---|---|---|---|---|---|
| 472.028 | 147 | 0,0 | 340,0 | 117,0 | 92,0 | 0,0 |

Chance de uma seção ter votos em um só candidato, por tamanho da seção (eleitores aptos):

| Tamanho | Seções | Com 1 só candidato | % com 1 só candidato |
|---|---|---|---|
| até 50 | 191 | 13 | 6,8 |
| 51–100 | 2.623 | 37 | 1,4 |
| 101–200 | 15.755 | 56 | 0,4 |
| 201–300 | 116.714 | 17 | 0,0 |
| 301–400 | 298.754 | 20 | 0,0 |
| mais de 400 | 37.991 | 4 | 0,0 |

### 2026 – 1º turno

| Seções | Seções com 1 só candidato | % das seções | Eleitores aptos (mediana) — todas | Eleitores aptos (mediana) — 1 só candidato | Comparecimento (mediana) — 1 só candidato | % dos votos válidos do país |
|---|---|---|---|---|---|---|
| 499.206 | 40 | 0,0 | 327,0 | 91,5 | 73,5 | 0,0 |

Chance de uma seção ter votos em um só candidato, por tamanho da seção (eleitores aptos):

| Tamanho | Seções | Com 1 só candidato | % com 1 só candidato |
|---|---|---|---|
| até 50 | 270 | 7 | 2,6 |
| 51–100 | 2.602 | 16 | 0,6 |
| 101–200 | 19.524 | 8 | 0,0 |
| 201–300 | 149.066 | 7 | 0,0 |
| 301–400 | 307.714 | 2 | 0,0 |
| mais de 400 | 20.030 | 0 | 0,0 |

### 2026 – 2º turno

| Seções | Seções com 1 só candidato | % das seções | Eleitores aptos (mediana) — todas | Eleitores aptos (mediana) — 1 só candidato | Comparecimento (mediana) — 1 só candidato | % dos votos válidos do país |
|---|---|---|---|---|---|---|
| 499.205 | 110 | 0,0 | 327,0 | 150,5 | 125,5 | 0,0 |

Chance de uma seção ter votos em um só candidato, por tamanho da seção (eleitores aptos):

| Tamanho | Seções | Com 1 só candidato | % com 1 só candidato |
|---|---|---|---|
| até 50 | 270 | 8 | 3,0 |
| 51–100 | 2.606 | 31 | 1,2 |
| 101–200 | 19.524 | 31 | 0,2 |
| 201–300 | 149.047 | 20 | 0,0 |
| 301–400 | 307.744 | 19 | 0,0 |
| mais de 400 | 20.014 | 1 | 0,0 |

### Por candidato

| Eleição | Candidato | Seções | % das seções do país | Votos nessas seções | % dos votos do candidato | Aptos (mediana) | Seções no exterior |
|---|---|---|---|---|---|---|---|
| 2022 – 1º turno | JAIR BOLSONARO | 1 | 0,00 | 58 | 0,00 | 91,00 | 0 |
| 2022 – 1º turno | LULA | 61 | 0,01 | 6.095 | 0,01 | 102,00 | 1 |
| 2022 – 2º turno | JAIR BOLSONARO | 4 | 0,00 | 124 | 0,00 | 327,50 | 2 |
| 2022 – 2º turno | LULA | 143 | 0,03 | 16.455 | 0,03 | 117,00 | 2 |
| 2026 – 1º turno | FLAVIO BOLSONARO | 2 | 0,00 | 130 | 0,00 | 96,00 | 0 |
| 2026 – 1º turno | LULA | 38 | 0,01 | 3.634 | 0,01 | 88,50 | 2 |
| 2026 – 2º turno | FLAVIO BOLSONARO | 4 | 0,00 | 296 | 0,00 | 96,00 | 0 |
| 2026 – 2º turno | LULA | 106 | 0,02 | 14.860 | 0,02 | 161,00 | 0 |


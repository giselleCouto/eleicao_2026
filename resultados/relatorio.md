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

**2026, 1º turno:** a diferença se concentra em 1 candidato(s) — LEONARDO AVALANCHE: +5.246 votos.

Quando toda a diferença está num único candidato, a causa é a situação da candidatura, não a contagem: votos dados a quem renunciou ou teve o registro negado continuam aparecendo no boletim da urna, mas a totalização os considera nulos. O arquivo `conferencia_*.csv` mostra cada UF.

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

- **2022:** a abstenção foi de 20,95% no 1º turno para 20,58% no 2º (-0,36 ponto percentual; 570.424 eleitores a menos faltaram).
- **2026:** a abstenção foi de 21,08% no 1º turno para 19,22% no 2º (-1,86 ponto percentual; 2.960.269 eleitores a menos faltaram).

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
| Lula 2022 | 88,6 | 8,1 | 0,3 | 3,0 | 0,0 |
| PL 2022 | 0,0 | 94,8 | 5,2 | 0,0 | 0,0 |
| Outros candidatos 2022 | 14,8 | 0,0 | 58,2 | 3,9 | 23,1 |
| Brancos/nulos 2022 | 0,0 | 0,0 | 10,5 | 68,4 | 21,2 |
| Abstenção 2022 | 2,8 | 7,0 | 0,0 | 0,1 | 90,1 |

Detalhe por candidato de 2026 (apenas a linha dos eleitores de Lula em 2022):

| Destino no 1º turno de 2026 | % dos eleitores de Lula 2022 |
|---|---|
| Lula | 88,1 |
| PL | 7,5 |
| Brancos/nulos | 3,1 |
| ESCRITOR AUGUSTO CURY | 1,3 |
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
| Lula (1º turno) | 57.259.504 | 95,3 | 0,0 | 2,6 | 54.592.627 | 0 |
| PL (1º turno) | 51.072.345 | 0,0 | 99,9 | 0,1 | 0 | 51.018.594 |
| SIMONE TEBET (1º turno) | 4.915.423 | 29,9 | 44,9 | 5,6 | 1.467.609 | 2.207.255 |
| CIRO GOMES (1º turno) | 3.599.287 | 48,1 | 40,6 | 0,0 | 1.730.234 | 1.461.337 |
| Demais candidatos (1º turno) | 1.383.160 | 23,0 | 60,5 | 0,0 | 317.830 | 837.376 |
| Brancos/nulos (1º turno) | 5.452.653 | 18,3 | 28,0 | 0,0 | 996.495 | 1.524.281 |
| Abstenção (1º turno) | 32.770.982 | 3,8 | 3,5 | 92,7 | 1.241.204 | 1.157.510 |

Diferença Lula − PL: +6.187.159 votos no 1º turno e +2.139.645 no 2º (variação de -4.047.514). A tabela abaixo reparte essa variação entre os grupos: nas duas primeiras linhas, o efeito de eleitores dos finalistas que deixaram de votar neles; nas demais, o saldo (votos para Lula menos votos para o PL) de cada grupo que não votou nos finalistas no 1º turno.

| Grupo no 1º turno | Efeito na diferença Lula − PL |
|---|---|
| Lula (1º turno) | -2.666.877 |
| PL (1º turno) | 53.751 |
| SIMONE TEBET (1º turno) | -739.646 |
| CIRO GOMES (1º turno) | 268.896 |
| Demais candidatos (1º turno) | -519.546 |
| Brancos/nulos (1º turno) | -527.786 |
| Abstenção (1º turno) | 83.694 |

Soma das linhas: -4.047.514 votos.

Abstenção: 20,95% no 1º turno → 20,58% no 2º turno.

### 2026

Seções casadas entre os turnos: 499.205

| Grupo no 1º turno | Tamanho do grupo | → Lula % | → PL % | → Abstenção % | Votos estimados para Lula | Votos estimados para o PL |
|---|---|---|---|---|---|---|
| Lula (1º turno) | 53.879.536 | 98,1 | 0,0 | 1,6 | 52.862.549 | 0 |
| PL (1º turno) | 56.104.503 | 0,0 | 97,2 | 2,1 | 0 | 54.516.753 |
| ESCRITOR AUGUSTO CURY (1º turno) | 3.448.569 | 58,7 | 25,2 | 0,0 | 2.023.517 | 869.418 |
| RENAN SANTOS (1º turno) | 2.675.887 | 45,4 | 37,1 | 0,0 | 1.215.778 | 992.592 |
| RONALDO CAIADO (1º turno) | 2.605.148 | 43,7 | 47,7 | 0,0 | 1.138.089 | 1.243.869 |
| Demais candidatos (1º turno) | 592.389 | 31,9 | 51,9 | 0,0 | 189.086 | 307.663 |
| Brancos/nulos (1º turno) | 5.969.801 | 58,2 | 8,0 | 0,0 | 3.475.117 | 480.567 |
| Abstenção (1º turno) | 33.469.144 | 10,0 | 4,2 | 85,1 | 3.352.096 | 1.415.179 |

Diferença Lula − PL: -2.224.965 votos no 1º turno e +4.430.191 no 2º (variação de +6.655.156). A tabela abaixo reparte essa variação entre os grupos: nas duas primeiras linhas, o efeito de eleitores dos finalistas que deixaram de votar neles; nas demais, o saldo (votos para Lula menos votos para o PL) de cada grupo que não votou nos finalistas no 1º turno.

| Grupo no 1º turno | Efeito na diferença Lula − PL |
|---|---|
| Lula (1º turno) | -1.016.987 |
| PL (1º turno) | 1.587.750 |
| ESCRITOR AUGUSTO CURY (1º turno) | 1.154.100 |
| RENAN SANTOS (1º turno) | 223.186 |
| RONALDO CAIADO (1º turno) | -105.780 |
| Demais candidatos (1º turno) | -118.577 |
| Brancos/nulos (1º turno) | 2.994.550 |
| Abstenção (1º turno) | 1.936.916 |

Soma das linhas: +6.655.158 votos.

Abstenção: 21,08% no 1º turno → 19,22% no 2º turno.

Como ler: a linha 'Abstenção (1º turno)' estima quantos eleitores que faltaram no 1º turno votaram no 2º e em quem; as linhas dos candidatos eliminados estimam como se dividiram os seus eleitores. As estimativas foram ajustadas para bater exatamente com os votos contados em cada turno. Os percentuais de cada linha somam 100% contando também brancos/nulos no 2º turno, que não aparecem na tabela. As linhas não são contagens, são estimativas com margem de erro.

## 6. Seções em que apenas um candidato recebeu votos

Esse padrão aparece em toda eleição e é usado em boatos de fraude. Os dados abaixo mostram três coisas: (1) é raríssimo — menos de 0,04% das seções; (2) acontece sobretudo em seções menores que a média, e a chance cresce muito quanto menor a seção; (3) quase todas ficam em aldeias indígenas, assentamentos, quilombos e comunidades rurais isoladas, onde um grupo pequeno e coeso costuma votar do mesmo jeito. Os votos dessas seções somados são uma fração mínima da diferença entre os candidatos.

### 2022 – 1º turno

| Indicador | Valor |
|---|---|
| Seções | 472.028 |
| Seções com 1 só candidato | 62 |
| % das seções | 0,013 |
| Eleitores aptos (mediana) — todas | 340 |
| Eleitores aptos (mediana) — 1 só candidato | 100 |
| Comparecimento (mediana) — 1 só candidato | 78 |
| Comparecimento (mediana) — todas | 268 |
| Votos válidos nessas seções | 6.153 |
| Diferença entre 1º e 2º colocados no país | 6.187.159 |

Tipo de local de votação dessas seções (pelo nome do local no cadastro do TSE):

| Tipo de local | Seções |
|---|---|
| Assentamento, quilombo ou comunidade rural | 37 |
| Aldeia / escola indígena | 17 |
| Outro (escola ou prédio comum) | 7 |
| Exterior | 1 |

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

| Indicador | Valor |
|---|---|
| Seções | 472.028 |
| Seções com 1 só candidato | 147 |
| % das seções | 0,031 |
| Eleitores aptos (mediana) — todas | 340 |
| Eleitores aptos (mediana) — 1 só candidato | 117 |
| Comparecimento (mediana) — 1 só candidato | 92 |
| Comparecimento (mediana) — todas | 270 |
| Votos válidos nessas seções | 16.579 |
| Diferença entre 1º e 2º colocados no país | 2.139.645 |

Tipo de local de votação dessas seções (pelo nome do local no cadastro do TSE):

| Tipo de local | Seções |
|---|---|
| Assentamento, quilombo ou comunidade rural | 80 |
| Aldeia / escola indígena | 47 |
| Outro (escola ou prédio comum) | 16 |
| Exterior | 4 |

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

| Indicador | Valor |
|---|---|
| Seções | 499.206 |
| Seções com 1 só candidato | 40 |
| % das seções | 0,008 |
| Eleitores aptos (mediana) — todas | 327 |
| Eleitores aptos (mediana) — 1 só candidato | 92 |
| Comparecimento (mediana) — 1 só candidato | 74 |
| Comparecimento (mediana) — todas | 257 |
| Votos válidos nessas seções | 3.764 |
| Diferença entre 1º e 2º colocados no país | 2.224.965 |

Tipo de local de votação dessas seções (pelo nome do local no cadastro do TSE):

| Tipo de local | Seções |
|---|---|
| Aldeia / escola indígena | 21 |
| Assentamento, quilombo ou comunidade rural | 15 |
| Outro (escola ou prédio comum) | 2 |
| Exterior | 2 |

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

| Indicador | Valor |
|---|---|
| Seções | 499.205 |
| Seções com 1 só candidato | 110 |
| % das seções | 0,022 |
| Eleitores aptos (mediana) — todas | 327 |
| Eleitores aptos (mediana) — 1 só candidato | 150 |
| Comparecimento (mediana) — 1 só candidato | 126 |
| Comparecimento (mediana) — todas | 263 |
| Votos válidos nessas seções | 15.156 |
| Diferença entre 1º e 2º colocados no país | 4.430.191 |

Tipo de local de votação dessas seções (pelo nome do local no cadastro do TSE):

| Tipo de local | Seções |
|---|---|
| Aldeia / escola indígena | 63 |
| Assentamento, quilombo ou comunidade rural | 41 |
| Outro (escola ou prédio comum) | 6 |

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
| 2022 – 1º turno | JAIR BOLSONARO | 1 | 0,0002 | 58 | 0,0001 | 91 | 0 |
| 2022 – 1º turno | LULA | 61 | 0,0129 | 6.095 | 0,0106 | 102 | 1 |
| 2022 – 2º turno | JAIR BOLSONARO | 4 | 0,0008 | 124 | 0,0002 | 328 | 2 |
| 2022 – 2º turno | LULA | 143 | 0,0303 | 16.455 | 0,0273 | 117 | 2 |
| 2026 – 1º turno | FLAVIO BOLSONARO | 2 | 0,0004 | 130 | 0,0002 | 96 | 0 |
| 2026 – 1º turno | LULA | 38 | 0,0076 | 3.634 | 0,0067 | 88 | 2 |
| 2026 – 2º turno | FLAVIO BOLSONARO | 4 | 0,0008 | 296 | 0,0005 | 96 | 0 |
| 2026 – 2º turno | LULA | 106 | 0,0212 | 14.860 | 0,0231 | 161 | 0 |


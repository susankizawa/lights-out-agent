# inteligencia-artificial

Trabalho de Inteligencia Artificial (ED1) com modelagem e comparacao de algoritmos de busca no problema Lights Out.

## Estrutura

- `codigo-fonte/`: implementacao em Python (board, buscas, metricas e CLI)
- `latex/`: relatorio em LaTeX
- `relatorio.pdf`: PDF final gerado

## Como executar os experimentos

No Windows PowerShell:

```powershell
cd codigo-fonte
python .\main.py --format csv > resultados.csv
```

Formatos disponiveis:

- `--format pretty`: tabela alinhada no terminal
- `--format tsv`: saida tabulada
- `--format csv`: saida CSV

## Como gerar o relatorio

```powershell
cd latex
.\build.ps1
```

## Requisitos

- Python 3.x
- Ambiente LaTeX (MiKTeX ou TeX Live) para compilar o PDF

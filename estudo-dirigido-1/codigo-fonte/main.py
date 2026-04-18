"""
Ponto de entrada (CLI) para rodar os experimentos do Lights Out.

Execute nesta pasta:
  python main.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

from experiments import (
    TableFormat,
    default_board_sizes,
    format_csv_table,
    format_table,
    format_table_examples,
    mock_experiment_rows,
    run_suite,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Experimentos de busca no Lights Out")
    parser.add_argument(
        "--sizes",
        type=str,
        default=",".join(map(str, default_board_sizes())),
        help="Tamanhos N do tabuleiro NxN, separados por virgula (padrao: 2,3,5,7,10)",
    )
    parser.add_argument(
        "--max-expansions",
        type=int,
        default=2_000_000,
        help="Para apos expandir/gerar esta quantidade de nos (conforme o algoritmo)",
    )
    parser.add_argument(
        "--max-wall-sec",
        type=float,
        default=30.0,
        help="Tempo maximo (s) de parede por execucao (cada par tamanho+algoritmo)",
    )
    parser.add_argument(
        "--initial-mode",
        choices=("all_off", "random"),
        default="all_off",
        help="Como montar o estado inicial (todas apagadas ou aleatorio)",
    )
    parser.add_argument(
        "--initial-seed",
        type=int,
        default=0,
        help="Semente do RNG quando initial-mode=random",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Sem mensagens de progresso; formato da tabela padrao vira tsv (bom para redirecionar)",
    )
    parser.add_argument(
        "--format",
        choices=("pretty", "tsv", "csv"),
        default=None,
        help=(
            "Saida da tabela: pretty (alinhada no terminal), tsv (TAB p/ planilha) ou "
            "csv (; e UTF-8, bom p/ Excel PT-BR). Padrao: pretty (ou tsv com --quiet)."
        ),
    )
    parser.add_argument(
        "--mock-table",
        action="store_true",
        help="Usa dados mockados para testar a tabela sem executar buscas.",
    )
    parser.add_argument(
        "--mock-all-formats",
        action="store_true",
        help="Com --mock-table, imprime exemplos de pretty, tsv e csv em uma unica execucao.",
    )
    parser.add_argument(
        "--csv-output-file",
        type=str,
        default=None,
        help="Salva somente a tabela CSV (sem progresso/rodape) no arquivo informado.",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    sizes = tuple(int(x.strip()) for x in args.sizes.split(",") if x.strip())
    out_fmt: TableFormat = args.format if args.format is not None else ("tsv" if args.quiet else "pretty")

    if args.mock_table:
        if args.csv_output_file is not None:
            rows = mock_experiment_rows()
            Path(args.csv_output_file).write_text(format_csv_table(rows), encoding="utf-8-sig", newline="")
            print(f"CSV salvo em: {args.csv_output_file}")
            return

        if args.mock_all_formats:
            samples = format_table_examples()
            print("=== MOCK OUTPUT: PRETTY ===")
            print(samples["pretty"], end="")
            print("\n=== MOCK OUTPUT: TSV ===")
            print(samples["tsv"], end="")
            print("\n=== MOCK OUTPUT: CSV ===")
            print(samples["csv"], end="")
            return

        rows = mock_experiment_rows()
        print(format_table(rows, fmt=out_fmt), end="")
        return

    rows = run_suite(
        sizes,
        max_expansions=args.max_expansions,
        max_wall_time_sec=args.max_wall_sec,
        initial_mode=args.initial_mode,
        initial_seed=args.initial_seed,
        verbose=not args.quiet,
    )

    if args.csv_output_file is not None:
        Path(args.csv_output_file).write_text(format_csv_table(rows), encoding="utf-8-sig", newline="")
        print(f"CSV salvo em: {args.csv_output_file}")
        return

    print(format_table(rows, fmt=out_fmt), end="")


if __name__ == "__main__":
    main()

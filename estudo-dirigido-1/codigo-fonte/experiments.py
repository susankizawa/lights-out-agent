"""
Experimentos em lote: varia tamanhos de tabuleiro e algoritmos.

Conecta `board`, `search` e `metrics` sem colocar regras do Lights Out dentro das buscas.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
import sys
from typing import Callable, Dict, Iterable, List, Literal, Tuple

from board import LightsOutProblem, all_lights_off, random_initial_state
from metrics import measure_callable
from search import (
    SearchLimits,
    SearchOutcome,
    TerminationReason,
    a_star_search,
    breadth_first_search,
    depth_first_search,
    greedy_best_first_search,
    hill_climbing,
)


AlgorithmFn = Callable[[LightsOutProblem, SearchLimits], SearchOutcome]


@dataclass(frozen=True)
class ExperimentRow:
    """Uma linha de resultado (TSV) para um algoritmo + tamanho de tabuleiro."""

    algorithm: str
    size: int
    termination: TerminationReason
    path_len: int | None
    nodes_expanded: int
    max_frontier: int
    wall_time_sec: float
    peak_traced_memory_bytes: int


def default_board_sizes() -> Tuple[int, ...]:
    """Tamanhos pedidos no enunciado (podem ser filtrados na CLI)."""
    return (2, 3, 5, 7, 10)


def mock_experiment_rows() -> List[ExperimentRow]:
    """Dados mockados para testar a formatacao da tabela sem executar buscas."""
    # Valores variados para exercitar colunas de sucesso, timeout e ausencia de solucao.
    return [
        ExperimentRow(
            algorithm="bfs",
            size=2,
            termination=TerminationReason.SUCCESS,
            path_len=4,
            nodes_expanded=16,
            max_frontier=7,
            wall_time_sec=0.000145,
            peak_traced_memory_bytes=2256,
        ),
        ExperimentRow(
            algorithm="astar",
            size=3,
            termination=TerminationReason.SUCCESS,
            path_len=9,
            nodes_expanded=84,
            max_frontier=42,
            wall_time_sec=0.001924,
            peak_traced_memory_bytes=11840,
        ),
        ExperimentRow(
            algorithm="greedy",
            size=5,
            termination=TerminationReason.TIME_LIMIT,
            path_len=None,
            nodes_expanded=5321,
            max_frontier=1209,
            wall_time_sec=30.000000,
            peak_traced_memory_bytes=450560,
        ),
        ExperimentRow(
            algorithm="hill_climbing",
            size=7,
            termination=TerminationReason.NO_SOLUTION,
            path_len=None,
            nodes_expanded=980,
            max_frontier=1,
            wall_time_sec=0.084312,
            peak_traced_memory_bytes=6912,
        ),
    ]


def format_table_examples() -> Dict[TableFormat, str]:
    """Gera exemplos prontos de saida para pretty/tsv/csv com dados mockados."""
    rows = mock_experiment_rows()
    return {
        "pretty": format_table(rows, fmt="pretty"),
        "tsv": format_table(rows, fmt="tsv"),
        "csv": format_table(rows, fmt="csv"),
    }


def format_csv_table(rows: Iterable[ExperimentRow]) -> str:
    """Gera somente a tabela CSV (cabecalho + dados), sem rodape ou logs."""
    data = list(rows)
    headers = list(TABLE_HEADERS_PT)
    buf = StringIO()
    writer = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    writer.writerow(headers)
    for r in data:
        writer.writerow(row_cells(r))
    return buf.getvalue()


def algorithm_registry() -> Dict[str, AlgorithmFn]:
    """Mapa nome-curto -> funcao de busca (para tabelas e comparacoes)."""
    return {
        "bfs": breadth_first_search,
        "dfs": depth_first_search,
        "greedy": greedy_best_first_search,
        "astar": a_star_search,
        "hill_climbing": hill_climbing,
    }


def run_single(
    name: str,
    algorithm: AlgorithmFn,
    size: int,
    limits: SearchLimits,
    *,
    initial_mode: str = "all_off",
    initial_seed: int = 0,
) -> ExperimentRow:
    if initial_mode == "all_off":
        initial = all_lights_off(size)
    elif initial_mode == "random":
        initial = random_initial_state(size, initial_seed)
    else:
        raise ValueError(f"initial_mode desconhecido: {initial_mode}")

    problem = LightsOutProblem(size=size, initial_state=initial)

    def runner() -> SearchOutcome:
        return algorithm(problem, limits)

    outcome, resources = measure_callable(runner)
    path_len = len(outcome.path) if outcome.path is not None else None
    return ExperimentRow(
        algorithm=name,
        size=size,
        termination=outcome.termination,
        path_len=path_len,
        nodes_expanded=outcome.nodes_expanded,
        max_frontier=outcome.max_frontier,
        wall_time_sec=resources.wall_time_sec,
        peak_traced_memory_bytes=resources.peak_traced_memory_bytes,
    )


def run_suite(
    sizes: Iterable[int],
    *,
    max_expansions: int,
    max_wall_time_sec: float,
    algorithms: Dict[str, AlgorithmFn] | None = None,
    initial_mode: str = "all_off",
    initial_seed: int = 0,
    verbose: bool = True,
) -> List[ExperimentRow]:
    algos = algorithms or algorithm_registry()
    rows: list[ExperimentRow] = []
    sizes_list = list(sizes)
    total_runs = len(sizes_list) * len(algos)
    run_idx = 0

    if verbose:
        print("=== Lights Out - experimentos ===", file=sys.stderr, flush=True)
        print(f"Tabuleiros: {', '.join(f'{s}x{s}' for s in sizes_list)}", file=sys.stderr, flush=True)
        print(f"Algoritmos: {', '.join(algos.keys())}", file=sys.stderr, flush=True)
        print(f"Estado inicial: {initial_mode} (seed={initial_seed})", file=sys.stderr, flush=True)
        print(
            f"Limites: ate {max_expansions} expansoes, ate {max_wall_time_sec:.1f}s de parede por execucao.",
            file=sys.stderr,
            flush=True,
        )
        print(f"Total de execucoes: {total_runs}. Aguarde...\n", file=sys.stderr, flush=True)

    for size in sizes_list:
        if verbose:
            print(f"--- Tamanho {size}x{size} ---", file=sys.stderr, flush=True)
        for name, fn in algos.items():
            run_idx += 1
            if verbose:
                print(
                    f"  [{run_idx}/{total_runs}] Rodando {name!r} em {size}x{size}...",
                    file=sys.stderr,
                    flush=True,
                )
            # Um objeto de limites NOVO por execucao (tempo/expansao nao "vazam" entre algoritmos).
            limits = SearchLimits.from_budgets(
                max_expansions=max_expansions,
                max_wall_time_sec=max_wall_time_sec,
            )
            row = run_single(
                name,
                fn,
                size,
                limits,
                initial_mode=initial_mode,
                initial_seed=initial_seed,
            )
            rows.append(row)
            if verbose:
                pl = "(nenhum)" if row.path_len is None else str(row.path_len)
                print(
                    f"      -> fim: {row.termination.value} | "
                    f"passos={pl} | expandidos={row.nodes_expanded} | "
                    f"tempo={row.wall_time_sec:.4f}s",
                    file=sys.stderr,
                    flush=True,
                )
        if verbose:
            print(file=sys.stderr, flush=True)

    if verbose:
        print("=== Concluido. Resultados (tabela) abaixo ===\n", file=sys.stderr, flush=True)

    return rows


TableFormat = Literal["pretty", "tsv", "csv"]

# Cabecalhos em portugues (mesma ordem que row_cells)
TABLE_HEADERS_PT: Tuple[str, ...] = (
    "Algoritmo",
    "N (tabuleiro NxN)",
    "Resultado",
    "Passos solucao",
    "Nos expandidos",
    "Max fronteira",
    "Tempo (s)",
    "Memoria pico (bytes)",
)


def row_cells(r: ExperimentRow) -> List[str]:
    """Uma linha da tabela de resultados como texto (para TSV/CSV/pretty)."""
    return [
        r.algorithm,
        str(r.size),
        r.termination.value,
        "" if r.path_len is None else str(r.path_len),
        str(r.nodes_expanded),
        str(r.max_frontier),
        f"{r.wall_time_sec:.6f}",
        str(r.peak_traced_memory_bytes),
    ]


def _memory_footer() -> str:
    return (
        "# Memoria pico (bytes): maior pico observado pelo tracemalloc do Python durante a busca.\n"
        "# Nao e a memoria total do processo (Gerenciador de Tarefas); e um indicador aproximado de alocacao em heap.\n"
    )


def _stdout_supports(text: str) -> bool:
    """Retorna True se a codificacao atual de stdout consegue representar `text`."""
    enc = sys.stdout.encoding
    if not enc:
        return False
    try:
        text.encode(enc)
        return True
    except (LookupError, UnicodeEncodeError):
        return False


def _format_pretty(headers: Tuple[str, ...], data: List[ExperimentRow]) -> str:
    """Tabela alinhada com separadores ASCII (bom para ler no terminal)."""
    rows_cells: list[list[str]] = [list(headers), *[row_cells(r) for r in data]]
    widths = [
        max(len(rows_cells[r][c]) for r in range(len(rows_cells)))
        for c in range(len(headers))
    ]

    def line(vals: list[str]) -> str:
        return " | ".join(vals[i].ljust(widths[i]) for i in range(len(headers)))

    sep = "-+-".join("-" * widths[i] for i in range(len(headers)))
    out_lines = [line(rows_cells[0]), sep, *[line(rows_cells[i]) for i in range(1, len(rows_cells))]]
    return "\n".join(out_lines) + "\n\n" + _memory_footer()


def format_table(rows: Iterable[ExperimentRow], fmt: TableFormat = "pretty") -> str:
    """
    Formata a tabela final.

    - pretty: colunas alinhadas + rodape explicando a memoria.
    - tsv: TAB entre colunas (colar no Excel/Sheets costuma separar colunas).
    - csv: separador ';' + BOM UTF-8 (costuma abrir bem no Excel em PT-BR).
    """
    data = list(rows)
    headers = list(TABLE_HEADERS_PT)
    include_footer = sys.stdout.isatty()

    if fmt == "tsv":
        lines = ["\t".join(headers), *("\t".join(row_cells(r)) for r in data)]
        body = "\n".join(lines) + "\n"
        if include_footer:
            return body + "\n" + _memory_footer()
        return body

    if fmt == "csv":
        buf = StringIO()
        writer = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(headers)
        for r in data:
            writer.writerow(row_cells(r))
        body = buf.getvalue() + "\n"
        foot = _memory_footer() if include_footer else ""
        # BOM UTF-8: util ao redirecionar para arquivo e abrir no Excel; no console pode atrapalhar
        prefix = "\ufeff" if (not sys.stdout.isatty() and _stdout_supports("\ufeff")) else ""
        return prefix + body + foot

    return _format_pretty(tuple(headers), data)

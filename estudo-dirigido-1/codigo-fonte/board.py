"""
Lights Out: representacao do tabuleiro e transicoes (cliques).

Separado dos algoritmos de busca: apenas codificacao de estado, aplicacao de acoes
e construcao de estados iniciais.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterator, Tuple


def goal_mask(size: int) -> int:
    """Mascara de bits com todas as N*N celulas acesas (valor binário 1)."""
    cells = size * size
    return (1 << cells) - 1


def all_lights_off(size: int) -> int:
    """Estado inicial com todas as luzes apagadas."""
    return 0


def random_initial_state(size: int, seed: int | None = None) -> int:
    """Estado inicial aleatorio reprodutivel com `seed`."""
    rng = random.Random(seed)
    cells = size * size
    return rng.getrandbits(cells)


def neighbor_indices(size: int, action: int) -> Tuple[int, ...]:
    """
    Retorna os indices lineares (ordem linha a linha) que um clique em `action` altera:
    a propria celula e os vizinhos ortogonais dentro do tabuleiro.
    """
    row, col = divmod(action, size)
    out: list[int] = []
    for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):   # dr = delta row, dc = delta col, nr = new row, nc = new col
        nr = row + dr
        nc = col + dc
        # filtra indices fora do tabuleiro (ex: clique na borda nao tem vizinho para fora)
        if 0 <= nr < size and 0 <= nc < size:
            out.append(nr * size + nc)
    return tuple(out)


def apply_click(size: int, state: int, action: int) -> int:
    """Aplica um clique: XOR (inverter bit) em cada indice afetado."""
    new_state = state
    for idx in neighbor_indices(size, action):
        new_state ^= 1 << idx
    return new_state


def is_goal(size: int, state: int) -> bool:
    """Verdadeiro se todas as luzes estao acesas (igual a goal_mask)."""
    return state == goal_mask(size)


def mismatch_count(size: int, state: int) -> int:
    """Quantas celulas diferem do objetivo 'todas acesas' (distancia de Hamming ao objetivo)."""
    return (state ^ goal_mask(size)).bit_count()


def iter_actions(size: int) -> Iterator[int]:
    """Acoes possiveis: indices 0 .. N*N-1 (um clique por celula)."""
    yield from range(size * size)


@dataclass(frozen=True)
class LightsOutProblem:
    """
    Visao do problema para a busca: estado inicial, transicoes e heuristica.

    A busca depende desta API pequena (e de funcoes puras em `board`) para nao
    misturar regras do jogo com filas/pilhas/heaps.
    """

    size: int
    initial_state: int

    def goal_state_mask(self) -> int:
        return goal_mask(self.size)

    def is_goal(self, state: int) -> bool:
        return is_goal(self.size, state)

    def actions(self) -> Tuple[int, ...]:
        return tuple(iter_actions(self.size))

    def step(self, state: int, action: int) -> int:
        return apply_click(self.size, state, action)

    def heuristic(self, state: int) -> int:
        return mismatch_count(self.size, state)

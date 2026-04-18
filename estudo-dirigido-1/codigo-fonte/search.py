"""
Estrategias de busca (cega, informada e local) para um espaco de estados deterministico.

Exige a API de `LightsOutProblem`: initial_state, is_goal, actions, step, heuristic.
"""

from __future__ import annotations

import heapq
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from board import LightsOutProblem


class TerminationReason(str, Enum):
    SUCCESS = "success"
    NO_SOLUTION = "no_solution"
    EXPANSION_LIMIT = "expansion_limit"
    TIME_LIMIT = "time_limit"


@dataclass(frozen=True)
class SearchLimits:
    """Limites praticos para encerrar buscas grandes (expansoes e tempo de parede)."""

    max_expansions: int
    max_wall_time_sec: float
    start_time_perf: float

    @classmethod
    def from_budgets(cls, max_expansions: int, max_wall_time_sec: float) -> "SearchLimits":
        return cls(
            max_expansions=max_expansions,
            max_wall_time_sec=max_wall_time_sec,
            start_time_perf=time.perf_counter(),
        )

    def poll(self, expansions_done: int) -> Optional[TerminationReason]:
        if expansions_done >= self.max_expansions:
            return TerminationReason.EXPANSION_LIMIT
        if (time.perf_counter() - self.start_time_perf) >= self.max_wall_time_sec:
            return TerminationReason.TIME_LIMIT
        return None


@dataclass(frozen=True)
class SearchOutcome:
    path: Optional[List[int]]
    nodes_expanded: int
    max_frontier: int
    termination: TerminationReason


def _reconstruct_path(
    goal: int,
    parent: Dict[int, Optional[int]],
    action_from_parent: Dict[int, int],
) -> List[int]:
    """Reconstroi a sequencia de cliques a partir dos mapas de pai/acao do BFS."""
    path_rev: list[int] = []
    cur = goal
    while parent[cur] is not None:
        prev = parent[cur]
        assert prev is not None
        path_rev.append(action_from_parent[cur])
        cur = prev
    path_rev.reverse()
    return path_rev


def breadth_first_search(problem: LightsOutProblem, limits: SearchLimits) -> SearchOutcome:
    start = problem.initial_state
    if problem.is_goal(start):
        return SearchOutcome([], 0, 1, TerminationReason.SUCCESS)

    q: deque[int] = deque([start])
    parent: Dict[int, Optional[int]] = {start: None}
    action_from_parent: Dict[int, int] = {}
    expanded = 0
    max_frontier = len(q)

    while q:
        term = limits.poll(expanded)
        if term is not None:
            return SearchOutcome(None, expanded, max_frontier, term)

        state = q.popleft()
        expanded += 1
        term = limits.poll(expanded)
        if term is not None:
            return SearchOutcome(None, expanded, max_frontier, term)

        if problem.is_goal(state):
            return SearchOutcome(
                _reconstruct_path(state, parent, action_from_parent),
                expanded,
                max_frontier,
                TerminationReason.SUCCESS,
            )

        for action in problem.actions():
            term = limits.poll(expanded)
            if term is not None:
                return SearchOutcome(None, expanded, max_frontier, term)
            nxt = problem.step(state, action)
            if nxt not in parent:
                parent[nxt] = state
                action_from_parent[nxt] = action
                q.append(nxt)
        max_frontier = max(max_frontier, len(q))

    return SearchOutcome(None, expanded, max_frontier, TerminationReason.NO_SOLUTION)


def depth_first_search(problem: LightsOutProblem, limits: SearchLimits) -> SearchOutcome:
    """
    DFS iterativo com conjunto `visited` para nao reprocessar o mesmo estado.
    Nao garante solucao de custo minimo (profundidade pode ser maior que a otima).
    """
    start = problem.initial_state
    if problem.is_goal(start):
        return SearchOutcome([], 0, 1, TerminationReason.SUCCESS)

    stack: list[tuple[int, list[int]]] = [(start, [])]
    visited: set[int] = set()
    expanded = 0
    max_frontier = len(stack)

    while stack:
        term = limits.poll(expanded)
        if term is not None:
            return SearchOutcome(None, expanded, max_frontier, term)

        state, path = stack.pop()
        if state in visited:
            continue
        visited.add(state)
        expanded += 1
        term = limits.poll(expanded)
        if term is not None:
            return SearchOutcome(None, expanded, max_frontier, term)

        if problem.is_goal(state):
            return SearchOutcome(path, expanded, max_frontier, TerminationReason.SUCCESS)

        for action in reversed(problem.actions()):
            term = limits.poll(expanded)
            if term is not None:
                return SearchOutcome(None, expanded, max_frontier, term)
            nxt = problem.step(state, action)
            if nxt not in visited:
                stack.append((nxt, path + [action]))
        max_frontier = max(max_frontier, len(stack))

    return SearchOutcome(None, expanded, max_frontier, TerminationReason.NO_SOLUTION)


def greedy_best_first_search(problem: LightsOutProblem, limits: SearchLimits) -> SearchOutcome:
    """Busca gulosa: prioriza estados com menor h(s) (melhor primeiro, sem garantia de otimalidade)."""
    start = problem.initial_state
    if problem.is_goal(start):
        return SearchOutcome([], 0, 1, TerminationReason.SUCCESS)

    counter = 0  # desempate estavel na heap do Python
    open_heap: list[tuple[int, int, int, list[int]]] = []
    heapq.heappush(open_heap, (problem.heuristic(start), counter, start, []))
    counter += 1

    visited: set[int] = set()
    expanded = 0
    max_frontier = len(open_heap)

    while open_heap:
        term = limits.poll(expanded)
        if term is not None:
            return SearchOutcome(None, expanded, max_frontier, term)

        _, _, state, path = heapq.heappop(open_heap)
        if state in visited:
            continue
        visited.add(state)
        expanded += 1
        term = limits.poll(expanded)
        if term is not None:
            return SearchOutcome(None, expanded, max_frontier, term)

        if problem.is_goal(state):
            return SearchOutcome(path, expanded, max_frontier, TerminationReason.SUCCESS)

        for action in problem.actions():
            term = limits.poll(expanded)
            if term is not None:
                return SearchOutcome(None, expanded, max_frontier, term)
            nxt = problem.step(state, action)
            if nxt in visited:
                continue
            h = problem.heuristic(nxt)
            heapq.heappush(open_heap, (h, counter, nxt, path + [action]))
            counter += 1
        max_frontier = max(max_frontier, len(open_heap))

    return SearchOutcome(None, expanded, max_frontier, TerminationReason.NO_SOLUTION)


def a_star_search(problem: LightsOutProblem, limits: SearchLimits) -> SearchOutcome:
    """A*: ordena por f = g + h; `best_g` descarta entradas obsoletas na fila de prioridade."""
    start = problem.initial_state
    if problem.is_goal(start):
        return SearchOutcome([], 0, 1, TerminationReason.SUCCESS)

    counter = 0
    start_g = 0
    start_f = start_g + problem.heuristic(start)
    open_heap: list[tuple[int, int, int, int, list[int]]] = []
    heapq.heappush(open_heap, (start_f, counter, start_g, start, []))
    counter += 1

    best_g: Dict[int, int] = {start: start_g}
    expanded = 0
    max_frontier = len(open_heap)

    while open_heap:
        term = limits.poll(expanded)
        if term is not None:
            return SearchOutcome(None, expanded, max_frontier, term)

        f, _, g, state, path = heapq.heappop(open_heap)
        if g != best_g.get(state, 10**18):
            continue

        expanded += 1
        term = limits.poll(expanded)
        if term is not None:
            return SearchOutcome(None, expanded, max_frontier, term)

        if problem.is_goal(state):
            return SearchOutcome(path, expanded, max_frontier, TerminationReason.SUCCESS)

        for action in problem.actions():
            term = limits.poll(expanded)
            if term is not None:
                return SearchOutcome(None, expanded, max_frontier, term)
            nxt = problem.step(state, action)
            ng = g + 1
            if ng >= best_g.get(nxt, 10**18):
                continue
            best_g[nxt] = ng
            nf = ng + problem.heuristic(nxt)
            heapq.heappush(open_heap, (nf, counter, ng, nxt, path + [action]))
            counter += 1
        max_frontier = max(max_frontier, len(open_heap))

    return SearchOutcome(None, expanded, max_frontier, TerminationReason.NO_SOLUTION)


def hill_climbing(problem: LightsOutProblem, limits: SearchLimits, max_sideways_steps: int = 50_000) -> SearchOutcome:
    """
    Subida de encosta (vizinho mais `promissor` pela heuristica).
    Pode parar em otimo local -> termination NO_SOLUTION.
    """
    current = problem.initial_state
    path: list[int] = []
    expanded = 0
    max_frontier = 1

    for _ in range(max_sideways_steps):
        term = limits.poll(expanded)
        if term is not None:
            return SearchOutcome(None, expanded, max_frontier, term)

        if problem.is_goal(current):
            return SearchOutcome(path, expanded, max_frontier, TerminationReason.SUCCESS)

        current_h = problem.heuristic(current)
        best_action: Optional[int] = None
        best_h = current_h
        best_next_state: Optional[int] = None

        for action in problem.actions():
            nxt = problem.step(current, action)
            h = problem.heuristic(nxt)
            expanded += 1
            term = limits.poll(expanded)
            if term is not None:
                return SearchOutcome(None, expanded, max_frontier, term)
            if h < best_h:
                best_h = h
                best_action = action
                best_next_state = nxt

        if best_action is None or best_next_state is None:
            return SearchOutcome(None, expanded, max_frontier, TerminationReason.NO_SOLUTION)

        path.append(best_action)
        current = best_next_state

    return SearchOutcome(None, expanded, max_frontier, TerminationReason.EXPANSION_LIMIT)

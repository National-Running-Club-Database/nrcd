"""Run many enrich API jobs; optional parallelism with per-item results."""

from __future__ import annotations

import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Generic, Iterable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


@dataclass(frozen=True)
class JobResult(Generic[R]):
    job_id: str
    ok: bool
    value: R | None = None
    error: str | None = None


@dataclass(frozen=True)
class EnrichJob(Generic[R]):
    """One unit of work (e.g. one meet altitude or one course weather row)."""

    job_id: str
    run: Callable[[], R]

    def execute(self) -> JobResult[R]:
        try:
            return JobResult(job_id=self.job_id, ok=True, value=self.run())
        except Exception as e:
            return JobResult(
                job_id=self.job_id,
                ok=False,
                error=f"{type(e).__name__}: {e}",
            )


def run_enrich_jobs(
    jobs: Iterable[EnrichJob[R]],
    *,
    parallel: int = 1,
    on_result: Callable[[JobResult[R]], None] | None = None,
) -> list[JobResult[R]]:
    """Execute jobs; process each result as it finishes (parallel or sequential).

    Parameters
    ----------
    parallel
        ``1`` = one job at a time (safest for rate limits). ``>1`` uses a thread pool
        but still invokes ``on_result`` once per completed job (order varies).
    on_result
        Called immediately when each job completes (success or failure).
    """
    job_list = list(jobs)
    if not job_list:
        return []

    results: list[JobResult[R]] = []

    def _emit(res: JobResult[R]) -> None:
        results.append(res)
        if on_result is not None:
            on_result(res)

    if parallel <= 1:
        for job in job_list:
            _emit(job.execute())
        return results

    with ThreadPoolExecutor(max_workers=parallel) as pool:
        future_map = {pool.submit(job.execute): job.job_id for job in job_list}
        for future in as_completed(future_map):
            try:
                res = future.result()
            except Exception as e:
                jid = future_map[future]
                res = JobResult(
                    job_id=jid,
                    ok=False,
                    error=f"{type(e).__name__}: {e}\n{traceback.format_exc()}",
                )
            _emit(res)

    return results

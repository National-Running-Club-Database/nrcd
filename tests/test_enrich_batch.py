from nrcd.enrich.batch import EnrichJob, run_enrich_jobs


def test_run_enrich_jobs_sequential():
    jobs = [
        EnrichJob(job_id="a", run=lambda: 1),
        EnrichJob(job_id="b", run=lambda: 2),
    ]
    results = run_enrich_jobs(jobs, parallel=1)
    assert len(results) == 2
    assert all(r.ok for r in results)
    assert {r.value for r in results} == {1, 2}


def test_run_enrich_jobs_captures_error():
    def boom():
        raise ValueError("fail")

    jobs = [EnrichJob(job_id="x", run=boom)]
    results = run_enrich_jobs(jobs)
    assert len(results) == 1
    assert not results[0].ok
    assert "ValueError" in (results[0].error or "")

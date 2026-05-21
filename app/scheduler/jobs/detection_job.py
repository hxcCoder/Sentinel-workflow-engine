async def run_detection_cycle():
    try:
        async with AsyncSessionLocal() as db:
            rules = [
                AuthBruteforceRule(threshold=5),
                SuspiciousRefreshRule(threshold=8, critical_threshold=20),
            ]
            engine = DetectionEngine(rules=rules)
            findings = await engine.run(
                db=db,
                start_time=datetime.now(timezone.utc) - timedelta(minutes=5),
                end_time=datetime.now(timezone.utc),
            )
            if findings:
                await AlertService(db).upsert_many(findings)
    except Exception:
        logger.exception("Detection cycle failed")
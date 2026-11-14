# CatalystRadar private research data
Owner-only personal research. Licensed raw daily prices stay in this private repository, never mirrored to the public dashboard, public artifacts or logs. Base64 preserves response bytes, **not encryption**; privacy depends on GitHub private-repository access. No brokerage or trades.

Collector: 10 initial research symbols plus SPY, compact100 raw daily rows per successful response. Preserves exact bytes, SHA256, actual retrieval time, revisions and source/schema flags. This is not historical point-in-time knowledge, full-market coverage, adjusted/total-return data or official auction prices. No forecast model or performance is claimed.

One consumer only. Private collector verifies owner-only access and a reviewed retired public-workflow hash, checks no outstanding public runs, and counts public+private run activity reservations over24hours before requests. At most22reserved calls inside this system (11per run); other external use of the same key is unknown. Retries/redirects disabled,13second pacing, and all errors sanitized. Schedule bounded Nov16–21,2026, runtime gate Nov14–21. No new spending or paid plan.

Data commit requires privacy recheck and nonforce push. A failed/partial run does not publish incomplete data; ephemeral partial files are discarded. Run reservation still counts after failure. Concurrent repository changes may safely reject the push without repeating provider calls. No secrets in Git; key supplied only by Actions secret.

Terms: https://www.alphavantage.co/terms_of_service/ permits private individual investment research, not commercial/public redistribution. Re-evaluate licensing before selling or sharing market-derived products. Raw prices and unsupported actions cannot unlock the separate paper engine.

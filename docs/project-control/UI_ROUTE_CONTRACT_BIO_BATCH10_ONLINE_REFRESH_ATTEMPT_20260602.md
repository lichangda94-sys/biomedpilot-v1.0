# Bioinformatics Batch 10 Online Refresh Attempt

- date: `2026-06-02`
- branch: `integration/release-bio-c1-ui-shell`
- head: `4a0577982b6c87645f6d1a0bac0adbd56728f7b0`
- scope: Refresh GEO online retrieval live-click evidence for `GSE6004` and `GSE153659`.

## Attempted Command

`QT_QPA_PLATFORM=offscreen python3 scripts/ui_route_contract_bio_batch10_geo_online_retrieval.py`

## Result

The current refresh attempt did not complete. The first GEO accession request failed at the network/proxy layer:

`Failed to fetch GEO accession page for GSE6004: HTTPSConnectionPool(host='www.ncbi.nlm.nih.gov', port=443): Max retries exceeded with url: /geo/query/acc.cgi?acc=GSE6004&targ=self&form=text&view=quick (Caused by ProxyError('Unable to connect to proxy', RemoteDisconnected('Remote end closed connection without response')))`

The validation process remained waiting on network I/O after the proxy failure and was stopped manually to avoid leaving a hung test runner.

## Evidence Handling

- The existing `docs/project-control/UI_ROUTE_CONTRACT_BIO_BATCH10_GEO_ONLINE_RETRIEVAL.*` reports remain prior passing online evidence from head `dc55902228f5`.
- The failed partial refresh changed only transient screenshots for `GSE6004`; those partial screenshot changes were restored and are not part of this evidence update.
- `UI_ROUTE_CONTRACT_BIO_C1_CLOSURE_MATRIX.*` now flags stale input batches so Batch 10 is not mistaken for current-HEAD regenerated evidence.

## Follow-Up

Rerun the Batch 10 script when NCBI GEO access is available through the current network/proxy path. A successful rerun must regenerate the Batch 10 JSON/Markdown and screenshots before the online GEO evidence can be treated as current-HEAD proof.

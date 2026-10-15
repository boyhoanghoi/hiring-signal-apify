# hiring-signal: launch verification

Verified 16 October 2026 (Asia/Saigon).

- Public Store: https://apify.com/reliable_quatrain/greenhouse-lever-ashby-jobs-hiring-signal
- GitHub: https://github.com/boyhoanghoi/hiring-signal-apify
- Actor ID: `2VTBeCh22BK3amvDJ`; build `0.1.1` / `T72cZc6bICBXkA1sD` succeeded.
- 22 meaningful Python unit tests passed in the standalone virtual environment.
- Official Apify CLI validated input, dataset and output schemas.
- Active single pay-per-event price: USD 0.0015 per `job-saved`.
- Unauthenticated public Actor metadata returned isPublic=true; the public Store URL returned HTTP 200 with the expected title.

## Cloud integration checks

1. Run `6fbnLvEU9xgDEu26A` succeeded: 3 dataset rows, 3 `job-saved` events.
   All three provider feeds succeeded; one job was saved per board. Board coverage was correctly marked partial due to the sample cap.
2. Run `r1SzqsTWEOhdCIhpb` reused known IDs: 3 old keys skipped, 3 different jobs saved and charged.
   Dataset job keys were checked against the previous known-ID array; no previously saved key was billed again.

Observed platform usage for these small owner-run samples: USD 0.0005058847409801351 and USD 0.0005413650514400669. These measurements do not predict all sources, batch sizes or customer costs.

Owner tests are not customer revenue. No first customer or payout is claimed. No promotional messages were sent.

## Artwork and recurring workflows

Upload `assets/brand/icon-512.png` under [Publishing / Display information](https://console.apify.com/actors/2VTBeCh22BK3amvDJ/publication) to replace the default Actor icon. The PNG and editable SVG are in the repository.

[Vietnamese workflow guide](WORKFLOW_COOKBOOK_VI.md) explains explicit state handoff. A fixed scheduled input does not automatically reload state. [Market research](MARKET.md) records observed demand, alternatives and scope differences.

# Re-entry checklist

A future refresh promotion may re-enter v2.26E only when:

- [ ] 14/14 providers have been replayed, or any exclusion has an explicit documented waiver.
- [ ] Every expected row has a disposition: retained, added, removed, changed, quarantined, or waived.
- [ ] An immutable candidate CSV exists.
- [ ] Candidate row count and SHA-256 are recorded and independently verified.
- [ ] Identity keys are unique under the v2.26C primary/fallback strategy.
- [ ] Real added, removed, and changed sets have been classified.
- [ ] Quality bounds and metadata non-regression checks pass.
- [ ] v2.26D rollback controls remain valid.
- [ ] The branch head and pointer are re-read immediately before an atomic fast-forward write.
- [ ] No scoring authorization is inferred from universe promotion.

Until every blocking item passes, the operational pointer must remain unchanged.

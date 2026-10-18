# Concept resolution overrides

Concept resolution (mapping a filer's actual XBRL tag names onto the canonical
metrics in `config/metrics/canonical.yaml`) is LLM-assisted and cached per
company. If a mapping is wrong, pin the correct one here rather than patching
output after the fact, see docs/ARCHITECTURE.md §5.

One file per CIK: `{cik}.yaml`, e.g. `0000320193.yaml` for Apple.

```yaml
# 0000320193.yaml
revenue: RevenueFromContractWithCustomerExcludingAssessedTax
net_income: NetIncomeLoss
```

An override here always wins over the LLM-assisted mapping, and is never
re-resolved. Empty by default, populated only when a specific filer's mapping
needs correcting.

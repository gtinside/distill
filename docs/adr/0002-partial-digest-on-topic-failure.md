# Partial Digest Delivery on Topic Card Failure

When one or more Topic Cards fail to generate (Exa.ai returns no results, or Claude times out), the Digest is still pushed to the user with the failed cards shown in an error state rather than withholding the entire Digest. Each Topic Card is retried up to 3 times before being marked failed. This matches the decision to make Topic Cards independently refreshable — a single bad Topic should not ruin the rest of the Digest. Failed cards surface a manual refresh tap so the user can retry on demand.

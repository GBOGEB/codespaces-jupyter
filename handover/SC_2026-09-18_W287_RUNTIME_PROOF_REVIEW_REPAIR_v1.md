# W287 lossless handover — runtime proof review repair

The original W286 PR #3 merged at
`98fedcf1147e5bb53e5f833b8a1c5cebb6ded3f9`, but its first runtime attempt
`35360464702` obtained a real runner and failed before notebook execution
because `torchvision==0.21.0` required `torch==2.6.0` while the repository
pinned `torch==2.7.1`.

Codex review also identified four proof-integrity gaps: local dirty trees could
claim an old SHA, rich outputs only hashed `text/plain`, PR checkout used the
synthetic merge ref, and generated probe artifacts dirtied the next local sync.

W287 repairs all five items:

1. aligns `torch==2.7.1` with `torchvision==0.22.1`;
2. adds `requirements-probe.txt` so CI proof does not install unrelated heavy packages;
3. rejects missing/dirty Git source before runtime proof;
4. hashes all MIME representations in rich notebook output;
5. checks out the exact PR head and ignores generated probe receipts locally.

The next gate is one fresh exact-head GitHub Actions run with a real runner,
more than zero executed code cells in both passes, equal all-MIME output digests,
and an uploaded receipt bound to the candidate SHA.

No engineering or domain-validation authority is transferred.

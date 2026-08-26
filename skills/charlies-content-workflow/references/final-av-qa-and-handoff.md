# Final AV QA and Handoff

Read this reference against every final language master. Final compiled output,
not preview alone, is the proof.

## Compiled-output QA

For each final file:

1. Full-decode the complete file and fail on any decode error.
2. Use `ffprobe` or an equivalent structured probe to record streams,
   dimensions, frame rate, duration, codecs, pixel format, audio layout, and
   language/master identity.
3. Measure integrated loudness and true peak after final encode against the
   configured delivery target.
4. Verify A/V sync at the beginning, representative middle sections, and end.
5. Verify captions cover all speech, match the correct language, stay within
   two lines, remain readable, and avoid the presenter's face.
6. Inspect real frames or contact sheets around every transition, evidence
   change, caption mode, and layout change.
7. Scan for black frames, blank renders, stale labels, clipping, illegible
   text, obsolete claims, frozen footage, and unintended private details.
8. Reconcile every visible and spoken claim with the final claim ledger,
   allowed wording, evidence, caveat, scope, and current freshness deadline.

When preview and render diverge, the compiled path fails. Reduce it, fix it,
full-decode again, and retain a regression proof for the divergence.

## Integrity and Provenance

Preserve hashes for original recordings, source evidence, benchmark manifests,
project files, and final masters. Record the exact command or tool version used
for the final encode. If only audio is remuxed, hash or compare the video stream
to verify video-stream identity rather than assuming it remained unchanged.

Never place private recordings, raw benchmark logs, credentials, or unpublished
masters in a public repository. The public handoff may reference approved-safe
artifacts while private evidence remains in its authorized storage boundary.

## Handoff

Deliver or report, as applicable:

- separately identified English and Spanish masters;
- stream/probe, full-decode, loudness, sync, caption, transition, and frame-scan
  QA artifacts;
- final claim ledger and source/evidence map;
- source, project, and final hashes plus the benchmark manifest when used;
- production state, missing material, blocked claims, and known limitations;
  and
- remaining publication actions and the authority required for each.

Use exact local or approved storage paths and explicit readiness states. Do not
claim a master exists when only a project, preview, or partial render exists.

## Publication Authority Boundary

Production completion does not authorize publishing. Hosting, uploads, social
posts, scheduling, Notion sharing, DMs, and external messages remain separate
authority gates. Stop after the requested handoff unless the user grants that
specific external action.

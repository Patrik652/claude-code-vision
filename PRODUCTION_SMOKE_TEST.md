# Production Smoke Test

This checklist is for final pre-deploy verification on Linux hosts.

## Preconditions

- Python virtualenv is created at `.venv`
- Config file exists at `~/.config/claude-code-vision/config.yaml`
- Screenshot tooling is installed for your target desktop:
  - X11: `scrot`, `xrectsel`
  - Wayland: `grim`, `slurp`
- API credentials are configured (`Claude` OAuth or `Gemini` API key)

## Automated Smoke Run

```bash
./scripts/smoke_test.sh
```

Expected result: final line `[smoke] PASS`.

## Manual Runtime Checks (Target Host)

1. Run `/vision "What do you see?"` and confirm response arrives.
2. Run `/vision.area --coords "100,100,300,200" "Describe this region"` and confirm response.
3. Run `/vision.auto --interval 10`, wait for at least one cycle, then `/vision.stop`.
4. Verify no persistent screenshot artifacts remain under `/tmp/claude-vision` (unless configured otherwise).

## Rollback Plan

If smoke checks fail after deployment:

1. Roll back to previous known-good commit/tag in your deployment environment.
2. Restore previous config backup:
   - `~/.config/claude-code-vision/config.yaml`
3. Re-run minimal health checks:
   - `claude-vision --doctor`
   - one `/vision` command
4. Open incident note with:
   - failing command
   - exact stderr/output
   - host display type (`X11`/`Wayland`)
   - commit hash currently deployed

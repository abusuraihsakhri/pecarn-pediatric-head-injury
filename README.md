# PECARN Pediatric Head Injury

An age-specific reference implementation of the **PECARN pediatric minor blunt head trauma clinical decision rules**, based on Kuppermann et al. (2009). It categorizes eligible assessments into **very-low**, **intermediate**, and **high-risk** decision-rule branches. PECARN is **not a numerical score**, an individual patient risk calculator, or a diagnosis.

This project includes an offline browser interface, a zero-third-party-dependency Python rule module, CSV assessment, and an optional FastAPI HTTP endpoint.

## Browser application

Open `web/index.html` directly in a modern browser; no Python installation, server, account, or network request is needed to calculate a result. A GitHub Pages deployment workflow is included, but a public URL should only be published after a successful live deployment check.

1. Enter the child's age in months, Glasgow Coma Scale (14 or 15), and hours since injury.
2. Confirm there are no PECARN study exclusions or special populations.
3. Answer all displayed examination/history criteria (the form changes at 24 months).
4. Review the decision-rule category, relevant predictors, and CT guidance.

**Scope:** Children under 18 years presenting within 24 hours of nontrivial blunt head trauma with GCS 14–15. Do not use the rule for penetrating injury, trivial asymptomatic trauma, significant pre-existing neurological disorders complicating assessment, brain tumours, prior outside-hospital imaging, ventricular shunts or bleeding disorders. GCS below 14 is outside this rule. Infants under 3 months and evolving symptoms warrant particular caution.

**Interpretation:** High-risk findings lead to a CT recommendation in the original PECARN algorithm. Intermediate risk calls for observation versus CT in context. Very-low risk generally does not require CT in an otherwise eligible child. No output provides a patient-specific ciTBI probability. All decisions require qualified clinical assessment.

## Python / CLI

Requires Python 3.10 or newer.

```bash
python -m pip install -e ".[all]"
pecarn single \
  --age-months 72 --gcs 15 --hours-since-injury 2 \
  --exclusion-present no --altered-mental-status no \
  --severe-mechanism no --basilar-skull-fracture-signs no \
  --any-loss-of-consciousness no --vomiting yes --severe-headache no
```

Alternatively, without installing dependencies, use `python pecarn_rule.py single ...`.

Batch processing (anonymous structured data only):

```bash
pecarn batch -i sample.csv -o results.csv
```

The input CSV uses `age_months`, `gcs`, `hours_since_injury`, `exclusion_present`, `altered_mental_status`, `severe_mechanism`, and applicable age-specific yes/no fields. See `sample.csv`. Irrelevant age-group cells are blank. Input data must contain no patient identifiers; extra CSV fields are rejected. Missing or ambiguous findings fail validation rather than being treated as negative.

Python API: `pecarn_rule.calculate_metrics(**case)` returns `risk_tier`, `age_group`, `predictors_present` and `ct_guidance` (no invented numeric score).

## HTTP API and legacy demonstration components

```bash
python -m pip install -e ".[web]"
pecarn-ops serve --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` for the same static application. The `POST /api/pecarn` endpoint accepts a JSON object with the clinical fields described above and validates them; `/docs` exposes the generated FastAPI schema. The static UI does **not** call the API.

The repository retains the older `pecarn-ops` demonstration CLI, `/api/audit`, `/api/chat`, `enrichment.py`, and related workers/tests for compatibility. **Their arbitrary numerical thresholds, simulated alerts, generic enrichment recommendations, and mock language output are not PECARN calculations, clinically validated functions, or autonomous clinical workflows.** Do not use them for patient care.

To start the optional Docker service:

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

The key is supplied at runtime, not committed. Previous versions included a static value in Docker Compose: rotate it in any installation that used it. The legacy identifier filter is pattern-based and does not ensure de-identification or HIPAA compliance; its HMAC log is process-local and not a durable clinical audit record.

## Privacy, compatibility, and testing

- Browser calculations are local JavaScript. The static interface has no analytics, server calls, cookies, or persistence. Do not enter names, dates of birth, identifiers, or other PHI.
- Python CSV assessments process local files. The optional API receives supplied JSON, so do not send identifiable patient data to an unsecured deployment.
- Modern Chromium, Firefox, and Safari browsers are supported by the JavaScript syntax; legacy browsers are not targeted. No Pyodide/PyScript is required because the small deterministic rule is implemented natively in the browser.
- Run `python -m pytest -q` for Python, clinical, API, and legacy compatibility tests; run `node --test web/app.test.cjs` for the browser rule (Node.js 22 in CI). GitHub Actions tests Python 3.10–3.13 and the standalone static app.
- Deployment: `.github/workflows/pages.yml` publishes the static `web/` application to GitHub Pages when Pages is enabled and the workflow succeeds. No backend executes on GitHub Pages.

## Clinical sources

- Kuppermann N, et al. Identification of children at very low risk of clinically-important brain injuries after head trauma: a prospective cohort study. *Lancet*. 2009;374:1160–1170. [doi:10.1016/S0140-6736(09)61558-0](https://doi.org/10.1016/S0140-6736(09)61558-0). See Figure 3 for the age-specific CT decision branches.
- [CDC Clinical Guidance for Pediatric Mild TBI](https://www.cdc.gov/traumatic-brain-injury/hcp/clinical-guidance/pediatric-mtbi.html).

This reference software has **not** undergone independent external clinical validation, medical-device regulatory evaluation, or assessment for autonomous clinical use.

## License

MIT. See [LICENSE](LICENSE).

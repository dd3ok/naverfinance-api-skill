# Release Checklist

Use this checklist before publishing or merging release-oriented changes to this skill.

- [ ] `SKILL.md` frontmatter has a short trigger-focused description for public, read-only Naver Finance/Npay Stock data.
- [ ] README install paths mention `$HOME/.agents/skills` for user installs and `.agents/skills/naverfinance-web-api/` for repository-scoped installs.
- [ ] Public prompts and metadata do not depend on the `$naverfinance-web-api` selector.
- [ ] Safety docs and helper code block login, MY, account, order, holding, balance, payment, cookie, token, and other sensitive endpoints.
- [ ] `request_bytes()` host and sensitive marker guards still cover all shared HTTP helpers.
- [ ] CI runs `ruff format --check .`, `ruff check .`, `compileall`, script `--help`, and `scripts/selftest.py`.
- [ ] Live smoke checks cover at least home summary, quote/index quote, marketindex JSON, mobile ranking, and Wisereport financials.
- [ ] README and safety notes still state this is an unofficial public web data skill, not an official Naver API, broker API, or trading API.

# Releasing a package of agent skills or plugins

A package of Claude Code skills (a plugin, or a marketplace of plugins) is released like code: license and IP
first, a leak scan (with `--skip "assistant trace"`, since the package must name the assistant), a version, a
citation file. What follows are the documented distribution options as read in the official documentation on
**2026-11-18** (Claude Code CLI 2.1.327). These features change; read the current pages before relying on any
detail: code.claude.com/docs/en/plugins (host-marketplace, publish, install, org, loading, measure),
code.claude.com/docs/en/skills, code.claude.com/docs/en/plugin-evals, claude.com/docs/plugins (share, submit,
pre-submission-checklist) and claude.com/docs/directory/publish.

## Options

| Option | Who can install | Access control | Updates | What the author learns |
|---|---|---|---|---|
| Public GitHub repository as a marketplace: users run `claude plugin marketplace add owner/repo` | anyone | none | users run `claude plugin update`; auto-update is off by default for third-party marketplaces | nothing: Claude Code reports no usage to an author |
| Private GitHub or GitLab repository, added by its full git URL | anyone who can clone it | the user's own git credentials (SSH agent or credential helper); there is no token field | as above | nothing |
| Project settings: `.claude/settings.json` in a repository with `extraKnownMarketplaces` and `enabledPlugins` | everyone who opens that repository, after the trust dialog; each person installs once per clone | access to the repository | as the marketplace | nothing |
| Managed settings (admin console, device management, `managed-settings.json`) | every machine under the policy | the admin; can force-enable, set `autoUpdate`, restrict sources with `strictKnownMarketplaces` | set by the admin | organization analytics: OpenTelemetry events `plugin_installed` and `skill_activated`; the Analytics API gives per-plugin installs and invocations |
| Plain folders: `~/.claude/skills/` or a repository's `.claude/skills/` | that machine, or everyone in that repository | none | manual copy or `git pull` | nothing |
| claude.ai Team or Enterprise: share with people, publish to the organization, or organization sync from a private repository | organization members | organization roles; sync reads the repository through the organization's GitHub or GitLab connection | shared edits arrive automatically; a published version updates when re-published | organization analytics |
| `--claudeai` marketplaces (the organization library or one's own uploads; registered as `claudeai-<name>`) | signed-in members | the claude.ai account | auto-update on | not stated in the docs |

Skills enabled on claude.ai reach Claude Code as `<name>@synced` under `~/.claude/skills/synced/` for a signed-in
user. A version can be pinned with `#<ref>` on the add command, or with `ref` or `sha` on a plugin entry.

## The official directory

- Submit at claude.ai/directory/manage. It needs a paid plan; on Team or Enterprise an Owner submits.
- The source must be a public GitHub repository. Each plugin folder is its own submission.
- **The listing belongs to the organization that submits it, and the first to submit a repository folder holds it.**
  Decide who submits before announcing the repository.
- Every version goes through automated validation and a security scan; a person reviews a new listing.
- It needs a README of at least 40 words and a LICENSE.
- The author gets a private Usage tab: installs, active accounts, retention, version share, per-skill use, errors,
  listing views, over 90 days, with CSV export. No public install counts were found in the docs.
- The docs do not address who owns a plugin. The directory terms make the submitter warrant that they hold all
  necessary rights, so settle the ownership questions in `license-ip.md` first.

## Versioning

- `version` in `plugin.json` wins over other sources. Bump it on every release, or omit it so that installs track
  commits.
- `claude plugin tag [--push]` creates `{name}--v{version}` tags.

## Measuring the effect before release

`claude plugin eval` runs each case with and without the plugin and reports a score per case, the delta and a suite
verdict ("Plugin effect: +X pts"). The JSON has `aggregates.meanDelta` and `costUsd`. Flags: `--runs` (default 3),
`--model`, `--judge-model`, `--max-cost-usd` (exits 2 with partial results when the limit is hit). `report.html` is
self-contained; `--no-publish` keeps it local.

## Credit: a citation file and an archive DOI

Checked in the GitHub documentation on 2026-11-18:

- A `CITATION.cff` file on the default branch makes the repository page show a "Cite this repository" link, which
  produces APA and BibTeX entries from the file (template in `assets/CITATION.cff`).
- Zenodo archives GitHub releases and mints a DOI: sign in to Zenodo with GitHub, authorize it, and switch the
  repository on in Zenodo's GitHub settings. The repository must be public and should carry a license; an
  organization owner may need to approve the Zenodo application. Zenodo issues a new DOI for each GitHub release. Put the DOI into `CITATION.cff` after the first
  archived release.

## A release order that follows from the above (Suggested, not yet tested in real work)

1. Settle ownership and license (`license-ip.md`); add LICENSE and a README of at least 40 words.
2. Run the package's own quality gate and evals; run the leak scan with `--skip "assistant trace"` and a private
   pattern file.
3. Set `version` in each `plugin.json`, commit, `claude plugin tag --push`.
4. Make the repository public; switch on the Zenodo archive before the first GitHub release; add the DOI to
   `CITATION.cff`.
5. Tell users the one install line (`claude plugin marketplace add owner/repo`, then install the plugin) and that
   updates are manual unless they turn auto-update on.
6. Decide whether the organization submits the plugin folders to the directory, and who holds the listing.

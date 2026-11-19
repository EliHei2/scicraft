# Sharing scicraft with a lab or an organization

Checked against the Claude Code documentation on 2026-11-18. Verify the commands
against the current documentation before a rollout.

## One person

```bash
claude plugin marketplace add EliHei2/scicraft     # or a full git URL, or a local path
claude plugin install scicraft@scicraft
```

A private repository works the same way. Claude Code uses the git credentials
already on the machine (an SSH key in the agent, or a credential helper); it
never asks for a token.

Update with `claude plugin update scicraft@scicraft`. Automatic updates are off
by default for marketplaces outside the official one.

## A lab

Add the marketplace to the settings of the repositories the lab works in, so
everyone who opens one is offered it. In `<repo>/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "scicraft": { "source": { "source": "github", "repo": "EliHei2/scicraft" } }
  },
  "enabledPlugins": { "scicraft@scicraft": true, "scicraft-ml@scicraft": true }
}
```

Each person accepts the folder trust dialog once and runs
`claude plugin install scicraft@scicraft --scope project` once per clone.

A lab that wants its own additions keeps them in a second marketplace of its own
and installs both. Do not fork this one to add a skill: forks drift.

## An organization

Two routes, both for administrators:

- **Managed settings.** The same two keys as above in the organization's managed
  settings enable the plugins on every machine under the policy, with automatic
  updates if the administrator sets them.
- **The organization's library on claude.ai** (Team and Enterprise plans). A
  skill or plugin can be shared with named people, published to the
  organization, or synced from a private repository through the organization's
  own git connection. Published items reach Claude Code for signed-in members.

Both routes give the organization's administrators usage figures (installs and
skill activations). Claude Code reports nothing to a plugin's author.

## Material that must stay inside

Keep institute-specific skills (clusters, storage, policies) in a separate
marketplace in the institute's own git host, with internal visibility. Personal
access details (user names, personal paths, key files) belong in no shared
skill: a skill that needs them reads them from a local file each user keeps.

## Releases

1. Run `python3 tools/check.py` and `claude plugin validate .`.
2. Bump `version` in each changed `plugins/<name>/.claude-plugin/plugin.json`.
   Users stay on the old copy if the version string does not change.
3. `claude plugin tag --push` creates the release tags.
4. For a citable release, archive the tag (for example with Zenodo) and put the
   DOI in `CITATION.cff`.

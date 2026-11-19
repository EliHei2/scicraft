# Web page gate

For a project page or results page before every push and after every deploy. The starter page, scripts and
deployment detail are in `paper-website`; this is the check.

## Scripted

- **Layout at several widths**: overflow, one-word last lines, labels that break, at 390, 768, 1024 and 1440 px
  (320 too when phones matter). "Affiliations for no reason go to second line only for one name" became a rule:
  no last line with one word or one name, at any width.
- **Behavior checks** as PASS or FAIL lines at desktop and phone width: every row opens, every dialog opens and
  closes, deep links open their row, nothing is reachable only by hover.
- **Banned patterns in the built HTML**: separators between phrases (`·`, `•`, ` | `), TODO, placeholders in
  [brackets], the author's banned words. The build fails if they come back.
- **Every number and quoted sentence on the page asserted against the records and the paper** by the builder, so a
  page cannot drift from the paper; keep six decimals in data and round once (rounding twice printed −.036 where
  the paper prints −.037).
- **Leak scan before every push**: home paths, emails, tokens, keys, image metadata, private sample identifiers,
  and the secret files named with a forbid list. It must print clean. Secrets are never printed, only their paths.
- **Small commits** when the host has a build time limit; watch the deployment finish.

## With eyes

- Screenshots at 1440 and 390 px of the first screen and of each opened row; read them.
- A full-page screenshot repeats the top of the page beyond about 16,000 px; shoot the viewport at targets
  instead.
- A hidden absolutely positioned card can widen the phone page; check horizontal scroll at 390 px.

## After deploy

Run the behavior checks against the live URL (with the password file if the page is gated) and lead the report
with whether it is live. Deploying, and going public, are the author's decisions, taken separately.

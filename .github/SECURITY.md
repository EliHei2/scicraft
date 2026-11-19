# Security

scicraft is a set of instructions and scripts that Claude Code runs on your
machine, with your permissions.

- **No telemetry.** No skill and no script collects or sends usage data.
- **Network use is named.** A few scripts reach the network because that is
  their job, and each says so in its help text: checking a bibliography against
  a public index, reading the file list of a remote archive, downloading
  published benchmark results, pushing code to a cluster you configured, and
  the browser code of the paper-website starter.
- **Scripts read and write where you point them.** Read a script before you run
  it on data you care about. Scripts prefer the Python standard library and
  answer `--help`.
- **Nothing private ships.** A gate fails the build on home paths, host names,
  e-mail addresses, keys and a list of forbidden strings.

## Reporting a vulnerability

Please do not open a public issue. Use GitHub's private vulnerability reporting
on this repository ("Security" tab, "Report a vulnerability"). You will get an
answer within a week.

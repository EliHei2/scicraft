# Gate, host, scan, take down

An unpublished paper's website is confidential. Deploying it is the author's decision: ask once what they want
(public, or a preview behind a password that can be taken down at any time), then that choice stands for the
preview. Going public is a separate decision.

## Contents
1. A gated preview on GitHub Pages
2. Before every push
3. Deploy and check
4. Take it down, change the password
5. What the gate is and is not
6. Going public
7. Private material
8. Commands the author runs

## 1. A gated preview on GitHub Pages

One-time setup (the author's account, a **private** repository, Pages served from its main branch):

```bash
cd <project>-site
python3 pipeline/gate.py --site . --title "Name" --subtitle "The rest of the title" --icon brand/mark.png
cd dist && git init -b main && git remote add origin https://github.com/<user>/<repo>.git
```

`gate.py` writes `dist/`: a sign-in page that carries the real page encrypted (AES-GCM, key from PBKDF2-SHA256 of
the password, 250,000 rounds), every asset under a folder with an unguessable name, `robots.txt` that disallows
everything, and `.nojekyll`. `dist/` is its own repository; the site's sources are not in it. It needs the
`cryptography` package.

The password is in `pipeline/.beta_password` and the folder name in `pipeline/.deploy_secret`. Both are created on
the first run with owner-only permissions. Rules:

- Never print either in logs, reports to others, commits or screenshots. When you show command output that could
  contain the folder name, pipe it through `sed -E 's/[a-z0-9]{24}/<secret>/g'`. When the author asks for the
  password in the conversation, give it to them there and nowhere else.
- Never commit or deploy them. `gate.py` skips dot-files; keep `pipeline/` out of `dist/`.
- The author may set the password themselves: write it into `.beta_password` and build again.
- `gate.py --skip data/gallery/<prefix>` holds back items that wait for something (a missing reference layer); keep
  the list in `DEPLOY.md`.
- `gate.py` skips files whose name contains `.part`. Anything that renders long outputs (an encoder, an agent
  making animations) writes `<name>.part` and renames it when done: a build once picked up half-written video files
  while an encoder was still running.

**A Pages site built by an Actions workflow needs `build_type: workflow`.** In the legacy branch mode a site once
kept serving a stale, broken build although every deploy reported success. Set it once with
`gh api --method PUT repos/<owner>/<repo>/pages -f build_type=workflow`. Symptom: new assets answer 404, or new
strings are missing, after a green deploy; check with `gh api repos/<owner>/<repo>/pages`.

## 2. Before every push

```bash
python3 pipeline/leak_scan.py dist --patterns pipeline/private_patterns.txt --forbid pipeline/.beta_password
```

`private_patterns.txt` holds one regular expression per line for what is private in this project: sample or patient
identifier shapes, host and user names of the cluster, internal names of runs and records, words the author has
retired from the page. Add to it whenever something private gets a name. The scan also flags local paths, e-mail
addresses, tokens and image metadata. A push happens only when it prints `clean`.

A hit inside a compressed binary can be chance bytes: a short secret or pattern once matched inside a gzip data
file. The scan marks such hits as binary; check whether the hit is text before acting, and say what you found.

Also look at what `dist/` holds besides data (`find dist -maxdepth 2`): nothing from `pipeline/`, `retired/` or any
raw-data folder may be there. Measure the total (`du -sh dist`) against the host's limits (section 3).

## 3. Deploy and check

```bash
python3 pipeline/gate.py --site . --title ... && python3 pipeline/leak_scan.py dist ... && ./pipeline/push_dist.sh dist
gh run watch $(gh run list -R <user>/<repo> --limit 1 --json databaseId -q '.[0].databaseId') -R <user>/<repo> --exit-status
URL=https://<user>.github.io/<repo>/ PW_FILE=pipeline/.beta_password node pipeline/gate_check.js 1440
URL=https://<user>.github.io/<repo>/ PW_FILE=pipeline/.beta_password node pipeline/behave.js 1440
URL=https://<user>.github.io/<repo>/ PW_FILE=pipeline/.beta_password node pipeline/behave.js 390
```

- `push_dist.sh` commits small files first and large ones two at a time, and retries each push five times. A single
  push of 711 MB died on a network drop; the batched push went through.
- Pages rebuilds a minute or two after the last push and has a ten-minute limit, so keep the site small (patterns.md
  section 11). A deploy of 711 MB timed out; 408 MB went through.
- A 503 on a single asset right after a deploy is the CDN catching up: check again before you call it a failure.
- `gate_check.js` checks the gate (a wrong password is refused, the right one opens the page, a reload opens it again
  from the browser's memory) and the open page as a co-author sees it (charts drew, images loaded with their widths, favicon, gallery tile
  and figure counts, no failed request, no console error). Its output is masked; pipe anything else you show through
  the same `sed`.
- Commit messages are plain and follow the project's rules (some authors want no tool attribution in them).
- **A fix for someone using the page right now ships alone.** When a tester reported a widget that needed a double
  click, the fix was reproduced, checked and deployed on its own, before the larger round went on.

## 4. Take it down, change the password

```bash
gh api -X DELETE repos/<user>/<repo>/pages                                   # down at once; the CDN may serve cached pages for minutes
gh api -X POST repos/<user>/<repo>/pages -f 'source[branch]=main' -f 'source[path]=/'      # back up
```

Change the password by editing `.beta_password` and deploying; old links keep working. Delete `.deploy_secret` as
well to move the data folder. Put these lines into `DEPLOY.md` on the first day.

When the author says a password does not work after a change, test which password each address accepts before
anything else (`gate_check.js` with each password file). Twice the cause was on their side: a tab opened before the
change, or the browser's autofill holding the old password, while the new build was not yet live. Then tell them to
clear the field and reload without the cache (Cmd+Shift+R on a Mac).

## 5. What the gate is and is not

It keeps out casual visitors, link previews and search engines. It is not access control: anyone with the password,
or with the exact address of a data file, can read it, and the host can read everything. Say this to the author in
one sentence before anything sensitive goes on the page. Data that may not leave the institute does not go on a
public host, gated or not.

The sign-in page says "Unpublished work. Please do not share the link or the password." It shows the project's name
and subtitle only, so even the gate reveals nothing the title would not.

## 6. Going public

A separate round, on the author's word, usually with the preprint:

- deploy `public/` itself (no gate), make the repository public or move it, remove `robots.txt`'s blanket disallow;
- add absolute `og:` and `twitter:` image addresses (they are useless inside a gated page);
- the citation block returns with its copy button (kept in `retired/` with the CSS and JS it needs);
- "coming soon" lines become links as each thing exists, and none claims more than exists;
- run the leak scan on what is now public once more, with fresh eyes on names, cohorts and licenses.

## 7. Private material

- **Anonymize in the builder.** The script that reads raw sample names writes "sample 1", "section A"; the mapping
  stays in memory or in a file that is never deployed.
- **Check numbers that describe a sample are that sample's.** A count taken from a slide-level field once printed the
  whole slide's total for every sample cut from it.
- **Licenses.** Name a license on the page only once the author has confirmed it; credit the source either way.
- **No project details to outside services**: no analytics, no hosted fonts, no web search with the title of an
  unpublished paper, no e-mail address in a request header.

## 8. Commands the author runs

- **Any command the author must run is one line.** A pasted two-line command broke at the newline. To hand over a
  message without terminal line breaks, write it to a file and give `pbcopy < file` (macOS).
- **Check machine state yourself before asking.** The author once waited to free disk space that `df` would have
  shown was already free ("please find out").
- A script the author runs on their own machine is tested with that machine's own tools (`/bin/bash`, BSD tools,
  rsync 2.6.9 on macOS) before it is handed over.
- **Run a handed-over script by its path** (`./push_dist.sh dist`, after `chmod +x` once), so its shebang chooses the
  shell. A push script written for zsh and started with `bash` failed after its first commit had already been
  pushed, which left the remote half updated. Test it with macOS `/bin/bash` before handing it over.

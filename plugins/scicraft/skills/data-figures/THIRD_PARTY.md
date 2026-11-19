# Third-party material

| Item | Where it is used | Source | License or status |
|---|---|---|---|
| Okabe-Ito color set (`#E69F00 #56B4E9 #009E73 #F0E442 #0072B2 #D55E00 #CC79A7 #000000`) | `assets/figstyle.py` palette roles | Okabe and Ito, "Color Universal Design" (2008) | color values, free to use; credited here |
| Apple system blue `#0A84FF` and red `#FF3B30` as the ends of `DIVERGING` | `assets/figstyle.py` | Apple Human Interface Guidelines | color values only; no code or asset copied |
| adjustText settings in `repel_labels` | `assets/figstyle.py` | adjustText (Python port of ggrepel), github.com/Phlya/adjustText | MIT; an optional dependency the user installs; only call parameters appear here |
| Computer Modern fonts `cmss10`, `cmr10`, `cmb10` | named by `S.apply(font=...)` | shipped inside matplotlib's own data folder | not copied into this skill; used under matplotlib's distribution |
| Helvetica Neue | registered from the user's macOS system folder; the bold face is extracted to the user's cache | Apple system font | not shipped; never copy the extracted file into a repository or package |

Everything else in this folder was written for the author's own projects and is released with the package.

# Header, footer, references, contacts

## 1. Header

- **Title**: the paper's title, 88/98 pt design, Helvetica Neue Bold, ragged right in a 72 cm minipage, broken by
  hand (`\\`) into two lines that do not leave one word alone. The method's name and the coined term are set in
  the accent.
- **Authors**: 35/42 pt, the paper's order, superscript affiliation numbers, the presenting author underlined
  (the only underline on the poster). Joint supervisors carry a dagger.
- **Affiliations**: 23/29 pt in slate, one paragraph 94 cm wide, each affiliation in an `\mbox` and separated by
  `\quad`, ending with `\textsuperscript{\dag}These authors jointly supervised this work.` The author called a
  line that broke for one name "for no reasons" broken; the `\mbox` prevents it.
- **Logo**: only when the host asks for it, top right, 21 cm wide on the design page, cropped to the mark
  (`trim`, `clip`). One logo, the host's.
- **Rule**: 0.55 cm under the affiliations, a 0.2 cm ink rule across the 94 cm.

## 2. Footer

Built from the bottom up, all pieces in one `fit` whose top sets the footer rule:

1. **Release line**, bottom right at (97, 1.3) design cm: 26/31 pt bold, for example "Preprint and code coming
   soon". It states what is coming; it never claims something is available when it is not.
2. **No-photos sign** 0.35 cm above the release line, centered on it, 2.4 cm high: `no_photos.tex`, a line-art
   camera under a prohibition ring in the ISO 7010 P029 layout (bar from upper left to lower right), ring and bar
   1.5 mm in process red `#E30613`, camera strokes 1.1 mm in ink, 24 x 24 mm, vector. The first version was
   raster; the author asked for "higher quality, more minimal, still effective".
3. **Contacts**, bottom left at (3, 1.3): a 77.4 cm minipage at 22/26 pt in slate: the presenting author's email
   and social handle, then each lab's name with its handle and web address, spread with `\hfill`. Icons for
   social platforms are allowed if their license permits; record them in the provenance block.
4. **References**, 0.4 cm above the contacts, same width, 18/22.5 pt slate with `\frenchspacing`:
   `\textbf{\color{ink}References}` then the entries run on, separated by a stretchable space
   (`\hspace{0.4em plus 0.2em minus 0.05em}`).
5. **Footer rule**: 0.55 cm above the highest footer piece, 0.2 cm thick, 94 cm wide.

## 3. Reference entries

- Form: `[n]~First author~\emph{et~al.}, short name or title, Venue~Year`; a single author has no "et al."
  Venue abbreviations as the field prints them (Nat. Methods, Nat. Genet., NeurIPS, ICML, CVPR, bioRxiv, arXiv).
- Numbered in the order of first citation on the poster: method components first (as the method band cites
  them), then the comparators in the order of the results table.
- Inline citations are slate `[n]` (the template redefines `\cite`); in the table, after the comparator's name.
- A "Data:" group lists the datasets shown, same form, no numbers. A further group may credit an idea the poster
  names (for example the work a term was borrowed from).
- Every entry checked against the paper's bibliography: venue and year as the publisher prints them; two
  sources of the same paper can disagree on the year.

## 4. Licenses of outside material

- A picture, icon, dataset or figure that is not the paper's own goes on the poster only after its license is
  read at the source and allows the use (for example CC BY 4.0 on a dataset record). Record the source address
  and the license in the provenance block, and give the credit in the "Data:" group or the caption.
- The paper's own figures carried no credit line on the poster; their provenance is in the source's
  provenance block.

## 5. What the poster this came from did not have

- No QR code and no repository link (nothing was public yet).
- No affiliation footnotes beyond the header line, no acknowledgements block, no funding logos.
- No second accent color and no colored bars (the orange bars of an older poster were replaced by black rules).

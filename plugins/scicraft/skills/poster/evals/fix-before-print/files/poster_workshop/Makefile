# Conference poster, A0. poster_design.tex is laid out on a 1000 x 1414.2 mm page (A0 proportions, absolute
# TikZ coordinates, two xelatex passes); poster_A0.tex places it on the 841 x 1189 mm sheet: poster.pdf is the
# file to print. `make check` runs the layout and printer gates.
#   TOOLS   folder holding the skill's scripts (copy them to tools/ or point here)
#   FIGS    BOX names of placed figures and tables: their own labels are listed for a look, not failed
#   PAPER   the paper's .tex files or folder, for the own-words check (`make words`)
#   FORBID  comma-separated strings that must not be in the text layer (retired names, superseded numbers)
TOOLS  ?= tools
PY     ?= python3 -I
FIGS   ?= f1,f2,t9
PAPER  ?= ../paper
FORBID ?=
SCALE  := 0.841

all: poster.pdf

build/poster_design.pdf: poster_design.tex assets/no_photos.pdf $(wildcard figures/*) $(wildcard tables/*.tex)
	mkdir -p build
	xelatex -interaction=nonstopmode -halt-on-error -output-directory=build -jobname=poster_design poster_design.tex
	xelatex -interaction=nonstopmode -halt-on-error -output-directory=build -jobname=poster_design poster_design.tex

poster.pdf: poster_A0.tex build/poster_design.pdf
	xelatex -interaction=nonstopmode -halt-on-error -jobname=poster poster_A0.tex

assets/no_photos.pdf: no_photos.tex
	mkdir -p build assets
	pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build no_photos.tex
	mv build/no_photos.pdf $@

check: poster.pdf
	$(PY) $(TOOLS)/box_check.py build/poster_design.log --gap 0.2
	$(PY) $(TOOLS)/layout_check.py build/poster_design.pdf --scale $(SCALE) --minpt 14 --dpi 20 \
	  --boxes build/poster_design.log --figure-boxes $(FIGS) --out build/poster
	$(PY) $(TOOLS)/line_breaks.py build/poster_design.pdf --scale $(SCALE) \
	  --boxes build/poster_design.log --figure-boxes $(FIGS)
	$(PY) $(TOOLS)/pdf_gate.py poster.pdf --size 841x1189 --max-mb 50 $(if $(FORBID),--forbid "$(FORBID)")

words: build/poster_design.pdf
	$(PY) $(TOOLS)/own_words_poster.py build/poster_design.pdf $(PAPER) \
	  --boxes build/poster_design.log --figure-boxes $(FIGS),n6,defs $(if $(wildcard departures.txt),--allow departures.txt)

preview: poster.pdf
	pdftoppm -png -r 30 -singlefile poster.pdf build/preview

clean:
	rm -f *.aux *.log *.out build/*.aux build/*.log build/*.out
.PHONY: all check words preview clean

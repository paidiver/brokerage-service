# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile fetch-repos clean-repos html-with-repos

fetch-repos:
	@echo "Fetching documentation from repositories..."
	@python3 lib/fetch_repo_docs.py

clean-repos:
	@echo "Cleaning fetched repository documentation..."
	@python3 -c 'import shutil; shutil.rmtree("$(SOURCEDIR)/repos", ignore_errors=True)'

html-with-repos: fetch-repos html

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

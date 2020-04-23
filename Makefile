# 'default' target does nothing
.PHONY: default
default:

# 'clean' removes generated files
.PHONY: clean
clean:; rm -rf *.pyc __pycache__

.PHONY: lint
lint:; pylint3 -E -dno-member *.py

# 'install' symlinks this directory into the first python3 site directory
# so these can be imported as modules
site := $(shell python3 -c'import site; print(site.getsitepackages()[0])')
link := ${site}/$(notdir ${CURDIR}) # Don't use ${PWD}!

.PHONY: install
install:
ifneq (${site},)
	mkdir -p ${site}
	ln -sf ${CURDIR} ${link}
endif

# 'uninstall' deletes the package symlink
.PHONY: uninstall
uninstall: clean
ifneq (${site},)
	rm -f ${link}
endif

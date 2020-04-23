.PHONY: default
default: # Nothing to do!

.PHONY: clean
clean:; rm -rf *.pyc __pycache__

.PHONY: lint
lint:; pylint3 -E -dno-member *.py

# install and uninstall require root
ifeq (${USER},root)
site := $(shell python3 -c'import site; print(site.getsitepackages()[0])')
ifeq ($(strip ${site}),)
$(error Unable to get python package directory)
endif

# pre-compile modules and symlink this directory as a package
.PHONY: install
install:
	rm -rf __pycache__
	py3compile *.py
	ln -sf ${CURDIR} ${site}

# delete package symlink
.PHONY: uninstall
uninstall: clean; rm -f ${site}/$(notdir ${CURDIR})

endif

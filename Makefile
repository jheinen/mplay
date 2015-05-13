  PYTHON = /usr/local/bin/python

cmplay.so:
	$(PYTHON) csetup.py build_ext --inplace
clean:
	rm -f *.c *.pyc cmplay.so

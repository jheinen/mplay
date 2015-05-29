  PYTHON = /opt/bin/python

cmplay.so:
	$(PYTHON) csetup.py build_ext --inplace

app:
	$(PYTHON) setup.py py2app

clean:
	rm -f *.c *.pyc cmplay.so
	rm -rf build dist/mplay.app .eggs

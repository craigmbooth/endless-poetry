# Makefile of convenience functions for working with my Inkplate 10

# List contents of Inkplate
ls:
	python pyboard.py --device /dev/ttyUSB0 -f ls

# Open a shell
# Ctrl-a Ctrl-q quits
shell:
	picocom /dev/ttyUSB0 -b115200

# Put a file on the device.  Use with make FILE=<filename> put
put:
	python pyboard.py --device /dev/ttyUSB0 -f cp src/$(FILE) :
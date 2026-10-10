PYTHON ?= python3

.PHONY: test host-demo clean

test:
	$(PYTHON) -m unittest discover -s tests -v

host-demo:
	$(PYTHON) host/logic_capture.py --input examples/sample_capture.json --baud 115200 --csv decoded.csv --vcd waveform.vcd

clean:
	rm -rf __pycache__ host/__pycache__ tests/__pycache__ decoded.csv waveform.vcd build

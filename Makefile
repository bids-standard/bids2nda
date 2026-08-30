.PHONY: test
test: .test

.test: $(wildcard bids2nda/**py)  $(wildcard examples/**) 
	python3 -m pytest tests/ | tee $@ # --pdb

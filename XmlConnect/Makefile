# ARGS := resources/multidrive.txt
# ARGS += resources/xml
# MAIN := MultiDriverTracer.py

ARGS := umc/runws/minicase/logical_view
ARGS += umc/runws/minicase/tile_view
ARGS += CHIP
MAIN := LogicalTileMapper.py


run:
	python3.10 src/$(MAIN) $(ARGS)

pdb:
	python3.10 -m ipdb -c continue src/$(MAIN) $(ARGS)

rep-match:
	python3.10 RepeaterMatch.py ../../resources/user_match ../../resources/xml/logical_info.yml
rep-match-pdb:
	python3.10 -m ipdb -c continue RepeaterMatch.py ../../resources/user_match ../../resources/xml/logical_info.yml
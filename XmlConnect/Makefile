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

JSON_DIR := ../../resources/user_match/json ../../resources/xml/logical_info.yml
MPU_LOGICAL_INFO := ../../resources/xml/logical_info.yml
REPEATET_MATCH := RepeaterMatch.py $(JSON_DIR) $(MPU_LOGICAL_INFO)

rep-match:
	python3.10 $(REPEATET_MATCH) 
rep-match-pdb:
	python3.10 -m ipdb -c continue $(REPEATET_MATCH)
# One command: `make all` (= final). `make preview` for a fast 540x960 Eevee pass.
MODE    ?= preview
BLENDER ?= blender
PY      ?= python3
JOBS    ?= 2
BUILD   := build/$(MODE)
BEATS   := 1 2 3 4 5 6 7 8

.PHONY: all preview final validate scenes overlays audio compose verify clean clean-frames

all: final

preview:
	$(MAKE) MODE=preview validate scenes overlays audio compose verify

final:
	$(MAKE) MODE=final validate scenes overlays audio compose verify

validate:
	$(PY) config/validate.py

# Renders each beat as a PNG sequence. Frames that already exist are skipped, so an
# interrupted render resumes. `make clean-frames MODE=...` forces a full re-render.
scenes:
	@mkdir -p $(BUILD)/logs
	@printf '%s\n' $(BEATS) | xargs -P $(JOBS) -I{} sh -c '\
	  echo "[scenes] beat {} ($(MODE))"; \
	  $(BLENDER) -b --factory-startup -P scenes/build_scene.py -- --beat {} \
	    --out $(BUILD)/frames/beat_{}/ --mode $(MODE) > $(BUILD)/logs/beat_{}.log 2>&1 \
	  || { echo "[scenes] beat {} failed, retrying once (log: $(BUILD)/logs/beat_{}.log)"; \
	       $(BLENDER) -b --factory-startup -P scenes/build_scene.py -- --beat {} \
	         --out $(BUILD)/frames/beat_{}/ --mode $(MODE) >> $(BUILD)/logs/beat_{}.log 2>&1; }'
	@grep -h "^\[build_scene\] beat" $(BUILD)/logs/beat_*.log || true

overlays:
	$(PY) overlays/make_hud.py --mode $(MODE)
	$(PY) overlays/make_captions.py --mode $(MODE)

audio:
	$(PY) audio/mix.py --out $(BUILD)/audio/mix.wav

compose:
	bash compose/compose.sh $(MODE)

verify:
	$(PY) compose/verify.py --mode $(MODE)

clean-frames:
	rm -rf $(BUILD)/frames

clean:
	rm -rf build/preview build/final

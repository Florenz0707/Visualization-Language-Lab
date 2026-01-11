#!/usr/bin/env python3
"""Test Kokoro segmentation behavior."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.main import _load_dotenv_from_repo_root

_load_dotenv_from_repo_root()

from loguru import logger

# Test text (similar length to chapter narratives)
test_text = """1812年6月24日，拿破仑的大军如一股钢铁洪流，在科夫诺附近分三路悄然渡过涅曼河，正式侵入俄国境内。这支史称"大军"的队伍，人数高达60余万，来自欧洲各地，火炮超过1370门。"""

logger.info(f"Test text length: {len(test_text)} chars")

try:
    from kokoro import KPipeline

    pipeline = KPipeline(lang_code="z", repo_id="hexgrad/Kokoro-82M")

    segments = []
    for i, (g, p, audio) in enumerate(pipeline(test_text, voice="af_heart", speed=1.0)):
        logger.info(f"Segment {i+1}: {len(audio)} samples, graphemes: {len(g)}")
        segments.append(audio)

    logger.success(f"Total segments: {len(segments)}")

except Exception as e:
    logger.error(f"Error: {e}")
    import traceback

    traceback.print_exc()

import soundfile as sf
import torch
from IPython.display import Audio, display
from kokoro import KPipeline

pipeline = KPipeline(lang_code="a")
text = """
[Kokoro](/kˈOkəɹO/) is an open-weight TTS model with 82 million parameters. Despite its lightweight architecture, it delivers comparable quality to larger models while being significantly faster and more cost-efficient. With Apache-licensed weights, [Kokoro](/kˈOkəɹO/) can be deployed anywhere from production environments to personal projects.
"""
generator = pipeline(text, voice="af_heart")
for i, (gs, ps, audio) in enumerate(generator):
    print(i, gs, ps)
    display(Audio(data=audio, rate=24000, autoplay=i == 0))
    sf.write(f"{i}.wav", audio, 24000)

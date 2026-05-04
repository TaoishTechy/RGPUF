Created the demo script for `/examples/`:

[Download `rgpuf_demo.py`](rgpuf_demo.py)

Suggested repo placement:

```bash
mkdir -p examples
cp rgpuf_demo.py examples/rgpuf_demo.py
chmod +x examples/rgpuf_demo.py
```

Run examples:

```bash
python examples/rgpuf_demo.py
python examples/rgpuf_demo.py --mode lander
python examples/rgpuf_demo.py --mode asteroids
python examples/rgpuf_demo.py --mode pressure
python examples/rgpuf_demo.py --steps 240 --seed 7
```

It includes a compact RGPUF demo stack: thrust, gravity wells, collision/bounce, toroidal wrapping, 256-step quantized heading, fuel/heat/pressure resource thermodynamics, procedural seed compression, and a simple playable-reality metric.

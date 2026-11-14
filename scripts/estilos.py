#!/usr/bin/env python3
"""Empaqueta los estilos de OpenFreeMap (claro y oscuro) con sus fuentes e iconos para usarlos sin conexión.

Deja en out/estilos/: liberty.json, dark.json, fonts/<fuente>/<rango>.pbf y sprites/<estilo>/sprite*.
En los estilos, glyphs y sprite apuntan a {{BASE}} (la app lo sustituye por la carpeta del móvil).
"""
import json, os, sys, urllib.parse, urllib.request

OUT = "out/estilos"
STYLES = {"liberty": "https://tiles.openfreemap.org/styles/liberty", "dark": "https://tiles.openfreemap.org/styles/dark"}
# Latín básico y extendido (castellano, catalán, francés, portugués...), puntuación y símbolos
RANGES = ["0-255", "256-511", "512-767", "7680-7935", "8192-8447", "8448-8703"]


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def fonts_in(value, found):
    """Listas de nombres de fuente dentro de text-font (lista simple o expresión)."""
    if isinstance(value, list):
        if value and all(isinstance(v, str) for v in value) and value[0] not in ("literal", "get", "case", "match", "step", "coalesce"):
            found.add(",".join(value))
        else:
            for v in value:
                fonts_in(v, found)
    elif isinstance(value, dict):
        for v in value.values():
            fonts_in(v, found)


def main():
    os.makedirs(OUT, exist_ok=True)
    stacks = set()
    for name, url in STYLES.items():
        style = json.loads(get(url))
        glyphs = style["glyphs"]
        sprite = style.get("sprite")

        # Solo se conserva el mapa vectorial: las capas de imagen (relieve) no están en el archivo sin conexión
        raster = [k for k, s in style["sources"].items() if s.get("type") != "vector"]
        for k in raster:
            del style["sources"][k]
        style["layers"] = [l for l in style["layers"] if l.get("source") not in raster]
        print(f"{name}: fuentes de datos {list(style['sources'])}, quitadas {raster}, {len(style['layers'])} capas")

        mine = set()
        for layer in style["layers"]:
            fonts_in(layer.get("layout", {}).get("text-font"), mine)
        print(f"{name}: fuentes {sorted(mine)}")
        for stack in mine:
            if stack in stacks:
                continue
            stacks.add(stack)
            os.makedirs(f"{OUT}/fonts/{stack}", exist_ok=True)
            for rng in RANGES:
                u = glyphs.replace("{fontstack}", urllib.parse.quote(stack)).replace("{range}", rng)
                try:
                    data = get(u)
                    open(f"{OUT}/fonts/{stack}/{rng}.pbf", "wb").write(data)
                except Exception as e:  # un rango que la fuente no tiene no es grave
                    print(f"  sin {stack} {rng}: {e}")

        if isinstance(sprite, str):
            os.makedirs(f"{OUT}/sprites/{name}", exist_ok=True)
            for suffix in (".json", ".png", "@2x.json", "@2x.png"):
                open(f"{OUT}/sprites/{name}/sprite{suffix}", "wb").write(get(sprite + suffix))
            style["sprite"] = "{{BASE}}/sprites/" + name + "/sprite"
        elif sprite is not None:
            print(f"AVISO: formato de sprite no previsto en {name}: {sprite}")
            style.pop("sprite", None)
        style["glyphs"] = "{{BASE}}/fonts/{fontstack}/{range}.pbf"
        json.dump(style, open(f"{OUT}/{name}.json", "w"), ensure_ascii=False)

    total = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(OUT) for f in fs)
    print(f"Total: {total / 1e6:.1f} MB")
    if not stacks:
        sys.exit("No se encontró ninguna fuente en los estilos")


if __name__ == "__main__":
    main()

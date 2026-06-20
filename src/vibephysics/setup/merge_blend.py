"""Merge multiple saved .blend reconstructions into one compare scene."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import bpy

_RESULT_COLLECTION_RE = re.compile(r".*_Result$", re.IGNORECASE)
_PREFERRED_COLLECTIONS = (
    "GLOMAP_Result",
    "COLMAP_Result",
    "VGGT_Omega_Result",
    "VGGT_TTT_Result",
    "LingBot_Map_Result",
)


def _detect_result_collection(blend_path: Path) -> str:
    with bpy.data.libraries.load(str(blend_path), link=False) as (data_from, _):
        collections = list(data_from.collections)
    for preferred in _PREFERRED_COLLECTIONS:
        if preferred in collections:
            return preferred
    for name in collections:
        if _RESULT_COLLECTION_RE.match(name):
            return name
    if collections:
        return collections[0]
    raise ValueError(f"No collections found in {blend_path}")


def append_collection(blend_path: Path, collection_name: str) -> bpy.types.Collection:
    blend_path = blend_path.expanduser().resolve()
    if not blend_path.is_file():
        raise FileNotFoundError(f"Blend file not found: {blend_path}")

    with bpy.data.libraries.load(str(blend_path), link=False) as (data_from, data_to):
        if collection_name not in data_from.collections:
            raise ValueError(
                f"Collection {collection_name!r} not found in {blend_path}. "
                f"Available: {list(data_from.collections)}"
            )
        data_to.collections = [collection_name]

    collection = data_to.collections[0]
    bpy.context.scene.collection.children.link(collection)
    return collection


def merge_blend_files(
    inputs: list[Path],
    output_path: Path,
    *,
    collection_names: list[str] | None = None,
    compress: bool = False,
) -> Path:
    if len(inputs) < 2:
        raise ValueError("Provide at least two .blend files to merge")
    if collection_names is not None and len(collection_names) != len(inputs):
        raise ValueError("collection_names must match the number of inputs")

    bpy.ops.wm.read_factory_settings(use_empty=True)

    merged_collections: list[str] = []
    for index, blend_path in enumerate(inputs):
        collection_name = (
            collection_names[index]
            if collection_names is not None
            else _detect_result_collection(blend_path)
        )
        collection = append_collection(blend_path, collection_name)
        merged_collections.append(collection.name)
        print(f"Appended {collection.name} from {blend_path}")

    from vibephysics.setup.viewport import (
        setup_compare_dual_viewport,
        setup_compare_triple_viewport,
    )

    if len(merged_collections) == 2:
        setup_compare_dual_viewport(merged_collections[0], merged_collections[1])
    elif len(merged_collections) == 3:
        setup_compare_triple_viewport(*merged_collections)
    else:
        print(
            f"⚠️ Viewport layout skipped for {len(merged_collections)} collections "
            "(supported: 2 or 3 panes)"
        )

    bpy.context.scene.frame_set(0)
    output_path = output_path.expanduser().resolve()
    if output_path.suffix.lower() != ".blend":
        output_path = output_path.with_suffix(".blend")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path), compress=compress)
    print(f"Saved merged blend: {output_path}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge multiple reconstruction .blend files into one compare scene.",
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Input .blend paths (2 or 3 files for side-by-side compare viewports)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="Output merged .blend path",
    )
    parser.add_argument(
        "--collection",
        action="append",
        dest="collections",
        default=None,
        help="Optional collection name per input (default: auto-detect *_Result)",
    )
    parser.add_argument("--compress", action="store_true", help="Save a compressed .blend file")
    args = parser.parse_args()

    try:
        merge_blend_files(
            args.inputs,
            args.output,
            collection_names=args.collections,
            compress=args.compress,
        )
    except Exception as exc:
        print(f"[ERROR] Merge blend failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

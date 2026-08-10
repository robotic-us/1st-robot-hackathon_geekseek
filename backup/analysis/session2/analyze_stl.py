#!/usr/bin/env python3
"""Reproducible mesh inspection for the RPI Session 2 report.

The script intentionally uses only NumPy and Matplotlib.  It treats triangles
as connected when they share an exactly equal STL vertex, reports disconnected
shells, detects phact-like housings from the reference STL envelope, detects
6807ZZ-like shells from the bearing reference, and renders orthographic and
kinematic views.  Axis signs and joint motion limits cannot be recovered from
an STL and are therefore never inferred here.
"""

from __future__ import annotations

import argparse
import csv
import json
import struct
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


@dataclass
class Shell:
    index: int
    triangle_ids: np.ndarray
    triangle_count: int
    lo: np.ndarray
    hi: np.ndarray

    @property
    def dimensions(self) -> np.ndarray:
        return self.hi - self.lo

    @property
    def center(self) -> np.ndarray:
        return (self.lo + self.hi) / 2.0


def read_stl(path: Path) -> np.ndarray:
    """Return an (N, 3, 3) float64 triangle array from binary or ASCII STL."""
    raw = path.read_bytes()
    if len(raw) >= 84:
        count = struct.unpack_from("<I", raw, 80)[0]
        if 84 + 50 * count == len(raw):
            dtype = np.dtype(
                [("normal", "<f4", 3), ("vertices", "<f4", (3, 3)), ("attr", "<u2")]
            )
            return np.frombuffer(raw, dtype=dtype, offset=84, count=count)[
                "vertices"
            ].astype(np.float64)

    vertices: list[list[float]] = []
    for line in raw.decode("ascii", errors="strict").splitlines():
        words = line.split()
        if len(words) == 4 and words[0].lower() == "vertex":
            vertices.append([float(x) for x in words[1:]])
    if len(vertices) % 3:
        raise ValueError(f"Malformed ASCII STL: {path}")
    return np.asarray(vertices, dtype=np.float64).reshape(-1, 3, 3)


def disconnected_shells(triangles: np.ndarray) -> tuple[list[Shell], np.ndarray]:
    """Split by exact shared vertices and return shells plus triangle->shell map."""
    triangle_count = len(triangles)
    _, inverse = np.unique(triangles.reshape(-1, 3), axis=0, return_inverse=True)
    parent = np.arange(triangle_count, dtype=np.int32)
    size = np.ones(triangle_count, dtype=np.int32)

    def root(item: int) -> int:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = int(parent[item])
        return item

    first_triangle: dict[int, int] = {}
    for triangle_id in range(triangle_count):
        for vertex_id in inverse[3 * triangle_id : 3 * triangle_id + 3]:
            vertex_id = int(vertex_id)
            other = first_triangle.get(vertex_id)
            if other is None:
                first_triangle[vertex_id] = triangle_id
                continue
            a, b = root(triangle_id), root(other)
            if a == b:
                continue
            if size[a] < size[b]:
                a, b = b, a
            parent[b] = a
            size[a] += size[b]

    roots = np.fromiter((root(i) for i in range(triangle_count)), np.int32)
    unique_roots, counts = np.unique(roots, return_counts=True)
    order = np.argsort(counts)[::-1]
    shells: list[Shell] = []
    triangle_to_shell = np.empty(triangle_count, dtype=np.int32)
    for shell_index, root_id in enumerate(unique_roots[order]):
        ids = np.flatnonzero(roots == root_id)
        points = triangles[ids].reshape(-1, 3)
        shell = Shell(
            index=shell_index,
            triangle_ids=ids,
            triangle_count=len(ids),
            lo=points.min(axis=0),
            hi=points.max(axis=0),
        )
        shells.append(shell)
        triangle_to_shell[ids] = shell_index
    return shells, triangle_to_shell


def envelope_score(dimensions: np.ndarray, reference: np.ndarray) -> float:
    return float(np.linalg.norm(np.sort(dimensions) - np.sort(reference)))


def detect_by_envelope(
    shells: list[Shell], reference_dimensions: np.ndarray, tolerance_mm: float
) -> list[Shell]:
    return sorted(
        [
            shell
            for shell in shells
            if envelope_score(shell.dimensions, reference_dimensions) <= tolerance_mm
        ],
        key=lambda shell: tuple(shell.center[::-1]),
    )


def set_equal_3d(ax, lo: np.ndarray, hi: np.ndarray) -> None:
    center = (lo + hi) / 2.0
    radius = float(max(hi - lo) / 2.0)
    ax.set_xlim(center[0] - radius, center[0] + radius)
    ax.set_ylim(center[1] - radius, center[1] + radius)
    ax.set_zlim(center[2] - radius, center[2] + radius)


def render_projection(
    triangles: np.ndarray,
    joint_centers: np.ndarray,
    joint_axes: np.ndarray,
    dimensions: tuple[int, int],
    title: str,
    output: Path,
) -> None:
    centers = triangles.mean(axis=1)
    i, j = dimensions
    fig, ax = plt.subplots(figsize=(8, 8), dpi=180)
    ax.scatter(centers[::2, i], centers[::2, j], s=0.10, c="#607d8b", alpha=0.42)
    ax.plot(joint_centers[:, i], joint_centers[:, j], "#e53935", ls="--", marker="o")
    for index, (center, axis) in enumerate(zip(joint_centers, joint_axes), start=1):
        half_length = 42.0
        p0, p1 = center - half_length * axis, center + half_length * axis
        ax.plot([p0[i], p1[i]], [p0[j], p1[j]], color="#1565c0", lw=2.0)
        ax.text(center[i] + 3, center[j] + 3, f"A{index}", color="#c62828", weight="bold")
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)
    ax.set_title(title)
    ax.set_xlabel(f"{'XYZ'[i]} [mm]")
    ax.set_ylabel(f"{'XYZ'[j]} [mm]")
    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def render_combined_views(
    triangles: np.ndarray, joint_centers: np.ndarray, joint_axes: np.ndarray, output: Path
) -> None:
    centers = triangles.mean(axis=1)
    projections = [((0, 2), "Front (X-Z)"), ((1, 2), "Side (Y-Z)"), ((0, 1), "Top (X-Y)")]
    fig, axes = plt.subplots(1, 3, figsize=(18, 7), dpi=180)
    for ax, ((i, j), title) in zip(axes, projections):
        ax.scatter(centers[::2, i], centers[::2, j], s=0.08, c="#78909c", alpha=0.42)
        ax.plot(joint_centers[:, i], joint_centers[:, j], "#e53935", ls="--", marker="o")
        for index, (center, axis) in enumerate(zip(joint_centers, joint_axes), start=1):
            p0, p1 = center - 42.0 * axis, center + 42.0 * axis
            ax.plot([p0[i], p1[i]], [p0[j], p1[j]], color="#1565c0", lw=1.8)
            ax.text(center[i] + 3, center[j] + 3, f"A{index}", color="#c62828", weight="bold")
        ax.set_aspect("equal")
        ax.grid(alpha=0.2)
        ax.set_title(title)
        ax.set_xlabel(f"{'XYZ'[i]} [mm]")
        ax.set_ylabel(f"{'XYZ'[j]} [mm]")
    fig.suptitle("joints.stl: detected joint centers, unsigned axes, and kinematic skeleton")
    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def render_shell_components(
    triangles: np.ndarray, shells: list[Shell], triangle_to_shell: np.ndarray, output: Path
) -> None:
    centers = triangles.mean(axis=1)
    top_count = min(24, len(shells))
    colors = plt.get_cmap("turbo")(np.linspace(0.03, 0.97, top_count))
    fig, axes = plt.subplots(1, 3, figsize=(18, 7), dpi=180)
    for ax, ((i, j), title) in zip(
        axes, [((0, 2), "Front"), ((1, 2), "Side"), ((0, 1), "Top")]
    ):
        small = triangle_to_shell >= top_count
        ax.scatter(centers[small, i], centers[small, j], s=0.05, c="#b0bec5", alpha=0.20)
        for shell_index in range(top_count - 1, -1, -1):
            mask = triangle_to_shell == shell_index
            ax.scatter(
                centers[mask, i], centers[mask, j], s=0.11, color=colors[shell_index], alpha=0.58
            )
        ax.set_aspect("equal")
        ax.grid(alpha=0.18)
        ax.set_title(title)
        ax.set_xlabel(f"{'XYZ'[i]} [mm]")
        ax.set_ylabel(f"{'XYZ'[j]} [mm]")
    fig.suptitle("24 largest disconnected shells colored separately; smaller shells in gray")
    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def render_skeleton(joints: np.ndarray, axes: np.ndarray, output: Path) -> None:
    fig = plt.figure(figsize=(9, 8), dpi=180)
    ax = fig.add_subplot(111, projection="3d")
    ax.plot(joints[:, 0], joints[:, 1], joints[:, 2], "#e53935", marker="o", lw=2.2)
    for index, (center, axis) in enumerate(zip(joints, axes), start=1):
        p0, p1 = center - 45.0 * axis, center + 45.0 * axis
        ax.plot(*np.vstack([p0, p1]).T, color="#1565c0", lw=3.0)
        ax.text(*center, f" A{index}", color="#b71c1c", weight="bold")
    set_equal_3d(ax, joints.min(axis=0) - 55, joints.max(axis=0) + 55)
    ax.set_proj_type("ortho")
    ax.view_init(elev=22, azim=-58)
    ax.set_xlabel("X [mm]")
    ax.set_ylabel("Y [mm]")
    ax.set_zlabel("Z [mm]")
    ax.set_title("Estimated home-pose kinematic skeleton (axis signs unresolved)")
    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembly", type=Path, required=True)
    parser.add_argument("--phact", type=Path, required=True)
    parser.add_argument("--bearing", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    assembly = read_stl(args.assembly)
    phact = read_stl(args.phact)
    bearing = read_stl(args.bearing)
    shells, triangle_to_shell = disconnected_shells(assembly)
    phact_shells, _ = disconnected_shells(phact)
    bearing_shells, _ = disconnected_shells(bearing)

    phact_reference = phact_shells[0].dimensions
    bearing_reference = bearing_shells[0].dimensions
    detected_phacts = detect_by_envelope(shells, phact_reference, tolerance_mm=1.0)
    detected_bearings = detect_by_envelope(shells, bearing_reference, tolerance_mm=1.0)
    if len(detected_phacts) != 5:
        raise RuntimeError(f"Expected five phact-like housings, detected {len(detected_phacts)}")

    # Sort into physical chain order: base, then increasing-Z pitch modules, then left end module.
    base = min(detected_phacts, key=lambda shell: shell.center[2])
    end = min(detected_phacts, key=lambda shell: shell.center[0])
    middle = sorted(
        [shell for shell in detected_phacts if shell not in (base, end)],
        key=lambda shell: shell.center[2],
    )
    ordered = [base, *middle, end]
    joints = np.vstack([shell.center for shell in ordered])
    axes = np.zeros((5, 3), dtype=float)
    for i, shell in enumerate(ordered):
        axes[i, int(np.argmin(shell.dimensions))] = 1.0

    render_projection(assembly, joints, axes, (0, 2), "Front view (X-Z)", args.output / "front.png")
    render_projection(assembly, joints, axes, (1, 2), "Side view (Y-Z)", args.output / "side.png")
    render_projection(assembly, joints, axes, (0, 1), "Top view (X-Y)", args.output / "top.png")
    render_combined_views(assembly, joints, axes, args.output / "annotated_views.png")
    render_shell_components(assembly, shells, triangle_to_shell, args.output / "shell_components.png")
    render_skeleton(joints, axes, args.output / "kinematic_skeleton.png")

    with (args.output / "shells.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["shell", "triangles", "cx", "cy", "cz", "dx", "dy", "dz", "xmin", "ymin", "zmin", "xmax", "ymax", "zmax"]
        )
        for shell in shells:
            writer.writerow(
                [shell.index, shell.triangle_count, *shell.center.tolist(), *shell.dimensions.tolist(), *shell.lo.tolist(), *shell.hi.tolist()]
            )

    distances = np.linalg.norm(np.diff(joints, axis=0), axis=1)
    summary = {
        "units": "STL unit; interpreted as mm by phact-401 drawing match",
        "assembly_triangles": len(assembly),
        "assembly_shells": len(shells),
        "assembly_bbox_min": assembly.min(axis=(0, 1)).tolist(),
        "assembly_bbox_max": assembly.max(axis=(0, 1)).tolist(),
        "assembly_dimensions": np.ptp(assembly, axis=(0, 1)).tolist(),
        "phact_reference_largest_shell_dimensions": phact_reference.tolist(),
        "detected_phact_housings": [
            {
                "joint": f"A{i}",
                "shell": shell.index,
                "center": shell.center.tolist(),
                "dimensions": shell.dimensions.tolist(),
                "axis_representative": axes[i - 1].tolist(),
                "axis_sign_known": False,
            }
            for i, shell in enumerate(ordered, start=1)
        ],
        "center_to_center_distances": distances.tolist(),
        "bearing_reference_largest_shell_dimensions": bearing_reference.tolist(),
        "detected_bearing_like_shells": [
            {"shell": shell.index, "center": shell.center.tolist(), "dimensions": shell.dimensions.tolist()}
            for shell in detected_bearings
        ],
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

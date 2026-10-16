"""Solids modelled as signed distance fields, as a sculptor models in clay: parts blended into each other, then
turned into a mesh by surface nets, its vertices drawn onto the surface and the grain of the grid smoothed out."""

import bmesh
import bpy
import numpy as np


def ellipsoid(p, centre, radii):
    q = (p - np.asarray(centre)) / np.asarray(radii)
    k0 = np.linalg.norm(q, axis=-1)
    k1 = np.linalg.norm(q / np.asarray(radii), axis=-1)
    return k0 * (k0 - 1) / np.maximum(k1, 1e-9)


def cone(p, a, b, ra, rb):
    """A rod from a to b whose radius runs from ra to rb, rounded at both ends."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(p - a - t[..., None] * ab, axis=-1) - (ra + (rb - ra) * t)


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def sample(field, lo, hi, step, coarse=4):
    """The field on the grid. Only the band round the surface is sampled at the full step: the rest takes the
    value of the coarse grid, coarse steps apart, which is enough to tell inside from out."""
    axes = [np.arange(a, b + step, step) for a, b in zip(lo, hi)]
    shape = tuple(len(a) for a in axes)
    origin = np.asarray(lo, dtype=np.float32)

    def evaluate(index):
        cells = np.stack(index, axis=-1)
        if not len(cells):
            return np.empty(0, dtype=np.float32)
        return np.concatenate([field(origin + chunk.astype(np.float32) * step) for chunk in np.array_split(cells, max(1, len(cells) // 1_000_000))])

    coarse_shape = tuple((n - 1) // coarse + 2 for n in shape)
    rough = evaluate(tuple(i.ravel() * coarse for i in np.indices(coarse_shape))).reshape(coarse_shape)
    nearest = np.ix_(*[(np.arange(n) + coarse // 2) // coarse for n in shape])
    values = rough[nearest].astype(np.float32)
    # A field drawn from blended parts is no true distance: the band is kept wide.
    near = np.nonzero(np.abs(values) < 2.5 * coarse * step)
    values[near] = evaluate(near)
    return values


def nets(field, lo, hi, step):
    """Surface nets: a vertex in every cell the surface passes through, drawn onto the surface, and a quad
    across every edge of the grid the surface cuts."""
    values = sample(field, lo, hi, step)
    inside = values < 0
    corners = [inside[i : inside.shape[0] - 1 + i, j : inside.shape[1] - 1 + j, k : inside.shape[2] - 1 + k] for i in (0, 1) for j in (0, 1) for k in (0, 1)]
    some = np.logical_or.reduce(corners)
    every = np.logical_and.reduce(corners)
    active = some & ~every
    index = np.full(active.shape, -1, dtype=np.int64)
    cells = np.argwhere(active)
    index[active] = np.arange(len(cells))
    origin = np.asarray(lo, dtype=float)
    verts = origin + (cells + 0.5) * step
    # Newton's method, kept inside each vertex's cell.
    for _ in range(4):
        f = field(verts)
        grad = np.stack([(field(verts + e) - field(verts - e)) / (2 * 0.01) for e in np.eye(3) * 0.01], axis=-1)
        verts = verts - (f / np.maximum((grad**2).sum(-1), 1e-9))[:, None] * grad
        verts = np.clip(verts, origin + cells * step, origin + (cells + 1) * step)
    quads = []
    nx, ny, nz = inside.shape
    # Edges along x, y and z, and the four cells round each, in turn.
    for axis, around in (
        (0, ((0, -1, -1), (0, 0, -1), (0, 0, 0), (0, -1, 0))),
        (1, ((-1, 0, -1), (-1, 0, 0), (0, 0, 0), (0, 0, -1))),
        (2, ((-1, -1, 0), (0, -1, 0), (0, 0, 0), (-1, 0, 0))),
    ):
        step_ = np.eye(3, dtype=int)[axis]
        a = inside[: nx - step_[0], : ny - step_[1], : nz - step_[2]]
        b = inside[step_[0] :, step_[1] :, step_[2] :]
        cut = np.argwhere(a != b)
        keep = np.all(cut >= 1, axis=1) & (cut[:, 0] < nx - 1) & (cut[:, 1] < ny - 1) & (cut[:, 2] < nz - 1)
        cut = cut[keep]
        flip = a[tuple(cut.T)]
        corners_ = np.stack([index[tuple((cut + np.asarray(o)).T)] for o in around], axis=1)
        corners_[flip] = corners_[flip][:, ::-1]
        quads.append(corners_[np.all(corners_ >= 0, axis=1)])
    return verts, np.concatenate(quads)


def mesh(stage, name, field, lo, hi, step, material):
    verts, quads = nets(field, lo, hi, step)
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts.tolist(), [], quads.tolist())
    data.validate()
    bm = bmesh.new()
    bm.from_mesh(data)
    # Surface nets leave a faint grain of the grid in the surface; a fired glaze has none.
    for _ in range(4):
        bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(data)
    bm.free()
    data.polygons.foreach_set("use_smooth", [True] * len(data.polygons))
    data.materials.append(material)
    return stage.add(name, data), verts

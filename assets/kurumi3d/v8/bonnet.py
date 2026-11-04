"""Front-facing, dimensional fabric bonnet for the v8 head study.

The curved band spans the forehead rather than lying across the roof of the
skull.  Its lacing therefore remains readable in the front orthographic view.
Coordinates use negative Y as the character's front.  No scene or render state
is changed here.
"""
import math


def build_bonnet(mesh, line, material, red, black):
    created = []
    pi = math.pi
    limit = 1.43

    def band_point(a, u, lift=0.0):
        """u=0 is the brow edge; u=1 is the upper binding."""
        s, c = math.sin(a), math.cos(a)
        x = (.438 + .020 * u) * s
        z = 1.600 + (.332 + .120 * u) * c
        front = -.275 + .080 * s * s
        rear = -.055 - .070 * s * s
        y = front + (rear - front) * u - lift
        # Lay the upper third back over the crown instead of leaving the
        # complete arch upright like a tiara.  Brow and hair-tie anchors stay
        # fixed; the lacing uses this same surface so it cannot separate.
        crown_bend = u * u * max(c, 0.0)**2
        y += .045 * crown_bend
        z -= .015 * crown_bend
        # Slight asymmetry follows the character's relaxed head angle.
        z += .020 * s
        return x, y, z

    def surface(name, point, cols=192, rows=16, mat=red, thick=.003):
        vertices, faces = [], []
        for i in range(cols + 1):
            a = -limit + 2 * limit * i / cols
            for j in range(rows + 1):
                vertices.append(point(a, j / rows))
        stride = rows + 1
        for i in range(cols):
            for j in range(rows):
                k = i * stride + j
                faces.append((k, k + stride, k + stride + 1, k + 1))
        obj = mesh(name, vertices, faces, mat, 1, thick)
        created.append(obj)
        return obj

    # A mildly puffed fabric strip with narrow gathering between bindings.
    def main_band(a, u):
        gathering = .0030 * math.sin(36 * a + .4 * math.sin(7 * a))
        puff = .008 * math.sin(pi * u) + gathering * math.sin(pi * u)**2
        return band_point(a, u, puff)

    surface('Bonnet | curved forehead fabric band', main_band)

    # The top frill is one continuous ribbon.  Its restrained folds curl in
    # depth instead of producing the pointed "crown" silhouette of v7.
    def outer_frill(a, v):
        phase = 26.0 * a + .22 * math.sin(5 * a)
        scallop = .5 + .5 * math.cos(phase)
        extension = .046 + .043 * scallop
        x, y, z = band_point(a, 1.0)
        s, c = math.sin(a), math.cos(a)
        # Broader scallops at the crown, compact gathering toward the ties.
        side_taper = .64 + .36 * max(c, 0.0)
        extent = extension * v * side_taper
        x += extent * s
        z += .85 * extent * c - .008 * v * v * max(c, 0.0)
        # The free edge curls rearwards over the rounded skull.  Its front
        # silhouette is still scalloped, but the side profile is now a low
        # folded ribbon rather than a near-vertical fin.
        y += (.020 + .100 * max(c, 0.0)**1.4) * v
        y += .014 * math.sin(phase + .3) * v
        y -= .018 * math.sin(pi * v)
        # Fine troughs in each gather are modelled, not cut-out jagged edges.
        y += .006 * math.cos(phase * 2) * math.sin(pi * v)**2
        return x, y, z

    surface('Bonnet | continuous scalloped upper ruffle', outer_frill,
            cols=256, rows=20, thick=.0028)

    # The lower frill drapes over the roots of the bangs.  It projects forward
    # and down with soft rolled lobes rather than a flat sawtooth border.
    def inner_frill(a, v):
        phase = 24.0 * a + .32 * math.sin(3 * a) + .8
        scallop = .5 + .5 * math.cos(phase)
        extent = (.026 + .026 * scallop) * v
        x, y, z = band_point(a, 0.0)
        s, c = math.sin(a), math.cos(a)
        x -= extent * s * .72
        z -= extent * c
        y -= .009 + .018 * math.sin(pi * v * .85)
        y += .012 * math.sin(phase) * v
        z += .0045 * math.sin(phase + .4) * math.sin(pi * v)
        return x, y, z

    surface('Bonnet | soft lower gathered frill', inner_frill,
            cols=256, rows=20, thick=.0028)

    # Narrow fabric bindings along both edges; full-width flat ribbons rather
    # than round black wires.  These remain visibly separate from the lacing.
    for edge, label in ((0.0, 'brow'), (1.0, 'upper')):
        surface('Bonnet | flat black ' + label + ' binding',
                lambda a, t, e=edge: band_point(a, e + (t - .5) * .055, .010),
                cols=192, rows=4, mat=black, thick=.002)

    def ribbon(name, a0, a1, upward):
        vertices, faces = [], []
        n = 42
        # A subtle alternating depth avoids coincident meshes at X crossings.
        lift = .017 if upward else .020
        for i in range(n + 1):
            t = i / n
            a = a0 + (a1 - a0) * t
            u = .045 + .91 * (t if upward else 1 - t)
            # x/z-width is measured perpendicular to the ribbon's direction
            # on the band surface, keeping every crossing approximately even.
            da = .012
            du = -(a1-a0) / .91 * da * (.55 if upward else -.55)
            for sign in (-1, 1):
                vertices.append(band_point(a + sign * da,
                                           u + sign * du, lift))
        for i in range(n):
            faces.append((2*i, 2*i+1, 2*i+3, 2*i+2))
        obj = mesh(name, vertices, faces, black, 1, .0018)
        created.append(obj)

    # Five large X-shaped intervals match the readable broad lacing rhythm.
    for i in range(5):
        a0 = -limit + 2 * limit * i / 5
        a1 = -limit + 2 * limit * (i + 1) / 5
        ribbon('Bonnet | woven rising ribbon %02d' % i, a0, a1, True)
        ribbon('Bonnet | woven falling ribbon %02d' % i, a0, a1, False)

    # A very fine rolled seam emphasizes the frill's cloth edge without a
    # bulky wire outline.  It is intentionally the same red as the fabric.
    for name, fn in (('upper', outer_frill), ('lower', inner_frill)):
        points = [fn(-limit + 2 * limit * i / 160, 1.0) for i in range(161)]
        created.append(line('Bonnet | ' + name + ' rolled cloth hem',
                            points, .0016, red))
    return created

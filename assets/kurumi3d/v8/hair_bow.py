"""Open folded-ribbon hair bows, with genuine holes through both loops."""
import math


def build_hair_bow(mesh, line, uvball, center, size, red, black, angle=0):
    """Build a small fabric bow facing -Y; angle rotates in the X/Z plane.

    At size=1 the loops span roughly 0.26 world units, with a 0.13 high
    silhouette.  The two tails are about 0.36 long.  Positive angle raises
    the viewer-right loop.  All parts are real ribbon surfaces or knot mesh;
    no solid petal-shaped patch fills the spaces inside the loops.
    """
    created = []
    cx, cy, cz = center
    ca, sa = math.cos(angle), math.sin(angle)

    def place(p):
        x, y, z = p
        return (cx + size * (ca*x-sa*z),
                cy + size * y,
                cz + size * (sa*x+ca*z))

    def interpolate(points, steps=12):
        result = []
        for i in range(len(points)-1):
            a, b = points[max(i-1, 0)], points[i]
            c, d = points[i+1], points[min(i+2, len(points)-1)]
            for j in range(steps):
                t = j/steps
                result.append(tuple(.5*(2*b[k]+(-a[k]+c[k])*t
                    +(2*a[k]-5*b[k]+4*c[k]-d[k])*t*t
                    +(-a[k]+3*b[k]-3*c[k]+d[k])*t*t*t)
                    for k in range(3)))
        result.append(points[-1])
        return result

    for side in (-1, 1):
        # The centreline goes out along the upper rim, around the folded end,
        # then back along the lower rim.  It leaves an open triangular centre.
        # A small depth twist makes the upper/back and lower/front layers clear.
        points = [
            (side*.009, -.003, .003),
            (side*.056, .000, .039),
            (side*.110, .014, .060),
            (side*.139, .007, .052),
            (side*.130, -.005, .014),
            (side*.105, -.014, -.040),
            (side*.057, -.020, -.022),
            (side*.010, -.013, -.003),
        ]
        points = [(x*.88, y, z) for x, y, z in points]
        # Slightly unequal folds avoid a rigid butterfly silhouette.
        if side == -1:
            points = [(x, y+.004, z*.93-.004*abs(x)/.139)
                      for x, y, z in points]
        path = interpolate(points)
        vertices, faces = [], []
        across_steps = 6
        for i, p in enumerate(path):
            t = i/(len(path)-1)
            previous, following = path[max(i-1, 0)], path[min(i+1, len(path)-1)]
            dx, dz = following[0]-previous[0], following[2]-previous[2]
            length = max(math.hypot(dx, dz), 1e-8)
            nx, nz = -dz/length, dx/length
            width = .007 + .013*math.sin(math.pi*t)**.65
            for j in range(across_steps+1):
                u = 2*j/across_steps-1
                # A convex fold across the strip gives it fabric thickness
                # visually without inflating or closing the hollow centre.
                roll = .0038*(1-u*u)*math.sin(math.pi*t)
                twist = .004*u*math.sin(2*math.pi*t+side*.3)
                vertices.append(place((p[0]+nx*width*u/2,
                                       p[1]-roll+twist,
                                       p[2]+nz*width*u/2)))
        stride = across_steps+1
        for i in range(len(path)-1):
            for j in range(across_steps):
                k=i*stride+j
                faces.append((k,k+1,k+stride+1,k+stride))
        obj=mesh('Hair bow | open folded loop '+str(side),
                 vertices,faces,red,1,.0025*size)
        created.append(obj)

        # Two ribbons leave the same knot, with distinct lengths and light
        # S-folds in depth.  Their final centre vertex lifts to make a V notch.
        vertices, faces = [], []
        rows, cols = 48, 8
        tail_length = .36 if side == -1 else .327
        for i in range(rows+1):
            t=i/rows
            x=side*(.012+.052*t+.010*math.sin(math.pi*t))
            z=-.010-tail_length*t
            y=.002-.020*math.sin(math.pi*t)+.006*math.sin(2*math.pi*t)
            # Cloth leaves the pinch narrow, then spreads to ~0.04 wide.
            width=.014+.027*math.sin(math.pi*.62*t)**.7
            for j in range(cols+1):
                u=2*j/cols-1
                notch=.025*(1-abs(u))*t**16
                wave=.0045*math.sin(math.pi*t)*u*u
                vertices.append(place((x+u*width/2,
                                       y+wave+.002*u*math.sin(3*math.pi*t),
                                       z+notch)))
        stride=cols+1
        for i in range(rows):
            for j in range(cols):
                k=i*stride+j
                faces.append((k,k+1,k+stride+1,k+stride))
        created.append(mesh('Hair bow | V-notched hanging ribbon '+str(side),
                            vertices,faces,red,1,.0022*size))

    # A narrow pinch bound by the knot, not the swollen ball used in v7.
    knot=uvball('Hair bow | narrow fabric knot',place((0,-.022,0)),
                (.0135*size,.014*size,.0235*size),red)
    # uvball local axes are rotated consistently with the front-plane tilt.
    knot.rotation_euler[1]=-angle
    created.append(knot)
    return created

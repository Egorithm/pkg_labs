import matplotlib.pyplot as plt
import matplotlib.patches as patches

class LiangBarskyClipper:
    def __init__(self, xmin, ymin, xmax, ymax):
        self.xmin, self.ymin, self.xmax, self.ymax = xmin, ymin, xmax, ymax

    def clip(self, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        p = [-dx, dx, -dy, dy]
        q = [x1 - self.xmin, self.xmax - x1, y1 - self.ymin, self.ymax - y1]
        u1, u2 = 0.0, 1.0
        for i in range(4):
            if p[i] == 0:
                if q[i] < 0: return None
            else:
                t = q[i] / p[i]
                if p[i] < 0: u1 = max(u1, t)
                else: u2 = min(u2, t)
        if u1 > u2: return None
        return [(x1 + u1 * dx, y1 + u1 * dy), (x1 + u2 * dx, y1 + u2 * dy)]

class SutherlandHodgmanClipper:
    def __init__(self, xmin, ymin, xmax, ymax):
        self.xmin, self.ymin, self.xmax, self.ymax = xmin, ymin, xmax, ymax

    def clip(self, polygon):
        def clip_with_edge(vertices, edge_type):
            new_vertices = []
            for i in range(len(vertices)):
                p1 = vertices[i]
                p2 = vertices[(i + 1) % len(vertices)]
                
                def is_inside(p):
                    if edge_type == 0: return p[0] >= self.xmin
                    if edge_type == 1: return p[0] <= self.xmax
                    if edge_type == 2: return p[1] >= self.ymin
                    if edge_type == 3: return p[1] <= self.ymax
                    return False

                def intersect(p1, p2):
                    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
                    if edge_type == 0:
                        return (self.xmin, p1[1] + dy * (self.xmin - p1[0]) / dx)
                    if edge_type == 1:
                        return (self.xmax, p1[1] + dy * (self.xmax - p1[0]) / dx)
                    if edge_type == 2:
                        return (p1[0] + dx * (self.ymin - p1[1]) / dy, self.ymin)
                    if edge_type == 3:
                        return (p1[0] + dx * (self.ymax - p1[1]) / dy, self.ymax)

                inside1, inside2 = is_inside(p1), is_inside(p2)

                if inside1 and inside2:
                    new_vertices.append(p2)
                elif inside1 and not inside2:
                    new_vertices.append(intersect(p1, p2))
                elif not inside1 and inside2:
                    new_vertices.append(intersect(p1, p2))
                    new_vertices.append(p2)
            return new_vertices

        result = polygon
        for edge in range(4):
            result = clip_with_edge(result, edge)
            if not result: break
        return result

def visualize(segments, polygon, window, clipped_segments, clipped_poly):
    fig, ax = plt.subplots(figsize=(10, 10))
    
    rect = patches.Rectangle((window[0], window[1]), window[2]-window[0], window[3]-window[1],
                             linewidth=2, edgecolor='green', facecolor='none', label='Clipping Window', zorder=5)
    ax.add_patch(rect)
    
    for seg in segments:
        ax.plot([seg[0][0], seg[1][0]], [seg[0][1], seg[1][1]], 'b--', alpha=0.3)
    
    for seg in clipped_segments:
        if seg:
            ax.plot([seg[0][0], seg[1][0]], [seg[0][1], seg[1][1]], 'blue', linewidth=2, 
                    label='Clipped Lines' if seg == next(s for s in clipped_segments if s) else "")

    if polygon:
        orig_poly = patches.Polygon(polygon, closed=True, linewidth=1, edgecolor='red', 
                                    facecolor='red', alpha=0.1, label='Original Polygon')
        ax.add_patch(orig_poly)
    
    if clipped_poly:
        res_poly = patches.Polygon(clipped_poly, closed=True, linewidth=2, edgecolor='red', 
                                   facecolor='red', alpha=0.4, label='Clipped Polygon')
        ax.add_patch(res_poly)

    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Line (Liang-Barsky) and Polygon (Sutherland-Hodgman) Clipping')
    ax.legend()
    plt.tight_layout()
    plt.show()

def main():
    window = (50, 50, 150, 150)
    
    segments = [
        ((20, 20), (180, 180)),
        ((100, 10), (100, 190)),
        ((10, 100), (40, 100))
    ]
    
    polygon = [(30, 80), (120, 180), (180, 80), (100, 20)]

    lb_clipper = LiangBarskyClipper(*window)
    clipped_segments = [lb_clipper.clip(s[0][0], s[0][1], s[1][0], s[1][1]) for s in segments]

    sh_clipper = SutherlandHodgmanClipper(*window)
    clipped_poly = sh_clipper.clip(polygon)

    print(f"Clipping Window: {window}")
    print("\nPolygon Clipping Result:")
    if clipped_poly:
        print(f"Number of vertices: {len(clipped_poly)}")
        for i, p in enumerate(clipped_poly):
            print(f"  Vertex {i+1}: ({p[0]:.2f}, {p[1]:.2f})")
    else:
        print("  Polygon is completely outside.")

    visualize(segments, polygon, window, clipped_segments, clipped_poly)

if __name__ == "__main__":
    main()
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import sys
import locale

class CyrillicLetterK3D:
    def __init__(self):
        self.vertices = np.array([
            [0, 0, 0],
            [3, 0, 0],
            [3, 10, 0],
            [0, 10, 0],
            [0, 0, 2],
            [3, 0, 2],
            [3, 10, 2],
            [0, 10, 2],
            [3, 5, 0],
            [6, 10, 0],
            [9, 10, 0],
            [6, 5, 0],
            [3, 5, 2],
            [6, 10, 2],
            [9, 10, 2],
            [6, 5, 2],
            [3, 5, 0],
            [6, 0, 0],
            [9, 0, 0],
            [6, 5, 0],
            [3, 5, 2],
            [6, 0, 2],
            [9, 0, 2],
            [6, 5, 2],
        ])
        
        self.faces = [
            [0, 1, 2, 3],
            [4, 5, 6, 7],
            [0, 1, 5, 4],
            [2, 3, 7, 6],
            [0, 3, 7, 4],
            [1, 2, 6, 5],
            [8, 9, 10, 11],
            [12, 13, 14, 15],
            [8, 9, 13, 12],
            [10, 11, 15, 14],
            [8, 11, 15, 12],
            [9, 10, 14, 13],
            [16, 17, 18, 19],
            [20, 21, 22, 23],
            [16, 17, 21, 20],
            [18, 19, 23, 22],
            [16, 19, 23, 20],
            [17, 18, 22, 21],
            [2, 8, 12, 6],
            [1, 16, 20, 5],
        ]
        
        self.face_colors = [
            [0.8, 0.5, 0.2, 0.8],
            [0.7, 0.4, 0.1, 0.8],
            [0.6, 0.3, 0.0, 0.8],
            [0.9, 0.6, 0.3, 0.8],
            [0.7, 0.4, 0.1, 0.8],
            [0.8, 0.5, 0.2, 0.8],
            [0.2, 0.5, 0.8, 0.8],
            [0.1, 0.4, 0.7, 0.8],
            [0.0, 0.3, 0.6, 0.8],
            [0.3, 0.6, 0.9, 0.8],
            [0.1, 0.4, 0.7, 0.8],
            [0.2, 0.5, 0.8, 0.8],
            [0.5, 0.8, 0.2, 0.8],
            [0.4, 0.7, 0.1, 0.8],
            [0.3, 0.6, 0.0, 0.8],
            [0.6, 0.9, 0.3, 0.8],
            [0.4, 0.7, 0.1, 0.8],
            [0.5, 0.8, 0.2, 0.8],
            [0.7, 0.7, 0.7, 0.8],
            [0.7, 0.7, 0.7, 0.8],
        ]
        
        self.original_vertices = self.vertices.copy()
        self.transform_matrix = np.eye(4)
        self.scale = [1.0, 1.0, 1.0]
        self.translate = [0.0, 0.0, 0.0]
        self.rotate = [0.0, 0.0, 0.0]
    
    def get_transformed_vertices(self):
        return self.vertices.copy()
    
    def get_transformed_faces(self):
        transformed_faces = []
        for face in self.faces:
            transformed_face = []
            for vertex_idx in face:
                transformed_face.append(self.vertices[vertex_idx])
            transformed_faces.append(transformed_face)
        return transformed_faces
    
    def update_transform(self):
        self.vertices = self.original_vertices.copy()
        self.apply_scaling()
        self.apply_rotation()
        self.apply_translation()
        self.update_final_matrix()
    
    def apply_scaling(self):
        scale_matrix = np.array([
            [self.scale[0], 0, 0, 0],
            [0, self.scale[1], 0, 0],
            [0, 0, self.scale[2], 0],
            [0, 0, 0, 1]
        ])
        
        for i in range(len(self.vertices)):
            v = np.append(self.vertices[i], 1)
            v_transformed = scale_matrix @ v
            self.vertices[i] = v_transformed[:3]
    
    def apply_rotation(self):
        rx = np.radians(self.rotate[0])
        ry = np.radians(self.rotate[1])
        rz = np.radians(self.rotate[2])
        
        Rx = np.array([
            [1, 0, 0, 0],
            [0, np.cos(rx), -np.sin(rx), 0],
            [0, np.sin(rx), np.cos(rx), 0],
            [0, 0, 0, 1]
        ])
        
        Ry = np.array([
            [np.cos(ry), 0, np.sin(ry), 0],
            [0, 1, 0, 0],
            [-np.sin(ry), 0, np.cos(ry), 0],
            [0, 0, 0, 1]
        ])
        
        Rz = np.array([
            [np.cos(rz), -np.sin(rz), 0, 0],
            [np.sin(rz), np.cos(rz), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        R_combined = Rz @ Ry @ Rx
        
        for i in range(len(self.vertices)):
            v = np.append(self.vertices[i], 1)
            v_transformed = R_combined @ v
            self.vertices[i] = v_transformed[:3]
    
    def apply_translation(self):
        for i in range(len(self.vertices)):
            self.vertices[i][0] += self.translate[0]
            self.vertices[i][1] += self.translate[1]
            self.vertices[i][2] += self.translate[2]
    
    def update_final_matrix(self):
        S = np.array([
            [self.scale[0], 0, 0, 0],
            [0, self.scale[1], 0, 0],
            [0, 0, self.scale[2], 0],
            [0, 0, 0, 1]
        ])
        
        rx = np.radians(self.rotate[0])
        ry = np.radians(self.rotate[1])
        rz = np.radians(self.rotate[2])
        
        Rx = np.array([
            [1, 0, 0, 0],
            [0, np.cos(rx), -np.sin(rx), 0],
            [0, np.sin(rx), np.cos(rx), 0],
            [0, 0, 0, 1]
        ])
        
        Ry = np.array([
            [np.cos(ry), 0, np.sin(ry), 0],
            [0, 1, 0, 0],
            [-np.sin(ry), 0, np.cos(ry), 0],
            [0, 0, 0, 1]
        ])
        
        Rz = np.array([
            [np.cos(rz), -np.sin(rz), 0, 0],
            [np.sin(rz), np.cos(rz), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        R = Rz @ Ry @ Rx
        
        T = np.array([
            [1, 0, 0, self.translate[0]],
            [0, 1, 0, self.translate[1]],
            [0, 0, 1, self.translate[2]],
            [0, 0, 0, 1]
        ])
        
        self.transform_matrix = T @ R @ S
    
    def get_projection_xy(self):
        proj = []
        for v in self.vertices:
            proj.append([v[0], v[1]])
        return np.array(proj)
    
    def get_projection_xz(self):
        proj = []
        for v in self.vertices:
            proj.append([v[0], v[2]])
        return np.array(proj)
    
    def get_projection_yz(self):
        proj = []
        for v in self.vertices:
            proj.append([v[1], v[2]])
        return np.array(proj)


class Visualization3D:
    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except locale.Error:
            locale.setlocale(locale.LC_ALL, 'C')
        
        self.letter = CyrillicLetterK3D()
        
        self.fig = plt.figure(figsize=(16, 12))
        
        self.ax3d = self.fig.add_subplot(221, projection='3d')
        self.ax_xy = self.fig.add_subplot(222)
        self.ax_xz = self.fig.add_subplot(223)
        self.ax_yz = self.fig.add_subplot(224)
        
        self.setup_sliders()
        self.setup_reset_button()
        self.setup_matrix_display()
        
        self.update_visualization()
        
        plt.subplots_adjust(left=0.07, right=0.93, top=0.92, bottom=0.28, wspace=0.25, hspace=0.3)
        plt.show()
    
    def setup_sliders(self):
        axcolor = 'lightgoldenrodyellow'
        
        ax_scale_x = plt.axes([0.07, 0.20, 0.25, 0.02], facecolor=axcolor)
        ax_scale_y = plt.axes([0.07, 0.17, 0.25, 0.02], facecolor=axcolor)
        ax_scale_z = plt.axes([0.07, 0.14, 0.25, 0.02], facecolor=axcolor)
        
        self.scale_x_slider = Slider(ax_scale_x, 'Scale X', 0.1, 3.0, valinit=1.0)
        self.scale_y_slider = Slider(ax_scale_y, 'Scale Y', 0.1, 3.0, valinit=1.0)
        self.scale_z_slider = Slider(ax_scale_z, 'Scale Z', 0.1, 3.0, valinit=1.0)
        
        ax_rot_x = plt.axes([0.40, 0.20, 0.25, 0.02], facecolor=axcolor)
        ax_rot_y = plt.axes([0.40, 0.17, 0.25, 0.02], facecolor=axcolor)
        ax_rot_z = plt.axes([0.40, 0.14, 0.25, 0.02], facecolor=axcolor)
        
        self.rot_x_slider = Slider(ax_rot_x, 'Rotate X', -180, 180, valinit=0)
        self.rot_y_slider = Slider(ax_rot_y, 'Rotate Y', -180, 180, valinit=0)
        self.rot_z_slider = Slider(ax_rot_z, 'Rotate Z', -180, 180, valinit=0)
        
        ax_trans_x = plt.axes([0.73, 0.20, 0.20, 0.02], facecolor=axcolor)
        ax_trans_y = plt.axes([0.73, 0.17, 0.20, 0.02], facecolor=axcolor)
        ax_trans_z = plt.axes([0.73, 0.14, 0.20, 0.02], facecolor=axcolor)
        
        self.trans_x_slider = Slider(ax_trans_x, 'Translate X', -20, 20, valinit=0)
        self.trans_y_slider = Slider(ax_trans_y, 'Translate Y', -20, 20, valinit=0)
        self.trans_z_slider = Slider(ax_trans_z, 'Translate Z', -20, 20, valinit=0)
        
        self.scale_x_slider.on_changed(self.update_sliders)
        self.scale_y_slider.on_changed(self.update_sliders)
        self.scale_z_slider.on_changed(self.update_sliders)
        self.rot_x_slider.on_changed(self.update_sliders)
        self.rot_y_slider.on_changed(self.update_sliders)
        self.rot_z_slider.on_changed(self.update_sliders)
        self.trans_x_slider.on_changed(self.update_sliders)
        self.trans_y_slider.on_changed(self.update_sliders)
        self.trans_z_slider.on_changed(self.update_sliders)
    
    def setup_reset_button(self):
        resetax = plt.axes([0.73, 0.08, 0.20, 0.04])
        self.reset_button = Button(resetax, 'Reset All', color='lightgoldenrodyellow')
        self.reset_button.on_clicked(self.reset_parameters)
    
    def setup_matrix_display(self):
        self.matrix_ax = self.fig.add_axes([0.07, 0.02, 0.86, 0.06])
        self.matrix_ax.axis('off')
        self.matrix_text = self.matrix_ax.text(0.02, 0.5, '', fontsize=9, 
                                               fontfamily='monospace',
                                               verticalalignment='center',
                                               bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    def update_sliders(self, val):
        self.letter.scale = [
            self.scale_x_slider.val,
            self.scale_y_slider.val,
            self.scale_z_slider.val
        ]
        
        self.letter.rotate = [
            self.rot_x_slider.val,
            self.rot_y_slider.val,
            self.rot_z_slider.val
        ]
        
        self.letter.translate = [
            self.trans_x_slider.val,
            self.trans_y_slider.val,
            self.trans_z_slider.val
        ]
        
        self.update_visualization()
    
    def reset_parameters(self, event):
        self.scale_x_slider.set_val(1.0)
        self.scale_y_slider.set_val(1.0)
        self.scale_z_slider.set_val(1.0)
        self.rot_x_slider.set_val(0)
        self.rot_y_slider.set_val(0)
        self.rot_z_slider.set_val(0)
        self.trans_x_slider.set_val(0)
        self.trans_y_slider.set_val(0)
        self.trans_z_slider.set_val(0)
        self.update_visualization()
    
    def draw_3d_view(self):
        self.ax3d.clear()
        
        faces = self.letter.get_transformed_faces()
        
        poly3d = Poly3DCollection(faces, alpha=0.8)
        
        poly3d.set_facecolor(self.letter.face_colors)
        poly3d.set_edgecolor([0, 0, 0, 0.5])
        poly3d.set_linewidth(0.5)
        
        self.ax3d.add_collection3d(poly3d)
        
        self.ax3d.set_xlabel('X')
        self.ax3d.set_ylabel('Y')
        self.ax3d.set_zlabel('Z')
        self.ax3d.set_title('3D Solid Model of Cyrillic Letter K')
        
        vertices = self.letter.get_transformed_vertices()
        
        max_range = np.array([
            vertices[:, 0].max() - vertices[:, 0].min(),
            vertices[:, 1].max() - vertices[:, 1].min(),
            vertices[:, 2].max() - vertices[:, 2].min()
        ]).max() / 2.0
        
        mid_x = (vertices[:, 0].max() + vertices[:, 0].min()) * 0.5
        mid_y = (vertices[:, 1].max() + vertices[:, 1].min()) * 0.5
        mid_z = (vertices[:, 2].max() + vertices[:, 2].min()) * 0.5
        
        self.ax3d.set_xlim(mid_x - max_range, mid_x + max_range)
        self.ax3d.set_ylim(mid_y - max_range, mid_y + max_range)
        self.ax3d.set_zlim(mid_z - max_range, mid_z + max_range)
        
        self.ax3d.view_init(elev=20, azim=45)
    
    def draw_projection_xy(self):
        self.ax_xy.clear()
        
        vertices = self.letter.get_transformed_vertices()
        faces = self.letter.faces
        
        for face in faces:
            x_coords = [vertices[idx][0] for idx in face]
            y_coords = [vertices[idx][1] for idx in face]
            x_coords.append(x_coords[0])
            y_coords.append(y_coords[0])
            self.ax_xy.plot(x_coords, y_coords, 'b-', linewidth=1, alpha=0.7)
        
        proj_xy = self.letter.get_projection_xy()
        self.ax_xy.scatter(proj_xy[:, 0], proj_xy[:, 1], c='r', s=20, alpha=0.6)
        
        self.ax_xy.set_xlabel('X')
        self.ax_xy.set_ylabel('Y')
        self.ax_xy.set_title('Projection on XY Plane')
        self.ax_xy.grid(True, linestyle='--', alpha=0.7)
        self.ax_xy.set_aspect('equal', adjustable='box')
    
    def draw_projection_xz(self):
        self.ax_xz.clear()
        
        vertices = self.letter.get_transformed_vertices()
        faces = self.letter.faces
        
        for face in faces:
            x_coords = [vertices[idx][0] for idx in face]
            z_coords = [vertices[idx][2] for idx in face]
            x_coords.append(x_coords[0])
            z_coords.append(z_coords[0])
            self.ax_xz.plot(x_coords, z_coords, 'g-', linewidth=1, alpha=0.7)
        
        proj_xz = self.letter.get_projection_xz()
        self.ax_xz.scatter(proj_xz[:, 0], proj_xz[:, 1], c='r', s=20, alpha=0.6)
        
        self.ax_xz.set_xlabel('X')
        self.ax_xz.set_ylabel('Z')
        self.ax_xz.set_title('Projection on XZ Plane')
        self.ax_xz.grid(True, linestyle='--', alpha=0.7)
        self.ax_xz.set_aspect('equal', adjustable='box')
    
    def draw_projection_yz(self):
        self.ax_yz.clear()
        
        vertices = self.letter.get_transformed_vertices()
        faces = self.letter.faces
        
        for face in faces:
            y_coords = [vertices[idx][1] for idx in face]
            z_coords = [vertices[idx][2] for idx in face]
            y_coords.append(y_coords[0])
            z_coords.append(z_coords[0])
            self.ax_yz.plot(y_coords, z_coords, 'm-', linewidth=1, alpha=0.7)
        
        proj_yz = self.letter.get_projection_yz()
        self.ax_yz.scatter(proj_yz[:, 0], proj_yz[:, 1], c='r', s=20, alpha=0.6)
        
        self.ax_yz.set_xlabel('Y')
        self.ax_yz.set_ylabel('Z')
        self.ax_yz.set_title('Projection on YZ Plane')
        self.ax_yz.grid(True, linestyle='--', alpha=0.7)
        self.ax_yz.set_aspect('equal', adjustable='box')
    
    def update_matrix_display(self):
        matrix_str = "TRANSFORMATION MATRIX (4×4):\n"
        matrix_str += "=" * 50 + "\n"
        
        for i in range(4):
            row = "|"
            for j in range(4):
                row += f" {self.letter.transform_matrix[i, j]:8.3f} "
            row += "|"
            matrix_str += row + "\n"
        
        matrix_str += "=" * 50 + "\n"
        matrix_str += f"Scale: X={self.letter.scale[0]:.2f}, Y={self.letter.scale[1]:.2f}, Z={self.letter.scale[2]:.2f}  |  "
        matrix_str += f"Rotation: X={self.letter.rotate[0]:.1f}°, Y={self.letter.rotate[1]:.1f}°, Z={self.letter.rotate[2]:.1f}°  |  "
        matrix_str += f"Translation: X={self.letter.translate[0]:.2f}, Y={self.letter.translate[1]:.2f}, Z={self.letter.translate[2]:.2f}"
        
        self.matrix_text.set_text(matrix_str)
    
    def update_visualization(self):
        self.letter.update_transform()
        self.draw_3d_view()
        self.draw_projection_xy()
        self.draw_projection_xz()
        self.draw_projection_yz()
        self.update_matrix_display()
        self.fig.canvas.draw_idle()


def main():    
        viz = Visualization3D()
if __name__ == "__main__":
    main()
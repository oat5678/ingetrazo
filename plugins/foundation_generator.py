import math
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QComboBox, 
                               QDoubleSpinBox, QPushButton, QMessageBox, QHBoxLayout)
from PySide6.QtGui import QVector3D
from core.history import SnapshotImport

# ==========================================================
# 1. โมดูลคำนวณเรขาคณิต (Geometry)
# ==========================================================
def round_up_to_05(n):
    if n <= 0: return 0.0
    return math.ceil(n * 20) / 20

def rotate_points(points, angle_deg):
    angle_rad = math.radians(angle_deg)
    return [(p[0] * math.cos(angle_rad) - p[1] * math.sin(angle_rad),
             p[0] * math.sin(angle_rad) + p[1] * math.cos(angle_rad)) for p in points]

def get_final_f3_geometry(D):
    D1 = 3 * D
    C = 1.5 * D
    h_piles = (math.sqrt(3) / 2) * D1

    y_centroid_piles = ((2/3 * h_piles) + 2 * (-1/3 * h_piles)) / 3
    pile_positions = [
        (0, (2/3) * h_piles - y_centroid_piles),
        (-D1 / 2, (-1/3) * h_piles - y_centroid_piles),
        (D1 / 2, (-1/3) * h_piles - y_centroid_piles)
    ]
    
    y_top = pile_positions[0][1] + C
    y_bottom = pile_positions[1][1] - C
    y_side = pile_positions[1][1]
    
    x_top_half = D1 / (2 * math.sqrt(3))
    x_side_half = y_top
    x_bottom_half = abs(y_bottom)
    
    footing_vertices_raw = [
        (x_top_half, y_top), (-x_top_half, y_top),
        (-x_side_half, y_side), (-x_bottom_half, y_bottom),
        (x_bottom_half, y_bottom), (x_side_half, y_side)
    ]
    
    y_centroid_footing = sum(v[1] for v in footing_vertices_raw) / 6
    final_vertices = [(v[0], v[1] - y_centroid_footing) for v in footing_vertices_raw]
    
    return pile_positions, final_vertices

def calculate_footing_dimensions(layout, D):
    E = round_up_to_05(1.5 * D)
    S = round_up_to_05(3 * D)
    S_prime = round_up_to_05(3 * math.sqrt(2) * D)
    layouts_dim = {
        'F1': (E * 2, E * 2), 'F2A': (E * 2, E * 2 + S), 'F2B': (E * 2 + S, E * 2),
        'F4': (E * 2 + S, E * 2 + S), 'F5': (E * 2 + S_prime, E * 2 + S_prime),
        'F6A': (E * 2 + S, E * 2 + S * 2), 'F6B': (E * 2 + S * 2, E * 2 + S),
        'F7A': (E * 2 + S_prime, E * 2 + S * 2), 'F7B': (E * 2 + S * 2, E * 2 + S_prime),
        'F8A-1': (E * 2 + S, E * 2 + S * 3), 'F8A-2': (E * 2 + S * 3, E * 2 + S),
        'F8B-1': (E * 2 + S_prime * 2, E * 2 + S_prime),
        'F8B-2': (2 * E + 1.25, 2 * E + 2.40)
    }
    return layouts_dim.get(layout, (0, 0))

def get_pile_positions_local(layout, D):
    if layout.startswith('F3'):
        piles, _ = get_final_f3_geometry(D)
        angle = {'F3A':0, 'F3B':180, 'F3C':90, 'F3D':270}.get(layout, 0)
        return rotate_points(piles, angle)

    S = round_up_to_05(3 * D)
    S_prime = round_up_to_05(3 * math.sqrt(2) * D)
    base_positions = {
        'F1': [(0, 0)],
        'F2A': [(0, -S / 2), (0, S / 2)],
        'F4': [(-S/2, -S/2), (S/2, -S/2), (-S/2, S/2), (S/2, S/2)],
        'F5': [(-S_prime/2,-S_prime/2),(S_prime/2,-S_prime/2),(-S_prime/2,S_prime/2),(S_prime/2,S_prime/2),(0,0)],
        'F6A': [(-S/2,-S),(-S/2,0),(-S/2,S),(S/2,-S),(S/2,0),(S/2,S)],
        'F7A': [(0,S),(-S_prime/2,S/2),(S_prime/2,S/2),(0,0),(-S_prime/2,-S/2),(S_prime/2,-S/2),(0,-S)],
        'F8A-1': [(-S/2,-S*1.5),(-S/2,-S/2),(-S/2,S/2),(-S/2,S*1.5),(S/2,-S*1.5),(S/2,-S/2),(S/2,S/2),(S/2,S*1.5)],
        'F8B-1': [(-S_prime,-S_prime/2),(0,-S_prime/2),(S_prime,-S_prime/2),(-S_prime/2,0),(S_prime/2,0),
                 (-S_prime,S_prime/2),(0,S_prime/2),(S_prime,S_prime/2)],
        'F8B-2': [(-0.625, 1.20), (0.625, 1.20), (0, 0.60), (-0.625, 0), (0.625, 0),
                  (0, -0.60), (-0.625, -1.20), (0.625, -1.20)]
    }
    base_key = layout.replace('B','A').replace('-2','-1')
    if layout in base_positions: return base_positions[layout]
    elif layout in ['F2B', 'F6B', 'F7B', 'F8A-2']: return rotate_points(base_positions[base_key], 90)
    return []

# ฟังก์ชันตัวช่วย: วาดกล่อง/แท่ง 3D จากระนาบ 2D
def create_extrusion(mesh, verts_2d, z_top, z_bottom):
    mesh.add_face([QVector3D(v[0], v[1], z_top) for v in verts_2d])
    mesh.add_face([QVector3D(v[0], v[1], z_bottom) for v in reversed(verts_2d)])
    n = len(verts_2d)
    for i in range(n):
        v1 = verts_2d[i]
        v2 = verts_2d[(i+1)%n]
        mesh.add_face([
            QVector3D(v1[0], v1[1], z_top),
            QVector3D(v2[0], v2[1], z_top),
            QVector3D(v2[0], v2[1], z_bottom),
            QVector3D(v1[0], v1[1], z_bottom)
        ])

# ==========================================================
# 2. ส่วนติดต่อผู้ใช้ (UI) และการวาด 3D
# ==========================================================
class FootingGeneratorDialog(QDialog):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.setWindowTitle("วาดฐานราก 3D (F-Plan)")
        self.resize(400, 450)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.layout_cb = QComboBox()
        self.layout_cb.addItems(['F1', 'F2A', 'F2B', 'F3A', 'F3B', 'F3C', 'F3D', 'F4', 'F5', 
                                 'F6A', 'F6B', 'F7A', 'F7B', 'F8A-1', 'F8A-2', 'F8B-1', 'F8B-2'])
        form.addRow("ประเภทฐานราก:", self.layout_cb)
        
        self.pile_type_cb = QComboBox()
        self.pile_type_cb.addItems(['Square (สี่เหลี่ยม)', 'Circle (กลม)', 'I-Beam (ตัวไอ)'])
        form.addRow("รูปร่างเสาเข็ม:", self.pile_type_cb)
        
        self.d_spin = QDoubleSpinBox(); self.d_spin.setValue(0.40); self.d_spin.setSingleStep(0.05)
        form.addRow("ขนาดเสาเข็ม (D) [m]:", self.d_spin)
        
        # ปรับการรับค่าตอม่อให้รับ 2 แกน X, Y
        pier_layout = QHBoxLayout()
        self.pier_x_spin = QDoubleSpinBox(); self.pier_x_spin.setValue(0.40); self.pier_x_spin.setSingleStep(0.05)
        self.pier_y_spin = QDoubleSpinBox(); self.pier_y_spin.setValue(0.40); self.pier_y_spin.setSingleStep(0.05)
        pier_layout.addWidget(self.pier_x_spin)
        pier_layout.addWidget(self.pier_y_spin)
        form.addRow("ขนาดตอม่อ แกน X(แดง), Y(เขียว) [m]:", pier_layout)
        
        self.pier_h_spin = QDoubleSpinBox(); self.pier_h_spin.setValue(1.00); self.pier_h_spin.setSingleStep(0.1)
        form.addRow("ความสูงตอม่อ (จาก 0.00) [m]:", self.pier_h_spin)
        
        self.thick_spin = QDoubleSpinBox(); self.thick_spin.setValue(0.50); self.thick_spin.setSingleStep(0.1)
        form.addRow("ความหนาฐานราก (จาก 0.00 ลงไป) [m]:", self.thick_spin)
        
        coord_layout = QHBoxLayout()
        self.x_spin = QDoubleSpinBox(); self.x_spin.setRange(-1000, 1000)
        self.y_spin = QDoubleSpinBox(); self.y_spin.setRange(-1000, 1000)
        coord_layout.addWidget(self.x_spin); coord_layout.addWidget(self.y_spin)
        form.addRow("พิกัด Grid X, Y [m]:", coord_layout)
        
        layout.addLayout(form)
        
        btn = QPushButton("สร้างฐานราก 3D")
        btn.clicked.connect(self.generate_3d)
        layout.addWidget(btn)

    def generate_3d(self):
        layout_type = self.layout_cb.currentText()
        pile_shape = self.pile_type_cb.currentText().split()[0]
        D = self.d_spin.value()
        Dp_x = self.pier_x_spin.value()
        Dp_y = self.pier_y_spin.value()
        pier_h = self.pier_h_spin.value()
        thick = self.thick_spin.value()
        off_x = self.x_spin.value()
        off_y = self.y_spin.value()

        def mutate(scene):
            mesh = scene.mesh
            
            # --- สร้างเส้น Grid Line ที่ระดับ Z=0 ---
            grid_ext = 2.0
            mesh.add_edge(QVector3D(off_x - grid_ext, off_y, 0), QVector3D(off_x + grid_ext, off_y, 0))
            mesh.add_edge(QVector3D(off_x, off_y - grid_ext, 0), QVector3D(off_x, off_y + grid_ext, 0))

            # --- 1. วาดตอม่อ (Pier) จาก Z=0 ถึง Z=pier_h ---
            hw_px = Dp_x / 2
            hw_py = Dp_y / 2
            pier_verts_2d = [
                (off_x - hw_px, off_y - hw_py), (off_x + hw_px, off_y - hw_py),
                (off_x + hw_px, off_y + hw_py), (off_x - hw_px, off_y + hw_py)
            ]
            create_extrusion(mesh, pier_verts_2d, pier_h, 0.0)

            # --- 2. วาดฐานราก (Footing) จาก Z=0 ถึง Z=-thick ---
            if layout_type.startswith('F3'):
                _, base_verts = get_final_f3_geometry(D)
                angle = {'F3A':0, 'F3B':180, 'F3C':90, 'F3D':270}.get(layout_type, 0)
                verts_2d = rotate_points(base_verts, angle)
            else:
                w, h = calculate_footing_dimensions(layout_type, D)
                bl_x, bl_y = -w/2, -h/2
                verts_2d = [(bl_x, bl_y), (bl_x+w, bl_y), (bl_x+w, bl_y+h), (bl_x, bl_y+h)]

            ft_verts_2d = [(v[0]+off_x, v[1]+off_y) for v in verts_2d]
            create_extrusion(mesh, ft_verts_2d, 0.0, -thick)

            # --- 3. วาดเสาเข็ม (Piles) จาก Z=-thick ถึง Z=-thick-pile_depth ---
            piles = get_pile_positions_local(layout_type, D)
            pile_depth = 1.0
            
            for px, py in piles:
                cx, cy = px + off_x, py + off_y
                p_verts = []
                
                if pile_shape == 'Square':
                    hw = D / 2
                    p_verts = [(cx-hw, cy-hw), (cx+hw, cy-hw), (cx+hw, cy+hw), (cx-hw, cy+hw)]
                elif pile_shape == 'Circle':
                    r = D / 2
                    for i in range(16):
                        a = 2 * math.pi * i / 16
                        p_verts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
                elif pile_shape == 'I-Beam':
                    hw = D / 2
                    fw = 0.05
                    p_verts = [
                        (cx-hw, cy-hw), (cx+hw, cy-hw), (cx+hw, cy-hw+fw),
                        (cx+fw, cy-hw+fw), (cx+fw, cy+hw-fw), (cx+hw, cy+hw-fw),
                        (cx+hw, cy+hw), (cx-hw, cy+hw), (cx-hw, cy+hw-fw),
                        (cx-fw, cy+hw-fw), (cx-fw, cy-hw+fw), (cx-hw, cy-hw+fw)
                    ]
                
                create_extrusion(mesh, p_verts, -thick, -thick - pile_depth)

        try:
            cmd = SnapshotImport(mutate)
            self.app.viewport.history.execute(cmd)
            self.app.viewport.notify_scene_changed()
            QMessageBox.information(self, "สำเร็จ", f"สร้างฐานราก {layout_type} เรียบร้อยแล้ว!")
        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", f"เกิดข้อผิดพลาด:\n{str(e)}")

# ==========================================================
# 3. ลงทะเบียนเมนู Extension
# ==========================================================
def setup(app):
    app.add_menu_action("วาดฐานราก 3D (F-Plan)", lambda: FootingGeneratorDialog(app, app.window).show())
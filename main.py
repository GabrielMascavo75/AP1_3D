import pygame
import math
import random
import os

# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================
WIDTH = 1200
HEIGHT = 700
FPS = 60

# Duração total da animação, em segundos. Ao chegar nesse
# tempo, a animação para sozinha em vez de reiniciar em loop.
ANIM_DURATION = 10.0

COLOR_BG = (12, 14, 22)
COLOR_HUD_BG = (20, 25, 38, 200)
COLOR_TEXT_PRIMARY = (235, 240, 250)
COLOR_TEXT_SECONDARY = (160, 175, 200)
COLOR_ACCENT = (100, 210, 255)
COLOR_WARN = (255, 180, 80)
COLOR_GREEN = (100, 230, 150)


# ============================================================
# CARREGADOR DE OBJ COM FALLBACK PROCEDURAL
# ============================================================
def create_fallback_mesh(mesh_type):
    """Gera uma malha simples caso o OBJ não seja encontrado."""
    if mesh_type == "estalagmite":
        vertices = [
            (0.0, 1.0, 0.0),
            (-0.6, -1.0, -0.6),
            (0.6, -1.0, -0.6),
            (0.6, -1.0, 0.6),
            (-0.6, -1.0, 0.6)
        ]
        faces = [
            [0, 1, 2], [0, 2, 3], [0, 3, 4],
            [0, 4, 1], [1, 2, 3], [1, 3, 4]
        ]

    elif mesh_type == "morcego":
        # Fallback apenas para o corpo caso os OBJ não existam.
        vertices = [
            (0, 0, 0),
            (-0.9, 0.4, -0.3),
            (-0.9, -0.4, -0.3),
            (0.9, 0.4, -0.3),
            (0.9, -0.4, -0.3)
        ]
        faces = [[0, 1, 2], [0, 3, 4]]

    elif mesh_type == "asa":
        # Fallback simples para uma asa.
        vertices = [
            (0, 0, 0),
            (-2.0, 0.8, 0),
            (-2.5, 0.0, 0),
            (-1.8, -0.8, 0),
            (-0.8, -0.3, 0)
        ]
        faces = [[0, 1, 4], [1, 2, 4], [2, 3, 4]]

    elif mesh_type == "rocha":
        vertices = [
            (-0.8, -0.6, -0.6), (0.8, -0.6, -0.6),
            (0.8, 0.6, -0.6), (-0.8, 0.6, -0.6),
            (-0.7, -0.4, 0.6), (0.7, -0.4, 0.6),
            (0.7, 0.4, 0.6), (-0.7, 0.4, 0.6)
        ]
        faces = [
            [0, 1, 2, 3], [4, 5, 6, 7],
            [0, 1, 5, 4], [2, 3, 7, 6],
            [1, 2, 6, 5], [3, 0, 4, 7]
        ]

    else:
        # Cristal -> octaedro
        vertices = [
            (0, 1.0, 0), (0, -1.0, 0),
            (1.0, 0, 0), (0, 0, 1.0),
            (-1.0, 0, 0), (0, 0, -1.0)
        ]
        faces = [
            [0, 2, 3], [0, 3, 4], [0, 4, 5], [0, 5, 2],
            [1, 3, 2], [1, 4, 3], [1, 5, 4], [1, 2, 5]
        ]

    return vertices, faces


def load_obj(filename, mesh_fallback_type):
    """Carrega somente vértices e faces do arquivo OBJ."""
    if os.path.exists(filename):
        vertices = []
        faces = []

        try:
            with open(filename, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()

                    if not line or line.startswith("#"):
                        continue

                    parts = line.split()

                    if parts[0] == "v":
                        try:
                            x, y, z = (
                                float(parts[1]),
                                float(parts[2]),
                                float(parts[3])
                            )
                            vertices.append((x, y, z))
                        except Exception:
                            continue

                    elif parts[0] == "f":
                        face = []

                        for part in parts[1:]:
                            vertex_index = part.split("/")[0]

                            try:
                                face.append(int(vertex_index) - 1)
                            except Exception:
                                pass

                        if face:
                            faces.append(face)

            if vertices and faces:
                print(f"Modelo carregado: {filename}")
                print(f"  Vértices: {len(vertices)} | Faces: {len(faces)}")
                return vertices, faces

        except Exception as e:
            print(f"Aviso ao carregar {filename}: {e}")

    print(
        f"Modelo {filename} não encontrado. "
        f"Usando malha procedural: {mesh_fallback_type}"
    )
    return create_fallback_mesh(mesh_fallback_type)


# ============================================================
# TRANSFORMAÇÕES GEOMÉTRICAS
# ============================================================
def rotate_x(vertex, angle):
    x, y, z = vertex
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    return x, y * cos_a - z * sin_a, y * sin_a + z * cos_a


def rotate_y(vertex, angle):
    x, y, z = vertex
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    return x * cos_a + z * sin_a, y, -x * sin_a + z * cos_a


def rotate_z(vertex, angle):
    x, y, z = vertex
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    return x * cos_a - y * sin_a, x * sin_a + y * cos_a, z


def apply_scale(vertex, scale):
    x, y, z = vertex

    if hasattr(scale, "__len__"):
        sx = scale[0]
        sy = scale[1]
        sz = scale[2] if len(scale) > 2 else sx
    else:
        sx = sy = sz = scale

    return x * sx, y * sy, z * sz


def transform_vertex(
    vertex,
    position=(0, 0, 0),
    scale=(1, 1, 1),
    rotation=(0, 0, 0)
):
    """Escala -> rotação -> translação."""
    v = apply_scale(vertex, scale)

    rx, ry, rz = rotation

    v = rotate_x(v, rx)
    v = rotate_y(v, ry)
    v = rotate_z(v, rz)

    return (
        v[0] + position[0],
        v[1] + position[1],
        v[2] + position[2]
    )


def transform_vertex_pivot(
    vertex,
    position=(0, 0, 0),
    scale=(1, 1, 1),
    rotation=(0, 0, 0),
    pivot=(0, 0, 0)
):
    """
    Transformação usada nas asas.

    A asa é deslocada para o pivô, escalada/rotacionada,
    e depois o pivô é recolocado. Assim a rotação acontece
    na região onde a asa se liga ao corpo.
    """

    # Escala aplicada também ao pivô, pois o modelo inteiro
    # é escalado antes da transformação.
    v = apply_scale(vertex, scale)
    p = apply_scale(pivot, scale)

    # Transladar o vértice para o pivô.
    v = (
        v[0] - p[0],
        v[1] - p[1],
        v[2] - p[2]
    )

    rx, ry, rz = rotation

    v = rotate_x(v, rx)
    v = rotate_y(v, ry)
    v = rotate_z(v, rz)

    # Recolocar o pivô e depois posicionar o morcego na cena.
    v = (
        v[0] + p[0] + position[0],
        v[1] + p[1] + position[1],
        v[2] + p[2] + position[2]
    )

    return v


# ============================================================
# PROJEÇÃO PERSPECTIVA
# ============================================================
def project(vertex, camera_pos=(0, 0, 0), focal_length=520):
    x, y, z = vertex
    cx, cy, cz = camera_pos

    x -= cx
    y -= cy
    z -= cz

    if z <= 0.1:
        return None

    screen_x = WIDTH / 2 + (x * focal_length / z)
    screen_y = HEIGHT / 2 - (y * focal_length / z)

    return int(screen_x), int(screen_y), z


# ============================================================
# RENDERIZAÇÃO
# ============================================================
def draw_model(
    screen,
    vertices,
    faces,
    position=(0, 0, 0),
    scale=(1, 1, 1),
    rotation=(0, 0, 0),
    color=(150, 150, 150),
    camera_pos=(0, 0, 0),
    wireframe=False,
    pivot=None
):
    """
    Desenha uma malha 3D usando projeção perspectiva e algoritmo
    do pintor.

    Se pivot for informado, a rotação será feita em torno dele.
    """

    if pivot is None:
        transformed = [
            transform_vertex(v, position, scale, rotation)
            for v in vertices
        ]
    else:
        transformed = [
            transform_vertex_pivot(
                v,
                position,
                scale,
                rotation,
                pivot
            )
            for v in vertices
        ]

    projected = [project(v, camera_pos) for v in transformed]

    faces_to_draw = []

    for face in faces:
        points = []
        depth = 0.0
        valid = True

        for idx in face:
            if idx < 0 or idx >= len(projected):
                valid = False
                break

            proj = projected[idx]

            if proj is None:
                valid = False
                break

            points.append((proj[0], proj[1]))
            depth += proj[2]

        if valid and len(points) >= 3:
            depth /= len(face)
            faces_to_draw.append((depth, points))

    # Algoritmo do Pintor
    faces_to_draw.sort(key=lambda item: item[0], reverse=True)

    for depth, points in faces_to_draw:
        if not wireframe:
            pygame.draw.polygon(screen, color, points)

            stroke_color = tuple(
                max(0, c - 40) for c in color
            )

            pygame.draw.polygon(
                screen,
                stroke_color,
                points,
                1
            )
        else:
            pygame.draw.polygon(
                screen,
                COLOR_ACCENT,
                points,
                1
            )


# ============================================================
# INTERFACE / HUD
# ============================================================
def draw_hud(
    screen,
    font,
    font_small,
    anim_running,
    time_elapsed,
    camera_mode,
    wireframe_mode
):
    hud_surface = pygame.Surface(
        (WIDTH, 110),
        pygame.SRCALPHA
    )
    hud_surface.fill(COLOR_HUD_BG)
    screen.blit(hud_surface, (0, 0))

    title = font.render(
        "Mundo Virtual Animado — Caverna Sombria (AP1)",
        True,
        COLOR_TEXT_PRIMARY
    )
    screen.blit(title, (20, 12))

    if time_elapsed >= ANIM_DURATION:
        state_str = "FINALIZADO"
        state_color = COLOR_ACCENT
    elif anim_running:
        state_str = "RODANDO"
        state_color = COLOR_GREEN
    else:
        state_str = "PAUSADO"
        state_color = COLOR_WARN

    state_text = font_small.render(
        f"Estado: {state_str}",
        True,
        state_color
    )
    screen.blit(state_text, (20, 42))

    time_text = font_small.render(
        f"Tempo: {time_elapsed:.1f}s",
        True,
        COLOR_TEXT_SECONDARY
    )
    screen.blit(time_text, (180, 42))

    cam_str = (
        "Geral (Visão Ampla)"
        if camera_mode == 0
        else "Foco no Morcego"
    )

    cam_text = font_small.render(
        f"Câmera: {cam_str}",
        True,
        COLOR_TEXT_SECONDARY
    )
    screen.blit(cam_text, (320, 42))

    vis_str = (
        "Arame (Wireframe)"
        if wireframe_mode
        else "Sólido (Polígonos)"
    )

    vis_text = font_small.render(
        f"Visual: {vis_str}",
        True,
        COLOR_TEXT_SECONDARY
    )
    screen.blit(vis_text, (550, 42))

    cycle_progress = min(time_elapsed / ANIM_DURATION, 1.0)

    pygame.draw.rect(
        screen,
        (50, 60, 80),
        (20, 68, 700, 8),
        border_radius=4
    )

    pygame.draw.rect(
        screen,
        COLOR_ACCENT,
        (20, 68, int(700 * cycle_progress), 8),
        border_radius=4
    )

    cmd_text = font_small.render(
        "[ESPAÇO] Iniciar/Pausar  |  "
        "[R] Reiniciar  |  "
        "[C] Alternar Câmera  |  "
        "[M] Modo Arame/Sólido  |  "
        "[V] Créditos",
        True,
        COLOR_TEXT_PRIMARY
    )

    screen.blit(cmd_text, (20, 84))


# ============================================================
# TELA DE CRÉDITOS
# ============================================================
def draw_credits(screen, font, font_small):
    """Desenha uma tela de créditos sobreposta à cena."""

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((8, 10, 16, 235))
    screen.blit(overlay, (0, 0))

    painel_w, painel_h = 620, 380
    painel_x = WIDTH // 2 - painel_w // 2
    painel_y = HEIGHT // 2 - painel_h // 2

    pygame.draw.rect(
        screen,
        (18, 22, 32),
        (painel_x, painel_y, painel_w, painel_h),
        border_radius=14
    )
    pygame.draw.rect(
        screen,
        COLOR_ACCENT,
        (painel_x, painel_y, painel_w, painel_h),
        width=2,
        border_radius=14
    )

    titulo = font.render("CRÉDITOS", True, COLOR_ACCENT)
    screen.blit(
        titulo,
        (WIDTH // 2 - titulo.get_width() // 2, painel_y + 24)
    )

    linhas = [
        ("Trabalho AP1", COLOR_ACCENT),
        ("Mundo Virtual Animado — Caverna Sombria", COLOR_TEXT_PRIMARY),
        ("", None),
        ("Desenvolvimento", COLOR_ACCENT),
        ("Guilherme Pinheiro - Filipe Moreira - Gabriel Macedo - Cauan Lemos", COLOR_TEXT_PRIMARY),
        ("", None),
        ("Nome da disciplina", COLOR_ACCENT),
        ("Computação Gráfica e RA/RV", COLOR_TEXT_PRIMARY),
        ("", None),
        ("Tecnologias", COLOR_ACCENT),
        ("Python + Pygame — renderização 3D própria", COLOR_TEXT_PRIMARY),
        ("", None),
        ("Modelos 3D", COLOR_ACCENT),
        ("Arquivos OBJ próprios, com malhas de fallback", COLOR_TEXT_PRIMARY),
    ]
    y = painel_y + 74
    for texto, cor in linhas:
        if texto:
            render = font_small.render(texto, True, cor)
            screen.blit(
                render,
                (WIDTH // 2 - render.get_width() // 2, y)
            )
        y += 24

    dica = font_small.render(
        "Pressione [V] para voltar ao mundo virtual",
        True,
        COLOR_WARN
    )
    screen.blit(
        dica,
        (WIDTH // 2 - dica.get_width() // 2, painel_y + painel_h - 34)
    )


# ============================================================
# CENÁRIO
# ============================================================

# Alturas do chão e do teto da caverna. Ficam aqui como
# constantes porque tanto o cenário (draw_ground/draw_walls)
# quanto o posicionamento dos objetos (estalagmites, estalactites,
# a rocha) precisam concordar sobre onde é "o chão" e "o teto".
FLOOR_Y = -2.5
CEILING_Y = 4.2

# Posição da câmera do modo "Geral (Visão Ampla)". Fica afastada
# (Z negativo) e um pouco elevada para enquadrar chão, teto e
# paredes junto com os objetos — sem isso a câmera fica bem perto
# das estalagmites/estalactites e a cena parece "flutuando" no
# vazio, sem noção de estar dentro de uma caverna.
GENERAL_CAMERA_POS = (0.0, 0.5, -7.0)

# Ângulo de guinada (rotação no eixo Y) que faz o morcego olhar
# para a ESQUERDA (-X), a direção real do seu voo. O modelo
# bat_corpo.obj foi feito com o focinho apontando para +Z (eixo
# de profundidade da câmera) — sem essa rotação ele voa "de lado",
# de bruços/costas para o movimento, em vez de de frente. Também é
# usado para pré-rotar a malha das asas (ver bake_mesh_yaw), já
# que elas giram em torno de um pivô fixo e precisam ser
# "renascer" já na orientação certa. Se o morcego aparecer olhando
# para a direita (de costas), troque o sinal: math.pi / 2.
BAT_FACING_Y = -math.pi / 2


def bake_mesh_yaw(vertices, angle):
    """
    Aplica uma rotação Y FIXA (guinada) diretamente aos vértices
    de uma malha, uma única vez, no lugar de fazer isso a cada
    quadro dentro da rotação da instância.

    Isso é necessário especificamente para as ASAS do morcego:
    elas giram em torno de um pivô fixo (ombro) para o batimento,
    e essa rotação de pivô já usa os eixos X/Y/Z do modelo
    original (asa se abre no eixo local X, bate girando em torno
    do eixo Z). Se a guinada fosse aplicada JUNTO com o batimento
    na mesma transformação por quadro, a ordem fixa de rotação
    (X, depois Y, depois Z) faria a guinada acontecer ANTES do
    batimento, o que muda qual eixo da asa aponta para os lados —
    e o batimento (que gira em Z) deixaria de ter efeito visível,
    porque depois da guinada a asa já não se abre mais no eixo X.

    Pré-rotacionando a malha (e o pivô) uma única vez, a asa já
    "nasce" na orientação certa, e o batimento por quadro só
    precisa trocar de qual eixo ele gira (ver onde é usado).
    """
    return [rotate_y(v, angle) for v in vertices]




def compute_bounds_y(vertices, faces=None, low_percentile=2, high_percentile=98):
    """
    Retorna (min_y, max_y) "robustos" dos vértices LOCAIS de uma
    malha (antes de qualquer escala/posição). Usado para encaixar
    um objeto exatamente no chão ou no teto, não importa se a
    malha é a procedural (fallback) ou um OBJ real carregado do
    disco — cada arquivo .obj pode ter uma altura bem diferente
    da outra.

    Duas melhorias em relação a um simples min()/max():

    1. Se `faces` for informado, considera só os vértices
       realmente usados em alguma face. Alguns exportadores
       deixam vértices "órfãos" (não usados em nenhuma face) no
       arquivo .obj, e um min()/max() ingênuo pode acabar pegando
       um desses pontos soltos, bem longe da malha visível.

    2. Usa um pequeno percentil (2%/98% por padrão) em vez do
       valor mínimo/máximo absoluto, para que um único vértice
       isolado (ruído da malha, um pico bem fino etc.) não defina
       sozinho onde o objeto encosta no chão/teto.
    """
    if faces:
        indices_usados = set()

        for face in faces:
            indices_usados.update(face)

        ys = [
            vertices[i][1]
            for i in indices_usados
            if 0 <= i < len(vertices)
        ]
    else:
        ys = []

    if not ys:
        ys = [v[1] for v in vertices]

    ys_ordenados = sorted(ys)
    n = len(ys_ordenados)

    def percentil(p):
        idx = int(round((p / 100.0) * (n - 1)))
        idx = max(0, min(n - 1, idx))
        return ys_ordenados[idx]

    return percentil(low_percentile), percentil(high_percentile)

def normalize_mesh(vertices, target_height=1.0):
    """
    Reescala os vértices para que a altura (eixo Y) seja
    target_height. Assim o código não precisa saber se o OBJ
    é o fallback (altura ~2) ou um modelo real (altura ~40).
    """
    min_y, max_y = compute_bounds_y(vertices)
    height = max_y - min_y

    if height <= 0:
        return vertices

    scale = target_height / height
    return [(x * scale, y * scale, z * scale) for x, y, z in vertices]
def deform_rock(vertices, amount=0.25, seed=42):
    """
    Aplica um deslocamento pseudo-aleatório em cada vértice,
    para transformar a esfera lisa do rockmaterial.obj em uma
    rocha irregular. `amount` controla a intensidade da
    deformação (0.0 = esfera perfeita, 0.5 = bem irregular).
    """
    rng = random.Random(seed)
    deformados = []

    for x, y, z in vertices:
        # Cada vértice recebe um offset fixo, reproduzível.
        dx = rng.uniform(-amount, amount)
        dy = rng.uniform(-amount, amount)
        dz = rng.uniform(-amount, amount)
        deformados.append((x + dx, y + dy, z + dz))

    return deformados
    
def anchor_y(target_y, local_anchor_y, scale_y, embed=0.0, teto=False):
    """
    Calcula a posição em Y para que o vértice LOCAL local_anchor_y
    — depois de multiplicado pela escala aplicada (scale_y), que
    pode ser negativa para inverter a malha de cabeça para baixo —
    fique exatamente em target_y (mais um pequeno "afundamento"
    opcional, embed, para dentro da superfície).

    IMPORTANTE: local_anchor_y não é sempre o mínimo nem sempre o
    máximo da malha — depende de como cada modelo .obj foi
    modelado. Analisando o Stalagmite_Medium0.obj real (ver
    profile_obj.py), descobrimos que ele é ESTREITO/pontudo no
    Y mínimo e LARGO no Y máximo — o oposto da malha de fallback
    (que é larga embaixo, pontuda em cima). Por isso quem chama
    esta função precisa escolher, para cada malha, qual extremo
    (min ou max) representa a ponta "larga" que deve encostar na
    superfície, e ajustar o sinal de scale_y de acordo.

    O parâmetro `teto` diz se o afundamento (embed) deve empurrar
    o objeto para CIMA (pendurado no teto) ou para BAIXO (apoiado
    no chão) — isso não dá pra inferir com segurança a partir do
    sinal de scale_y, já que malhas diferentes podem precisar de
    sinais diferentes dependendo de como foram modeladas (foi
    justamente essa suposição errada que causava o "flutuando").

    Modelos OBJ reais quase nunca têm uma base perfeitamente
    plana: eles têm reentrâncias e picos irregulares. Se
    ancorarmos exatamente na superfície, normalmente só uma
    pontinha da malha toca de verdade, e o resto do volume visível
    fica com uma folga acima dela — dando a impressão de estar
    flutuando. Afundar um pouco (embed) garante que a base "grude"
    visualmente na superfície mesmo com essa irregularidade. Como
    o objeto é desenhado por cima do chão/teto (nunca o
    contrário), essa parte afundada fica simplesmente escondida
    atrás do próprio modelo — não aparece nenhum buraco ou corte
    estranho.
    """
    base = target_y - local_anchor_y * scale_y
    return base + embed if teto else base - embed



def draw_hole(screen, camera_pos, x, z, radius, segments=24):
    """
    Desenha um buraco escuro (um círculo de pontos no plano do
    chão, projetado em perspectiva) na posição (x, FLOOR_Y, z).
    É nele que a rocha rola e cai no fim da animação — fica
    visível no chão o tempo todo, como uma fenda já existente na
    caverna, não algo que "aparece do nada" quando a rocha chega.
    """
    pontos_mundo = []

    for i in range(segments):
        ang = (2 * math.pi * i) / segments
        px = x + math.cos(ang) * radius
        pz = z + math.sin(ang) * radius
        pontos_mundo.append((px, FLOOR_Y, pz))

    proj = [project(p, camera_pos) for p in pontos_mundo]

    if all(p is not None for p in proj):
        pts = [(p[0], p[1]) for p in proj]

        pygame.draw.polygon(screen, (5, 6, 9), pts)
        pygame.draw.polygon(screen, (2, 2, 4), pts, 2)


def draw_ground(screen, camera_pos):
    corners = [
        (-12.0, FLOOR_Y, 3.0),
        (12.0, FLOOR_Y, 3.0),
        (12.0, FLOOR_Y, 30.0),
        (-12.0, FLOOR_Y, 30.0)
    ]

    proj = [
        project(c, camera_pos)
        for c in corners
    ]

    if all(p is not None for p in proj):
        pts = [(p[0], p[1]) for p in proj]

        pygame.draw.polygon(
            screen,
            (36, 44, 58),
            pts
        )

    for x in range(-10, 11, 2):
        p1 = project(
            (x, FLOOR_Y, 3.0),
            camera_pos
        )
        p2 = project(
            (x, FLOOR_Y, 30.0),
            camera_pos
        )

        if p1 and p2:
            pygame.draw.line(
                screen,
                (60, 72, 92),
                (p1[0], p1[1]),
                (p2[0], p2[1]),
                1
            )

    for z in range(3, 31, 2):
        p1 = project(
            (-12.0, FLOOR_Y, z),
            camera_pos
        )
        p2 = project(
            (12.0, FLOOR_Y, z),
            camera_pos
        )

        if p1 and p2:
            pygame.draw.line(
                screen,
                (60, 72, 92),
                (p1[0], p1[1]),
                (p2[0], p2[1]),
                1
            )


def draw_walls(screen, camera_pos):
    """
    Fecha o cenário com quatro superfícies: parede esquerda,
    parede direita, parede do fundo e teto — formando uma
    caverna "em caixa" ao redor do chão já desenhado em
    draw_ground.
    """

    y_bottom = FLOOR_Y
    y_top = CEILING_Y
    x_left = -12.0
    x_right = 12.0
    z_near = 3.0
    z_far = 30.0

    wall_color = (30, 34, 48)
    ceiling_color = (30, 34, 46)
    ceiling_grid_color = (58, 66, 88)
    edge_color = (42, 50, 68)

    left_wall = [
        (x_left, y_bottom, z_near),
        (x_left, y_bottom, z_far),
        (x_left, y_top, z_far),
        (x_left, y_top, z_near)
    ]

    right_wall = [
        (x_right, y_bottom, z_near),
        (x_right, y_top, z_near),
        (x_right, y_top, z_far),
        (x_right, y_bottom, z_far)
    ]

    back_wall = [
        (x_left, y_bottom, z_far),
        (x_right, y_bottom, z_far),
        (x_right, y_top, z_far),
        (x_left, y_top, z_far)
    ]

    ceiling = [
        (x_left, y_top, z_near),
        (x_right, y_top, z_near),
        (x_right, y_top, z_far),
        (x_left, y_top, z_far)
    ]

    surfaces = [
        (left_wall, wall_color),
        (right_wall, wall_color),
        (back_wall, wall_color),
        (ceiling, ceiling_color)
    ]

    for quad, color in surfaces:
        proj = [project(v, camera_pos) for v in quad]

        if all(p is not None for p in proj):
            pts = [(p[0], p[1]) for p in proj]

            pygame.draw.polygon(screen, color, pts)
            pygame.draw.polygon(screen, edge_color, pts, 1)

    # Linhas verticais na parede esquerda e direita, para dar
    # sensação de profundidade (mesmo estilo do grid do chão).
    for z in range(int(z_near), int(z_far) + 1, 3):
        p1 = project((x_left, y_bottom, z), camera_pos)
        p2 = project((x_left, y_top, z), camera_pos)

        if p1 and p2:
            pygame.draw.line(
                screen, edge_color, (p1[0], p1[1]), (p2[0], p2[1]), 1
            )

        p1 = project((x_right, y_bottom, z), camera_pos)
        p2 = project((x_right, y_top, z), camera_pos)

        if p1 and p2:
            pygame.draw.line(
                screen, edge_color, (p1[0], p1[1]), (p2[0], p2[1]), 1
            )

    # Grid no teto, no mesmo estilo do grid do chão (draw_ground),
    # para deixar claro onde o teto realmente está e permitir
    # conferir se as estalactites encostam nele de verdade.
    for x in range(-10, 11, 2):
        p1 = project((x, y_top, z_near), camera_pos)
        p2 = project((x, y_top, z_far), camera_pos)

        if p1 and p2:
            pygame.draw.line(
                screen, ceiling_grid_color, (p1[0], p1[1]), (p2[0], p2[1]), 1
            )

    for z in range(int(z_near), int(z_far) + 1, 2):
        p1 = project((x_left, y_top, z), camera_pos)
        p2 = project((x_right, y_top, z), camera_pos)

        if p1 and p2:
            pygame.draw.line(
                screen, ceiling_grid_color, (p1[0], p1[1]), (p2[0], p2[1]), 1
            )


def draw_cave(screen):
    w, h = screen.get_size()

    cave_color = (10, 12, 16)
    pygame.draw.rect(
        screen,
        cave_color,
        (0, 0, w, int(h * 0.55))
    )

    mouth_color = (18, 20, 28)

    mouth_rect = pygame.Rect(
        w * 0.05,
        -h * 0.2,
        w * 0.9,
        h * 0.9
    )

    pygame.draw.ellipse(
        screen,
        mouth_color,
        mouth_rect
    )


def clamp(v, a, b):
    return max(a, min(b, v))


def clamp_scene_positions(
    instances,
    x_min=-11.0,
    x_max=11.0,
    z_min=3.5,
    z_max=28.0,
    # Os limites de Y precisam sobrar espaço além do chão/teto
    # reais (FLOOR_Y/CEILING_Y): objetos ancorados no teto ficam
    # com "pos" perto de CEILING_Y, e um limite mais apertado
    # (como o antigo y_max=3.5, menor que o teto em 4.2) puxava
    # a estalactite de volta para baixo, desfazendo o encaixe no
    # teto e fazendo ela parecer flutuando no vazio.
    y_min=FLOOR_Y - 0.5,
    y_max=CEILING_Y + 0.5
):
    for inst in instances:
        pos = inst.get("pos")

        if isinstance(pos, (list, tuple)) and len(pos) >= 3:
            p = list(pos)

            p[0] = clamp(p[0], x_min, x_max)
            p[1] = clamp(p[1], y_min, y_max)
            p[2] = clamp(p[2], z_min, z_max)

            inst["pos"] = p


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================
def main():
    pygame.init()

    screen = pygame.display.set_mode(
        (WIDTH, HEIGHT)
    )

    pygame.display.set_caption(
        "AP1 - Caverna Sombria - Mundo Virtual Animado"
    )

    clock = pygame.time.Clock()

    font = pygame.font.SysFont(
        "Arial",
        22,
        bold=True
    )

    font_small = pygame.font.SysFont(
        "Arial",
        16
    )

    # ========================================================
    # CARREGAMENTO DOS MODELOS
    # ========================================================

    stalagmite_v, stalagmite_f = load_obj(
        "models/Stalagmite_Medium0.obj",
        "estalagmite"
    )
    stalagmite_v = normalize_mesh(stalagmite_v, target_height=10.0)
    
    rock_v, rock_f = load_obj(
        "models/rockmaterial.obj",
        "rocha"
    )

    # Caixas delimitadoras (só o eixo Y) das malhas, usadas mais
    # abaixo para encostar cada objeto exatamente no chão ou no
    # teto, com base no tamanho real do modelo carregado.
    stalagmite_min_y, stalagmite_max_y = compute_bounds_y(
        stalagmite_v, stalagmite_f
    )
    
    rock_min_y, rock_max_y = compute_bounds_y(rock_v, rock_f)

    # ---- DIAGNÓSTICO ----
    # Se algum objeto ainda parecer flutuando depois disso, o
    # próximo passo é olhar esses números no console (aparecem
    # assim que o programa inicia) — sem eles, eu só consigo
    # adivinhar pela captura de tela. É útil copiar e colar essas
    # linhas de volta na conversa.
    print(
        "[DEBUG] Estalagmite/estalactite — extensão local em Y: "
        f"min={stalagmite_min_y:.3f}  max={stalagmite_max_y:.3f}  "
        f"altura_bruta={stalagmite_max_y - stalagmite_min_y:.3f}"
    )
    print(
        "[DEBUG] Rocha — extensão local em Y: "
        f"min={rock_min_y:.3f}  max={rock_max_y:.3f}  "
        f"altura_bruta={rock_max_y - rock_min_y:.3f}"
    )

    # NOVO: o morcego agora é composto por 3 OBJ.
    bat_corpo_v, bat_corpo_f = load_obj(
        "models/bat_corpo.obj",
        "morcego"
    )

    bat_asa_esq_v, bat_asa_esq_f = load_obj(
        "models/bat_asa_esquerda.obj",
        "asa"
    )

    bat_asa_dir_v, bat_asa_dir_f = load_obj(
        "models/bat_asa_direita.obj",
        "asa"
    )

    # Pré-rotaciona as asas (malha e pivô) pela mesma guinada
    # BAT_FACING_Y do corpo — ver docstring de bake_mesh_yaw.
    bat_asa_esq_v = bake_mesh_yaw(bat_asa_esq_v, BAT_FACING_Y)
    bat_asa_dir_v = bake_mesh_yaw(bat_asa_dir_v, BAT_FACING_Y)
    pivot_esq = rotate_y((-0.18, 0.0, 0.0), BAT_FACING_Y)
    pivot_dir = rotate_y((0.18, 0.0, 0.0), BAT_FACING_Y)

    random.seed(1)

    # ========================================================
    # INSTÂNCIAS DA CENA
    # ========================================================

    s1 = random.uniform(0.30, 0.45)
    s2 = random.uniform(0.30, 0.45)
    s3 = random.uniform(0.30, 0.45)

    # Alturas (metade da altura, já escaladas) de cada
    # estalagmite/estalactite. Usadas para encostar a base de
    # cada uma exatamente no chão ou no teto, em vez de deixá-las
    # "flutuando" no meio do ar.
    # Reduzidas ~35% em relação à versão anterior: com os OBJ
    # reais, a estalagmite do meio ficava alta demais (quase
    # encostando no teto).
    altura1 = 0.22 * s1
    altura2 = 0.32 * s2
    altura3 = 0.28 * s3

    # Escala e apoio no chão da rocha, calculados a partir da
    # caixa delimitadora real do modelo carregado (fallback ou
    # OBJ), em vez de um valor de Y fixo "chutado" — assim ela
    # encosta no chão não importa o tamanho do modelo.
    ROCK_SCALE = 1.3
    # Margem de "afundamento": empurra o ponto de ancoragem um
    # pouco além do chão/teto, para compensar bases/topos
    # irregulares dos modelos OBJ reais (ver docstring de anchor_y).
    FLOOR_EMBED = 0.15
    CEILING_EMBED = 0.15

    rock_floor_y = anchor_y(FLOOR_Y, rock_min_y, ROCK_SCALE, embed=0.08)
    ROCK_RADIUS = max(
        (rock_max_y - rock_min_y) * ROCK_SCALE / 2.0,
        0.1
    )

    # O morcego agora possui 3 partes.
    morcego_pos = [0.0, 1.0, 5.0]

    instancias = [
        {
            # Estalagmite: cresce do CHÃO para cima. O
            # Stalagmite_Medium0.obj real é ESTREITO no Y mínimo e
            # LARGO no Y máximo (o oposto da malha de fallback) —
            # analisamos os vértices para confirmar isso. Por isso
            # usamos escala em Y NEGATIVA (inverte a malha) e
            # ancoramos pelo stalagmite_max_y (a ponta LARGA), que
            # assim vira a base apoiada no chão, com a ponta fina
            # (min local) sobrando pra cima.
            "modelo": "estalagmite",
            "v": stalagmite_v,
            "f": stalagmite_f,
            "pos": [-4.0, anchor_y(FLOOR_Y, stalagmite_min_y, altura1, embed=FLOOR_EMBED), 7.0],
            "scale": [
                0.18 * s1,
                altura1,
                0.18 * s1
            ],
            "rot": [0, 0.2, 0],
            "color": (110, 110, 120)
        },

        {
            "modelo": "estalagmite",
            "v": stalagmite_v,
            "f": stalagmite_f,
            "pos": [3.5, anchor_y(FLOOR_Y, stalagmite_min_y, altura2, embed=FLOOR_EMBED), 8.5],
            "scale": [
                0.24 * s2,
                altura2,
                0.24 * s2
            ],
            "rot": [0, -0.5, 0],
            "color": (95, 95, 105)
        },

        {
            # Estalactite: pendurada no TETO. Como esse mesmo
            # modelo já é NATURALMENTE largo no topo (Y máximo) e
            # estreito embaixo (Y mínimo) — o formato certo pra uma
            # estalactite (larga onde gruda no teto, afinando até
            # virar ponta pendurada) — usamos escala em Y POSITIVA
            # (SEM inverter) e ancoramos pelo mesmo stalagmite_max_y,
            # que assim vira o topo encostado no teto.
            "modelo": "estalactite_teto",
            "v": stalagmite_v,
            "f": stalagmite_f,
            "pos": [-0.5, anchor_y(CEILING_Y, stalagmite_max_y, -altura3, embed=CEILING_EMBED, teto=True), 6.5],
            "scale": [
                0.22 * s3,
                -altura3,
                0.22 * s3
            ],
            "rot": [0, 0.8, 0],
            "color": (120, 115, 130)
        },

        {
            "modelo": "rocha",
            "v": rock_v,
            "f": rock_f,
            "pos": [-7.0, rock_floor_y, 4.0],
            "scale": [ROCK_SCALE, ROCK_SCALE, ROCK_SCALE],
            "rot": [0, 0, 0],
            "color": (100, 85, 75)
        },

        # Corpo do morcego
        {
            "modelo": "morcego_corpo",
            "v": bat_corpo_v,
            "f": bat_corpo_f,
            "pos": morcego_pos,
            "scale": [0.8, 0.8, 0.8],
            "rot": [0, 0, 0],
            "color": (75, 60, 90)
        },

        # Asa esquerda
        {
            "modelo": "morcego_asa_esquerda",
            "v": bat_asa_esq_v,
            "f": bat_asa_esq_f,
            "pos": morcego_pos,
            "scale": [0.8, 0.8, 0.8],
            "rot": [0, 0, 0],
            "pivot": pivot_esq,
            "color": (65, 50, 80)
        },

        # Asa direita
        {
            "modelo": "morcego_asa_direita",
            "v": bat_asa_dir_v,
            "f": bat_asa_dir_f,
            "pos": morcego_pos,
            "scale": [0.8, 0.8, 0.8],
            "rot": [0, 0, 0],
            "pivot": pivot_dir,
            "color": (65, 50, 80)
        }
    ]

    print(
        "[DEBUG] Posições Y finais — "
        f"estalagmite1={instancias[0]['pos'][1]:.3f}  "
        f"estalagmite2={instancias[1]['pos'][1]:.3f}  "
        f"estalactite={instancias[2]['pos'][1]:.3f}  "
        f"rocha={instancias[3]['pos'][1]:.3f}  "
        f"(FLOOR_Y={FLOOR_Y}  CEILING_Y={CEILING_Y})"
    )

    clamp_scene_positions(instancias)

    cameras = [
        list(GENERAL_CAMERA_POS),
        [0.0, 0.0, 0.0]
    ]

    camera_mode = 0
    anim_running = False
    time_elapsed = 0.0
    wireframe_mode = False
    show_credits = False

    # Parâmetros da rocha rolando: ela sai de rock_start_x,
    # percorre em linha reta até rock_end_x — bem em cima de um
    # buraco no chão — desacelerando (ease-out) até parar de vez
    # aos ROCK_ROLL_DURATION segundos. Depois de parar, ela cai
    # dentro do buraco (ver ROCK_FALL_*), sumindo de cena antes do
    # fim da animação.
    rock_start_x = -7.0
    rock_end_x = 7.0
    ROCK_ROLL_DURATION = 6.0
    # ROCK_RADIUS já foi calculado acima, a partir do modelo real.

    # O buraco fica exatamente onde a rocha para de rolar (mesmo
    # X/Z), um pouco maior que ela para "engolir" a rocha
    # visualmente. A queda dura ROCK_FALL_DURATION segundos, com
    # aceleração tipo gravidade (ease-in): devagar no começo da
    # queda, acelerando até sumir de vista bem abaixo do chão.
    #
    # ROCK_FALL_START é um pouco ANTES de ROCK_ROLL_DURATION, não
    # igual: a curva de ease-out cúbico do rolamento já deixa a
    # rocha visualmente parada bem antes do fim "matemático" do
    # rolamento (a cauda da curva é bem achatada — por volta de
    # 90% da duração, o movimento restante já é imperceptível).
    # Se a queda só começasse exatamente em ROCK_ROLL_DURATION,
    # sobrava uma pausa visível: a rocha parecia já ter parado em
    # cima do buraco e ficava um tempo ali "esperando" antes de
    # cair. Começar a queda um pouco antes remove essa espera.
    HOLE_X = rock_end_x
    HOLE_Z = 4.0
    HOLE_RADIUS = ROCK_RADIUS * 1.4
    ROCK_FALL_START = ROCK_ROLL_DURATION * 0.85
    ROCK_FALL_DURATION = 2.0
    ROCK_FALL_DEPTH = 6.0

    # Parâmetros do voo do morcego: sai da direita da tela
    # (X positivo) e termina à esquerda (X negativo), desacelerando
    # (ease-out) ao longo de toda a duração da animação, de forma
    # que ele chegue perto da borda esquerda exatamente quando a
    # animação está terminando. Percurso um pouco mais curto que
    # antes (8 em vez de 10) para reforçar a sensação de voo mais
    # lento — o grosso da desaceleração agora acontece com uma
    # curva mais suave (ver flight_eased no loop principal).
    BAT_FLIGHT_START_X = 8.0
    BAT_FLIGHT_END_X = -8.0

    running = True

    # ========================================================
    # LOOP PRINCIPAL
    # ========================================================
    while running:

        dt = clock.tick(FPS) / 1000.0

        # ----------------------------------------------------
        # EVENTOS
        # ----------------------------------------------------
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    anim_running = not anim_running

                elif event.key == pygame.K_r:
                    time_elapsed = 0.0

                elif event.key == pygame.K_c:
                    camera_mode = (
                        camera_mode + 1
                    ) % len(cameras)

                elif event.key == pygame.K_m:
                    wireframe_mode = not wireframe_mode

                elif event.key == pygame.K_v:
                    show_credits = not show_credits

        # ----------------------------------------------------
        # TEMPO DA ANIMAÇÃO
        # ----------------------------------------------------
        if anim_running and not show_credits:
            time_elapsed += dt

            if time_elapsed >= ANIM_DURATION:
                time_elapsed = ANIM_DURATION
                anim_running = False

        t = time_elapsed

        # ====================================================
        # ANIMAÇÃO DO MORCEGO
        # ====================================================

        morcego_corpo = instancias[4]
        asa_esquerda = instancias[5]
        asa_direita = instancias[6]

        # Movimento do morcego pela caverna: viagem principal da
        # DIREITA para a ESQUERDA da tela, com uma curva de
        # ease-out mais suave — desacelera aos poucos e termina
        # perto da borda esquerda quando t chega em ANIM_DURATION.
        # Voo mais LENTO que antes: percurso um pouco mais curto,
        # curva de aceleração mais suave (quadrática em vez de
        # cúbica, sem aquele "arranco" inicial rápido) e todas as
        # oscilações (sobe/desce, balanço lateral, vaivém em
        # profundidade, batida de asa, giro do corpo) com
        # frequência menor, para o voo inteiro parecer mais calmo.
        flight_progress = clamp(t / ANIM_DURATION, 0.0, 1.0)
        flight_eased = 1 - (1 - flight_progress) ** 2  # ease-out suave

        bat_x_viagem = BAT_FLIGHT_START_X + (
            (BAT_FLIGHT_END_X - BAT_FLIGHT_START_X) * flight_eased
        )
        bat_x_balanco = math.sin(t * 0.9) * 0.8  # leve esq./dir.

        nova_pos = [
            bat_x_viagem + bat_x_balanco,
            0.8 + math.cos(t * 1.8) * 0.4,
            5.5 + math.sin(t * 1.2) * 1.0
        ]

        morcego_corpo["pos"] = nova_pos
        asa_esquerda["pos"] = nova_pos.copy()
        asa_direita["pos"] = nova_pos.copy()

        # Rotação geral do corpo. BAT_FACING_Y (constante definida
        # lá em cima, perto de GENERAL_CAMERA_POS) gira o morcego
        # para que o focinho — que no modelo bat_corpo.obj aponta
        # para +Z (confirmado analisando a malha: é onde está
        # concentrada a maior parte dos vértices/detalhes,
        # indicando a cabeça) — passe a apontar para a ESQUERDA
        # (-X), a direção real do voo. Antes a rotação Y crescia
        # sem parar (t * algo), fazendo o morcego girar
        # continuamente em vez de olhar para onde estava voando
        # ("voando de lado").
        morcego_corpo["rot"] = (
            math.sin(t * 1.8) * 0.2,
            BAT_FACING_Y + math.sin(t * 1.0) * 0.06,
            math.cos(t * 1.2) * 0.15
        )

        # ====================================================
        # BATIMENTO DAS ASAS
        # ====================================================
        #
        # A função seno cria um movimento periódico.
        #
        # As asas fazem movimentos opostos:
        # esquerda:  +angulo
        # direita:   -angulo
        #
        # A rotação é aplicada no eixo X, não mais Z: como a malha
        # da asa já foi pré-rotacionada pela guinada do morcego
        # (bake_mesh_yaw, lá no carregamento), o lado que antes
        # apontava para os lados (eixo X original) agora aponta
        # para a profundidade (Z). Girar em torno de X é o que
        # move essa ponta da asa para cima/baixo (eixo Y) — exatamente
        # o batimento — nessa nova orientação. Girar em Z, como
        # antes, não teria mais efeito visível algum.
        # ====================================================

        flap_angle = math.sin(t * 4.0) * 0.65

        asa_esquerda["rot"] = (
            flap_angle,
            0.0,
            0.0
        )

        asa_direita["rot"] = (
            -flap_angle,
            0.0,
            0.0
        )

        # ====================================================
        # ANIMAÇÃO DA ROCHA (rolando até parar, depois caindo)
        # ====================================================
        #
        # A rocha se desloca em linha reta pelo chão (eixo X) e
        # gira em torno do eixo Z — eixo perpendicular ao
        # deslocamento — simulando o rolamento sem deslizar
        # (ângulo = distância percorrida / raio). Uma curva de
        # "ease-out" faz o avanço desacelerar suavemente até
        # parar de vez em ROCK_ROLL_DURATION segundos: como a
        # rotação depende da mesma distância percorrida, ela
        # para exatamente junto com a translação, dando a
        # sensação real de "parou de rolar" em vez de continuar
        # girando no lugar ou deslizar sem girar.
        #
        # O Z fica fixo em 4.0 — bem mais perto da câmera do que
        # as estalagmites (que estão em z=7.0 e z=8.5) — para que
        # a rocha role sempre NA FRENTE delas, sem atravessar o
        # modelo durante o percurso.
        #
        # Assim que o rolamento termina, ela cai dentro do buraco
        # (mesmo X/Z de HOLE_X/HOLE_Z): desce com aceleração tipo
        # gravidade (ease-in) e ao mesmo tempo encolhe até
        # desaparecer. O encolhimento é só um truque visual — este
        # renderizador não tem oclusão de verdade (os objetos são
        # sempre desenhados por cima do chão, não importa a
        # profundidade real), então sem encolher a rocha ficaria
        # visível "flutuando" abaixo do buraco em vez de parecer
        # que sumiu dentro dele.
        # ====================================================

        rocha = instancias[3]

        roll_progress = clamp(t / ROCK_ROLL_DURATION, 0.0, 1.0)
        eased = 1 - (1 - roll_progress) ** 3  # ease-out cúbico

        distancia_percorrida = (rock_end_x - rock_start_x) * eased
        angulo_rolamento = distancia_percorrida / ROCK_RADIUS

        fall_progress = clamp(
            (t - ROCK_FALL_START) / ROCK_FALL_DURATION, 0.0, 1.0
        )
        fall_eased = fall_progress ** 2  # ease-in, tipo gravidade

        rock_y_atual = rock_floor_y - fall_eased * ROCK_FALL_DEPTH
        rock_scale_atual = ROCK_SCALE * (1.0 - fall_progress)

        rocha["pos"][0] = rock_start_x + distancia_percorrida
        rocha["pos"][1] = rock_y_atual
        rocha["pos"][2] = 4.0

        rocha["scale"] = [
            rock_scale_atual, rock_scale_atual, rock_scale_atual
        ]

        rocha["rot"] = (
            fall_progress * 4.0,  # um pequeno tombo enquanto cai
            0.0,
            -angulo_rolamento
        )

        clamp_scene_positions(instancias)

        # O clamp_scene_positions trava todo objeto numa faixa
        # "seguraz" perto do chão/teto — ótimo para os outros, mas
        # durante a queda a rocha PRECISA sair bem abaixo dessa
        # faixa pra sumir dentro do buraco. Reaplicamos a posição
        # real por cima do clamp só para a rocha.
        rocha["pos"][1] = rock_y_atual

        # ====================================================
        # CÂMERA
        # ====================================================

        cameras[1] = [
            morcego_corpo["pos"][0] * 0.5,
            morcego_corpo["pos"][1] * 0.5,
            morcego_corpo["pos"][2] - 4.5
        ]

        # ====================================================
        # DESENHO
        # ====================================================

        screen.fill(COLOR_BG)

        cam_active = cameras[camera_mode]

        draw_cave(screen)
        draw_walls(screen, cam_active)
        draw_ground(screen, cam_active)
        draw_hole(screen, cam_active, HOLE_X, HOLE_Z, HOLE_RADIUS)

        for inst in instancias:

            draw_model(
                screen,
                inst["v"],
                inst["f"],
                position=inst.get(
                    "pos",
                    [0, 0, 6]
                ),
                scale=inst.get(
                    "scale",
                    [1, 1, 1]
                ),
                rotation=inst.get(
                    "rot",
                    [0, 0, 0]
                ),
                color=inst.get(
                    "color",
                    (200, 200, 200)
                ),
                camera_pos=cam_active,
                wireframe=wireframe_mode,
                pivot=inst.get("pivot")
            )

        draw_hud(
            screen,
            font,
            font_small,
            anim_running,
            time_elapsed,
            camera_mode,
            wireframe_mode
        )

        if show_credits:
            draw_credits(screen, font, font_small)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

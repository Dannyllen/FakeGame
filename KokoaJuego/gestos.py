import pygame
import cv2
import mediapipe as mp

# --- 1. Configuración de Pygame ---
pygame.init()

ANCHO_VENTANA = 800
ALTO_VENTANA = 600
PANTALLA = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
pygame.display.set_caption("RPG con Control de Gestos")
RELOJ = pygame.time.Clock()
FPS = 30 # Limitamos el frame rate

# Colores
NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
VERDE = (0, 255, 0)
AZUL = (0, 0, 255)

# --- 2. Configuración de MediaPipe y Cámara ---

# Inicializar MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    model_complexity=0, # Preferimos un modelo menos complejo para velocidad
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# Inicializar la cámara (0 es el índice de la cámara por defecto)
cap = cv2.VideoCapture(0)
# Ajustar el tamaño del frame de la cámara para la ventana (opcional)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, ANCHO_VENTANA)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, ALTO_VENTANA)

# Definición de los índices de los puntos clave (Landmarks) para cada dedo
PUNTA_DEDOS = [4, 8, 12, 16, 20] 

def detectar_gesto(hand_landmarks):
    """
    Analiza los puntos clave de la mano para determinar el gesto con la lógica final.
    :param hand_landmarks: Objeto con los 21 landmarks de la mano detectada.
    :return: Una cadena que describe el gesto detectado ('ACCIÓN_A', 'PALMA_ABIERTA', 'MOVER_ARRIBA', 'MOVER_ABAJO', 'NINGUNO').
    """
    
    landmarks = hand_landmarks.landmark
    
    # 1. Determinar qué dedos están extendidos
    dedos_extendidos = []
    # Iteramos sobre los dedos (Índice=1, Medio=2, Anular=3, Meñique=4)
    for i in range(1, 5): 
        # Un dedo está extendido si la punta (landmark i * 4) tiene una coordenada Y menor (más arriba) 
        # que el nudillo inferior (landmark i * 4 - 2)
        if landmarks[i * 4].y < landmarks[i * 4 - 2].y:
            dedos_extendidos.append(i)
            
    # El pulgar (índice 0)
    pulgar_extendido = landmarks[4].x < landmarks[3].x # Asumiendo mano derecha volteada

    # 2. Lógica para los Gestos Definidos

    # Gesto: Palma Abierta (Prioridad alta)
    if pulgar_extendido and len(dedos_extendidos) == 4:
        return 'PALMA_ABIERTA'

    # Gesto: ACCIÓN_A (Atacar) -> Índice y Medio alzados.
    # Los códigos 1 y 2 representan el Índice y el Medio
    # Usamos set() para asegurar que sean SOLO esos dos, excluyendo el pulgar.
    if not pulgar_extendido and set(dedos_extendidos) == {1,2}:
        return 'MOVER_ARRIBA' 

    # Gesto: Mover Arriba -> Índice alzado, el resto abajo.
    # El código 1 representa el dedo Índice
    if not pulgar_extendido and dedos_extendidos == [1]:
        return 'MOVER_ABAJO'
        
    # Gesto: Mover Abajo -> Ningún dedo alzado (Puño cerrado).
    if pulgar_extendido and set(dedos_extendidos) == {1,2}:
        return 'ACCION_A' 

    return 'NINGUNO' # Gesto no reconocido


# Variable global para almacenar el gesto actual
gesto_actual = "INICIO"

# --- Bucle Principal del Juego ---
ejecutando = True
while ejecutando:
    # --- Manejo de Eventos ---
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False

    # --- Procesamiento de la Cámara/MediaPipe ---
    
    # 1. Leer el frame de la cámara
    éxito, imagen_bgr = cap.read()
    if not éxito:
        continue # Si no se lee, pasamos al siguiente ciclo

    # 2. Voltear la imagen horizontalmente para un efecto de espejo
    imagen_bgr = cv2.flip(imagen_bgr, 1)

    # 3. Convertir la imagen a RGB (MediaPipe lo requiere)
    imagen_rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)

    # 4. Procesar la imagen para detección de manos
    resultado = hands.process(imagen_rgb)

    # 5. Dibujar la detección y determinar el Gesto
    gesto_actual = "NINGUNO"
    
    if resultado.multi_hand_landmarks:
        for hand_landmarks in resultado.multi_hand_landmarks:
            
            # --- LLAMADA A LA FUNCIÓN DE GESTO ---
            gesto_actual = detectar_gesto(hand_landmarks)
            # -------------------------------------
            
            # Dibujamos los puntos clave y las conexiones
            mp_drawing.draw_landmarks(
                imagen_rgb,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=VERDE, thickness=2, circle_radius=4),
                mp_drawing.DrawingSpec(color=AZUL, thickness=2, circle_radius=2)
            )
            
    # ... el resto del código de la cámara sigue igual ...
    # 6. Convertir la imagen procesada de nuevo a un formato compatible con Pygame
    # El resultado ahora es una imagen RGB (numpy array)
    
    # Convertir a formato BGR para que Pygame lo muestre correctamente (OpenCV usa BGR, Pygame usa RGB/Surface)
    imagen_bgr = cv2.cvtColor(imagen_rgb, cv2.COLOR_RGB2BGR)

    # Crear una superficie de Pygame a partir de la imagen BGR
    # (NOTA: Es importante que el array tenga el formato correcto para Pygame)
    frame_surface = pygame.surfarray.make_surface(imagen_bgr.swapaxes(0, 1))
    
    PANTALLA.fill(NEGRO) # Limpia la pantalla
    
    # Dibujar la superficie de la cámara escalada
    frame_surface_escalada = pygame.transform.scale(frame_surface, (ANCHO_VENTANA, ALTO_VENTANA))
    PANTALLA.blit(frame_surface_escalada, (0, 0))

    # 7. Mostrar el Gesto Detectado (Nueva Lógica)
    fuente = pygame.font.Font(None, 74) # Fuente para el texto
    texto_gesto = fuente.render(f"Gesto: {gesto_actual}", True, BLANCO)
    
    # Dibujar el texto en la parte superior izquierda de la pantalla
    PANTALLA.blit(texto_gesto, (10, 10))

    # Actualizar la pantalla
    pygame.display.flip()
    
    # Control de FPS
    RELOJ.tick(FPS)

# --- Limpieza Final ---
cap.release()
pygame.quit()
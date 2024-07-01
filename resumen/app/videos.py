import os
from moviepy.editor import VideoFileClip, clips_array

# Ruta a la carpeta que contiene los videos
folder_path = 'D:\\pruebacollagevideos'

# Obtener lista de archivos en la carpeta
video_paths = [os.path.join(folder_path, file) for file in os.listdir(folder_path) 
               if os.path.isfile(os.path.join(folder_path, file)) and file.endswith('.mp4')]

# Cargar cada video como un VideoFileClip
video_clips = [VideoFileClip(path) for path in video_paths]

# Obtener la duración máxima entre todos los clips
max_duration = max([clip.duration for clip in video_clips])

# Ajustar la duración de todos los clips al máximo
video_clips = [clip.set_duration(max_duration) for clip in video_clips]

# Determinar el número de filas y columnas en la cuadrícula
num_videos = len(video_clips)
num_rows = 2  # Por ejemplo, 2 filas
num_cols = 2  # Por ejemplo, 2 columnas

# Asegurarse de que haya suficientes clips para llenar la cuadrícula
while len(video_clips) < num_rows * num_cols:
    video_clips.append(video_clips[0])  # Añadir el primer clip repetidamente si no hay suficientes

# Tomar solo los primeros clips necesarios
video_clips = video_clips[:num_rows * num_cols]

# Crear una cuadrícula con los clips de video
grid = [[video_clips[col + row * num_cols] for col in range(num_cols)] for row in range(num_rows)]

# Combinar los clips en una cuadrícula
final_clip = clips_array(grid)

# Guardar el video resultante
output_path = 'collage_video.mp4'
final_clip.write_videofile(output_path, codec='libx264', fps=24)

print(f"El collage de video se ha guardado correctamente en '{output_path}'.")

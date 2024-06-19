import cv2

def main(rtsp_url):
    # Abre la conexión RTSP
    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        print("Error: No se puede abrir la transmisión RTSP.")
        return

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error: No se puede recibir frame (stream end?). Saliendo ...")
            break

        # Muestra el frame
        cv2.imshow('RTSP Viewer', frame)

        if cv2.waitKey(1) == ord('q'):
            break

    # Libera los recursos
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    rtsp_url = "rtsp://jupache:Pip0l3iras@192.168.1.43/ch0_0.h264"
    main(rtsp_url)

import cv2

for i in range(5):
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print(f"Камера {i}: не открылась")
        continue

    ret, frame = cap.read()

    if ret:
        print(f"Камера {i}: кадр получен")
    else:
        print(f"Камера {i}: ошибка получения кадра")

    cap.release()

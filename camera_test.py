import cv2

camera = cv2.VideoCapture(1)

if not camera.isOpened():
    print("Camera could not be opened!")
else:
    print("Press Q to close the camera.")

    while True:
        ret, frame = camera.read()

        if not ret:
            print("Could not read frame.")
            break
        cv2.imshow("Camera Index 0",frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
camera.release()
cv2.destroyAllWindows()
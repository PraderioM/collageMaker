import os

import cv2

from input_request_tools import get_file_path, get_integer



def main():
    in_video = get_file_path('Insert path of the video whose frames you want to extract')
    period = get_integer('One every X frames will be stored. Insert X', default=100, min_val=1)
    out_img_name = os.path.splitext(in_video)[0]
    video = cv2.VideoCapture(in_video)
    ret, img = video.read()
    i = 1
    j = 1
    while ret:
        if i % period == 0:
            cv2.imwrite(f'{out_img_name}_frame_number_{j:03}.jpg', img)
            j += 1
            i = 0
        i += 1
        ret, img = video.read()
    pass

if __name__ == '__main__':
    main()

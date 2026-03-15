import hashlib
import time
import os
import threading
import subprocess
from PIL import Image
import imagehash
import glob

def fill_zeroes(str1):
    if len(str1) == 258:
        return str1
                        
    str1 = str1[2:]
    diff = 256 - len(str1)
    extra = (diff) * "0"
    str1 = "0b" + extra + str1
    return str1

def extract_frame(sec, vid, opss):
    #print("extract frame")
    cmd_str = "ffmpeg -ss 00:00:{} -i {} -frames:v 1 -q:v 2 {}".format(sec, vid, opss)
    subprocess.run(cmd_str, shell=True)
    #print(cmd_str)
    #print("frmae extracted")
    

def get_length(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)

def worker(path, filename):


    filepath = os.path.join(path, filename)
    ss_path = './screenshots/ss.bmp'
    print(filepath)
    try:
        vid_len = get_length(filepath)

        frame_time = "01"
        if vid_len >= 28:
            frame_time = "13"
        elif vid_len >= 19:
            frame_time = "9"
        elif vid_len >= 13:
            frame_time = "07"
        elif vid_len >= 9:
            frame_time = "04"
        elif vid_len >= 4:
            frame_time = "03"

        extract_frame(frame_time, filepath, ss_path)
        image=Image.open(ss_path)
        image=image.resize((400,300))
        phash = imagehash.average_hash(image, hash_size=16)
        phash = str(bin(int(str(phash), 16)))
        print("frame time: ", frame_time)
        #print("[{}]".format(tid), phash)
        #os.remove(ss_path)

        phash = fill_zeroes(phash)
        if len(phash) < 258:
            phash="NA"

        print("[{}]".format(filename), phash)
        #end_time_del = time.time()
    except Exception as e:
        #pass
        print("Other error in wget: ", e)
        
        # print("hash: " ,hashlib.md5(open('./downloads/temp.mp4','rb').read()).hexdigest())
    #print("!!!!!!!! Closing thread {} !!!!!!!!!!!!!!!!".format(tid))

if __name__ =="__main__":
    # get all mp4 files in the downloads folder and create a thread for each file to compute the phash
    path = r"C:\\Users\\vishw_7p78elj\\Downloads\\*.mp4"
    files = glob.glob(path)
    print("files: ", files)
    threads = []
    for filename in files:
        worker(r"C:\\Users\\vishw_7p78elj\\Downloads", filename)
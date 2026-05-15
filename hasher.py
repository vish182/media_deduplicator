import os
import subprocess
import tempfile

from PIL import Image
import imagehash

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
    # -y: temp path is pre-created by mkstemp; ffmpeg must overwrite without tty prompt.
    cmd_str = "ffmpeg -y -ss 00:00:{} -i {} -frames:v 1 -q:v 2 {}".format(
        sec, vid, opss
    )
    subprocess.run(
        cmd_str, shell=True, stdin=subprocess.DEVNULL
    )
    #print(cmd_str)
    #print("frmae extracted")
    

def get_length(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)


def frame_time_for_duration(vid_len):
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
    return frame_time


def compute_video_phash_meta(filepath):
    """Return ``(phash, frame_time)``; ``phash`` is None on failure.

    ``filepath`` may be a str or path-like object. Uses a temp frame image so
    parallel callers do not clobber a shared screenshot path.
    """
    filepath = os.fspath(filepath)
    fd, ss_path = tempfile.mkstemp(suffix=".bmp")
    os.close(fd)
    try:
        vid_len = get_length(filepath)
        frame_time = frame_time_for_duration(vid_len)

        extract_frame(frame_time, filepath, ss_path)
        with Image.open(ss_path) as image:
            small = image.resize((400, 300))
            phash = imagehash.average_hash(small, hash_size=16)
        phash = str(bin(int(str(phash), 16)))
        phash = fill_zeroes(phash)
        if len(phash) < 258:
            return "NA", frame_time
        return phash, frame_time
    except Exception as e:
        print("Other error in wget: ", e)
        return None, None
    finally:
        try:
            os.unlink(ss_path)
        except OSError:
            pass


def compute_video_phash(filepath):
    """Return normalized binary perceptual hash string, or None on failure."""
    phash, _ = compute_video_phash_meta(filepath)
    return phash


def worker(path, filename):
    filepath = os.path.join(path, filename)
    print(filepath)
    phash, frame_time = compute_video_phash_meta(filepath)
    if phash is None:
        print("[{}] ERROR".format(filename))
        return
    print("frame time: ", frame_time)
    print("[{}]".format(filename), phash)

if __name__ =="__main__":
    # get all mp4 files in the downloads folder and create a thread for each file to compute the phash
    worker("./samples/", "game_640x360.mp4")
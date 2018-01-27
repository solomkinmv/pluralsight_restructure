import sys
import os
import json
from glob import glob
from shutil import copyfile


class VideoHashed:

    def __init__(self, module_hash, clip_hash, video_path):
        self.module_hash = module_hash
        self.clip_hash = clip_hash
        self.video_path = video_path

    def __str__(self) -> str:
        return f"VideoHashed: {self.video_path}"


class Video:

    def __init__(self, module_title, clip_title, video_path):
        self.module_title = module_title
        self.clip_title = clip_title
        self.video_path = video_path

    def __str__(self) -> str:
        return f"Video: {self.video_path}"


def lookup_json(course_dir):
    mask = "/*.json"
    json_list = glob(course_dir + mask)
    if len(json_list) != 1:
        raise Exception(f"Couldn't find json file in dir: {course_dir}")

    return json_list[0]


def restructure_course(course_dir):
    if not is_pluralsight_course(course_dir):
        return

    print(f"Started processing course: {course_dir}")

    try:
        file_name = lookup_json(course_dir)
    except Exception as e:
        print(f"Couldn't process directory {course_dir}: {str(e)}")
        return

    meta_data = read_json(file_name)
    video_paths = lookup_video_files(course_dir)
    hashed_videos = list(map(lambda p: to_hashed(p), video_paths))

    module_id_to_title = {}
    clip_id_to_title = {}
    for module_index, module in enumerate(meta_data['modules']):
        module_id_to_title[module['id']] = str(module_index + 1) + '. ' + module['title']

        for clip_index, clip in enumerate(module['clips']):
            clip_id_to_title[clip['id']] = str(clip_index + 1) + '. ' + clip['title']

    hashed_to_video = build_hashed_to_videos()
    videos = map(lambda hashed_video: hashed_to_video(hashed_video, module_id_to_title, clip_id_to_title), hashed_videos)
    save_videos(videos, meta_data['title'])

    print(f"Finished processing course: {course_dir}")


def lookup_video_files(start_dir):
    mask = "/*/*/*/*/*/*/*/*/*"
    return glob(start_dir + mask)


def to_path_chunks(path):
    return path.split('/')


def extract_module_id(path_chunks):
    return path_chunks[-4]


def extract_clip_id(path_chunks):
    return path_chunks[-3]


def to_hashed(path):
    chunks = to_path_chunks(path)
    return VideoHashed(extract_module_id(chunks), extract_clip_id(chunks), path)


def read_json(file_name):
    return json.load(open(file_name))


def lookup_title_by_hash(id_part, id_to_title_map):
    results = []
    for key in id_to_title_map:
        if id_part in key:
            results.append(id_to_title_map[key])

    if len(results) != 1:
        print(f"Wrong number of filtered elements. Expected to be 1, but received: {results} from {id_to_title_map} for hash {id_part}")
        return None

    return results[0]


def build_hashed_to_videos():
    module_hash_to_title = {}
    clip_hash_to_title = {}

    def hashed_to_video(hashed_video, module_id_to_title, clip_id_to_title):
        module_hash = hashed_video.module_hash
        if module_hash not in module_hash_to_title:
            module_hash_to_title[module_hash] = lookup_title_by_hash(module_hash, module_id_to_title)

        clip_hash = hashed_video.clip_hash
        if clip_hash not in clip_hash_to_title:
            clip_hash_to_title[clip_hash] = lookup_title_by_hash(clip_hash, clip_id_to_title)

        module_title = module_hash_to_title[module_hash]
        clip_title = clip_hash_to_title[clip_hash]
        if module_title is None or clip_title is None:
            return None

        return Video(module_title, clip_title, hashed_video.video_path)

    return hashed_to_video


def save_videos(videos, course_title):
    output_path = './output'
    course_title = course_title.replace('/', '')

    for video in videos:
        if video is None:
            continue

        video.module_title = video.module_title.replace('/', '')
        video.clip_title = video.clip_title.replace('/', '')
        try:
            module_path = os.path.join(output_path, course_title, video.module_title)
            if not os.path.exists(module_path):
                os.makedirs(module_path)

            target_path = os.path.join(module_path, video.clip_title + '.mp4')
        except Exception as e:
            print(f"Couldn't create target path: ${target_path}")

        try:
            copyfile(video.video_path, target_path)
        except Exception as e:
            print(f"Couldn't copy video from ${video.video_path} to ${target_path} because of ${e}")


def is_pluralsight_course(dir_path):
    if not os.path.isdir(dir_path):
        return False

    for content in os.listdir(dir_path):
        if 'pluralsight' in content:
            return True

    return False


if __name__ == '__main__':

    for course in os.listdir('.'):
        restructure_course(course)
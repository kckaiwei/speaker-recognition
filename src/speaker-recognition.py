#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: speaker-recognition.py
# Date: Sun Feb 22 22:36:46 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import argparse
import sys
import glob
import os
import itertools
import datetime
import scipy.io.wavfile as wavfile

sys.path.append(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'gui'))
from gui.interface import ModelInterface
from gui.utils import read_wav
from filters.silence import remove_silence

def get_args():
    desc = "Speaker Recognition Command Line Tool"
    epilog = """
Wav files in each input directory will be labeled as the basename of the directory.
Note that wildcard inputs should be *quoted*, and they will be sent to glob.glob module.

Examples:
    Train (enroll a list of person named person*, and mary, with wav files under corresponding directories):
    ./speaker-recognition.py -t enroll -i "/tmp/person* ./mary" -m model.out

    Predict (predict the speaker of all wav files):
    ./speaker-recognition.py -t predict -i "./*.wav" -m model.out
"""
    parser = argparse.ArgumentParser(description=desc,epilog=epilog,
                                    formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-t', '--task',
                       help='Task to do. Either "enroll" or "predict"',
                       required=True)

    parser.add_argument('-i', '--input',
                       help='Input Files(to predict) or Directories(to enroll)',
                       required=True)

    parser.add_argument('-m', '--model',
                       help='Model file to save(in enroll) or use(in predict)',
                       required=True)

    ret = parser.parse_args()
    return ret

def task_enroll(input_dirs, output_model):
    m = ModelInterface()
    input_dirs = [os.path.expanduser(k) for k in input_dirs.strip().split()]
    dirs = itertools.chain(*(glob.glob(d) for d in input_dirs))
    dirs = [d for d in dirs if os.path.isdir(d)]
    files = []
    if len(dirs) == 0:
        print "No valid directory found!"
        sys.exit(1)
    for d in dirs:
        label = os.path.basename(d.rstrip('/'))

        wavs = glob.glob(d + '/*.wav')
        if len(wavs) == 0:
            print "No wav file found in {0}".format(d)
            continue
        print "Label {0} has files {1}".format(label, ','.join(wavs))
        for wav in wavs:
            fs, signal = read_wav(wav)
            m.enroll(label, fs, signal)

    m.train()
    m.dump(output_model)


def task_predict(input_files, input_model):
    m = ModelInterface.load(input_model)
    #Counters
    total = 0.0
    wrong = 0.0
    total_confidence = 0.0
    count = 0
    wrong_list = []
    time_start = datetime.datetime.now()
    for f in glob.glob(os.path.expanduser(input_files)):
        count += 1
        total += 1
        fs, signal = read_wav(f)
        #remove_silence(fs, signal)
        #label, confidence, average_confidence = m.predict(fs, signal)
        label, confidence, average_confidence = m.predict(fs, remove_silence(fs, signal))
        print label, f
        if not is_correct(label, f):
            wrong +=1
            wrong_list.append(label + ": " + str(f))
            did_gain = "-"
            #if str(label) in output:
            #    output[str(label)].append(str(f))
            #else:
            #    output[str(label)] = [str(f)]
        else:
            did_gain = "+"
        total_confidence = total_confidence + confidence
        #print "Current confidence: ", (100-confidence)
        #print "Average confidence: ", average_confidence
        print "Accuracy:", (total-wrong)/total, did_gain
    #print output
    #print wrong_list
    for item in wrong_list:
        print item
    print "Operation took: ", (datetime.datetime.now()-time_start)


def is_correct(label, f):
    if str(label[0:4]) in str(f):
    #if str(label[0:4]) == "1245" or str(label[0:4]) == "1240":
        return True
    else:
        return False

def speech_trim(filename, directory, seg_length):
    """Detects and splits file into segments with non-silence
    :type seg_length : length of segment in milliseconds
    """
    convo = AudioSegment.from_wav(directory + "/" + str(filename))

    ten_seconds = 10 * 1000
    sliced = AudioSegment.empty()

    #print silence.detect_silence(convo, min_silence_len=1000, silence_thresh=-35)
    print convo.rms

    start = 0
    finish = 0

    #milliseconds padding, so not harsh cutoff
    silence_padding = 300
    count = 0
    for items in silence.detect_silence(convo, min_silence_len=1000, silence_thresh=-30):
        count += 1
        print items[0], items[1]
        finish = items[0]
        if len(sliced) < seg_length:
            sliced = sliced + convo[start:finish]
        else:
            sliced.export(directory + "/" + str(count) + ".wav", format='wav', bitrate='192k')
            sliced = AudioSegment.empty()
            print "Completed part:", count
        start = items[1]

if __name__ == '__main__':
    global args
    args = get_args()

    task = args.task
    if task == 'enroll':
        task_enroll(args.input, args.model)
    elif task == 'predict':
        task_predict(args.input, args.model)

#!/usr/bin/env python
# encoding: utf=8
"""
mix_track_utils.py

Utilities to combine tracks end to end with specifications transitions.

An AudioQuantumList can be used to render a remix.AudioData object like this:
	out = audio.getpieces(audiofile, final["music"])
Then render the new file with:
    out.encode(output_filename)

By Mike iLL/mZoo.org, 2015-01-13.
"""
from __future__ import print_function
import echonest.remix.audio as audio
from Queue import Queue
import glob
import sys, os
import pickle

usage = """
Usage: 
    import mix_track_utils

"""

def make_save_one(filename):
    """
    Get filename, make LocalAudioFile objects and save it. Return LAF.
    """
    audiofile = audio.LocalAudioFile(filename)
    'audiofile2 = audiofile'
    audiofile.save()
    return audiofile
    
def make_save_all(files):
    """
    Get a list of files, make LocalAudioFile objects and save them.
    """
    q = file_queue(files)

    while not q.empty():
        file = q.get()
        save_me(file)
        
def file_queue(files):
    """
    Get list of files, add them to a queue and return the queue.
    """
    q = Queue() 
    
    for f in files:
        q.put(f)
    
    return q
    
def get_files(directory = 'audio/', extension = 'mp3'):
    return glob.glob(directory + '*.' + extension)
    
def import_queue(q):
    """
    Get a queue, iterate and yield a list of two imported LocalAudioFiles
    """
    t1 = q.get()
    q.task_done()
    while not q.empty():
        t2 = q.get()
        q.task_done()
        audiofile1 = lazarus(t1)
        audiofile2 = lazarus(t2)
        yield (audiofile1, audiofile2)
        t1 = t2
        
def lazarus(filename):
    """
    Get pickled (*.en) filename (path) and return echonest analysis object
    """
    with open(filename) as f:
        return pickle.load(f)
        
def show_transitions():
    while not q.empty():
        while True:
            try:
                next_two = here.next()
                print(next_two[0].filename, '->', next_two[1].filename)
            except StopIteration:
                print("All done.")
                return
                
def trim_track(track, trim_start=0, trim_end=0):
	"""Get echonest analysis object with count and return trimmed AudioQuantum list."""
	music = audio.AudioQuantumList()
	for k, v in enumerate(track.analysis.tatums):
		if k >= trim_start and k < len(track.analysis.tatums) - trim_end:
			music.append(v)
	return music
	
def tatum_count(track):
	"""Get echonest analysis object and return tatum count."""
	return len(track.analysis.tatums)

def analize(input_filename):
    """
    Get mp3 filename and return echonest analysis object
    """
    audiofile = audio.LocalAudioFile(input_filename)
    return audiofile.analysis
    
def visualize_analysis(track):
    import matplotlib.pyplot as plt
    
    rates = ["tatums", "segments", "beats"]

    title = "Start and End Bits of {}".format(track.filename)
    plt.figure()
    plt.title(title)
    plt.axis([-1, 5, -3, 3])
    plt.grid(True)
    
    label_height = .2
    graph_height = 0
    for name in rates:
        label_height += .5
        graph_height += .5
        plt.text(0, label_height, 'Start ' + name.capitalize())
        for i in getattr(track.analysis, name)[:8]:
            j = (i.start, i.end)
            plt.plot(j,[graph_height,graph_height], linewidth=10)
            
    label_height = 0
    graph_height = -.2
    offset = None 

    for name in rates:
        label_height -= .5
        graph_height -= .5
        plt.text(0, label_height, 'End ' + name.capitalize())
        for i in getattr(track.analysis, name)[:8]:
            j = (i.start, i.end)
            if offset is None:
                offset = j[0]
            k = (j[0] - offset, j[1] - offset)
            plt.plot(k,[graph_height,graph_height], linewidth=10)
    
    plt.show()
    
def compare(track, rate1="segments", rate2="tatums", direction="start", number=8):
    """
    Get track and compare rates at start or end.
    """
    if direction == "end":
        number = number - (number * 2)
        section1 = getattr(track.analysis, rate1)[number:]
    else:
        section1 = getattr(track.analysis, rate1)[:number]
    try:
        print("{} {}: {}".format(direction, rate1, section1))
    except AttributeError:
        print("No {}.".format(rate1))
    
    
    
if __name__ == "__main__":
	print(usage)
	sys.exit(-1)


#!/usr/bin/env python
# encoding: utf=8
"""
mix_track_utils.py

Utilities to combine tracks end to end with specifications transitions.

An AudioQuantumList can be used to render a remix.AudioData object like this:
	out = audio.getpieces(audiofile, final["music"])
Then render the new file with:
    out.encode(output_filename)
    
Rates can be in "beats", "tatums", "segments", "bars", "sections".

By Mike iLL/mZoo.org, 2015-01-13.
"""
from __future__ import print_function
import echonest.remix.audio as audio
from Queue import Queue
import glob
import sys, os
import pickle
import subprocess
import echonest

usage = """
Usage: 
    import mix_track_utils

"""

ffmpeg_command = None
for command in ("avconv", "ffmpeg", "en-ffmpeg"):
	try:
		subprocess.Popen([command],stdout=subprocess.PIPE,stderr=subprocess.STDOUT).wait()
		ffmpeg_command = command
		break
	except OSError:
		# The command wasn't found. Move on to the next one.
		pass
if not ffmpeg_command:
	raise RuntimeError("No avconv/ffmpeg found, cannot continue")
echonest.remix.support.ffmpeg.FFMPEG = ffmpeg_command

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
        make_save_one(file)
        
def file_queue(files):
    """
    Get list of files, add them to a queue and return the queue.
    """
    q = Queue() 
    
    for f in files:
        q.put(f)
    
    return q
    
def get_mp3s(directory = 'audio/', extension = 'mp3'):
    return glob.glob(directory + '*.' + extension)
    
def get_saved(directory = 'audio/', extension = 'en'):
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
	plt.subplots_adjust(top=0.9)
	plt.rcParams["axes.titlesize"] = 11
	try:
		plt.axis([0, track.analysis.beats[9].start, -4, 4])
	except IndexError:
		plt.axis([0, 6, -4, 4])
	ax = plt.subplot(211)
	ax.grid(True)
	ax.set_title(title)
	label_height = .05
	graph_height = 0
	for name in rates:
		label_height += .5
		graph_height += .5
		plt.text(0, label_height, 'Start ' + name.capitalize())
		for i in getattr(track.analysis, name)[:8]:
			j = (i.start, i.end)
			plt.plot(j,[graph_height,graph_height], linewidth=10)
		
	label_height = -.15
	graph_height = -.2
	offset = None 

	ax1 = plt.subplot(212)
	ax1.grid(True)
	for name in rates:
		label_height -= .5
		graph_height -= .5
		plt.text(0, label_height, 'End ' + name.capitalize())
		for i in getattr(track.analysis, name)[-8:]:
			j = (i.start, i.end)
			if offset is None:
				offset = j[0]
			k = (j[0] - offset, j[1] - offset)
			plt.plot(k,[graph_height,graph_height], linewidth=10)

	plt.show()
    
def compare(track, rate1="segments", rate2="tatums", direction="first", number=8):
    """
    Get track and compare rates at start or end.
    """
    if direction == "final":
        number = number - (number * 2)
        section1 = getattr(track.analysis, rate1)[number:]
        section2 = getattr(track.analysis, rate2)[number:]
    else:
        section1 = getattr(track.analysis, rate1)[:number]
        section2 = getattr(track.analysis, rate2)[:number]
        
    try:
        print("{} {} {} span {} to {}".format(direction.capitalize(), abs(number), rate1, section1[0].start, \
                                                section1[-1].start + section1[-1].duration))
    except IndexError:
        print("No {}.".format(rate1))
        
    try:
        print("{} {} {} span {} to {}".format(direction.capitalize(), abs(number), rate2, section2[0].start, \
                                                section2[-1].start + section2[-1].duration))
    except IndexError:
        print("No {}.".format(rate2))
        
def end_trans(track, beats_to_mix = 0):
    """
    Return tuples with times to be sent to Playback and Crossmix objects
    """
    try:
    	track.analysis.beats[-1]
    except IndexError:
    	return {"playback": (track.analysis.segments[-8].start, track.analysis.duration)}
    avg_duration = sum([b.duration for b in track.analysis.beats[-8:]]) / 8	
    if beats_to_mix > 0:
    	track_end = track.analysis.duration - (avg_duration * beats_to_mix)
    else:
    	track_end = track.analysis.duration

    final_eight = {"last_beat": track.analysis.beats[-1].start,
                    "subsequent_beat": track.analysis.beats[-1].start}
    while final_eight['subsequent_beat'] < track_end:
        final_eight['subsequent_beat'] += avg_duration

    #start, end, duration of playback part
    final_eight["playback"] = (track.analysis.segments[-8].start, 
    							track.analysis.beats[-1].start + track.analysis.beats[-1].duration,
    							track.analysis.beats[-1].start + track.analysis.beats[-1].duration \
    															- track.analysis.segments[-8].start)
    
    #start, end, duration of mix part
    final_eight["mix_me"] = (final_eight['subsequent_beat'], track.analysis.duration, \
    														track.analysis.duration - \
    														final_eight['subsequent_beat']) 
   
    return (final_eight['playback'], final_eight["mix_me"])
    
def lead_in(track):
	"""
	Return the time between start of track and first beat.
	"""
	return track.analysis.beats
    
if __name__ == "__main__":
	print(usage)
	sys.exit(-1)


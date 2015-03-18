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
from action import Crossfade as cf
from action import Playback as pb
from action import render
import glob
import sys, os
import pickle
import subprocess
import echonest

usage = """
Usage: 
    import mix_track_utils

"""

LOUDNESS_THRESH = -8
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
        
def lazarus(filename):
    """
    Get pickled (*.en) filename (path) and return echonest analysis object
    """
    with open(filename) as f:
        return pickle.load(f)
        
def raise_pairs_from_queue(q):
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
        
def lazarus_queue(q):
	"""
	Get a queue of saved track filenames and return a container of name: track for each.
	"""
	container = {}
	while not q.empty():
		track = q.get()	
		filename = track.replace('.mp3.analysis.en', '')
		filename = filename.replace('audio/', '')
		container[filename] = lazarus(track)
	return container
        
def resurrect():
    files = get_saved()
    q = file_queue(files)
    return lazarus_queue(q)
        
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
    
def visualize(track):
	"""
	Get a track and generate a graph showing relationships between rates at start and end of track.
	"""
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
        
def last_viable(track):
	for seg in reversed(track.analysis.segments):
		if seg.loudness_max > -60:
			#time of last audible piece of track
			return seg.start + seg.duration
			
def first_viable(track):
	for seg in track.analysis.segments:
		if seg.loudness_max > -60:
			#time of first audible segment of track
			return seg.start
			

					
def end_trans(track, beats_to_mix = 0):
	"""
	Return tuples with times to be sent to Playback and Crossmix objects
	"""
	end_viable = last_viable(track)
	try:
		avg_duration = sum([b.duration for b in track.analysis.tatums[-16:]]) / 16
	except IndexError:
		avg_duration = sum([b.duration for b in track.analysis.segments[-8:]]) / 8
	#How much of the track are we returning - adjust for beats to mix?
	start = track.analysis.duration - (10 + (avg_duration * beats_to_mix))
	if beats_to_mix > 0:
		#if we're crossfading, playback ends at first beat of crossfade
		playback_end = end_viable - (avg_duration * beats_to_mix)
		final =  beats_to_mix #count tatums from end of tatum list

	else:
		#if we're not crossfading playback to end, final beat being last tatum
		playback_end = end_viable
		final = 1
		
	try:
		track.analysis.tatums[-1]
	except IndexError:
		# if no tatums play through end of track
		final_segments = {"subsequent_beat": track.analysis.segments[-final].start}
		final_segments["playback_start"] = start
		final_segments["playback_duration"] = playback_end - final_segments["playback_start"]
		final_segments["mix_start"] = final_segments['subsequent_beat']
		final_segments["mix_duration"] = end_viable - final_segments['subsequent_beat']
		final_segments["avg_duration"] = avg_duration
		return final_segments

	final_segments = {"subsequent_beat": track.analysis.tatums[-final].start}
	while final_segments['subsequent_beat'] < playback_end:
		#get first "beat" following end of playback
		final_segments['subsequent_beat'] += avg_duration

	final_segments["playback_start"] = start
	final_segments["playback_duration"] = playback_end - final_segments["playback_start"]
	final_segments["mix_start"] = final_segments['subsequent_beat']
	final_segments["mix_duration"] = end_viable - final_segments['subsequent_beat']
	final_segments["avg_duration"] = avg_duration

	return final_segments
	
def db_2_volume(loudness):
		return (1.0 - LOUDNESS_THRESH * (LOUDNESS_THRESH - loudness) / 100.0)
		
def gimme_two(track1, track2, xfade=0, otrim=0, itrim=0):
	for track in [track1, track2]:
		loudness = track.analysis.loudness
		track.gain = db_2_volume(loudness)
		
	if xfade == 0:
		times = end_trans(track1)
		if times["playback_duration"] - otrim < 0:
			raise Exception("You can't trim off more than 100%.")
		pb1 = pb(track1, times["playback_start"], times["playback_duration"] - otrim)
		pb2 = pb(track2, first_viable(track2) + itrim, pb1.duration + 10)
		return [pb1, pb2]
	else:
		times = end_trans(track1, beats_to_mix=xfade)
		'''We would start at zero, but make it first audible segment'''
		t2start = first_viable(track2)
		'''offset between start and first theoretical beat.'''
		t2offset = lead_in(track2)
		pb1 = pb(track1, times["playback_start"], times["playback_duration"] - t2offset)
		pb2 = cf((track1, track2), (times["playback_start"] + times["playback_duration"] - t2offset, t2start), times["mix_duration"])
		pb3 = pb(track2, t2start + times["mix_duration"], 10)
		return [pb1, pb2, pb3]

def lead_in(track):
	"""
	Return the time between start of track and first beat.
	"""
	avg_duration = sum([b.duration for b in track.analysis.beats[:8]]) / 8
	try:
		earliest_beat = track.analysis.beats[0].start
	except IndexError:
		earliest_beat = track.analysis.segments[0].start
	while earliest_beat > 0:
		earliest_beat -= avg_duration
	offset = earliest_beat
	return offset
	
def play(filename):
	"""
	Play track - only works on OSX.
	"""
	import subprocess
	subprocess.call(["afplay", filename])
    
if __name__ == "__main__":
	print(usage)
	sys.exit(-1)


#
# File name: autoplayer.py
#
# Author: Piyush
#
# Description: Scheduled Audio/Video/WebLink Player
# 
# Chanage log:
# 2017/08/29 : Initial version. (Piyush)
#
#

import os
import sys
import time
import Tkinter as tk
#import tkinter as tk
import glob
import re
import subprocess
import urllib

class SystemLockGUI(tk.Frame):
	def __init__(self, master=None):
		tk.Frame.__init__(self, master)
		self.root = master
		self.root.title("Auto Player")
		##### User Parameters #####
		self.PATH = os.path.dirname(os.path.abspath(__file__))	#Path for Audio/Video/WebLink dirs/files
		###########################
		## Variables
		self.playlist = []
		self.current_playlist = []
		## To Keep window on TOP
		self.root.lift()
		self.root.call('wm', 'attributes', '.', '-topmost', True)
		self.root.after_idle(master.call, 'wm', 'attributes', '.', '-topmost', False)
		## create widgets
		self.root.protocol('WM_DELETE_WINDOW', self.closeGUI)
		self.pack()
		self.createWidgets()

	def createWidgets(self):
		self.info = tk.Button(self) #tk.Label(self)
		self.info["state"] = "disable"
		self.info["fg"]   = "black"
		self.info["text"] = "Not Scheduled"
		self.info.grid(row=0,column=0, columnspan=3, sticky="WE")

		self.QUIT = tk.Button(self)
		self.QUIT["fg"]   = "red"
		self.QUIT["text"] = "Close"
		self.QUIT["command"] =  self.closeGUI
		self.QUIT.grid(row=1, column=0, columnspan=3, sticky="WE")

		self.onUpdate()

	def get_playlistall(self):
		playlistall = []
		for path in glob.glob(self.PATH + "/*HM-*"):
			if(os.path.isdir(path)):
				playlistall.append([os.path.basename(path),path]+glob.glob(path+"/*"))
			else:
				links = []
				try:
					with open(path) as f:
						for l in f.readlines():
							if(len(l.split())==1):
								links.append(l.strip())
							elif(len(l.split())==2):
								try:
									url = urllib.urlopen(l.split()[1])
									webpage_text = url.read()
									url.close()
									links = re.findall(re.compile("\/watch\?v=..........."),webpage_text)
									unique_links = []
									[unique_links.append(l) for l in links if not unique_links.count(l)]
									for link in unique_links:
										links.append("https://www.youtube.com"+link)
								except:
									print("ERROR: No internet connection.")
				except:
					print("ERROR: File/Dir does not exist.")
				if(links):
					playlistall.append([os.path.basename(path).split('.')[0],path]+links)
		return playlistall
	
	def get_timeHM(self):
		return int(time.strftime("%H"))*60+int(time.strftime("%M"))
	
	def update_playlist(self):
		self.playlist = []
		rd = False
		currentHM = self.get_timeHM()
		currentYMDW = {'Y':time.strftime("%2Y"),
			'M':time.strftime("%2m"),
			'D':time.strftime("%2d"),
			'W':time.strftime("%2w")
			}
		for pl in self.get_playlistall():
			playlist_validity = True
			playlist_rd = False
			for t in pl[0].split('_'):
				ts = t.split('-')
				if(ts[0] == "RD"):
					playlist_rd = True
				elif(re.match("^[YMDW]+-",t[0]+'-')):
					if not ''.join([currentYMDW[dt] for dt in ts[0]]) in ts[1:]:
						playlist_validity = False
			if(playlist_validity == True):
				for t in pl[0].split('_'):
					ts = t.split('-')
					if(ts[0] == "HM"):
						hm = [(int(hmt[0:2])*60)+int(hmt[2:5]) for hmt in ts[1:]]
						for hmt in zip(hm[::2],hm[1::2]):
							if(hmt[0]<currentHM<hmt[1]):# or currentHM<hmt[0]
								if(playlist_rd):
									self.playlist.append([hmt[0],hmt[1]]+random.shuffle(pl[2:]))
								else:
									self.playlist.append([hmt[0],hmt[1]]+pl[2:])
		self.playlist.sort(key=lambda x:(x[0]-currentHM) if(x[0]>=currentHM)else (24*60)+currentHM-x[0])

	def get_current_playlist(self):
		playlist = next(iter(self.playlist),[])
		if(playlist):
			if(playlist[0]<self.get_timeHM()<playlist[1]):
				return playlist
		return []

	def get_pids(self,searchstr):
		p = subprocess.Popen("ps aux | grep '"+searchstr+"' | awk '{print $2}' | tr '\n' ' '", stdout=subprocess.PIPE, shell=True)
		return p.communicate()[0]

	def kill_process(self,searchstr):
		p = subprocess.Popen("kill "+self.get_pids(searchstr), stdout=subprocess.PIPE, shell=True)
		p.communicate()[0]

	def isplaylist_same(self):
		return self.current_playlist == self.get_current_playlist()

	def onUpdate(self):
		if(len(self.get_pids("vlc --loop \| omxplayer -o local").split())<=1):
			player_closed = True
		else:
			player_closed = False
		self.update_playlist()
		if(not self.isplaylist_same() or (player_closed and self.get_current_playlist())):
			self.current_playlist = self.get_current_playlist()
			self.kill_process("vlc --loop ")
			self.kill_process("omxplayer -o local ")
			self.info["text"] = "Not Scheduled"
			print("Old vlc/omxplayer process has been killed.")
			if(self.current_playlist):
				if(self.current_playlist[2][0] == '/'):
					subprocess.Popen(("vlc --loop "+" ".join(self.current_playlist[2:])).split(), stdout=subprocess.PIPE)
					self.info["text"] = os.path.basename(self.current_playlist[2])
					print("vlc has been started.")
				else:
					try:
						link = random.choice(self.current_playlist[2:])
						os.system("""omxplayer -o local `youtube-dl -f "(mp4,3gp)best[height<=350]" -g """+link+"`")
						self.info["text"] = link
						print("omxplayer has been started.")
					except:
						print("Connection error")
		print("Current Playlist:",self.current_playlist)
		self.after(15*1000, self.onUpdate)

	def closeGUI(self):
		self.kill_process("vlc --loop ")
		self.kill_process("omxplayer -o local ")
		self.quit()

if __name__ == '__main__':
	#if(os.name == 'posix'): #For POSIX
	#	print("Current OS type: POSIX.")
	#elif(os.name == 'nt'): #For Window
	#	print("Current OS type: Window.")
	#elif(os.name == 'mac'): #For MacOS
	#	print("Current OS type: MacOS.")
	#else: # Not supported system
	#	print("This program is not supported in current OS.")
	#	sys.exit(0)
	root = tk.Tk()
	app = SystemLockGUI(master=root)
	app.mainloop()
	try:
		root.destroy()
	except:
		pass
	#print("GUI Destroyed.")
	#raw_input("Press any to key to Exit.")


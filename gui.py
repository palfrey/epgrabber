#!/usr/bin/env python

import sys
import gtk

ver = gtk.check_version(2,12,0)
if ver:
	raise Exception,ver

import gobject
from pysqlite2 import dbapi2 as sqlite
from time import *

class EpgrabberGUI:
	def __init__(self):
		
		#Set the Glade file
		self.intffile = "epgrabber.glade"  
		self.wTree = gtk.Builder()
		self.wTree.add_from_file(self.intffile)
		
		#Get the Main Window, and connect the "destroy" event
		self.window = self.wTree.get_object("wndMain")
		if self.window:
			self.window.connect("destroy", gtk.main_quit)
		self.window.show()

		self.episodes = gtk.ListStore(gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_UINT, gobject.TYPE_UINT,gobject.TYPE_STRING, gobject.TYPE_STRING) # name, search, series, episode, command
		con = sqlite.connect("watch.db")
		cur = con.cursor()
		cur.execute("select name,search,season,episode,command,last from series order by last desc")
		for row in cur.fetchall():
			self.episodes.append(row)
		
		def build_tree_column(name,column):
			editable = gtk.CellRendererText()
			editable.set_property('editable', True)
			editable.connect('edited', self.edit_data,(self.episodes,column))
			return gtk.TreeViewColumn(name,editable,text=column)

		self.episodesList = self.wTree.get_object("tblEpisodes")
		self.episodesList.set_model(self.episodes)
		self.episodesList.append_column(build_tree_column("Name",0))
		self.episodesList.append_column(build_tree_column("Search",1))
		self.episodesList.append_column(build_tree_column("Series",2))
		self.episodesList.append_column(build_tree_column("Episode",3))
		self.episodesList.append_column(build_tree_column("Command",4))
		
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn("Last retrieved",cell,text=5)
		col.set_cell_data_func(cell,self.date_field,5)
		self.episodesList.append_column(col)

	def date_field(self, column, cell, model, iter, user_data):
		when = float(model.get_value(iter, user_data))
		if when == 0:
			when = "<span foreground=\"red\">Never</span>"
		else:
			when = strftime("%a, %d %b %Y",localtime(when))
		cell.set_property('markup', when)
	
	def edit_data(self, cellrenderertext, path, new_text, (model,column)):
		print "changed",path,new_text,column

if __name__ == "__main__":
	main = EpgrabberGUI()
	gtk.main()

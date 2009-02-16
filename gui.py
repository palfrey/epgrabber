#!/usr/bin/env python

import sys
import gtk

ver = gtk.check_version(2,12,0)
if ver:
	raise Exception,ver

import gobject
try:
	import sqlite3 as sqlite
except ImportError:
	from pysqlite2 import dbapi2 as sqlite
from time import *

class EpgrabberGUI:
	def __init__(self):
		#Set the Glade file
		self.intffile = "epgrabber.glade"  
		self.wTree = gtk.Builder()
		self.wTree.add_from_file(self.intffile)
		self.wTree.connect_signals(self)
		
		#Get the Main Window, and connect the "destroy" event
		self.window = self.wTree.get_object("wndMain")
		self.window.connect("destroy", gtk.main_quit)
		self.window.show_all()

		types = (gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_UINT, gobject.TYPE_UINT,gobject.TYPE_STRING, gobject.TYPE_FLOAT)
		self.episodes = gtk.ListStore(*types)
		self.con = sqlite.connect("watch.db")
		self.cur = self.con.cursor()
		self.cur.execute("select name,search,season,episode,command,last from series order by last desc")
		for row in self.cur.fetchall():
			iter = None
			try:
				iter = self.episodes.append(row)
			except TypeError:
				self.episodes.remove(self.episodes[-1].iter)
				newrow = []
				for (t,val) in zip(types,row):
					if t == gobject.TYPE_STRING:
						newrow.append(str(val))
					elif t == gobject.TYPE_UINT:
						if val == None:
							newrow.append(0)
						else:
							newrow.append(int(val))
					elif t == gobject.TYPE_FLOAT:
						if val == None:
							newrow.append(0.0)
						else:
							newrow.append(float(val))
					else:
						raise Exception,t
				self.episodes.append(newrow)
		
		def build_tree_column(name,column):
			typ = self.episodes.get_column_type(column)
			if typ == gobject.TYPE_UINT:
				editable = gtk.CellRendererSpin()
				editable.set_property("adjustment",gtk.Adjustment(lower=0,upper=1000,step_incr=1)) # FIXME: 1000 is a randomly picked "probably highest" value
				editable.connect('editing-started',self.edit_spin)
			else:
				editable = gtk.CellRendererText()
			editable.set_property('editable', True)
			editable.connect('edited', self.edit_data,(self.episodes,column))
			tvc = gtk.TreeViewColumn(name,editable,text=column)
			tvc.set_sort_column_id(column)
			return tvc

		self.episodesList = self.wTree.get_object("tblEpisodes")
		self.episodesList.set_model(self.episodes)
		
		self.mapping = ("Name","Search","Season","Episode","Command")
		self.mapping = dict(zip(range(len(self.mapping)),self.mapping))
		self.rev_mapping = dict([list(x)[::-1] for x in self.mapping.items()])
		for k in self.mapping:
			self.episodesList.append_column(build_tree_column(self.mapping[k],k))
		
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn("Last retrieved",cell,text=5)
		col.set_cell_data_func(cell,self.date_field,5)
		col.set_sort_column_id(5)
		self.episodesList.append_column(col)

	def date_field(self, column, cell, model, iter, user_data):
		when = float(model.get_value(iter, user_data))
		if when == 0:
			when = "<span foreground=\"red\">Never</span>"
		else:
			when = strftime("%a, %d %b %Y",localtime(when))
		cell.set_property('markup', when)
	
	def edit_data(self, cellrenderertext, path, new_text, (model,column)):
		print "trying to change",path,new_text,column
		cmd = "update series set %s=\"%s\" where name=\"%s\""%(self.mapping[column].lower(),new_text,self.episodes[path][self.rev_mapping["Name"]])
		typ = self.episodes.get_column_type(column)
		if typ == gobject.TYPE_UINT:
			try:
				new_text = int(new_text)
			except ValueError:
				dialog = gtk.MessageDialog(parent=self.window, flags=gtk.DIALOG_MODAL, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format="Only allowed numbers in that column!")
				dialog.run()
				dialog.destroy()
				return
		print cmd
		try:
			self.cur.execute(cmd)
			assert self.cur.rowcount == 1, self.cur.rowcount
			self.episodes[path][column] = new_text
			self.con.commit()
		except sqlite.IntegrityError,e:
			dialog = gtk.MessageDialog(parent=self.window, flags=gtk.DIALOG_MODAL, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format="Sqlite integrity failure. Can't use that name!")
			dialog.run()
			dialog.destroy()

	def edit_spin(self, cellrenderer, editable, path):
		editable.set_numeric(True)
	
	def add_changed(self,editable):
		self.wTree.get_object("btnAddNew").set_sensitive(editable.get_text()!="")
	
	def btnAdd_clicked_cb(self, button):
		dlg = self.wTree.get_object("dlgSeries")
		self.wTree.get_object("entNewSeries").connect('changed',self.add_changed)
		self.wTree.get_object("btnAddNew").connect('clicked',lambda x:dlg.response(gtk.RESPONSE_OK))
		self.wTree.get_object("btnCancelNew").connect('clicked',lambda x:dlg.response(gtk.RESPONSE_CANCEL))
		ret = dlg.run()
		dlg.destroy()

	def btnWizard_clicked_cb(self, button):
		dlg = self.wTree.get_object("dlgEpguides")
		ret = dlg.run()
		dlg.destroy()

if __name__ == "__main__":
	main = EpgrabberGUI()
	gtk.main()


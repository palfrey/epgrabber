#!/usr/bin/env python

import sys
import gtk, pango

ver = gtk.check_version(2, 12, 0)
if ver:
    raise Exception(ver)

import gobject
from time import *
from episodes_pb2 import All

import fetch


class EpgrabberGUI:
    def _addrow(self, row):
        iter = None
        try:
            iter = self.episodes.append(row)
        except TypeError:
            self.episodes.remove(self.episodes[-1].iter)
            newrow = []
            for (t, val) in zip(self.types, row):
                if t == gobject.TYPE_STRING:
                    if val == None:
                        newrow.append("")
                    else:
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
                    raise Exception(t)
            self.episodes.append(newrow)

    def rowClicked(self, treeview, path, view_column):
        # print "rowClicked",treeview, path, view_column.get_property("title")
        if view_column.get_property("title") == "Command":
            dlg = self.wTree.get_object("dlgCommand")
            command = self.episodes.get(self.episodes.get_iter(path), 4)[0]
            print("command", command)
            commands = command.split(";")
            print("commands", commands)

            if commands == []:
                count = 1
                parsed = [(None, ())]
            else:
                count = len(commands)
                parsed = []
                for k in commands:
                    open_brkt = k.find("(")
                    close_brkt = k.find(")")
                    assert open_brkt != -1 and close_brkt != -1, k
                    name = k[:open_brkt]
                    args = k[open_brkt + 1 : close_brkt].split(",")
                    print("name,args", name, args)
                    parsed.append(tuple([name, args]))

            # FIXME: we're assembling tblCommands manually. This could also be done with treeview
            # and a bunch of specialised renderers once we get the whole widget rendering thing fixed

            tbl = self.wTree.get_object("tblCommands")

            for c in tbl.get_children():
                tbl.remove(c)

            tbl.resize(count, 4)
            for i in range(count):
                name = parsed[i][0]
                args = parsed[i][1]

                argboxes = []

                liststore = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
                cmb = gtk.ComboBox(liststore)
                cell = gtk.CellRendererText()
                cmb.pack_start(cell, True)
                cmb.add_attribute(cell, "text", 0)

                for k in dir(fetch):
                    if k[0] == "_":
                        continue
                    cls = getattr(fetch, k)
                    liststore.append((k, cls))
                    if k == name:
                        cmb.set_active(len(liststore) - 1)
                        arg_count = len(cls.args)
                        if len(args) < arg_count:
                            assert arg_count <= len(args) + len(cls.run.__defaults__), (
                                args,
                                cls.args,
                                cls.run.__defaults__,
                            )
                            defaults = [str(x) for x in cls.run.__defaults__]
                            args.extend(defaults[-(arg_count - len(args)) :])
                            assert arg_count == len(args), (args, cls.args, defaults)
                            print("args", args)
                        for j in range(arg_count):
                            tb = gtk.TextBuffer()
                            tb.set_text(args[j])
                            txt = gtk.TextView(tb)
                            txt.set_property("editable", True)
                            txt.set_tooltip_text(cls.args[list(cls.args.keys())[j]])
                            txt.set_border_window_size(gtk.TEXT_WINDOW_LEFT, 5)
                            argboxes.append(txt)

                tbl.attach(cmb, 0, 1, i, i + 1)

                argtable = gtk.Table(rows=1, columns=len(argboxes))
                for a in range(len(argboxes)):
                    argtable.attach(argboxes[a], a, a + 1, 0, 1)
                tbl.attach(argtable, 1, 2, i, i + 1)

                btn = gtk.Button(stock="gtk-add")
                tbl.attach(btn, 2, 3, i, i + 1)

                btn = gtk.Button(stock="gtk-remove")
                tbl.attach(btn, 3, 4, i, i + 1)
            tbl.show_all()
            dlg.set_geometry_hints(
                dlg, max_height=dlg.size_request()[1], max_width=10000
            )
            dlg.run()
            dlg.hide()

    def __init__(self):
        # Set the Glade file
        self.intffile = "epgrabber.xml"
        self.wTree = gtk.Builder()
        self.wTree.add_from_file(self.intffile)
        self.wTree.connect_signals(self)

        # Get the Main Window, and connect the "destroy" event
        self.window = self.wTree.get_object("wndMain")
        self.window.connect("destroy", gtk.main_quit)
        self.window.maximize()
        self.window.show_all()

        self.types = (
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_UINT,
            gobject.TYPE_UINT,
            gobject.TYPE_STRING,
            gobject.TYPE_FLOAT,
        )
        self.episodes = gtk.ListStore(*self.types)

        self.db = All()
        self.db.ParseFromString(open("watch.list", "rb").read())
        for s in self.db.series:
            fields = ("name", "search", "season", "episode", "listing", "last")
            self._addrow([getattr(s, f) for f in fields])

        def build_tree_column(name, column):
            typ = self.episodes.get_column_type(column)
            editable = True

            if typ == gobject.TYPE_UINT:
                widget = gtk.CellRendererSpin()
                widget.set_property(
                    "adjustment", gtk.Adjustment(lower=0, upper=1000, step_incr=1)
                )  # FIXME: 1000 is a randomly picked "probably highest" value
                widget.connect("editing-started", self.edit_spin)
            elif name == "Command":
                widget = gtk.CellRendererText()
                widget.set_property("weight", pango.WEIGHT_BOLD)
                editable = False
            else:
                widget = gtk.CellRendererText()
            if editable:
                widget.set_property("editable", True)
                widget.connect("edited", self.edit_data, (self.episodes, column))
            tvc = gtk.TreeViewColumn(name, widget, text=column)
            tvc.set_sort_column_id(column)
            return tvc

        self.episodesList = self.wTree.get_object("tblEpisodes")
        self.episodesList.set_model(self.episodes)
        self.episodesList.connect("row-activated", self.rowClicked)

        self.mapping = ("Name", "Search", "Season", "Episode", "Command")
        self.mapping = dict(list(zip(list(range(len(self.mapping))), self.mapping)))
        self.rev_mapping = dict([list(x)[::-1] for x in list(self.mapping.items())])
        for k in self.mapping:
            self.episodesList.append_column(build_tree_column(self.mapping[k], k))

        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn("Last retrieved", cell, text=5)
        col.set_cell_data_func(cell, self.date_field, 5)
        col.set_sort_column_id(5)
        self.episodesList.append_column(col)

        # FIXME: test code
        self.episodesList.row_activated((0,), self.episodesList.get_columns()[-2])

    def date_field(self, column, cell, model, iter, user_data):
        when = float(model.get_value(iter, user_data))
        if when == 0:
            when = '<span foreground="red">Never</span>'
        else:
            when = strftime("%a, %d %b %Y", localtime(when))
        cell.set_property("markup", when)

    def edit_data(self, cellrenderertext, path, new_text, xxx_todo_changeme):
        (model, column) = xxx_todo_changeme
        print("trying to change", path, new_text, column)
        cmd = 'update series set %s="%s" where name="%s"' % (
            self.mapping[column].lower(),
            new_text,
            self.episodes[path][self.rev_mapping["Name"]],
        )
        typ = self.episodes.get_column_type(column)
        if typ == gobject.TYPE_UINT:
            try:
                new_text = int(new_text)
            except ValueError:
                dialog = gtk.MessageDialog(
                    parent=self.window,
                    flags=gtk.DIALOG_MODAL,
                    type=gtk.MESSAGE_ERROR,
                    buttons=gtk.BUTTONS_OK,
                    message_format="Only allowed numbers in that column!",
                )
                dialog.run()
                dialog.destroy()
                return
        print(cmd)
        try:
            self.cur.execute(cmd)
            assert self.cur.rowcount == 1, self.cur.rowcount
            self.episodes[path][column] = new_text
            self.con.commit()
        except sqlite.IntegrityError as e:
            dialog = gtk.MessageDialog(
                parent=self.window,
                flags=gtk.DIALOG_MODAL,
                type=gtk.MESSAGE_ERROR,
                buttons=gtk.BUTTONS_OK,
                message_format="Sqlite integrity failure. Can't use that name!",
            )
            dialog.run()
            dialog.destroy()

    def edit_spin(self, cellrenderer, editable, path):
        editable.set_numeric(True)

    def add_changed(self, editable):
        self.wTree.get_object("btnAddNew").set_sensitive(editable.get_text() != "")

    def btnAdd_clicked_cb(self, button):
        dlg = self.wTree.get_object("dlgSeries")
        self.wTree.get_object("entNewSeries").set_text("")
        self.wTree.get_object("entNewSeries").connect("changed", self.add_changed)
        self.wTree.get_object("btnAddNew").connect(
            "clicked", lambda x: dlg.response(gtk.RESPONSE_OK)
        )
        self.wTree.get_object("entNewSeries").connect(
            "activate", lambda x: dlg.response(gtk.RESPONSE_OK)
        )
        self.wTree.get_object("btnCancelNew").connect(
            "clicked", lambda x: dlg.response(gtk.RESPONSE_CANCEL)
        )
        ret = dlg.run()
        if ret == gtk.RESPONSE_OK:
            series = self.wTree.get_object("entNewSeries").get_text()
            cmd = 'insert into series (name) values("%s")' % series
            self.cur.execute(cmd)
            self.con.commit()
            self.cur.execute(
                'select name,search,season,episode,command,last from series where name="%s" order by last desc'
                % series
            )
            for row in self.cur.fetchall():
                self._addrow(row)
        dlg.hide()

    def _removerow(self, model, path, iter):
        series = model.get_value(iter, 0)
        print("del series", series)
        model.remove(iter)
        cmd = 'delete from series where name="%s"' % series
        self.cur.execute(cmd)

    def btnRemove_clicked_cb(self, button):
        sel = self.episodesList.get_selection()
        sel.selected_foreach(self._removerow)
        self.con.commit()

    def btnWizard_clicked_cb(self, button):
        dlg = self.wTree.get_object("dlgEpguides")
        ret = dlg.run()
        dlg.destroy()


if __name__ == "__main__":
    main = EpgrabberGUI()
    gtk.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "Jussi Räsänen"
__copyright__ = "Copyright 2014, Skyred Media"
__credits__ = ["Jussi Räsänen",]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Jussi Räsänen"
__email__ = "jussi@skyred.fi"
__status__ = "Development"

import sys
import signal
from pprint import pprint
from jinja2 import Environment, FileSystemLoader
from hoedown import Markdown, HtmlRenderer
from gi.repository import Gtk, Gio, WebKit, Gdk, GtkSource


signal.signal(signal.SIGINT, signal.SIG_DFL)
env = Environment(loader=FileSystemLoader('themes'))


class EditWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title='')
        self.set_border_width(5)
        self.set_default_size(800, 600)

        # Vertical box. Contains menu and PaneView
        self.vbox = Gtk.VBox(False, 2)
        self.add(self.vbox) 
        self.init_menu()

        # Markdown Editor
        self.tv1 = GtkSource.View.new()
        self.tv1.set_left_margin(5)
        self.tv1.set_right_margin(5)
        self.tv1.set_name("markdownContent")
        self.tv1.set_show_line_numbers(True)
        self.tv1.set_show_line_marks(True)
        self.tv1.set_insert_spaces_instead_of_tabs(True)
        self.tv1.set_right_margin_position(80)
        self.tv1.set_tab_width(4)
        self.tv1.set_auto_indent(True)
        #self.tv1.set_highlight_current_line(True) #FIXME: Ugly color

        # Textbuffer
        self.buffer = GtkSource.Buffer()
        self.buffer.connect("changed", self.on_button_clicked)
        self.buffer.set_highlight_syntax(True)

        # Set textview buffer
        self.tv1.set_buffer(self.buffer)

        # Dunno
        lm = GtkSource.LanguageManager.get_default()
        language = lm.get_language("markdown")
        self.buffer.set_language(language)
        self.tv1.connect("key-press-event", self.on_key_press)

        # WebKit
        self.wv = WebKit.WebView()
        self.wv.connect("navigation-policy-decision-requested", self.on_navigation)

        # Scrolled Window 1 (for markdown)
        sw1 = Gtk.ScrolledWindow()
        sw1.set_hexpand(False)
        sw1.set_vexpand(True)

        # Scrolled Window 2 (for webkit)
        sw2 = Gtk.ScrolledWindow()
        sw2.set_hexpand(False)
        sw2.set_vexpand(True)

        # Add textview and webkit
        sw1.add(self.tv1)
        sw2.add(self.wv)

        # PaneView, contains markdown editor and html view (webkit)
        hpaned = Gtk.HPaned()
        hpaned.pack1(sw1, True, True)
        hpaned.pack2(sw2, True, True)
        self.vbox.pack_start(hpaned, True, True, 0)

        # Init Jinja, markdown
        self.init_template()

        # Load editor gtk styles
        self.load_styles()

        # Set windows title
        self.set_win_title()

        self.current_filepath = None

    def load_file_dialog(self, widget):
        dialog = Gtk.FileChooserDialog("Open file", self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        self.add_filters(dialog)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.load_file(dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            pass  # TODO? User cancelled

        dialog.destroy()

    def load_file(self, file_path=None):
        self.current_filename = "untitled"
        self.current_filepath = file_path
        
        if self.current_filepath:
            f = open(self.current_filepath, 'r')
            self.buffer.set_text(f.read())
            f.close()
            self.current_filename = file_path.split("/")[-1]

        self.set_win_title(self.current_filename)
        self.update_buffer()

    def save_current_file(self, widget):
        fp = self.current_filepath
        if fp:
            f = open(fp, 'w')
            f.write(self.get_buffer())
            f.close()

    def set_win_title(self, cztitle=None):
        title = "Markdown Editor"
        if cztitle:
            title = "{0} - {1}".format(title, cztitle)
        self.set_title(title)

    def init_menu(self):
        self.mb = Gtk.MenuBar()
        filemenu = Gtk.Menu()
        filem = Gtk.MenuItem("File")
        filem.set_submenu(filemenu)
        
        exit = Gtk.MenuItem("Exit")
        exit.connect("activate", Gtk.main_quit)
        save_as = Gtk.MenuItem("Save As...")
        save_as.connect("activate", self.save_as_dialog)

        load = Gtk.MenuItem("Open file...")
        load.connect("activate", self.load_file_dialog)

        action_save = Gtk.MenuItem("Save")
        action_save.connect("activate", self.save_current_file)


        filemenu.append(action_save)
        filemenu.append(load)
        filemenu.append(save_as)
        filemenu.append(exit)
        self.mb.append(filem)
        self.vbox.pack_start(self.mb, False, False, 0)

    def save_as_dialog(self, widget):
        dialog = Gtk.FileChooserDialog("Save file", self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK))

        self.add_filters(dialog)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            fname = dialog.get_filename()
            f = open(fname, 'w')
            f.write(self.get_buffer())
            f.close()
        elif response == Gtk.ResponseType.CANCEL:
            pass  # TODO? User cancelled

        dialog.destroy()

    def add_filters(self, dialog):
        filter_text = Gtk.FileFilter()

        filter_markdown = Gtk.FileFilter()
        filter_markdown.set_name("Markdown ")
        filter_markdown.add_mime_type("text/x-markdown")
        dialog.add_filter(filter_markdown)

        filter_text.set_name("Plain text")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)


    def init_template(self):
        # Markdown renderer
        self.rndr = HtmlRenderer()
        self.md = Markdown(self.rndr)
        
        # Jinja templates        
        self.jt = template = env.get_template('header.html')
        self.update_buffer()

    def load_styles(self):
        self.style_provider = Gtk.CssProvider()
        
        css = open('themes/gtk.css', 'rb')
        css_data = css.read()
        css.close()
        self.style_provider.load_from_data(css_data)

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), self.style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_key_press(self, widget, event):
        self.update_buffer()

    def on_button_clicked(self, widget):
        self.update_buffer()

    def get_buffer(self):
        contentBuffer = self.buffer
        text = contentBuffer.get_text(
            contentBuffer.get_start_iter(),
            contentBuffer.get_end_iter(), False).decode('utf-8')
        return text

    def update_buffer(self):
        # Fetch Text from buffer
        text = self.get_buffer()
        
        # Convert markdown text into html
        html_content = self.md.render(text)

        # Render template using Jinja
        rendered = self.jt.render(content=html_content)

        # Load page to WebView
        self.wv.load_string(rendered, "text/html", "utf-8", "/")

    def on_navigation(self, web_view, frame, request, nav_action, policy_decision, data=None):
        if request.get_uri() != '/':
            policy_decision.ignore()
        

if __name__ == "__main__":
    win = EditWindow()
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()
    sys.exit(Gtk.main_quit())
    signal.signal(signal.SIGINT, signal_handler)

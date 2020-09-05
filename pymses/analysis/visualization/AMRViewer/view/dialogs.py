# License:
#   Copyright (C) 2011 Thomas GUILLET, Damien CHAPON, Marc LABADENS. All Rights Reserved.
#
#   This file is part of PyMSES.
#
#   PyMSES is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   PyMSES is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with PyMSES.  If not, see <http://www.gnu.org/licenses/>.
import wx, numpy
from os.path import abspath, basename, splitext, dirname
from os import listdir
from tempfile import gettempdir
import tables as T
from .widget_ids import WidgetIds as wid
from pymses.analysis.visualization import *
import numpy as N

class RamsesSimOutputDialog(wx.DirDialog):#{{{
	"""
	RamsesSimOutputDialog is a DirDialog which allows the user to define
	a Ramses simulation outputs directory.
	"""
	def __init__(self, parent, controller):
		wx.DirDialog.__init__(self, parent, "Choose a RAMSES outputs directory",
				      style=wx.DD_DEFAULT_STYLE, defaultPath=abspath("./"))
		self.controller = controller


	def run(self):#{{{
		if self.ShowModal() == wx.ID_OK: # The user selected a directory
			out_dir = self.GetPath()
			if not self.controller.SelectRamsesDir(out_dir): # This is not a valid RAMSES outputs dir.
				message = "No output found in the directory :\n\n%s"%out_dir
				print(message)
#				dial = wx.MessageDialog(self, message, 'Warning', wx.OK | wx.ICON_EXCLAMATION)
#				dial.ShowModal()
		self.Destroy()
	#}}}
#}}}


class CameraFileDialog(wx.FileDialog):#{{{
	def __init__(self, parent, controller, isTypeOpen=False):#{{{
		self.controller = controller
		self.load = isTypeOpen
		wildcard = "Camera files (*.csv; *.h5)|*.csv;*.h5"
		if isTypeOpen:
			wx.FileDialog.__init__(self, parent, "Choose a camera file",
				self.controller.model.ramses_dir, "", wildcard, style=wx.FD_OPEN)
		else:
			wx.FileDialog.__init__(self, parent, "Choose a camera file",
				self.controller.model.ramses_dir, "camera.csv", wildcard,
				style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
	#}}}

	def run(self):#{{{
		if self.ShowModal() == wx.ID_OK: # The user selected a Camera file
			path = self.GetPath()
			if not self.load:
				fname = basename(path)
				ext = fname[-3:]
				if ext != "csv" and ext != ".h5" and ext != ".hdf5":
					path = "%s.csv"%path
				# Save camera into a file
				if self.controller.SaveLosCameraToFile(path):
					print("Camera parameters correctly saved into file :\n\n%s"%path)
			else:
				# Load Camera from a file
				self.controller.LoadLosCameraFromFile(path)
		self.Destroy()
	#}}}

#}}}

class CameraPNGFileDialog(wx.FileDialog):#{{{
	def __init__(self, parent, controller, image):#{{{
		self.controller = controller
		self.image = image
		wildcard = "Image PNG files (*.png)|*.PNG;*.png"
		wx.FileDialog.__init__(self, parent, "Choose a png file",
			self.controller.model.ramses_dir, "img.png", wildcard,
			style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
	#}}}

	def run(self):#{{{
		if self.ShowModal() == wx.ID_OK: # The user selected a png file
			path = self.GetPath()
			fname = basename(path)
			ext = fname[-4:]
			if ext != ".png" and ext != ".PNG":
				path = "%s.png"%path
			# Save image into png file
			success = self.image.SaveFile(path,wx.BITMAP_TYPE_PNG)
			if success:
				message = "Image correctly saved into file :\n%s"%path
				print(message)
			else:
				message = "Error occured while trying so save image into file :\n%s"%path
				print(message)
		self.Destroy()
	#}}}

#}}}

class HDF5FileDialog(wx.FileDialog):#{{{
	def __init__(self, controller):#{{{
		self.controller = controller
		wildcard = "PYMSES HDF5 files (*.h5)|*.h5"
		wx.FileDialog.__init__(self, None, "Choose a PYMSES HDF5 file", gettempdir(), "", wildcard, style=wx.FD_OPEN)
	#}}}

	def run(self):#{{{
		if self.ShowModal() == wx.ID_OK: # The user selected a HDF5 file
			path = self.GetPath()
			# Load map from HDF5 file
			self.controller.LoadmapFromHDF5(path)
			self.controller.gui.list_hdf5_file = []
			hdf5_file = self.controller.model.map_name_list["hdf5"][0]
			self.controller.gui.hdf5_file_dirname = dirname(hdf5_file)
			for file in listdir(self.controller.gui.hdf5_file_dirname):
				if splitext(file)[1] == ".h5" or splitext(file)[1] == ".hdf5":
					self.controller.gui.list_hdf5_file.append(file)
			self.controller.gui.hdf5_cb.Show(True)
			self.controller.gui.hdf5_cb.SetItems(self.controller.gui.list_hdf5_file)
			self.controller.gui.hdf5_cb.SetValue(basename(hdf5_file))
			self.controller.gui.UpdateLayout(None)
		self.Destroy()
	#}}}

#}}}

class customFileDialog(wx.FileDialog):#{{{
	up="num_func=lambda dset:(-N.sum(N.array([0,0,1.])[N.newaxis,:]*dset[\"vel\"], axis=1)* dset[\"rho\"]*dset.get_sizes()**3)"
	down="denom_func=lambda dset:(dset[\"rho\"]*dset.get_sizes()**3)"
	op_s="self.op = FractionOperator(num_func, denom_func)#ScalarOperator(lambda dset:(dset[\"rho\"]))"
	log=False
	def __init__(self, lev_init):
		wx.Dialog.__init__(self, None, -1, "Custom map operator",size=(820, 200))
		pan = wx.Panel(self, -1)
		pan.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		pan.SetFocus()
		
		self.upTextCtrl = wx.TextCtrl(pan, -1, size=(800,30), pos=(10,10),\
					style=wx.TE_PROCESS_ENTER)
		self.upTextCtrl.SetValue(customFileDialog.up)
		#self.upTextCtrl.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		
		self.downTextCtrl = wx.TextCtrl(pan, -1, size=(800,30), pos=(10,50),\
					style=wx.TE_PROCESS_ENTER)
		self.downTextCtrl.SetValue(customFileDialog.down)
		#self.downTextCtrl.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		
		self.opTextCtrl = wx.TextCtrl(pan, -1, size=(800,30), pos=(10,90),\
					style=wx.TE_PROCESS_ENTER)
		self.opTextCtrl.SetValue(customFileDialog.op_s)
		
		#self.logCheckBox = wx.CheckBox(pan, -1, 'log scale', (340, 130))
		#self.logCheckBox.SetValue(customFileDialog.log)
		
		ok_btn = wx.Button(pan, -1, "Ok", pos=(340,165))
		ok_btn.Bind(wx.EVT_BUTTON, self.On_ok_btn)

		self.CentreOnParent(wx.BOTH)
	def On_ok_btn(self, event):
		self.update_and_close()
	def OnKeyDown(self, event):
		keycode = event.GetKeyCode()
		if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER \
				or keycode == wx.WXK_ESCAPE:
			self.update_and_close()
	def update_and_close(self):
		customFileDialog.up=self.upTextCtrl.GetValue()
		customFileDialog.down=self.downTextCtrl.GetValue()
		customFileDialog.op_s=self.opTextCtrl.GetValue()
		#customFileDialog.log=self.logCheckBox.GetValue()
		exec(customFileDialog.up)
		exec(customFileDialog.down)
		exec(customFileDialog.op_s)
		self.Destroy()

class FieldsToLoadFileDialog(wx.FileDialog):#{{{
	ftl="field_to_load = [\"vel\", \"rho\"]"
	def __init__(self, lev_init):
		wx.Dialog.__init__(self, None, -1, "Custom map field to load",size=(400, 100))
		pan = wx.Panel(self, -1)
		pan.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		pan.SetFocus()
		self.fieldTextCtrl = wx.TextCtrl(pan, -1, size=(350,30), pos=(20,20),\
					style=wx.TE_PROCESS_ENTER)
		self.fieldTextCtrl.SetValue(FieldsToLoadFileDialog.ftl)
		#self.fieldTextCtrl.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		
		ok_btn = wx.Button(pan, -1, "Ok", pos=(160,60))
		ok_btn.Bind(wx.EVT_BUTTON, self.On_ok_btn)

		self.CentreOnParent(wx.BOTH)
	def On_ok_btn(self, event):
		self.update_and_close()
	def OnKeyDown(self, event):
		keycode = event.GetKeyCode()
		if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER \
				or keycode == wx.WXK_ESCAPE:
			self.update_and_close()
	def update_and_close(self):
		FieldsToLoadFileDialog.ftl=self.fieldTextCtrl.GetValue()
		self.Destroy()

class SelectViewDialog(wx.Dialog):
	def __init__(self):
		wx.Dialog.__init__(self, None, -1, "Choose which region finder axis image to save",size=(410, 80))
		self.WID = wid()
		self.selected_view=self.WID.RF_TAB_LOS_WIN
		pan = wx.Panel(self, self.WID.ANY)
		los_view_btn = wx.Button(pan, -1, "line-of-sight", (50,30))
		los_view_btn.Bind(wx.EVT_BUTTON, self.On_los_view_btn)
		u_view_btn = wx.Button(pan, -1, "u view", (150,30))
		u_view_btn.Bind(wx.EVT_BUTTON, self.On_u_view_btn)
		v_view_btn = wx.Button(pan, -1, "v view", (250,30))
		v_view_btn.Bind(wx.EVT_BUTTON, self.On_v_view_btn)
		self.CentreOnParent(wx.BOTH)
		self.SetFocus()
	def On_los_view_btn(self, event):
		self.selected_view=self.WID.RF_TAB_LOS_WIN
		self.Destroy()
	def On_u_view_btn(self, event):
		self.selected_view=self.WID.RF_TAB_U_WIN
		self.Destroy()
	def On_v_view_btn(self, event):
		self.selected_view=self.WID.RF_TAB_V_WIN
		self.Destroy()

class SelectParametersDialog(wx.Dialog):
	def __init__(self, lev_init):
		wx.Dialog.__init__(self, None, -1, "Build a local octree source",size=(400, 150))
		pan = wx.Panel(self, -1)
		pan.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		pan.SetFocus()
		
		wx.StaticText(pan, 0, "Fields to read : ", pos=(10,10))
		self.rhoCheckBox = wx.CheckBox(pan, -1, 'rho', (20, 30))
		self.rhoCheckBox.SetValue(True)
		self.PCheckBox = wx.CheckBox(pan, -1, 'P', (20, 60))
		self.PCheckBox.SetValue(True)
		self.velCheckBox = wx.CheckBox(pan, -1, 'vel', (20, 90))
		self.velCheckBox.SetValue(True)
		
		wx.StaticText(pan, 0, "ngrid_max :", pos=(170,30))
		self.ngrid_maxTextCtrl = wx.TextCtrl(pan, -1, size=(100,30), pos=(250,20),\
					style=wx.TE_PROCESS_ENTER)
		self.ngrid_maxTextCtrl.SetValue("2e6")
		
		wx.StaticText(pan, 0, "levelmax :", pos=(170,70))
		self.levTextCtrl = wx.TextCtrl(pan, -1, size=(100,30), pos=(250,60),\
					style=wx.TE_PROCESS_ENTER)
		self.levTextCtrl.SetValue(str(lev_init))
		wx.EVT_TEXT_ENTER(pan, -1, self.On_load_btn)
		
		self.load = False
		load_btn = wx.Button(pan, -1, "Load", pos=(200,100))
		load_btn.Bind(wx.EVT_BUTTON, self.On_load_btn)

		self.CentreOnParent(wx.BOTH)
	
	def On_load_btn(self, event):
		self.load = True
		self.Destroy()
	def OnKeyDown(self, event):
		keycode = event.GetKeyCode()
		if keycode == wx.WXK_ESCAPE:
			self.Destroy()
		elif keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER:
			self.load = True
			self.Destroy()
			
class EditCameraDialog(wx.Dialog):
	def __init__(self, cam):
		wx.Dialog.__init__(self, None, -1, "Edit camera parameters",size=(350, 150))
		pan = wx.Panel(self, -1)
		pan.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		pan.SetFocus()
		psizer = wx.BoxSizer(wx.VERTICAL)
		pan.SetSizer(psizer)
		gs = wx.FlexGridSizer(4,2)
		self.center = wx.TextCtrl(pan, 0, size=(200,-1), \
			value="["+str(float("%.5f"%(cam.center[0])))+", "+str(float("%.5f"%(cam.center[1]))) + \
			", "+str(float("%.5f"%(cam.center[2])))+"]", style=wx.TE_PROCESS_ENTER)
		self.line_of_sight_axis = wx.TextCtrl(pan, 0, size=(200,-1),\
			value="["+str(float("%.5f"%(cam.los_axis[0])))+", "+str(float("%.5f"%(cam.los_axis[1]))) + \
			", "+str(float("%.5f"%(cam.los_axis[2])))+"]", style=wx.TE_PROCESS_ENTER)
		self.region_size = wx.TextCtrl(pan, 0, size=(200,-1), value=str(cam.region_size[0]), style=wx.TE_PROCESS_ENTER)
		gs.AddMany([(wx.StaticText(pan, 0, "  center :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.center, 0),\
			(wx.StaticText(pan, 0, "  line_of_sight_axis : "), 0, wx.ALIGN_CENTER_VERTICAL), (self.line_of_sight_axis, 0),\
			(wx.StaticText(pan, 0, "  region cube size :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.region_size, 0)])
		psizer.Add(wx.StaticText(pan),0)
		psizer.Add(gs, 0, wx.LEFT|wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND, border=5)
		wx.EVT_TEXT_ENTER(pan, -1, self.On_ok_btn)
		self.ok = False
		cancel_btn = wx.Button(pan, -1, "Cancel", pos=(60,110))
		cancel_btn.Bind(wx.EVT_BUTTON, self.On_cancel_btn)
		cancel_btn.SetFocus()
		load_btn = wx.Button(pan, -1, "OK", pos=(190,110))
		load_btn.Bind(wx.EVT_BUTTON, self.On_ok_btn)
		self.CentreOnParent(wx.BOTH)
	
	def On_ok_btn(self, event):
		self.ok = True
		self.Destroy()
	def On_cancel_btn(self, event):
		self.Destroy()
	def OnKeyDown(self, event):
		keycode = event.GetKeyCode()
		if keycode == wx.WXK_ESCAPE:
			self.Destroy()
		elif keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER:
			self.ok = True
			self.Destroy()
			
class ConfirmBuildSourceDialog(wx.Dialog):
	def __init__(self):
		wx.Dialog.__init__(self, None, -1, "New local octree source needed !",size=(410, 80))
		self.WID = wid()
		self.answer=self.WID.RF_TAB_LOS_WIN
		pan = wx.Panel(self, self.WID.ANY)
		wx.StaticText(pan, 0, "Load new data from disk ?", pos=(10,10))
		yes_btn = wx.Button(pan, -1, "Yes", (55,35))
		yes_btn.Bind(wx.EVT_BUTTON, self.On_yes_btn)
		no_btn = wx.Button(pan, -1, "No", (155,35))
		no_btn.Bind(wx.EVT_BUTTON, self.On_no_btn)
		cancel_btn = wx.Button(pan, -1, "Cancel", (255,35))
		cancel_btn.Bind(wx.EVT_BUTTON, self.On_cancel_btn)
		self.CentreOnParent(wx.BOTH)
		self.SetFocus()
	def On_yes_btn(self, event):
		self.answer=1
		self.Destroy()
	def On_no_btn(self, event):
		self.answer=0
		self.Destroy()
	def On_cancel_btn(self, event):
		self.answer=-1
		self.Destroy()
#!/boot/system/bin/python3
from Be import BApplication, BWindow, BView, BMenu,BMenuBar, BMenuItem, BSeparatorItem, BMessage, window_type, B_NOT_RESIZABLE, B_CLOSE_ON_ESCAPE, B_QUIT_ON_WINDOW_CLOSE
from Be import BButton, BTextView, BTextControl, BAlert, BListItem, BListView, BScrollView, BRect, BBox, BFont, InterfaceDefs, BPath, BDirectory, BEntry, BTabView, BTab
from Be import BNode, BStringItem, BFile, BPoint, BLooper, BHandler, BTextControl, TypeConstants, BScrollBar, BStatusBar, BStringView, BUrl, BBitmap,BLocker,BCheckBox,BQuery
from Be import BTranslationUtils,BScreen#,BAppFileInfo#,BQuery
from Be.NodeMonitor import *
from Be.Node import node_ref
from Be.GraphicsDefs import *
from Be.View import *
from Be.Menu import menu_info,get_menu_info
from Be.FindDirectory import *
from Be.View import B_FOLLOW_NONE,set_font_mask,B_WILL_DRAW,B_NAVIGABLE,B_FULL_UPDATE_ON_RESIZE,B_FRAME_EVENTS,B_PULSE_NEEDED
from Be.Alert import alert_type
from Be.InterfaceDefs import border_style,orientation
from Be.ListView import list_view_type
from Be.AppDefs import *
from Be.Font import be_plain_font, be_bold_font
from Be import AppDefs
from Be.TextView import text_run, text_run_array
# from Be.fs_attr import attr_info
from Be.Application import *

from Be import Entry
from Be.Entry import entry_ref, get_ref_for_path

import configparser,re, os, sys, feedparser, struct, datetime, subprocess
from threading import Thread

Config=configparser.ConfigParser()
def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

def openlink(link):
	osd=BUrl(link)
	retu=osd.OpenWithPreferredApplication()

def attr(node):
	al = []
	while 1:
		an = node.GetNextAttrName()
		if not an[1]:
			a = an[0]
		else:
			a = None
		if a is None:
			node.RewindAttrs()
			break
		else:
			pnfo = node.GetAttrInfo(a)
			if not pnfo[1]:
				nfo = pnfo[0]
			type_string = get_type_string(nfo.type)
			ritorno=node.ReadAttr(a, nfo.type, 0, None,nfo.size)
			al.append((a,("Type:",type_string,"Size:",nfo.size),node.ReadAttr(a, nfo.type, 0, None,nfo.size)))
	return al

def get_type_string(value):
	#type_string = ''.join([chr((value >> (8*i)) & 0xFF) for i in range(4)]) #<--- this works better if the binary representation of the integer contains bytes that are not valid for UTF-8 encoding
	type_string = struct.pack('>I', value).decode('utf-8')
	return type_string


class NewsItem(BListItem):
	def __init__(self, title, entry, link, unread,published,consist):
		self.name=title
		self.consistent=consist
		self.entry = entry
		self.link = link
		self.unread = unread
		self.published = published
		fon=BFont()
		self.font_height_value=font_height()
		fon.GetHeight(self.font_height_value)
		BListItem.__init__(self)
		
	def DrawItem(self, owner, frame, complete):
		if self.IsSelected() or complete:
			owner.SetHighColor(200,200,200,255)
			owner.SetLowColor(200,200,200,255)
			owner.FillRect(frame)
		owner.SetHighColor(0,0,0,0)
		owner.MovePenTo(5,frame.bottom-self.font_height_value.descent)
		if self.unread:
			owner.SetFont(be_bold_font)
		else:
			owner.SetFont(be_plain_font)
		owner.DrawString(self.name,None)
		if not self.consistent:
			sp=BPoint(3,frame.bottom-((frame.bottom-frame.top)/2))
			ep=BPoint(frame.right-3,frame.bottom-(frame.bottom-frame.top)/2)
			owner.StrokeLine(sp,ep)
		owner.SetLowColor(255,255,255,255)

		

from Be.Font import font_height

class NewsItemBtn(BListItem):
	def __init__(self):
		self.fon=BFont()
		self.font_height_value=font_height()
		self.fon.GetHeight(self.font_height_value)
		self.ch="Click here to load the remaining news"
		self.widdo=self.fon.StringWidth(self.ch)
		BListItem.__init__(self)
		
	def DrawItem(self, owner, frame, complete):
		owner.SetHighColor(200,200,200,255)
		owner.SetLowColor(200,200,200,255)
		owner.FillRect(frame)
		owner.SetHighColor(100,100,100,255)
		owner.SetLowColor(100,100,100,255)
		myrect=BRect(frame.left+1,frame.top+1,frame.right-1,frame.bottom-1)
		owner.StrokeRect(myrect)
		owner.SetHighColor(0,100,0,255)
		owner.SetLowColor(0,100,0,255)
		owner.MovePenTo(frame.Width()/2-self.widdo/2,frame.bottom-self.font_height_value.descent)
		owner.SetFont(be_plain_font)
		owner.DrawString("Click here to load the remaining news",None)
		
		
class PaperItem(BListItem):
	nocolor = (0, 0, 0, 0)

	def __init__(self, path,address):
		self.name = path.Leaf()
		self.path = path
		self.address = address
		self.color=self.nocolor
		self.newnews=False
		self.cnnews=0
		self.datapath=BDirectory(path.Path())
		self.newscount=self.datapath.CountEntries()
		fon=BFont()
		self.font_height_value=font_height()
		fon.GetHeight(self.font_height_value)
		self.newscount=self.datapath.CountEntries()

####### watch_node not working ##################
####### commented while waiting for a fix #######
#		n_ref=node_ref()
#		entu=BEntry(self.datapath,self.path.Path())
#		rr=entu.GetNodeRef(n_ref)
#		if not rr:
#			rdue=watch_node(n_ref,B_WATCH_DIRECTORY,be_app_messenger)#B_WATCH_ALL
#			print("risultato return watch_node:",rdue)
##################################################
		#print(value.ascent,value.descent,value.leading,"is descending the useful value to place the string?")


		BListItem.__init__(self)

	def Statistics(self):
		self.newscount=self.datapath.CountEntries()
		if self.newscount > 0:
			perc=BPath()
			self.datapath.Rewind()
			ret=False
			while not ret:
				evalent=BEntry()
				ret=self.datapath.GetNextEntry(evalent)
				if not ret:
					evalent.GetPath(perc)
					nf=BNode(perc.Path())
					attributes=attr(nf)
					for element in attributes:
						if element[0] == "Unread":
							unr=element[2][0]
							if unr:
								self.cnnews+=1

	def DrawItem(self, owner, frame, complete):
		self.newnews=False
		perc=BPath()
		self.newscount=self.datapath.CountEntries()
		if self.newscount > 0:
			self.datapath.Rewind()
			ret=False
			while not ret:
				evalent=BEntry()
				ret=self.datapath.GetNextEntry(evalent)
				if not ret:
					evalent.GetPath(perc)
					nf=BNode(perc.Path())
					attributes=attr(nf)
					for element in attributes:
						if element[0] == "Unread":
							unr=element[2][0]
							if unr:
								ret=True
								self.newnews=True
								break
		if self.IsSelected() or complete:
			if self.newnews == True:
				owner.SetHighColor(250,80,80,255)
				owner.SetLowColor(200,200,200,255)
			else:
				owner.SetHighColor(250,230,0,255)
				owner.SetLowColor(200,200,200,255)
			owner.FillRect(frame)
			owner.SetHighColor(0,0,0,255)
			owner.SetLowColor(255,255,255,255)
		owner.MovePenTo(5,frame.bottom-self.font_height_value.descent)#2
		if self.newnews:
			owner.SetFont(be_bold_font)
			owner.DrawString(self.name,None)#"▶ "+
		else:
			owner.SetFont(be_plain_font)
			owner.DrawString(self.name,None)


class NewsScrollView:
	HiWhat = 32 #Doppioclick
	NewsSelection = 102
	def __init__(self, rect, name):
		self.lv = BListView(rect, name, list_view_type.B_SINGLE_SELECTION_LIST)
		self.lv.SetResizingMode(B_FOLLOW_ALL_SIDES)
		self.lv.SetSelectionMessage(BMessage(self.NewsSelection))
		self.lv.SetInvocationMessage(BMessage(self.HiWhat))
		self.sv = BScrollView(name, self.lv,B_FOLLOW_NONE,0,False,True,border_style.B_FANCY_BORDER)
		self.sv.SetResizingMode(B_FOLLOW_ALL_SIDES)
		#'NewsScrollView'
	def topview(self):
		return self.sv

	def listview(self):
		return self.lv

class PapersScrollView:
	HiWhat = 33 #Doppioclick
	PaperSelection = 101

	def __init__(self, rect, name):
		self.lv = BListView(rect, name, list_view_type.B_SINGLE_SELECTION_LIST)
		self.lv.SetResizingMode(B_FOLLOW_TOP_BOTTOM)
		self.lv.SetSelectionMessage(BMessage(self.PaperSelection))
		self.lv.SetInvocationMessage(BMessage(self.HiWhat))
		self.sv = BScrollView(name, self.lv,B_FOLLOW_NONE,0,True,True,border_style.B_FANCY_BORDER)
		self.sv.SetResizingMode(B_FOLLOW_TOP_BOTTOM)
		#'PapersScrollView'
	def topview(self):
		return self.sv

	def listview(self):
		return self.lv

class ScrollView:
	HiWhat = 53 #Doppioclick
	SectionSelection = 54

	def __init__(self, rect, name):
		self.lv = BListView(rect, name, list_view_type.B_SINGLE_SELECTION_LIST)
		self.lv.SetResizingMode(B_FOLLOW_TOP_BOTTOM)
		self.lv.SetSelectionMessage(BMessage(self.SectionSelection))
		self.lv.SetInvocationMessage(BMessage(self.HiWhat))
		self.sv = BScrollView(name, self.lv,B_FOLLOW_NONE,0,True,True,border_style.B_FANCY_BORDER)
		self.sv.SetResizingMode(B_FOLLOW_TOP_BOTTOM)
		#'NormalScrollView'


class PBox(BBox):
	def __init__(self,frame,name,immagine):
		self.immagine = immagine
		self.frame = frame
		BBox.__init__(self,frame,name,0x0202|0x0404,InterfaceDefs.border_style.B_NO_BORDER)

	def Draw(self,rect):
		BBox.Draw(self, rect)
		inset = BRect(2, 2, self.frame.Width()-1, self.frame.Height()-2)
		self.DrawBitmap(self.immagine,inset)
		
class AboutWindow(BWindow):
	def __init__(self):
		scr=BScreen()
		scrfrm=scr.Frame()
		x=(scrfrm.right+1)/2-550/2
		y=(scrfrm.bottom+1)/2-625/2
		BWindow.__init__(self, BRect(x, y, x+550, y+625),"About",window_type.B_MODAL_WINDOW, B_NOT_RESIZABLE|B_CLOSE_ON_ESCAPE)
		self.bckgnd = BView(self.Bounds(), "backgroundView", 8, 20000000)
		self.bckgnd.SetResizingMode(B_FOLLOW_V_CENTER|B_FOLLOW_H_CENTER)
		bckgnd_bounds=self.bckgnd.Bounds()
		self.AddChild(self.bckgnd,None)
		self.box = BBox(bckgnd_bounds,"Underbox",0x0202|0x0404,border_style.B_FANCY_BORDER)
		self.bckgnd.AddChild(self.box,None)
		################## PBOX ###############################
		pbox_rect=BRect(0,0,self.box.Bounds().Width(),241)
		perc=BPath()
		find_directory(directory_which.B_SYSTEM_DATA_DIRECTORY,perc,False,None)
		ent=BEntry(perc.Path()+"/BGator2/FeedGator1c.png")
		if ent.Exists():
			#use mascot installed in system data folder
			ent.GetPath(perc)
			img1=BTranslationUtils.GetBitmap(perc.Path(),None)
			self.pbox=PBox(pbox_rect,"PictureBox",img1)
			self.box.AddChild(self.pbox,None)
		else:
			find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
			ent=BEntry(perc.Path()+"/BGator2/Data/FeedGator1c.png")
			if ent.Exists():
				#use mascot installed in user data folder
				ent.GetPath(perc)
				img1=BTranslationUtils.GetBitmap(perc.Path(),None)
				self.pbox=PBox(pbox_rect,"PictureBox",img1)
				self.box.AddChild(self.pbox,None)
			else:
				nopages=True
				cwd = os.getcwd()
				ent=BEntry(cwd+"/Data/FeedGator1c.png")
				if ent.Exists():
					#use mascot downloaded with git by cmdline
					ent.GetPath(perc)
					img1=BTranslationUtils.GetBitmap(perc.Path(),None)
					self.pbox=PBox(pbox_rect,"PictureBox",img1)
					self.box.AddChild(self.pbox,None)
					nopages=False
				else:
					alt="".join(sys.argv)
					mydir=os.path.dirname(alt)
					link=mydir+"/Data/FeedGator1c.png"
					ent=BEntry(link)
					if ent.Exists():
						#use mascot downloaded with git by graphical launc
						ent.GetPath(perc)
						img1=BTranslationUtils.GetBitmap(perc.Path(),None)
						self.pbox=PBox(pbox_rect,"PictureBox",img1)
						self.box.AddChild(self.pbox,None)
						nopages=False
				if nopages:
					print("no mascot found")
		#######################################################
		abrect=BRect(2,242, self.box.Bounds().Width()-2,self.box.Bounds().Height()-2)
		inner_ab=BRect(4,4,abrect.Width()-4,abrect.Height()-4)
		mycolor=rgb_color()
		mycolor.red=0
		mycolor.green=200
		mycolor.blue=0
		mycolor.alpha=0
		self.AboutText = BTextView(abrect, 'aBOUTTxTView', inner_ab , B_FOLLOW_NONE)
		self.AboutText.MakeEditable(False)
		self.AboutText.MakeSelectable(False)
		#self.AboutText.SetStylable(True)
		stuff="FeedGator\n\nFeed our alligator with tasty newspapers!\n\nThis is a simple feed aggregator written in Python + Haiku-PyAPI and feedparser\n\nspecial thanks to coolcoder613eb and Zardshard\n\nFeedGator is a reworked update of BGator.\n\nVersion 2.1-beta\n\t\t\t\t\t\t\t\t\tby TmTFx\n\n\t\tpress ESC to close this window"
		txtrun1=text_run()
		txtrun1.offset=0
		fon1=BFont(be_bold_font)
		fon1.SetSize(48.0)
		txtrun1.font=fon1
		col1=rgb_color()
		col1.red=0
		col1.green=200
		col1.blue=0
		col1.alpha=200
		txtrun1.color=col1
		n=stuff.find("Feed our")
		txtrun2=text_run()
		txtrun2.offset=n
		txtrun2.font=be_plain_font
		col2=rgb_color()
		col2.red=0
		col2.green=0
		col2.blue=0
		col2.alpha=0
		txtrun2.color=col2
		arra=text_run_array()
		arra.count=2
		arra.runs[0]=txtrun1
		arra.runs[1]=txtrun2
		self.AboutText.SetText(stuff,arra)
		self.box.AddChild(self.AboutText,None)

#	def MessageReceived(self, msg):
		#msg.PrintToStream()
		#BWindow.MessageReceived(self, msg)

	def FrameResized(self,x,y):
		self.ResizeTo(550,625)

	def QuitRequested(self):
		#print("In AboutWindow Quit Requested")
		#a=self.FindView("PictureBox")
		#print(a,a.Name())
		#r=self.RemoveChild(a)
		#print(r)
		#self.Lock()
		self.Quit()
		
class PapDetails(BWindow):
	def __init__(self,item):
		BWindow.__init__(self, BRect(400,150,800,450), item.name, window_type.B_FLOATING_WINDOW,  B_NOT_RESIZABLE|B_CLOSE_ON_ESCAPE)
		self.bckgnd = BView(self.Bounds(), "bckgnd_View", 8, 20000000)
		bckgnd_bounds=self.bckgnd.Bounds()
		self.AddChild(self.bckgnd,None)
		self.box = BBox(bckgnd_bounds,"Underbox",0x0202|0x0404,border_style.B_FANCY_BORDER)
		self.bckgnd.AddChild(self.box,None)
		self.listitem=item

		fon=BFont()
		font_height_value=font_height()
		fon.GetHeight(font_height_value)
		desc1="Paper Name:"
		self.desc1=BStringView(BRect(5,5,fon.StringWidth(desc1)+5,font_height_value.ascent+5),"desc1",desc1)
		self.box.AddChild(self.desc1,None)
		desc1_bounds=self.desc1.Frame()
		######
		risp1=item.name
		self.risp1=BStringView(BRect(15,desc1_bounds.bottom+5,fon.StringWidth(risp1)+15,desc1_bounds.bottom+font_height_value.ascent+5),"risp1",risp1)
		self.box.AddChild(self.risp1,None)
		risp1_bounds=self.risp1.Frame()
		###########################
		desc2="Paper path on disk:"
		self.desc2=BStringView(BRect(5,15+risp1_bounds.bottom,fon.StringWidth(desc2)+5,risp1_bounds.bottom + font_height_value.ascent+15),"desc2",desc2)
		self.box.AddChild(self.desc2,None)
		desc2_bounds=self.desc2.Frame()
		######
		risp2=item.path.Path()
		self.risp2=BTextControl(BRect(15,desc2_bounds.bottom+5,bckgnd_bounds.right-15,desc2_bounds.bottom+font_height_value.ascent+5),"risp2",None,risp2,BMessage(152))
		# questo non funziona
		#a=self.risp2.TextView()
		#l=a.TextLength()-10
		#print(l,"<- mi posiziono qui")
		#a.Select(l,l)
		#a.ScrollToSelection()
		self.box.AddChild(self.risp2,None)
		risp2_bounds=self.risp2.Frame()
		###########################
		desc3="Feed address:"
		self.desc3=BStringView(BRect(5,15+risp2_bounds.bottom,fon.StringWidth(desc3)+5,risp2_bounds.bottom + font_height_value.ascent+15),"desc3",desc3)
		self.box.AddChild(self.desc3,None)
		desc3_bounds=self.desc3.Frame()
		######
		risp3=item.address
		self.risp3=BTextControl(BRect(15,desc3_bounds.bottom+5,bckgnd_bounds.right-15,desc3_bounds.bottom+font_height_value.ascent+5),"risp3",None,risp3,BMessage(153))
		self.box.AddChild(self.risp3,None)
		risp3_bounds=self.risp3.Frame()
		###########################
		desc4="Number of news(files) on disk:"
		self.desc4=BStringView(BRect(5,15+risp3_bounds.bottom,fon.StringWidth(desc4)+5,risp3_bounds.bottom + font_height_value.ascent+15),"desc4",desc4)
		self.box.AddChild(self.desc4,None)
		desc4_bounds=self.desc4.Frame()
		######
		risp4=str(item.newscount)
		self.risp4=BStringView(BRect(15,desc4_bounds.bottom+5,fon.StringWidth(risp4)+15,desc4_bounds.bottom+font_height_value.ascent+5),"risp4",risp4)
		self.box.AddChild(self.risp4,None)
		

	def FrameResized(self,x,y):
		self.ResizeTo(400,300)

class BoolBox(BBox):
	def __init__(self,rect,name,res,flag,value):
		BBox.__init__(self,rect,name,res,flag)
		a=BFont()
		l=self.StringWidth("Boolean")
		self.CheckBox=BCheckBox(BRect(4,rect.Height()/2-a.Size()/2,l+34,rect.Height()/2+a.Size()/2+4),"option_value","Boolean",BMessage(1600))
		if value == "True":
			self.CheckBox.SetValue(1)
		elif value == "False":
			self.CheckBox.SetValue(0)
		self.AddChild(self.CheckBox,None)
class StringBox(BBox):
	def __init__(self,rect,name,res,flag,value):
		BBox.__init__(self,rect,name,res,flag)
		a=BFont()
		self.labello=BStringView(BRect(8,rect.Height()-a.Size()*2,rect.Width()-8,rect.Height()-4),"suggest","Tip: Press Enter to confirm modifications")
		self.AddChild(self.labello,None)
		self.stringvalue=BTextControl(BRect(8,rect.Height()/2-a.Size()/2,rect.Width()-8,rect.Height()/2+a.Size()/2-4),"option_value", "String:",value,BMessage(1700))
		self.stringvalue.SetDivider(self.StringWidth("String:"))
		self.AddChild(self.stringvalue,None)
class IntBox(BBox):
	def __init__(self,rect,name,res,flag,value):
		BBox.__init__(self,rect,name,res,flag)
		a=BFont()
		self.labello=BStringView(BRect(8,rect.Height()-a.Size()*2,rect.Width()-8,rect.Height()-4),"suggest","Tip: Press Enter to confirm modifications")
		self.AddChild(self.labello,None)
		self.stringvalue=BTextControl(BRect(8,rect.Height()/2-a.Size()/2,rect.Width()-8,rect.Height()/2+a.Size()/2-4),"option_value", "Int:",str(value),BMessage(1800))
		self.stringvalue.SetDivider(self.StringWidth("Int:"))
		self.AddChild(self.stringvalue,None)
class FloatBox(BBox):
	def __init__(self,rect,name,res,flag,value):
		BBox.__init__(self,rect,name,res,flag)
		a=BFont()
		self.labello=BStringView(BRect(8,rect.Height()-a.Size()*2,rect.Width()-8,rect.Height()-4),"suggest","Tip: Press Enter to confirm modifications")
		self.AddChild(self.labello,None)
		self.stringvalue=BTextControl(BRect(8,rect.Height()/2-a.Size()/2,rect.Width()-8,rect.Height()/2+a.Size()/2-4),"option_value", "Float:",str(value),BMessage(1900))
		self.stringvalue.SetDivider(self.StringWidth("Float:"))
		self.AddChild(self.stringvalue,None)
		
class SectionView(BView):
	def __init__(self,frame,sezione,htabs,conpath):
		BView.__init__(self,frame,sezione,8,20000000)
		self.sezione=sezione
		self.Options = ScrollView(BRect(4 , 4, self.Bounds().Width()/2.5-4, self.Bounds().Height()-htabs ), 'OptionsScrollView')
		self.AddChild(self.Options.sv,None)
		Config.read(conpath)
		for key in Config[sezione]:
			self.Options.lv.AddItem(BStringItem(key))
		self.valuebox=[]

class SettingsWindow(BWindow):
	def __init__(self):
		BWindow.__init__(self, BRect(200,150,800,450), "Settings", window_type.B_FLOATING_WINDOW,  B_NOT_RESIZABLE|B_CLOSE_ON_ESCAPE)
		self.bckgnd = BView(self.Bounds(), "bckgnd_View", 8, 20000000)
		self.AddChild(self.bckgnd,None)
		self.bckgnd.SetResizingMode(B_FOLLOW_ALL_SIDES)
		self.tabview=BTabView(self.bckgnd.Bounds(),"TabView")
		self.bckgnd.AddChild(self.tabview,None)
		self.tablabels=[]
		self.views=[]
		tabrect=BRect(0,0,self.Bounds().Width(),self.Bounds().Height()-self.tabview.TabHeight())
		self.optionbox=[]
		perc=BPath()
		find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
		ent=BEntry(perc.Path()+"/BGator2")
		if not ent.Exists():
			self.Close()
		else:
			ent.GetPath(perc)
			confile=BPath(perc.Path()+'/config.ini',None,False)
			self.confile=confile
			ent=BEntry(confile.Path())
			if ent.Exists():
				Config.read(confile.Path())
				try:
					sez=Config.sections()
					for s in sez:
						self.views.append(SectionView(tabrect,s,self.tabview.TabHeight(),confile.Path()))
						self.tablabels.append(BTab(self.views[-1]))
						self.tabview.AddTab(self.views[-1],self.tablabels[-1])
				except:
					saytxt="This should not happen: there's no section in config.ini!"
					alert= BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
					alert.Go()
					self.Close()
			else:
				saytxt="This should not happen: there's no config.ini!"
				alert= BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
				alert.Go()
				self.Close()
			
	def MessageReceived(self,msg):
		if msg.what == 54:
			#elimino l'ultimo box caricato
			tabsel=self.tabview.Selection()
			theview=self.views[tabsel]
			son=theview.CountChildren()
			if son>1:
				rmView=theview.ChildAt(theview.CountChildren()-1)
				rmView.Hide()
				rmView.RemoveSelf()
				del theview.valuebox[0]

			if theview.Options.lv.CurrentSelection()>-1:
				option=theview.Options.lv.ItemAt(theview.Options.lv.CurrentSelection()).Text()
				Config.read(self.confile.Path())
				value=ConfigSectionMap(self.views[tabsel].sezione)[option]
				bondi=self.views[tabsel].Bounds()
				if value == "True" or value == "False":
					theview.valuebox.append(BoolBox(BRect(bondi.Width()/2.5+20 , 4, bondi.Width()-8, bondi.Height()-8 ),None,0x0202|0x0404,border_style.B_FANCY_BORDER,value))
				else:
					try:
						entire=int(value)
						theview.valuebox.append(IntBox(BRect(bondi.Width()/2.5+20 , 4, bondi.Width()-8, bondi.Height()-8 ),None,0x0202|0x0404,border_style.B_FANCY_BORDER,entire))
					except:
						try:
							flt = float(value)
							theview.valuebox.append(FloatBox(BRect(bondi.Width()/2.5+20 , 4, bondi.Width()-8, bondi.Height()-8 ),None,0x0202|0x0404,border_style.B_FANCY_BORDER,flt))
						except:
							theview.valuebox.append(StringBox(BRect(bondi.Width()/2.5+20 , 4, bondi.Width()-8, bondi.Height()-8 ),None,0x0202|0x0404,border_style.B_FANCY_BORDER,value))
				theview.AddChild(theview.valuebox[-1],None)
		elif msg.what == 1600:
			#cambia valore booleano
			tabsel=self.tabview.Selection()
			theview=self.views[tabsel]
			if theview.Options.lv.CurrentSelection()>-1:
				option=theview.Options.lv.ItemAt(theview.Options.lv.CurrentSelection()).Text()
				perc=BPath()
				find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
				ent=BEntry(perc.Path()+"/BGator2")
				ent.GetPath(perc)
				confile=BPath(perc.Path()+'/config.ini',None,False)
				ent=BEntry(confile.Path())
				if ent.Exists():
					Config.read(confile.Path())
					if theview.valuebox[-1].CheckBox.Value():
						value="True"
					else:
						value="False"
					cfgfile = open(confile.Path(),'w')
					Config.set(theview.sezione,option, value)
					Config.write(cfgfile)
					cfgfile.close()
					Config.read(confile.Path())
		elif msg.what == 1700:
			#cambia valore stringa
			tabsel=self.tabview.Selection()
			theview=self.views[tabsel]
			if theview.Options.lv.CurrentSelection()>-1:
				option=theview.Options.lv.ItemAt(theview.Options.lv.CurrentSelection()).Text()
				perc=BPath()
				find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
				ent=BEntry(perc.Path()+"/BGator2")
				ent.GetPath(perc)
				confile=BPath(perc.Path()+'/config.ini',None,False)
				ent=BEntry(confile.Path())
				if ent.Exists():
					Config.read(confile.Path())
					cfgfile = open(confile.Path(),'w')
					value=theview.valuebox[-1].stringvalue.Text()
					Config.set(theview.sezione,option, value)
					Config.write(cfgfile)
					cfgfile.close()
					Config.read(confile.Path())
		elif msg.what == 1800:
			#cambia valore intero
			tabsel=self.tabview.Selection()
			theview=self.views[tabsel]
			if theview.Options.lv.CurrentSelection()>-1:
				option=theview.Options.lv.ItemAt(theview.Options.lv.CurrentSelection()).Text()
				perc=BPath()
				find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
				ent=BEntry(perc.Path()+"/BGator2")
				ent.GetPath(perc)
				confile=BPath(perc.Path()+'/config.ini',None,False)
				ent=BEntry(confile.Path())
				if ent.Exists():
					Config.read(confile.Path())
					val=theview.valuebox[-1].stringvalue.Text()
					try:
						value=int(val)
						theview.valuebox[-1].stringvalue.MarkAsInvalid(False)
						cfgfile = open(confile.Path(),'w')
						Config.set(theview.sezione,option, val)
						Config.write(cfgfile)
						cfgfile.close()
						Config.read(confile.Path())
					except:
						theview.valuebox[-1].stringvalue.MarkAsInvalid(True)
		elif msg.what == 1900:
			#cambia valore virgola mobile
			tabsel=self.tabview.Selection()
			theview=self.views[tabsel]
			if theview.Options.lv.CurrentSelection()>-1:
				option=theview.Options.lv.ItemAt(theview.Options.lv.CurrentSelection()).Text()
				perc=BPath()
				find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
				ent=BEntry(perc.Path()+"/BGator2")
				ent.GetPath(perc)
				confile=BPath(perc.Path()+'/config.ini',None,False)
				ent=BEntry(confile.Path())
				if ent.Exists():
					Config.read(confile.Path())
					val=theview.valuebox[-1].stringvalue.Text()
					try:
						value=float(val)
						theview.valuebox[-1].stringvalue.MarkAsInvalid(False)
						cfgfile = open(confile.Path(),'w')
						Config.set(theview.sezione,option, val)
						Config.write(cfgfile)
						cfgfile.close()
						Config.read(confile.Path())
					except:
						theview.valuebox[-1].stringvalue.MarkAsInvalid(True)
		BWindow.MessageReceived(self,msg)

	def FrameResized(self,x,y):
		self.ResizeTo(600,300)

class AddFeedWindow(BWindow):
	def __init__(self):
		BWindow.__init__(self, BRect(150,150,500,300), "Add Feed Address", window_type.B_FLOATING_WINDOW,  B_NOT_RESIZABLE | B_CLOSE_ON_ESCAPE)#B_QUIT_ON_WINDOW_CLOSE)#B_BORDERED_WINDOW B_FLOATING_WINDOW
		self.bckgnd = BView(self.Bounds(), "bckgnd_View", 8, 20000000)
		bckgnd_bounds=self.bckgnd.Bounds()
		self.AddChild(self.bckgnd,None)
		self.box = BBox(bckgnd_bounds,"Underbox",0x0202|0x0404,border_style.B_FANCY_BORDER)
		self.bckgnd.AddChild(self.box,None)
		a=BFont()
		wid=a.StringWidth("Feed address:")
		self.feedaddress = BTextControl(BRect(10,30,bckgnd_bounds.Width()-10,60),'TxTCtrl', "Feed address:",None,BMessage(1),0x0202|0x0404)
		self.feedaddress.SetDivider(wid+5)
		self.box.AddChild(self.feedaddress,None)
		self.cancelBtn = BButton(BRect(10,80,bckgnd_bounds.Width()/2-5,110),'GetNewsButton','Cancel',BMessage(6))
		self.addfeedBtn = BButton(BRect(bckgnd_bounds.Width()/2+5,80,bckgnd_bounds.Width()-10,110),'GetNewsButton','Add Feed',BMessage(7))
		self.box.AddChild(self.cancelBtn,None)
		self.box.AddChild(self.addfeedBtn,None)

	def MessageReceived(self, msg):
		if msg.what == 6:
			self.Hide()
		elif msg.what == 7:
			msg=BMessage(245)
			msg.AddString("feed",self.feedaddress.Text())
			be_app.WindowAt(0).PostMessage(msg)
			self.Hide()
		
		BWindow.MessageReceived(self, msg)

	def FrameResized(self,x,y):
		self.ResizeTo(350,150)
	def QuitRequested(self):
		self.Hide()
#		self.Quit()
#		#return BWindow.QuitRequested(self)

class GatorWindow(BWindow):
	global tmpNitm,tmpPitm
	tmpPitm=[]
	tmpNitm=[]
	tmpWind=[]
	papdetW=[]
	shiftok=False
	enabletimer=False
	Menus = (
		('File', ((1, 'Add Paper'),(2, 'Remove Paper'),(6, 'Settings'),(None, None),(int(AppDefs.B_QUIT_REQUESTED), 'Quit'))),('News', ((66, 'Download News'),(4, 'All as read'),(5, 'Clear news'))),('Sort By', ((40, 'Title'),(41, 'Unread'),(42, 'Date'))),
		('Help', ((8, 'Help'),(3, 'About')))
		)
	def __init__(self):
		global tab,name
		BWindow.__init__(self, BRect(50,100,1024,750), "Feed the Gator", window_type.B_TITLED_WINDOW, B_QUIT_ON_WINDOW_CLOSE) #B_NOT_RESIZABLE | B_QUIT_ON_WINDOW_CLOSE)#B_MODAL_WINDOW
		bounds=self.Bounds()
		self.bckgnd = BView(self.Bounds(), "background_View", 8, 20000000)
		self.bckgnd.SetResizingMode(B_FOLLOW_ALL_SIDES)
		bckgnd_bounds=self.bckgnd.Bounds()
		self.AddChild(self.bckgnd,None)
		self.bar = BMenuBar(bckgnd_bounds, 'Bar')
		x, barheight = self.bar.GetPreferredSize()
		self.box = BBox(BRect(0,barheight,bckgnd_bounds.Width(),bckgnd_bounds.Height()),"Underbox",0x0202|0x0404,border_style.B_FANCY_BORDER)
		self.cres=0
		perc=BPath()
		find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
		datapath=BDirectory(perc.Path()+"/BGator2")
		ent=BEntry(datapath,perc.Path()+"/BGator2")
		if not ent.Exists():
			datapath.CreateDirectory(perc.Path()+"/BGator2", datapath)
		ent.GetPath(perc)
		confile=BPath(perc.Path()+'/config.ini',None,False)
		ent=BEntry(confile.Path())
		if ent.Exists():
			Config.read(confile.Path())
			try:
				sort=ConfigSectionMap("General")['sort']
			except:
				#no section
				cfgfile = open(confile.Path(),'w')
				Config.add_section('General')
				Config.set('General','sort', "1")
				sort="1"
				Config.write(cfgfile)
				cfgfile.close()
				Config.read(confile.Path())
			try:
				min=ConfigSectionMap("General")['minimized']
				if min == "True":
					self.startmin=True
				else:
					self.startmin=False
			except:
				cfgfile = open(confile.Path(),'w')
				Config.set('General','minimized', "False")
				Config.write(cfgfile)
				cfgfile.close()
				Config.read(confile.Path())
				self.startmin=False
			try:
				resu=ConfigSectionMap("Timer")['enabled']
				if resu == "True":
					self.enabletimer= True
				else:
					self.enabletimer=False
			except:
				cfgfile = open(confile.Path(),'w')
				Config.add_section('Timer')
				Config.set('Timer','enabled', "False")
				Config.set('Timer','timer', "300000000")
				self.timer=300000000
				self.enabletimer=False
				Config.write(cfgfile)
				cfgfile.close()
				Config.read(confile.Path())
			if self.enabletimer:
				try:
					self.timer=int(ConfigSectionMap("Timer")['timer'])
				except:
					cfgfile = open(confile.Path(),'w')
					Config.set('Timer','timer', "300000000")
					self.timer=300000000
					Config.write(cfgfile)
					cfgfile.close()
					Config.read(confile.Path())
				be_app.SetPulseRate(self.timer)
		else:
			#no file
			cfgfile = open(confile.Path(),'w')
			Config.add_section('General')
			Config.set('General','sort', "1")
			Config.set('General','minimized', "False")
			Config.add_section('Timer')
			Config.set('Timer','enabled', "False")
			Config.set('Timer','timer', "300000000")
			sort="1"
			self.startmin=False
			self.enabletimer=False
			self.timer=300000000
			Config.write(cfgfile)
			cfgfile.close()
			Config.read(confile.Path())
		self.set_savemenu = False
		for menu, items in self.Menus:
			if menu == "Sort By":
				self.set_savemenu = True
				set_savemenu=True
			else:
				set_savemenu = False
			menu = BMenu(menu)
			for k, name in items:
				if k is None:
						menu.AddItem(BSeparatorItem())
				else:
					if name == "Help" or name == "Quit" or name == "Clear news" or name == "Settings":
						mitm=BMenuItem(name, BMessage(k),name[0],0)
					else:
						mitm=BMenuItem(name, BMessage(k),name[1],0)
						if name == "Title" and sort == "1":
							mitm.SetMarked(True)
						elif name == "Unread" and sort == "2":
							mitm.SetMarked(True)
						elif name == "Date" and sort == "3":
							mitm.SetMarked(True)
					menu.AddItem(mitm)
			if set_savemenu:
				self.savemenu = menu
				self.bar.AddItem(menu)
			else:	
				self.bar.AddItem(menu)
		bf=BFont()
		oldSize=bf.Size()
		bf.SetSize(32)
		self.addBtn = BButton(BRect(8,8,68,58),'AddButton','⊕',BMessage(1))
		self.addBtn.SetFont(bf)
		self.box.AddChild(self.addBtn,None)
		self.remBtn = BButton(BRect(72,8,132,58),'RemoveButton','⊖',BMessage(2))
		self.remBtn.SetFont(bf)
		self.box.AddChild(self.remBtn,None)
		boxboundsw=self.box.Bounds().Width()
		boxboundsh=self.box.Bounds().Height()
		self.getBtn = BButton(BRect(136,8,boxboundsw / 3,58),'GetNewsButton','⇩',BMessage(66))
		self.getBtn.SetFont(bf)
		self.progress = BStatusBar(BRect(boxboundsw / 3+6,8, boxboundsw - 12, 68),'progress',None, None)
		self.infostring= BStringView(BRect(boxboundsw/3+6,8,boxboundsw-12,28),"info",None)
		self.box.AddChild(self.progress,None)
		self.box.AddChild(self.infostring,None)
		self.box.AddChild(self.getBtn,None)
		self.box.SetFont(bf)
		self.Paperlist = PapersScrollView(BRect(8 , 70, boxboundsw / 3 -20, boxboundsh - 28 ), 'NewsPapersScrollView')
		self.box.AddChild(self.Paperlist.topview(), None)
		self.NewsList = NewsScrollView(BRect(8 + boxboundsw / 3 , 70, boxboundsw -28 , boxboundsh / 1.8 ), 'NewsListScrollView')
		self.box.AddChild(self.NewsList.sv,None)
		txtRect=BRect(8 + boxboundsw / 3, boxboundsh / 1.8 + 8,boxboundsw -8,boxboundsh - 38)
		self.outbox_preview=BBox(txtRect,"previewframe",B_FOLLOW_LEFT|B_FOLLOW_BOTTOM|B_FOLLOW_RIGHT,border_style.B_FANCY_BORDER)#
		self.box.AddChild(self.outbox_preview,None)
		innerRect= BRect(8,8,txtRect.Width()-30,txtRect.Height())
		self.NewsPreView = BTextView(BRect(2,2, self.outbox_preview.Bounds().Width()-20,self.outbox_preview.Bounds().Height()-2), 'NewsTxTView', innerRect,B_FOLLOW_ALL_SIDES)#, 0x0404|0x0202)#,2000000)
		self.NewsPreView.MakeEditable(False)
		self.NewsPreView.SetStylable(True)
		NewsPreView_bounds=self.outbox_preview.Bounds()
		self.scroller=BScrollBar(BRect(NewsPreView_bounds.right-21,NewsPreView_bounds.top+1.2,NewsPreView_bounds.right-1.4,NewsPreView_bounds.bottom-1.6),'NewsPreView_ScrollBar',self.NewsPreView,0.0,0.0,orientation.B_VERTICAL)
		self.outbox_preview.AddChild(self.scroller,None)
		
		btnswidth=round((boxboundsw - 8 - (8 + boxboundsw / 3) -8 - 8)/3,2)
		markBounds=BRect(round(8 + boxboundsw / 3, 2),round(boxboundsh - 36, 2),round(8 + boxboundsw / 3 + btnswidth, 2) ,round(boxboundsh - 8,2))
		self.markUnreadBtn = BButton(markBounds,'markUnreadButton','Mark as Unread',BMessage(9),B_FOLLOW_BOTTOM)
		self.openBtn = BButton(BRect(round(boxboundsw-8-btnswidth, 2),round( boxboundsh - 36, 2),round(boxboundsw-8, 2),round(boxboundsh-8, 2)),'openButton','Open with browser',BMessage(self.NewsList.HiWhat),B_FOLLOW_BOTTOM)
		self.markReadBtn = BButton(BRect(round(8 + boxboundsw / 3 + btnswidth + 8, 2),round( boxboundsh - 36, 2),round(boxboundsw-16-btnswidth, 2),round(boxboundsh-8, 2)),'markReadButton','Mark as Read',BMessage(10),B_FOLLOW_BOTTOM)
		self.outbox_preview.AddChild(self.NewsPreView,None)
		self.box.AddChild(self.markUnreadBtn,None)
		markUnreadBtn_bounds=self.markUnreadBtn.Frame()
		if markUnreadBtn_bounds != markBounds:
			hdelta=markUnreadBtn_bounds.Height()-markBounds.Height()
			self.markUnreadBtn.MoveBy(0.0,-hdelta)
			self.openBtn.MoveBy(0.0,-hdelta)
			self.markReadBtn.MoveBy(0.0,-hdelta)
			self.NewsPreView.ResizeBy(0.0,-hdelta)
			self.scroller.ResizeBy(0.0,-hdelta)
			self.outbox_preview.ResizeBy(0.0,-hdelta)
		self.box.AddChild(self.openBtn,None)
		self.box.AddChild(self.markReadBtn,None)

		self.bckgnd.AddChild(self.bar, None)
		self.bckgnd.AddChild(self.box, None)
		
		self.UpdatePapers()
		
		#pbox_rect=BRect(0,0,550,241)
		#patty=os.getcwd()+"/FeedGator1c.bmp"
		#img1=BTranslationUtils.GetBitmap(patty,None)
		#self.pbox=PBox(pbox_rect,"PictureBox",img1)
		#self.pbox.SetFlags(B_WILL_DRAW)
		#self.box.AddChild(self.pbox,None)


	def ClearNewsList(self):
			self.NewsList.lv.DeselectAll()
			self.NewsList.lv.MakeEmpty()
			if len(tmpNitm)>0:
				for item in tmpNitm:
					del item
				tmpNitm.clear()

	def ClearPaperlist(self):
		if self.Paperlist.lv.CountItems()>0:
			self.Paperlist.lv.DeselectAll()
			i=0
			while i>self.Paperlist.lv.CountItems():
				self.Paperlist.lv.RemoveItem(i)
			self.NewsList.lv.MakeEmpty()
			if len(tmpPitm)>0:
				for item in tmpPitm:
					del item
				tmpPitm.clear()

	def UpdatePapers(self):
		self.ClearPaperlist()
		
		perc=BPath()
		find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
		datapath=BDirectory(perc.Path()+"/BGator2/Papers")
		ent=BEntry(datapath,perc.Path()+"/BGator2/Papers")
		if not ent.Exists():
			datapath.CreateDirectory(perc.Path()+"/BGator2/Papers", datapath)
		ent.GetPath(perc)
		if datapath.CountEntries() > 0:
			datapath.Rewind()
			ret=False
			while not ret:
				evalent=BEntry()
				ret=datapath.GetNextEntry(evalent)
				if not ret:
					porc=BPath()
					evalent.GetPath(porc)
					self.PaperItemConstructor(porc)

	# def NewsItemLoadMore(self):
		# tmpNitm.append(NewsItemBtn())
		# self.Paperlist.lv.AddItem(tmpNitm[-1])
					
	def PaperItemConstructor(self, perc):
		nf=BNode(perc.Path())
		attributes=attr(nf)
		for element in attributes:
			if element[0] == "address":
				tmpPitm.append(PaperItem(perc,element[2][0]))
				self.Paperlist.lv.AddItem(tmpPitm[-1])

	def gjornaaltolet(self,firstload):
			self.NewsList.lv.DeselectAll()
			self.NewsList.lv.RemoveItems(0,self.NewsList.lv.CountItems()) #azzera newslist
			self.NewsList.lv.ScrollToSelection()
			#### check sort type
			if self.set_savemenu:
				marked=self.savemenu.FindMarked().Label()
			curpaper=self.Paperlist.lv.ItemAt(self.Paperlist.lv.CurrentSelection())
			x=curpaper.datapath.CountEntries()
			if x>0:
				curpaper.datapath.Rewind()
				loaded = 0
				rit = False
				if self.set_savemenu:
					if marked == "Title":
						self.tr=[]
						while not rit:
							itmEntry=BEntry()
							rit=curpaper.datapath.GetNextEntry(itmEntry)
							#self.NewsItemConstructor(itmEntry)
							self.tr.append(itmEntry)
						tmsg=BMessage(444)
						tmsg.AddBool("fl",firstload)
						be_app.WindowAt(0).PostMessage(tmsg)
					if marked == "Unread":
						self.listunread=[]
						self.listread=[]
						while not rit:
							itmEntry=BEntry()
							rit=curpaper.datapath.GetNextEntry(itmEntry)
							nf = BNode(itmEntry)
							attributes = attr(nf)
							gotounread = False
							for element in attributes:
								if element[0] == "Unread":
									unread = element[2][0]
									if unread == True:
										gotounread = True
							if gotounread==True:
								self.listunread.append(itmEntry)
							else:
								self.listread.append(itmEntry)
						self.totallist=[]
						self.totallist+=self.listunread
						self.totallist+=self.listread
						tmsg=BMessage(455)
						tmsg.AddBool("fl",firstload)
						be_app.WindowAt(0).PostMessage(tmsg)
						#for item in listunread:
						#	self.NewsItemConstructor(item)
						#for item in listread:
						#	self.NewsItemConstructor(item)
						
					if marked == "Date": # TODO
						from Be import stat
						getlist=[]
						self.orderedlist=[]
						
						while not rit:
							itmEntry=BEntry()
							rit=curpaper.datapath.GetNextEntry(itmEntry)
							nf = BNode(itmEntry)
							attributes = attr(nf)
							gotdate = False
							for element in attributes:
								if element[0] == "published":
									published = element[2][0]
									gotdate = True
							if not gotdate:
								#fetch filesystem date info
								tmpPath=BPath()
								rt = itmEntry.GetPath(tmpPath)
								if not rt:
									st=os.stat(tmpPath.Path())
									published=datetime.datetime.fromtimestamp(st.st_mtime)
							getlist.append((itmEntry, published))
						self.orderedlist = sorted(getlist, key=lambda x: x[1], reverse=True)
						tmsg=BMessage(465)
						tmsg.AddBool("fl",firstload)
						be_app.WindowAt(0).PostMessage(tmsg)
						#for item in self.orderedlist:
						#	self.NewsItemConstructor(item[0])
				else:
					while not rit:
						itmEntry=BEntry()
						rit=curpaper.datapath.GetNextEntry(itmEntry)
						self.NewsItemConstructor(itmEntry)

	def NewsItemConstructor(self,entry):
		if entry.Exists():
			stato,charro = entry.GetName()
			nf = BNode(entry)
			attributes = attr(nf)
			addnews = False
			blink = False
			bunread = False
			btitle = False
			bpub = False
			for element in attributes:
				if element[0] == "link":
						link = element[2][0]
						blink = True
				if element[0] == "Unread":
						unread = element[2][0]
						bunread = True
				if element[0] == "title":
						title = element[2][0]
						btitle = True
				if element[0] == "published":
						published = element[2][0]
						bpub = True
			try:
				type(link)
				type(unread)
				type(title)			
				addnews=True
			except:
				stato,charro=entry.GetName()
				if stato:
					print("stato true unconsistent news for "+charro)
				else:
					print("stato false unconsistent news for "+charro)
			if not bpub:
				tmpPath=BPath()
				rt = entry.GetPath(tmpPath)
				if not rt:
					st=os.stat(tmpPath.Path())
					published=datetime.datetime.fromtimestamp(st.st_mtime)
			if addnews:
				consist=True
				tmpNitm.append(NewsItem(title,entry,link,unread,published,consist))
				self.NewsList.lv.AddItem(tmpNitm[-1])
			else:
				consist=False
				if not blink:
					link = ""
				if not bunread:
					unread = False
				if not btitle:
					if link == "":
						title = "No Title and no link"
					else:
						title = link
				tmpNitm.append(NewsItem(title,entry,link,unread,consist))
				self.NewsList.lv.AddItem(tmpNitm[-1])
				
	def BtnItemConstructor(self):
		tmpNitm.append(NewsItemBtn())
		self.NewsList.lv.AddItem(tmpNitm[-1])
# se è il primo caricamento carica solo 99 elementi, atrimenti li carica tutti
					#if firstload:
					#	loaded+=1
					#	if loaded == 99:
					#		ret = True
					#		self.PaperItemLoadMore()
					#		print("interrompo caricamento")

	def MessageReceived(self, msg):
		#msg.PrintToStream()
		if msg.what == system_message_code.B_MODIFIERS_CHANGED: #shif pressed
			value=msg.FindInt32("modifiers")
			self.shiftok = (value & InterfaceDefs.B_SHIFT_KEY) != 0
		elif msg.what == 444: #manage newslist ordered by title
			vfl=msg.FindBool("fl")
			print(vfl)
			if vfl:
				try:
					lx=len(self.tr)
					if lx<100:
						en=lx
					else:
						en=100
				except:
					en=100
			else:
				en=len(self.tr)
			print(en)
			i=0
			while i<en-1:
				mxg=BMessage(445)
				mxg.AddInt32("index",i)
				thr=Thread(target=be_app.WindowAt(0).PostMessage,args=(mxg,))
				thr.start()
				i+=1
			if vfl and (len(self.tr)>99):
				mxg=BMessage(446)
				# mxg.AddInt32("index",100)
				thr=Thread(target=be_app.WindowAt(0).PostMessage,args=(mxg,))
				thr.start()
		elif msg.what == 445: #construct and add newsitem
			value=msg.FindInt32("index")
			print("valore",value)
			self.NewsItemConstructor(self.tr[value])
		elif msg.what == 446: #construct Button-Blistitem
			# value=msg.FindInt32("index")
			self.BtnItemConstructor()
		elif msg.what == 455: #manage newslist ordered by Unread
			vfl=msg.FindBool("fl")
			print("vfl",vfl)
			if vfl:
				try:
					lx=len(self.totallist)
					if lx<100:
						en=lx
					else:
						en=100
				except:
					en=100
			else:
				en = len(self.totallist)
			print(en)
			i=0
			while i<en-1:
				mxg=BMessage(456)
				mxg.AddInt32("index",i)
				thr=Thread(target=be_app.WindowAt(0).PostMessage,args=(mxg,))
				thr.start()
				i+=1
			if vfl and (len(self.totallist)>99):
				mxg=BMessage(446)
				# mxg.AddInt32("index",100)
				thr=Thread(target=be_app.WindowAt(0).PostMessage,args=(mxg,))
				thr.start()
		elif msg.what == 456: #construct and add newsitem
			value=msg.FindInt32("index")
			self.NewsItemConstructor(self.totallist[value])
		elif msg.what == 465: #manage newslist ordered by datetime
			vfl=msg.FindBool("fl")
			if vfl:
				try:
					lx=len(self.orderedlist)
					if lx<100:
						en=lx
					else:
						en=100
				except:
					en=100
			else:
				en = len(self.orderedlist)
			print(en)
			i=0
			while i<en:
				mxg=BMessage(466)
				mxg.AddInt32("index",i)
				thr=Thread(target=be_app.WindowAt(0).PostMessage,args=(mxg,))
				thr.start()
				i+=1
			if vfl and (len(self.orderedlist)>99):
				mxg=BMessage(446)
				# mxg.AddInt32("index",100)
				thr=Thread(target=be_app.WindowAt(0).PostMessage,args=(mxg,))
				thr.start()
		elif msg.what == 466: #construct and add newsitem
			value=msg.FindInt32("index")
			self.NewsItemConstructor(self.orderedlist[value][0])
		elif msg.what == 5: #clear paper news
			cursel=self.Paperlist.lv.CurrentSelection()
			if cursel>-1:
				stuff="You are going to remove all "+self.Paperlist.lv.ItemAt(cursel).name+"'s feeds. Proceed?"
				ask=BAlert('cle', stuff, 'Yes', "No",None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_INFO_ALERT)
				ri=ask.Go()
				if ri==0:
					self.Paperlist.lv.DeselectAll()
					dirname=self.Paperlist.lv.ItemAt(cursel).path.Path()
					datapath = BDirectory(dirname)
					if datapath.CountEntries() > 0:
						datapath.Rewind()
						ret=False
						while not ret:
							evalent=BEntry()
							ret=datapath.GetNextEntry(evalent)
							if not ret:
								ret_status=evalent.Remove()
		elif msg.what == 8:
			perc=BPath()
			find_directory(directory_which.B_SYSTEM_DOCUMENTATION_DIRECTORY,perc,False,None)
			link=perc.Path()+"/packages/feedgator/BGator2/index.html"
			print(link)
			ent=BEntry(link)
			if ent.Exists():
				# open system documentation help
				cmd = "open "+link
				t = Thread(target=os.system,args=(cmd,))
				t.run()
			else:
				find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
				link=perc.Path()+"/BGator2/Data/help/index.html"
				ent=BEntry(link)
				if ent.Exists():
					#open user installed help
					cmd = "open "+link
					t = Thread(target=os.system,args=(cmd,))
					t.run()
				else:
					nopages=True
					cwd = os.getcwd()
					link=cwd+"/Data/help/index.html"
					ent=BEntry(link)
					if ent.Exists():
						#open git downloaded help
						cmd = "open "+link
						t = Thread(target=os.system,args=(cmd,))
						t.run()
						nopages=False
					else:
						alt="".join(sys.argv)
						mydir=os.path.dirname(alt)
						link=mydir+"/Data/help/index.html"
						ent=BEntry(link)
						if ent.Exists():
							cmd = "open "+link
							t = Thread(target=os.system,args=(cmd,))
							t.run()
							nopages=False
					if nopages:
						wa=BAlert('noo', 'No help pages installed', 'Poor me', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
						wa.Go()
		elif msg.what == 3: #open aboutWindow
			self.about_window = AboutWindow()
			self.about_window.Show()
		elif msg.what == 6: #open settings window
			self.settings_window = SettingsWindow()
			self.settings_window.Show()
		elif msg.what == 2: #remove feed and relative files and dir
			cursel=self.Paperlist.lv.CurrentSelection()
			if cursel>-1:
				stuff="You are going to remove "+self.Paperlist.lv.ItemAt(cursel).name+". Proceed?"
				ask=BAlert('rem', stuff, 'Yes', "No",None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_INFO_ALERT)
				ri=ask.Go()
				if ri==0:
					self.Paperlist.lv.DeselectAll()
					dirname=self.Paperlist.lv.ItemAt(cursel).path.Path()
					datapath = BDirectory(dirname)
					if datapath.CountEntries() > 0:
						datapath.Rewind()
						ret=False
						while not ret:
							evalent=BEntry()
							ret=datapath.GetNextEntry(evalent)
							if not ret:
								ret_status=evalent.Remove()
					if datapath.CountEntries() == 0:
						ent=BEntry(dirname)
						ent.Remove()
					x=len(tmpPitm)
					i=0
					remarray=False
					while i<x:
						if tmpPitm[i].path.Path() == dirname:
							remarray=True
							break
						i+=1
					self.Paperlist.lv.RemoveItem(cursel)
					if remarray:
						del tmpPitm[i]
		
		elif msg.what == 40:
			#TODO snellire Sort By Name
			perc=BPath()
			find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
			datapath=BDirectory(perc.Path()+"/BGator2")
			ent=BEntry(datapath,perc.Path()+"/BGator2")
			if not ent.Exists():
				datapath.CreateDirectory(perc.Path()+"/BGator2", datapath)
			ent.GetPath(perc)
			confile=BPath(perc.Path()+'/config.ini',None,False)
			ent=BEntry(confile.Path())
			if ent.Exists():
				cfgfile = open(confile.Path(),'w')
				Config.set('General','sort', "1")
				Config.write(cfgfile)
				cfgfile.close()
				Config.read(confile.Path())
			menuitm=self.savemenu.FindItem(40)
			menuitm.SetMarked(1)
			menuitm=self.savemenu.FindItem(41)
			menuitm.SetMarked(0)
			menuitm=self.savemenu.FindItem(42)
			menuitm.SetMarked(0)
			tmpindex=self.Paperlist.lv.CurrentSelection()
			#TODO crash on changing
			self.Paperlist.lv.DeselectAll()
			self.Paperlist.lv.Select(tmpindex)
		elif msg.what == 41:
			#TODO snellire Sort By Unread
			perc=BPath()
			find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
			datapath=BDirectory(perc.Path()+"/BGator2")
			ent=BEntry(datapath,perc.Path()+"/BGator2")
			if not ent.Exists():
				datapath.CreateDirectory(perc.Path()+"/BGator2", datapath)
			ent.GetPath(perc)
			confile=BPath(perc.Path()+'/config.ini',None,False)
			ent=BEntry(confile.Path())
			if ent.Exists():
				cfgfile = open(confile.Path(),'w')
				Config.set('General','sort', "2")
				Config.write(cfgfile)
				cfgfile.close()
				Config.read(confile.Path())
			menuitm=self.savemenu.FindItem(40)
			menuitm.SetMarked(0)
			menuitm=self.savemenu.FindItem(41)
			menuitm.SetMarked(1)
			menuitm=self.savemenu.FindItem(42)
			menuitm.SetMarked(0)
			tmpindex=self.Paperlist.lv.CurrentSelection()
			#TODO: crash on changing
			self.Paperlist.lv.DeselectAll()
			self.Paperlist.lv.Select(tmpindex)
		elif msg.what == 42:
			#TODO snellire Sort By Date
			perc=BPath()
			find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
			datapath=BDirectory(perc.Path()+"/BGator2")
			ent=BEntry(datapath,perc.Path()+"/BGator2")
			if not ent.Exists():
				datapath.CreateDirectory(perc.Path()+"/BGator2", datapath)
			ent.GetPath(perc)
			confile=BPath(perc.Path()+'/config.ini',None,False)
			ent=BEntry(confile.Path())
			if ent.Exists():
				cfgfile = open(confile.Path(),'w')
				Config.set('General','sort', "3")
				Config.write(cfgfile)
				cfgfile.close()
				Config.read(confile.Path())
			menuitm=self.savemenu.FindItem(40)
			menuitm.SetMarked(0)
			menuitm=self.savemenu.FindItem(41)
			menuitm.SetMarked(0)
			menuitm=self.savemenu.FindItem(42)
			menuitm.SetMarked(1)
			tmpindex=self.Paperlist.lv.CurrentSelection()
			#TODO: crash on changing
			self.Paperlist.lv.DeselectAll()
			self.Paperlist.lv.Select(tmpindex)
		elif msg.what == self.Paperlist.PaperSelection: #Paper selection
			self.NewsList.lv.MakeEmpty()
			cursel=self.Paperlist.lv.CurrentSelection()
			if len(tmpNitm)>0:
				for item in tmpNitm:
					del item
				tmpNitm.clear()
			if cursel>-1:
				self.Paperlist.lv.ItemAt(cursel).Statistics()
				stuff = self.Paperlist.lv.ItemAt(cursel).name+"\n\nTotal news: "+str(self.Paperlist.lv.ItemAt(cursel).newscount)+"\nNew news: "+str(self.Paperlist.lv.ItemAt(cursel).cnnews)
				#ta=text_run_array()
				#txtrun1=text_run()
				#txtrun1.offset=0
				#fon1=BFont(be_bold_font)
				#fon1.SetSize(48.0)
				#txtrun1.font=fon1
				#col1=rgb_color()
				#col1.red=0
				#col1.green=200
				#col1.blue=0
				#col1.alpha=255
				#txtrun1.color=col1
				#ta.count=1
				#ta.runs[0]=txtrun1
				#self.NewsPreView.SetText(stuff,ta)
				self.NewsPreView.SetText(stuff,None)
				#self.NewsPreView.SetRunArray(0,self.NewsPreView.TextLength(),ta)
				self.gjornaaltolet(True)
			else:
				self.NewsPreView.SelectAll()
				self.NewsPreView.Clear()

		elif msg.what == self.NewsList.NewsSelection: #News selection
			curit = self.NewsList.lv.CurrentSelection()
			if curit>-1:
				Nitm = self.NewsList.lv.ItemAt(curit)
				print(type(Nitm))
				if type(Nitm)==NewsItemBtn:
					self.gjornaaltolet(False)
				else:
					if Nitm.unread:
						Nitm.unread=False
						msg=BMessage(83)
						pth=BPath()
						Nitm.entry.GetPath(pth)
						msg.AddString("path",pth.Path())
						msg.AddBool("unreadValue",False)
						msg.AddInt32("selected",curit)
						msg.AddInt32("selectedP",self.Paperlist.lv.CurrentSelection())
						be_app.WindowAt(0).PostMessage(msg)
					NFile=BFile(Nitm.entry,0)
					r,s=NFile.GetSize()
					if not r:
						self.NewsPreView.SetText(NFile,0,s,None)
						txtnfile=self.NewsPreView.Text()
						newtxt="Published or stored (Y-m-d, H:M):\t\t\t\t\t"+Nitm.published.strftime("%Y-%m-%d, at %H:%M")+"\n\n"+txtnfile
						self.NewsPreView.SetText(newtxt,None)
					else:
						self.NewsPreView.SetText("There\'s no preview here",None)
			else:
				self.NewsPreView.SelectAll()
				self.NewsPreView.Clear()

		elif msg.what == 4: #mark all read
			if self.NewsList.lv.CountItems()>0:
				for item in self.NewsList.lv.Items():
					if item.unread:
						item.unread = False
						msg=BMessage(83)
						pth=BPath()
						item.entry.GetPath(pth)
						msg.AddString("path",pth.Path())
						msg.AddBool("unreadValue",False)
						msg.AddInt32("selected",self.NewsList.lv.IndexOf(item))
						msg.AddInt32("selectedP",self.Paperlist.lv.CurrentSelection())
						be_app.WindowAt(0).PostMessage(msg)

		elif msg.what == 9: #mark unread btn
			curit = self.NewsList.lv.CurrentSelection()
			if curit>-1:
				Nitm = self.NewsList.lv.ItemAt(curit)
				if not Nitm.unread:
					Nitm.unread = True
					msg=BMessage(83)
					pth=BPath()
					Nitm.entry.GetPath(pth)
					msg.AddString("path",pth.Path())
					msg.AddBool("unreadValue",True)
					msg.AddInt32("selected",curit)
					msg.AddInt32("selectedP",self.Paperlist.lv.CurrentSelection())
					be_app.WindowAt(0).PostMessage(msg)

		elif msg.what == 10: #mark read btn
			curit = self.NewsList.lv.CurrentSelection()
			if curit>-1:
				Nitm = self.NewsList.lv.ItemAt(curit)
				if Nitm.unread:
					Nitm.unread = True
					msg=BMessage(83)
					pth=BPath()
					Nitm.entry.GetPath(pth)
					msg.AddString("path",pth.Path())
					msg.AddBool("unreadValue",False)
					msg.AddInt32("selected",curit)
					msg.AddInt32("selectedP",self.Paperlist.lv.CurrentSelection())
					be_app.WindowAt(0).PostMessage(msg)

		elif msg.what == 83: # Mark Read/unread
			e = msg.FindString("path")
			unrVal = msg.FindBool("unreadValue")
			nd=BNode(e)
			ninfo,ret=nd.GetAttrInfo("Unread")
			if not ret:
				if unrVal:
					givevalue=bytearray(b'\x01')
				else:
					givevalue=bytearray(b'\x00')
				nd.WriteAttr("Unread",ninfo.type,0,givevalue)
				itto=self.NewsList.lv.ItemAt(msg.FindInt32("selected"))
				itto.DrawItem(self.NewsList.lv,self.NewsList.lv.ItemFrame(msg.FindInt32("selected")),True)
				itto=self.Paperlist.lv.ItemAt(msg.FindInt32("selectedP"))
				itto.DrawItem(self.Paperlist.lv,self.Paperlist.lv.ItemFrame(msg.FindInt32("selectedP")),False)
			self.NewsList.lv.Hide()
			self.NewsList.lv.Show()

		elif msg.what == self.NewsList.HiWhat: #open link
			curit=self.NewsList.lv.CurrentSelection()
			if curit>-1:
				itto=self.NewsList.lv.ItemAt(curit)
				if itto.link != "":
					t = Thread(target=openlink,args=(itto.link,))
					t.run()
			
		elif msg.what == self.Paperlist.HiWhat: #open paper folder or details
			curit=self.Paperlist.lv.CurrentSelection()
			if curit>-1:
				if self.shiftok:
					self.papdetW.append(PapDetails(self.Paperlist.lv.ItemAt(curit)))
					self.papdetW[-1].Show()
				else:
					ittp=self.Paperlist.lv.ItemAt(curit)
					subprocess.run(["open",ittp.path.Path()])

		elif msg.what == 1: #open add feed window
			self.tmpWind.append(AddFeedWindow())
			self.tmpWind[-1].Show()

		elif msg.what == 245: # ADD FEED
			feedaddr=msg.FindString("feed")
			d=feedparser.parse(feedaddr)
			if d.feed.has_key('title'):
				dirname=d.feed.title
				perc=BPath()
				find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
				folder=perc.Path()+"/BGator2/Papers/"+dirname
				datapath=BDirectory(folder)
				entr=BEntry(folder)
				if entr.Exists():
					saytxt="The folder "+folder+" is present, please remove it and add the feed again"
					about = BAlert('Ops', saytxt, 'Ok', None,None,InterfaceDefs.B_WIDTH_AS_USUAL,alert_type.B_WARNING_ALERT)
					about.Go()
				else:
					datapath.CreateDirectory(perc.Path()+"/BGator2/Papers/"+dirname,datapath)
					del perc
					nd=BNode(entr)
					givevalue=feedaddr.encode('utf-8')#bytes(feedaddr,'utf-8')
					nd.WriteAttr("address",TypeConstants.B_STRING_TYPE,0,givevalue)
					attributes=attr(nd)
					pirc=BPath()
					entr.GetPath(pirc)
					for element in attributes:
						if element[0] == "address":
							tmpPitm.append(PaperItem(pirc,element[2][0]))
							self.Paperlist.lv.AddItem(tmpPitm[-1])
							be_app.WindowAt(0).PostMessage(66)
				#controlla se esiste cartella chiamata titul&
				#se esiste ma gli attributi non corrispondono, chiedere cosa fare
				#se esiste ma non ha tutti gli attributi scrivili

		elif msg.what == 66: #Parallel Update news
			self.infostring.SetText("Updating news, please wait...")
			self.progress.SetMaxValue(self.Paperlist.lv.CountItems()*100+self.Paperlist.lv.CountItems())
			self.cres=0
			for item in self.Paperlist.lv.Items():
				Thread(target=self.DownloadNews,args=(item,)).start()
			self.Paperlist.lv.Hide()
			self.Paperlist.lv.Show()
			
		elif msg.what == 542:
			# eventually remove this
			self.Paperlist.lv.Hide()
			self.Paperlist.lv.Show()
			
			
		elif msg.what == 1990:
			d = msg.FindFloat("delta")
			self.progress.Update(d,None,None)
		elif msg.what == 1991:
			self.cres+=1
			if self.cres == self.Paperlist.lv.CountItems():
				self.progress.Reset(None,None)
				self.infostring.SetText(None)
					
			
		BWindow.MessageReceived(self, msg)

	def remove_html_tags(self,data):
		p = re.compile(r'<.*?>')
		return p.sub('', data)
		
		
	def DownloadNews(self,item):
				# TODO inserire un lock per non sballare i valori di progress				
				perc=BPath()
				find_directory(directory_which.B_USER_NONPACKAGED_DATA_DIRECTORY,perc,False,None)
				dirpath=BPath(perc.Path()+"/BGator2/Papers/"+item.name,None,False)
				datapath=BDirectory(dirpath.Path())
				stringa=item.address.encode('utf-8')
				rss = feedparser.parse(stringa.decode('utf-8'))
				valueperentry=100/(len(rss.entries)+1)
				mxg=BMessage(1990)
				mxg.AddFloat("delta",valueperentry)
				be_app.WindowAt(0).PostMessage(mxg)
				del stringa
				y=len(rss['entries'])
				for x in range (y):
					filename=rss.entries[x].title
					newfile=BFile()
					if datapath.CreateFile(dirpath.Path()+"/"+filename,newfile,True):
						pass
					else:
						nd=BNode(dirpath.Path()+"/"+filename)
						try:
							givevalue=bytes(rss.entries[x].title,'utf-8')
						except:
							givevalue=bytes("No title",'utf-8')
						finally:
							nd.WriteAttr("title",TypeConstants.B_STRING_TYPE,0,givevalue)
						try:
							givevalue=bytes(rss.entries[x].link,'utf-8')
						except:
							givevalue=bytes("no link",'utf-8')
						else:
							nd.WriteAttr("link",TypeConstants.B_STRING_TYPE,0,givevalue)
						givevalue=bytearray(b'\x01')
						nd.WriteAttr("Unread",TypeConstants.B_BOOL_TYPE,0,givevalue)
						try:
							givevalue=bytes(rss.entries[x].author,'utf-8')
						except:
							givevalue=bytes("No author",'utf-8')
						finally:
							nd.WriteAttr("author",TypeConstants.B_STRING_TYPE,0,givevalue)
						try:
							published = rss.entries[x].published_parsed
						except:
							published = None
						else:
						#if published != None:
							#print(published)# TODO There's a difference of 1 hour between time parsed from feedrss and what is written and read in the filesystem attribute
							################## does this means I didn't care of timezone? or something else? legal hour?
							asd=datetime.datetime(published.tm_year,published.tm_mon,published.tm_mday,published.tm_hour,published.tm_min,published.tm_sec)
							#print(rss.entries[x].title,asd)
							asd_sec = round((asd - datetime.datetime(1970, 1, 1,0,0,0)).total_seconds()) 
							pass_time = struct.pack('q',asd_sec)
							nd.WriteAttr("published",TypeConstants.B_TIME_TYPE,0,pass_time)
#							try:
#									rssdate=rss.entries[x].date
#									date,timeall= rssdate.split('T')
#									time,all= timeall.split('+')
#									zornade=(date+' '+time)
#							except:
#									now=datetime.datetime.now()
#									zornade=(str(now.year)+'-'+str(now.month)+'-'+str(now.day)+' '+str(now.hour)+':'+str(now.minute)+':'+str(now.second))
						try:
							texttowrite=bytes(self.remove_html_tags(rss.entries[x].summary_detail.value),'utf-8')
						except:
							Texttowrite=bytes("No summary available",'utf-8')
						finally:
							newfile.Write(texttowrite)
					be_app.WindowAt(0).PostMessage(mxg)
				be_app.WindowAt(0).PostMessage(542)
				be_app.WindowAt(0).PostMessage(1991)
	
	def FrameResized(self,x,y):
		resiz=False
		if x<974:
			x=974
			resiz=True
		if y<650:
			y=650
			resiz=True
		if resiz:
			self.ResizeTo(x,y)
		self.box.ResizeTo(x,y-29)
		self.bar.ResizeTo(x,self.bar.Bounds().bottom)
		self.progress.ResizeTo(x-self.progress.Bounds().left-340,self.progress.Bounds().bottom)
		self.NewsList.sv.ResizeTo(x-self.NewsList.sv.Frame().left-8,self.box.Bounds().Height() / 1.8-68)
		self.NewsList.lv.ResizeTo(self.NewsList.sv.Bounds().Width()-24,self.NewsList.sv.Bounds().Height()-5)
		self.outbox_preview.MoveTo(self.NewsList.sv.Frame().left+2,self.NewsList.sv.Frame().bottom+5)
		self.outbox_preview.ResizeTo(x-342,y-self.outbox_preview.Frame().top -self.markUnreadBtn.Bounds().Height()-40)
		boxboundsw=self.box.Bounds().Width()
		btnswidth=round((boxboundsw - 8 - (8 + self.Paperlist.sv.Bounds().right) -8 - 8)/3,2)
		self.markUnreadBtn.ResizeTo(btnswidth,self.markUnreadBtn.Bounds().Height())
		self.markReadBtn.MoveTo(self.markUnreadBtn.Frame().right+8,self.markReadBtn.Frame().top)
		self.markReadBtn.ResizeTo(btnswidth,self.markReadBtn.Bounds().Height())
		self.openBtn.MoveTo(self.markReadBtn.Frame().right+8,self.openBtn.Frame().top)
		self.openBtn.ResizeTo(btnswidth-4,self.openBtn.Bounds().Height())
		BWindow.FrameResized(self,x,y)

	def QuitRequested(self):
		wnum = be_app.CountWindows()
		if wnum>1:
			if len(self.tmpWind)>0:
				for wind in self.tmpWind:
					wind.Lock()
					wind.Quit()
			if len(self.papdetW)>0:
				for papw in self.papdetW:
					papw.Lock()
					papw.Quit()
		return BWindow.QuitRequested(self)
		
class App(BApplication):
	def __init__(self):
		BApplication.__init__(self, "application/x-python-BGator2")
	def ReadyToRun(self):
		self.window = GatorWindow()
		self.window.Show()
		self.window.Minimize(self.window.startmin)
	def MessageReceived(self,msg):
		msg.PrintToStream()
		BApplication.MessageReceived(self,msg)

	def Pulse(self):
		if self.window.enabletimer:
			be_app.WindowAt(0).PostMessage(BMessage(66))

def main():
    global be_app
    be_app = App()
    be_app.Run()
	
 
if __name__ == "__main__":
    main()

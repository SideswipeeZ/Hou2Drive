
# -*- coding: utf-8 -*-

##      @file           Hou2Drive.py
##      @author         Bilal Malik
##      @contact        echopraxiavfx@gmail.com
##
##      @desc           Upload Current Houdini File to Authenticated Google Drive Account.
##                      It Can also retrive files uploaded to the specific folder.
##----------------------------------------------------------------------------------------

import sys, os, time, datetime, hou

#Set If Application is a Python Panel App or Shelf.
isPanel = False

#Root Folder Location. This must be pointed to the correct path.
#Point this path to the root folder. Can also be retrieved from houdini env
rootL = "PATH_HERE"
#Import Modules Folder
sys.path.insert(0,(rootL + "\modules.zip"))
#Required Line as Houdini (Self Tool) wont detect Qt module
sys.path.insert(0,(rootL + "\modules.zip\Qt.py-1.2.0.b3"))

#import Qt Modules
from Qt import QtWidgets, QtCompat, QtGui, QtCore
from Qt.QtGui import QColor, QPixmap, QPainter, QIcon

#Import PyDrive Module
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
#Set Clients Config file Location (Expected Location is in Root Folder)
GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = os.path.join(rootL + "\client_secret.json")

#File Interface File.
file_interface = os.path.join(rootL + "\GUI\H2CV2.ui")
#Pixmaps
gicon = os.path.join(rootL  + "\GUI\GDrive40.png")
hicon = os.path.join(rootL  + "\GUI\Hou40.png")
header = os.path.join(rootL  + "\GUI\header.png")

#Main Qt Class
class MyWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent, QtCore.Qt.WindowStaysOnTopHint )
        self.mw = QtCompat.loadUi(file_interface)
        self.setCentralWidget(self.mw)
        self.setWindowTitle("Hou2Cloud")
        stylesheet = hou.qt.styleSheet()
        self.setStyleSheet(stylesheet)
        #Clear Conditions
        self.mw.listWidget.clear()
        self.mw.header_lbl.setPixmap(QPixmap(header))
        self.mw.bttn_link.setText("Link Google Account")

        #Get Init Conditions
        self.Start()
        #Check if Houdini is running Apprentice.
        self.mw.combo_file.clear()
        if hou.isApprentice() == False:
                self.mw.combo_file.addItem(".hip")
        self.mw.combo_file.addItem(".hipnc")
        self.mw.combo_file.addItem(".hiplc")

        #Button Assignment
        #Link to Google Drive
        self.mw.bttn_link.clicked.connect(self.linkDrive)
        self.mw.bttn_link.setIcon(QIcon(gicon))
        #Get File List from Drive
        self.mw.bttn_getFiles.clicked.connect(self.getFiles)
        self.mw.bttn_getFiles.setIcon(QIcon(gicon))
        #Clear List
        self.mw.bttn_clear.clicked.connect(self.clearList)
        self.mw.bttn_clear.setIcon(QIcon(hicon))
        #Upload Button
        self.mw.bttn_upload.clicked.connect(self.upload)
        self.mw.bttn_upload.setIcon(QIcon(gicon))

    def Start(self,*args):
        print("Starting")
        #Check for credentials.json file 
        if os.path.isfile(rootL + "\credentials.json") == True:
                self.mw.bttn_link.setText("Google Account is Linked. (Re-Auth)")
                self.mw.bttn_getFiles.setEnabled(True)
                self.mw.bttn_clear.setEnabled(True)
                self.mw.bttn_upload.setEnabled(True)
        else:
                self.mw.bttn_getFiles.setEnabled(False)
                self.mw.bttn_clear.setEnabled(False)
                self.mw.bttn_upload.setEnabled(False)

    #Login to G Drive to obtain token.
    def login(self,*args):
        global gauth, drive
        gauth = GoogleAuth()
        gauth.LoadCredentialsFile(rootL + "\credentials.json")
        if gauth.credentials is None:
                gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
                gauth.Refresh()
        else:
                gauth.Authorize()
        gauth.SaveCredentialsFile(rootL + "\credentials.json")
        #Create Drive wrapper.
        drive = GoogleDrive(gauth)

    #Get Folder ID from Drive.
    def find_folders(self,fldname):
        file_list = drive.ListFile({'q': "title='{}' and mimeType contains 'application/vnd.google-apps.folder' and trashed=false".format(fldname)}).GetList()
        return file_list

    #Flow to Obtain credentials for drive link.
    def linkDrive(self,*args):
        print("Linking to Drive")
        self.mw.listWidget.clear()
        self.login()
        self.Start()
    #Retrives filenames of uploaded files from Drive folder if any. 
    def getFiles(self,*args):
        print("Getting Files")
        self.mw.listWidget.clear()
        self.login()
        fld = self.find_folders("Houdini2Cloud")
        #Folder search hardwired two tries per try.
        global fld_id
        fld_id = ""
        if fld == []:
                print("Creating Root Folder on GDrive")
                try:
                        new_folder = drive.CreateFile({'title':'{}'.format("Houdini2Cloud"),'mimeType':'application/vnd.google-apps.folder'})
                        new_folder.Upload()
                except:
                        print("Unable to create a root Folder")
                fld2 = find_folders("Houdini2Cloud")
                if fld2 == []:
                        print("Root Folder could not be found.")
                else:
                        for i in fld2:
                                fld_id = i['id']
        else:
                for i in fld:
                        fld_id = i['id']
        if fld_id == "":
                print("Something went wrong finding a folder")
        else:
                #Get File List in Drive DIR ~ Currently gets all types of files inside the folder.
                file_list = drive.ListFile({'q': "'{}' in parents and trashed=false".format(fld_id)}).GetList()
                #Fill listWidget with name of files.
                if file_list != None:
                        for each in file_list:
                                self.mw.listWidget.addItem(str(each['title']))
                else:
                        self.mw.listWidget.addItem("No Files Found.")
    def clearList(self,*args):
        print("Clearing list")
        self.mw.listWidget.clear()
        print("Cleared.")

    def upload(self,*args):
        print("Uploading")
        self.login()
        #Get File Name
        if self.mw.lineEdit.text() != "":
                print("Saving.")
                dateVar = datetime.datetime.now().strftime("_Autosave_%d%m%Y_%H%M%S")
                fle_nme = str(self.mw.lineEdit.text()) + str(dateVar) + str(self.mw.combo_file.currentText())
                fle_path = rootL + "\SaveTemp\\" + fle_nme
                hou.hipFile.save(file_name=fle_path, save_to_recent_files=False)

                #Upload Saved File.
                global fld_id
                fld = self.find_folders("Houdini2Cloud")
                fld_id = ""
                if fld == []:
                        print("Creating Root Folder on GDrive")
                        try:
                                new_folder = drive.CreateFile({'title':'{}'.format("Houdini2Cloud"),'mimeType':'application/vnd.google-apps.folder'})
                                new_folder.Upload()
                        except:
                                print("Unable to create a root Folder")
                        fld2 = find_folders("Houdini2Cloud")
                        if fld2 == []:
                                print("Root Folder could not be found.")
                        else:
                                for i in fld2:
                                        fld_id = i['id']
                else:
                        for i in fld:
                                fld_id = i['id']
                if fld_id == "":
                        print("Something went wrong finding a folder")
                else:
                        #Upload File to Drive
                        upFile = drive.CreateFile({'title':fle_nme,"parents": [{"kind": "drive#fileLink","id": fld_id}]})
                        upFile.SetContentFile(fle_path)
                        upFile.Upload()
                        print("File Uploaded!")
                        self.mw.lineEdit.clear()
                        upFile.SetContentFile(rootL+"\dummy.txt")
                        try:
                                os.remove(fle_path)
                        except:
                                print("Coudnt Remove File.")
        else:
                    print("Upload Failed.")

if isPanel == True:
    #Create Interface Python Panel
    def onCreateInterface():
        my_window = MyWindow()
        my_window.show()
        return my_window
elif isPanel == False:
    #Create Interface Shelf.
    try:
        my_window.close()
    except:
        pass
    my_window = MyWindow()
    my_window.resize(392,639)
    my_window.show()

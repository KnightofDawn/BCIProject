from distutils.core import setup
import py2exe # Patching distutils setup
from guidata.disthelpers import create_vs2008_data_files, remove_dir
from guidata.disthelpers import Distribution
import matplotlib
import os, shutil
#from guidata.disthelpers.Distribution import  add_module_data_files, add_modules, DEFAULT_EXCLUDES, DEFAULT_BIN_EXCLUDES

remove_dir('build')
remove_dir('dist')

guidata_dist = Distribution()

# Removing old build/dist folders
#remove_build_dist()

# Including/excluding DLLs and Python modules
EXCLUDES = guidata_dist.DEFAULT_EXCLUDES
INCLUDES = []
DLL_EXCLUDES = guidata_dist.DEFAULT_BIN_EXCLUDES
DATA_FILES = []
DATA_FILES += create_vs2008_data_files()
DATA_FILES += matplotlib.get_py2exe_datafiles()
DATA_FILES += [('entropic_logo.jpg')]
DATA_FILES += [('snr_table.txt')]

#print DATA_FILES
#print matplotlib.get_py2exe_datafiles()
# Distributing application-specific data files
#guidata_dist.add_module_data_files("spyderlib", ("images", ),
#                      ('.png', '.svg',), copy_to_root=True)
guidata_dist.add_module_data_files("spyderlib", ("", ),
                      ('.qm', '.py'), copy_to_root=True)

# Configuring/including Python modules
guidata_dist.add_pyqt4()
guidata_dist.add_matplotlib()

#guidata_dist.build('py2exe')

#guidata_dist.add_modules(['PyQt4', 'matplotlib']) # add 'matplotlib' after 'PyQt4' if you need it
            #DATA_FILES, INCLUDES, EXCLUDES)

setup(
        options={
                "py2exe": {"compressed": 2, "optimize": 2, 'bundle_files': 3,
                          "includes": INCLUDES, "excludes": EXCLUDES,
                          "dll_excludes": DLL_EXCLUDES,
                          "dist_dir": "dist",},
               },
        data_files=DATA_FILES,
        #data_files=[DATA_FILES, matplotlib.get_py2exe_datafiles()],
        windows=[{
                "script": "main_app.py",
                "dest_base": "PHYSysTD",
                "version": "1.0",
                "author": "Veeresh Taranalli",
                "company_name": "Entropic Communications",
                "copyright": u"Copyright 2012 Entropic Communications",
                "name": u"PhySysTD-GUI",
                "description": u"PHY Systems Debugger",
                },],
        zipfile = None,

)

#MPLDATA_SOURCE = 'C:/Python27/Lib/site-packages/matplotlib/mpl-data/'
SPYDERLIB_IMAGES_SOURCE = os.getcwd() + '/spyderlib/images'
QT_PLUGINS_SOURCE = 'C:/Python27/Lib/site-packages/PyQt4/plugins'

#MPLDATA_DEST = os.getcwd() + '/dist/mpl-data/'
SPYDERLIB_IMAGES_DEST = os.getcwd() + '/dist/spyderlib/images/'
QT_PLUGINS_DEST = os.getcwd() + '/dist/plugins/'

#shutil.copytree(MPLDATA_SOURCE, MPLDATA_DEST)
shutil.copytree(SPYDERLIB_IMAGES_SOURCE, SPYDERLIB_IMAGES_DEST)
shutil.copytree(QT_PLUGINS_SOURCE, QT_PLUGINS_DEST)

fp = open(os.getcwd() + '/dist/qt.conf', 'w')
fp.write('[PATH] \n Plugins = plugins')
fp.close()


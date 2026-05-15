#!/usr/local/bin/python3

# tk_plot for 3D data
# Uses matplotlib with pyplot namespace 

# John Kielkopf

# 2019-10-29
# Version 1.0


# User interface

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

# Plotting graphics

import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

mpl.use('TkAgg')


# Necessary support

import os
import sys
import numpy as np


# Identify global variables

global selected_files
global x_data
global y_data
global z_data

# Preset variables

selected_files = []
x_data = np.zeros(1024)
y_data = np.zeros(1024)
z_data = np.zeros(1024)
x_axis_label = ""
y_axis_label = ""
z_axis_label = ""

# 
# Define tk callbacks
#

# Make a graceful exit

def graceful_exit():
  response = tk.messagebox.askokcancel('Confirmation','Exit now?')
  if response:    
    exit()
  return()  
  

# Select a file and update the panel information

def select_file():

  global selected_files
  
  # Use the tk file dialog to identify file(s)
  
  newfile = ""
  try:
    newfile, = tk.filedialog.askopenfilenames()  
    selected_files.append(newfile)
  except:
    tk_info.set("No file selected")

  if newfile !="":
    tk_info.set("Latest file: "+newfile)

  return()
  

# Read a file of xy data into numpy arrays for x and y

def read_file(infile):
  global x_data
  global y_data
  global z_data

  datafp = open(infile, 'r')
  datatext = datafp.readlines()
  datafp.close()

  # How many lines were there?

  i = 0
  for line in datatext:
    i = i + 1

  nlines = i

  # Fill  the arrays for fixed size is much faster than appending on the fly

  x_data = np.zeros((nlines))
  y_data = np.zeros((nlines))
  z_data = np.zeros((nlines))

  # Parse the lines into the data

  i = 0
  for line in datatext:
    
    # Test for a comment line
    
    if ((line[0] == "#") or (line[0] == "!") ):
      continue
       
    # Treat the case of a plain text comma separated entries    
    
    try:
            
      entry = line.strip().split(",")  
      x_data[i] = float(entry[0])
      y_data[i] = float(entry[1])
      z_data[i] = float(entry[2])

      i = i + 1    
    except:      
    
      # Treat the case of space separated entries
    
      try:
        entry = line.strip().split()
        x_data[i] = float(entry[0])
        y_data[i] = float(entry[1])
        z_data[i] = float(entry[2])
        i = i + 1
      except:
        pass

  return()
  
    
# Create the desired plot

def make_plot(event=None):
  
  global selected_files
  global x_axis_label
  global y_axis_label
  global z_axis_label
  
  nfiles = len(selected_files)
  this_file = selected_files[nfiles-1]
  
  read_file(this_file)

  # Create the plot.
  fig = plt.figure(nfiles)
  subfig = fig.add_subplot(111, projection='3d')
  subfig.scatter(x_data,y_data,z_data, c='r', marker='o') 
  subfig.set_title(this_file)
  subfig.set_xlabel(x_axis_label)
  subfig.set_ylabel(y_axis_label)
  subfig.set_zlabel(z_axis_label)
  plt.show()




# Define a bold header font

LARGE_BOLD = ('Verdana', '12', 'bold')


# Check the command line for a file

infile = ""

if len(sys.argv) > 2:
  print (" ")
  print ("Usage: tk_plot [data.dat] ")
  print (" ")
  sys.exit("Plot 2-column data\n")
elif len(sys.argv) == 2:
  infile = sys.argv[1]

# Create a control panel for managing the graphics

panel = tk.Tk()
panel.title("Tk Plot")
#panel.geometry("320x160")

# Add a frame to the panel

mainframe = ttk.Frame(panel, padding="12 12 12")
mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

tk_info = tk.StringVar()

info = ttk.Label(mainframe, textvariable=tk_info)

# Add a message for the user

if infile !="":
  tk_info.set("Latest file: "+infile)
  selected_files.append(infile)
else:  
  tk_info.set("Select a file to begin")

info.grid(column=2, row=1)

ttk.Separator(mainframe, orient=tk.HORIZONTAL).grid(row=2, column=1, columnspan=3, sticky=(tk.EW), pady=20)

# Add a button to select a file

ttk.Button(mainframe, text="File", command=select_file).grid(column=1, row=3, sticky=tk.W)

# Add a button to plot the data

ttk.Button(mainframe, text="Plot", command=make_plot).grid(column=2, row=3, sticky=(tk.E,tk.W))

# Add a button to exit

ttk.Button(mainframe, text="Exit", command=graceful_exit).grid(column=3, row=3, sticky=tk.E)


# Press <Return> to create plot

panel.bind('<Return>', make_plot)


# Activate the panel

panel.mainloop()

exit()

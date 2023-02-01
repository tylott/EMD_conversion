#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 31 19:40:56 2023

@author: tyler

A script to convert single .emd files into image files.

"""

import os
import hyperspy.api as hs 
import tkinter as tk
from tkinter import filedialog
from PIL import Image
import numpy as np
import h5py
import json

root = tk.Tk()
root.withdraw()

file = filedialog.askopenfilename()
print(file)
file_path2 = os.rename(file, file[0:-4].replace(".","_")+".emd") # Auto-renaming of the folder to prevent mis-reading later in the file 
file_path2 = file[0:-4].replace(".","_")+".emd"
file_path = open(os.path.expanduser(str(file_path2)))
s = hs.load(file_path.name, lazy = True, stack = True) # lazy = True, A Lazy Signal instance that delays computation until explicitly saved (assuming storing the full result of computation in memory is not feasible)
print("Hyperspy API load complete.")
num_imgs = len(s)

### Save all of the metadata to a text file for a single image ###
def save_pet(pet):
    filename = "Image_MD.txt"
    with open(filename, 'w') as f:
        f.write(json.dumps(pet))
        
############################## Metadata storage ####################################

f = h5py.File(file, 'r')
class navigate:

    @staticmethod
    def getGroupsNames(group):
        items = []
        for item in group:
            if group.get(item, getclass=True) == h5py._hl.group.Group:
                items.append(group.get(item).name)

    @staticmethod
    def getGroup(group, item):
        if group.get(item, getclass=True) == h5py._hl.group.Group:
            return group.get(item)

    @staticmethod
    def getSubGroup(group, path):
        return group[path]

    @staticmethod
    def getDirectoryMap(group):
        for item in group:
            # check if group
            if group.get(item, getclass=True) == h5py._hl.group.Group:
                item = group.get(item)
                # process subgroups
                if type(item) is h5py._hl.group.Group:
                    navigate.getDirectoryMap(item)

    @staticmethod
    def getMemberName(group, path):
        members = list(group[path].keys())
        if len(members) == 1:
            return str(members[0])
        else:
            return members

class decode:

    @staticmethod
    def convertASCII(ascii_meta):
        metadata_text = ''.join(chr(i) for i in ascii_meta)
        return metadata_text.replace("\0", '')

# Get metadata.
metalocation = navigate.getMemberName(f, '/Data/Image/')
#options = navigate.getMemberName(f, '/Data/Image/' + metalocation) # shows name for metadata subdir.

if num_imgs > 1:
    print(str(num_imgs)+" images")
else:
    print(str(num_imgs)+" image")
s_metadata = []   

### Saving selected metadata parameters to txt ### 
if num_imgs > 1: 
    img_num = 0
    while img_num < len(s):
        ascii_meta = f['/Data/Image/' + str(metalocation) + '/Metadata'][:][:,img_num] # frame
        jsonmeta = decode.convertASCII(ascii_meta)
        result = json.loads(jsonmeta)
        pixel_size_width = float(result['BinaryResult']['PixelSize']['width'])
        pixel_size_height = float(result['BinaryResult']['PixelSize']['height'])
        frame_time = float(result['Scan']['FrameTime'])
        magnification = float(result['Optics']['NominalMagnification'])
        screen_current = float(result['Optics']['LastMeasuredScreenCurrent'])
        image_metadata = {"Pixel size height (m):": pixel_size_height,"Pixel size width (m):": pixel_size_width, "Frame time (s):": frame_time, "Magnification:": magnification, "Screen current (A):": screen_current}
        s_metadata.append(image_metadata)
        img_num += 1 

else:
    img_num = 0
    ascii_meta = f['/Data/Image/' + str(metalocation) + '/Metadata'][:][:,img_num] # frame
    jsonmeta = decode.convertASCII(ascii_meta)
    result = json.loads(jsonmeta)
    pixel_size_width = float(result['BinaryResult']['PixelSize']['width'])
    pixel_size_height = float(result['BinaryResult']['PixelSize']['height'])
    frame_time = float(result['Scan']['FrameTime'])
    screen_current = float(result['Optics']['LastMeasuredScreenCurrent'])
    #magnification = float(result['Optics']['NominalMagnification'])
    #frame_time = float(s.original_metadata.Scan.FrameTime)
    image_metadata = {"Pixel size height (m)": pixel_size_height,"Pixel size width (m)": pixel_size_width}#,  "Magnification": magnification}#, "Frame time (s)": frame_time}
    s_metadata.append(image_metadata)
    
img_lst = []
imarray = np.array(s)
img_num = 0

### Placeholder boolean to choose PIL, OpenCV could also be implemented here (not included)

if num_imgs > 1:    
    while img_num < num_imgs:   # Converting the image arrays in Hyperspy format to numpy array, then placing the array in a list
        img_lst.append(imarray[img_num])
        img_num += 1    
        
    img_norm_lst = []
    img_num = 0
    
    ### File saving
    save_input = input("Would you like to save? (Y/N)? ")
    if save_input == "Y" or save_input == "Yes" or save_input == "yes" or save_input == "y":
        save_path = filedialog.asksaveasfilename(initialfile = "frame")
        file_ext = save_path[save_path.rfind("."):] # rfind finds the last occurrence of a substring within a string
        if save_path[-1] == file_ext:   # Defaults to save as a tif if the user does not specify the file extension, also possible through Tkinter
            save_path = str(save_path) + ".tif"
            file_ext = ".tif"
        file_dir = save_path[0:save_path.rfind(".")]
        with open(str(file_dir)+"_s_metadata.txt", "w") as output:
            MD_count = 1
            for i in s_metadata:
                output.write("["+str(MD_count)+"]"+str(i)+"\n")
                MD_count += 1
        print("END OF PROGRAM")
        root.destroy()
    else:
        print("END OF PROGRAM")

else:   # Dealing with single image EMD files
    #imarray *= 255/imarray.max() # Commented out to remove 8-bit conversion which appeared to create artifacts
    PIL_image = Image.fromarray(imarray) # Changed Image.fromarray(np.uint8(imarray)) to Image.fromarray(imarray) to maintain the 16 bit file size which reduces artifacts 
 
### File saving
    save_input = input("Would you like to save? (Y/N)? ")
    if save_input == "Y" or save_input == "Yes" or save_input == "yes" or save_input == "y":
        save_path = filedialog.asksaveasfilename(initialfile = "frame")
        file_ext = save_path[save_path.rfind("."):]
        if save_path[-1] == file_ext:   # Defaults to save as a tif if the user does not specify the file extension
            save_path = str(save_path) + ".tif"
            file_ext = ".tif"
        file_dir = save_path[0:save_path.rfind(".")]
        with open(str(file_dir)+"_s_metadata.txt", "w") as output:
            output.write(str(s_metadata)+"\n")
        PIL_image.save((save_path))
        root.destroy()
    else:
        print("END OF PROGRAM")
        root.destroy()

save_pet(result)
"""
Created on Tue Jan 31 19:47:17 2023

@author: tyler

A script to batch convert .emd files into image files.

MIT License

Copyright (c) 2023 Tyler Lott

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import hyperspy.api as hs 
import tkinter as tk
from tkinter import filedialog
from PIL import Image
import numpy as np
from pathlib import Path
import h5py
import json

root = tk.Tk()
root.withdraw()

### Iterate through all of the emd files within a directory 
choose_dir = filedialog.askdirectory()
mydir = Path(str(choose_dir))
for file in mydir.glob('*.emd'):
    if file.name[0:2] == "._": # If the h5py files are improperly downloaded they will leave a corrupted "ghost" file with "._" at the beginning of the filename, this for loop acts as a filter for this miswrite
        continue
    else:
        print(file.name)
        
        s = hs.load(str(file), lazy = True) # lazy = True, A Lazy Signal instance that delays computation until explicitly saved (assuming storing the full result of computation in memory is not feasible)
        s_name = file.name
        print("Hyperspy API load complete.")
        num_imgs = len(s)
        
        ############################## Metadata storage ####################################

        f = h5py.File(str(file), 'r')
        
        class navigate:

            @staticmethod
            def getGroupsNames(group):
                items = []
                for item in group:
                    if group.get(item, getclass=True) == h5py._hl.group.Group:
                        items.append(group.get(item).name)
                print(items)

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
        
        if num_imgs > 1: 
            img_num = 0
            while img_num < len(s):
                ascii_meta = f['/Data/Image/' + str(metalocation) + '/Metadata'][:][:,img_num] # frame
                jsonmeta = decode.convertASCII(ascii_meta)
                result = json.loads(jsonmeta)
                pixel_size_width = float(result['BinaryResult']['PixelSize']['width'])
                pixel_size_height = float(result['BinaryResult']['PixelSize']['height'])
                frame_time = float(result['Scan']['FrameTime'])
                screen_current = float(result['Optics']['LastMeasuredScreenCurrent'])
                image_metadata = {"Pixel size height (m)": pixel_size_height,"Pixel size width (m)": pixel_size_width, "Frame time (s)": frame_time}
                s_metadata.append(image_metadata)
                img_num += 1 
        
        else:
            img_num = 0
            ascii_meta = f['/Data/Image/' + str(metalocation) + '/Metadata'][:][:,img_num] # frame
            jsonmeta = decode.convertASCII(ascii_meta)
            result = json.loads(jsonmeta)
            pixel_size_width = float(result['BinaryResult']['PixelSize']['width'])
            pixel_size_height = float(result['BinaryResult']['PixelSize']['height'])
            #frame_time = float(s.original_metadata.Scan.FrameTime)
            image_metadata = {"Pixel size height (m)": pixel_size_height,"Pixel size width (m)": pixel_size_width}#, "Frame time (s)": frame_time}
            s_metadata.append(image_metadata)
            
        img_lst = []
        imarray = np.array(s)
        img_num = 0
        
        if num_imgs > 1:    
            while img_num < num_imgs:   # Converting the image arrays in Hyperspy format to numpy array, then placing the array in a list
                img_lst.append(imarray[img_num])
                img_num += 1    
            

        ### File saving
            save_input = "Y" # Defaulted to yes
            if save_input == "Y" or save_input == "Yes" or save_input == "yes" or save_input == "y":
                initial_file_name = s_name[0:len(s_name)-len(s_name[s_name.find("."):])]
                initial_file_name = initial_file_name.replace(" ", "_")
                path = str(mydir) + "/" + str(initial_file_name)
                print(path)
                # Check whether the specified path exists or not
                isExist = os.path.exists(path)
                
                if not isExist:
                  # Create a new directory because it does not exist 
                  os.makedirs(path)
                  print("The new directory is created!")
                path = str(path)+"/"+str(initial_file_name)
                with open(str(path)+"_s_metadata.txt", "w") as output:
                    MD_count = 1
                    for i in s_metadata:
                        output.write("["+str(MD_count)+"]"+str(i)+"\n")
                        MD_count += 1
                print("Analyzing image stack...")
                #root.destroy()
            else:
                print("END OF PROGRAM")
                #root.destroy()
                img_num = 0 

            file_ext = ".tif"
            file_dir = path
            for i in img_lst:  
                    img_num += 1
                    imarray = i
                    PIL_image = Image.fromarray(imarray) 
                    PIL_image.save((f"{file_dir}{img_num}{file_ext}"))

        else:   # Dealing with single image EMD files
            PIL_image = Image.fromarray(imarray) 

        ### File saving
            save_input = "Y"
            if save_input == "Y" or save_input == "Yes" or save_input == "yes" or save_input == "y":
                initial_file_name = s_name[0:len(s_name)-len(s_name[s_name.find("."):])]
                initial_file_name = initial_file_name.replace(" ", "_")
                path = str(mydir) + "/" + str(initial_file_name)
                print(path)
                # Check whether the specified path exists or not
                isExist = os.path.exists(path)
                
                if not isExist:
                  # Create a new directory because it does not exist 
                  os.makedirs(path)
                  print("The new directory is created!")
                path = str(path)+"/"+str(initial_file_name)
                with open(str(path)+"_s_metadata.txt", "w") as output:
                    for i in s_metadata:
                        output.write(str(s_metadata)+"\n")
                PIL_image.save((str(path) + ".tif"))
                print("END OF PROGRAM")
                #root.destroy()
            else:
                print("END OF PROGRAM")
                #root.destroy()
            img_num = 0 
                
print("END OF PROGRAM")


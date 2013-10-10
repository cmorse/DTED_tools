# Copyright (c) 2013 Caleb Morse
# Released under the MIT license
# http://opensource.org/licenses/mit-license.php

# Repairs dted level 0, avg, min, and max files which are missing file
# headers or have invalid lat/lon origin values

import fnmatch
import os
import shutil
import sys

# File to use to construct other files
# Must be available as an avg, min, and max file
base_filename = 'dted/e015/s28.'
file_exts = ['avg', 'min', 'max']

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")

for cur_file_ext in file_exts:

  with open(base_filename, 'rb') as ifile:
    # Read a copy of this files headers
    base_file_headers = ifile.read(3428)

  for root, dirnames, filenames in os.walk('dted'):
    for filename in fnmatch.filter(filenames, '*.avg'):
      cur_path = os.path.join(root, filename)
      
      print 'Working on file: ', cur_path 

      cur_path_copy = cur_path + '.bak'
      
      filename, fileext = os.path.splitext(cur_path)

      dt0_filename = filename + '.dt0' 
      
      # Skip this file if it has already been worked on,
      # otherwise make a backup copy of it
      if os.path.isfile(cur_path_copy):
        continue
      else:
        shutil.copy(cur_path, cur_path_copy)
      
      with open(cur_path, 'rb') as ifile:
        if('UHL' == ifile.read(3)):
          # If this file already has the proper headers,
          # then we just need to fix the lon_origin, lat_origin,
          # and orient_angle to be something sane
          with open(dt0_filename, 'rb') as dt0_ifile:
            dt0_ifile.seek(4, 0)
            dt0_lon_origin_to_lat_origin = dt0_ifile.read(16)

            # Start at 80 bytes
            dt0_ifile.seek(80 + 185)
            dt0_lat_origin_to_orient_angle = dt0_ifile.read(88)
            
          with open(cur_path, 'r+b') as ofile:
            ofile.seek(4, 0)
            ofile.write(dt0_lon_origin_to_lat_origin)

            # Start at 80 bytes
            ofile.seek(80 + 185, 0)
            ofile.write(dt0_lat_origin_to_orient_angle)
        else:
          # This file doesn't have the proper headers,
          # Save a copy of its current contents so that they can be appended
          ifile.seek(0, 0)
          orig_file_contents = ifile.read() 

          with open(dt0_filename, 'rb') as dt0_ifile:
            dt0_ifile.seek(4, 0)
            dt0_lon_origin_to_abs_accuracy = dt0_ifile.read(28)

            dt0_ifile.seek(47, 0)
            dt0_num_lat_lines = dt0_ifile.read(4);
            dt0_num_lon_lines = dt0_ifile.read(4);
            dt0_mult_acc = dt0_ifile.read(1);
            
            dt0_num_lon_lines_to_mult_acc = dt0_ifile.read(9)

            # DSI Header: Start at 80 bytes
            dt0_ifile.seek(80 + 64, 0)
            dt0_uniq_ref = dt0_ifile.read(15)

            dt0_ifile.seek(80 + 87, 0)
            dt0_edition_to_prod_code = dt0_ifile.read(23)

            dt0_ifile.seek(80 + 126, 0)
            dt0_prod_spec_to_comp_date = dt0_ifile.read(37)

            dt0_ifile.seek(80 + 185) 
            dt0_lat_origin_to_coverage = dt0_ifile.read(106)

            # ACC Header: Start at 80 + 648 bytes

            dt0_ifile.seek(80 + 648 + 3); 
            dt0_acc_hor_abs_to_multi_acc = dt0_ifile.read(54)
            
          with open(cur_path, 'r+b') as ofile:
            ofile.write(base_file_headers)
            ofile.write(orig_file_contents)

            ofile.seek(4, 0)
            ofile.write(dt0_lon_origin_to_abs_accuracy)

            # Fix lat/lon line counts
            ofile.seek(47, 0)
            
            if int(dt0_num_lat_lines) % 10 == 1 and int(dt0_num_lon_lines) % 10 == 1:
              ofile.write(str(int(dt0_num_lat_lines) - 1).zfill(4))
              ofile.write(str(int(dt0_num_lon_lines) - 1).zfill(4))
            elif int(dt0_num_lat_lines) % 10 == 0 and int(dt0_num_lon_lines) % 10 == 0:
              ofile.write(dt0_num_lat_lines)
              ofile.write(dt0_num_lon_lines)
            else:
              print 'Something weird is going on, these num_lat_lines or num_lon_lines values don\'t make sense.'
              sys.exit(-1)
            ofile.write(dt0_mult_acc)
            

            # DSI Header: Start at 80 bytes
            ofile.seek(80 + 64, 0)
            ofile.write(dt0_uniq_ref)

            ofile.seek(80 + 87, 0)
            ofile.write(dt0_edition_to_prod_code)

            ofile.seek(80 + 126, 0)
            ofile.write(dt0_prod_spec_to_comp_date)

            ofile.seek(80 + 185) 
            ofile.write(dt0_lat_origin_to_coverage)

            ofile.seek(80 + 291)
            reserved5 = " " + cur_file_ext.upper() + " ELEV IN INTERVALS" 
            if len(reserved5) <= 357:
              ofile.write(reserved5)
            else:
              print "Reserved5 field length of " + str(len(reserved5)) + " is too long"
              sys.exit(-1)

            # ACC Header: Start at 80 + 648 bytes
            ofile.seek(80 + 648 + 3); 
            ofile.write(dt0_acc_hor_abs_to_multi_acc)


         


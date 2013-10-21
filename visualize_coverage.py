#!/usr/bin/env python

# Copyright (c) 2013 Caleb Morse
# Released under the MIT license
# http://opensource.org/licenses/mit-license.php

import Image
import sys
import os
import fnmatch
import getopt

def main(argv):
  src_image = 'k_earth.bmp'
  dest_image = 'k_earth_out.bmp'
  dted_path = 'DTED'
  dted_level = 0

  try:
    opt, args = getopt.getopt(argv, 'hd:', ['help', 'src-image=', 'dest-image=', 'dted-level=', 'dted-path='])
    
    if not opt:
      print 'No options supplied'
      usage()
      sys.exit(2)
  
    for o, a in opt:
      if o in ("-h", "--help"):
        usage()
        sys.exit()
      elif o in ("-d", "--dted-level"):
        dted_level = int(a)
      elif o in ("--dted-path"):
        dted_path = str(a)
      elif o in("--src-image"):
        src_image = str(a)
      elif o in ("--dest-image"):
        dest_iamge = str(a)
  
  except getopt.GetoptError, e:
    print e
    usage()
    sys.exit(2)

  file_ext = "*.dt" + str(dted_level)
  
  image = Image.open(src_image)

  size = [image.size[0] / 360, image.size[1] / 180]

  pixels = image.load()

  for root, dirnames, filenames in os.walk(dted_path):
    for filename in fnmatch.filter(filenames, file_ext):
      cur_path = os.path.join(root, filename)

      with open(cur_path, 'rb') as ifile:
        ifile.seek(4, 0)

        lon_origin_hr  = int(ifile.read(3))
        ifile.seek(11, 0)
        lon_origin_hem = ifile.read(1)
        lat_origin_hr  = int(ifile.read(3))
        ifile.seek(19, 0)
        lat_origin_hem = ifile.read(1)

      if lon_origin_hem == 'E':
        lon_origin_hr += 180

      if lon_origin_hem == 'W':
        lon_origin_hr = 180 - lon_origin_hr

      if lat_origin_hem == 'N':
        lat_origin_hr = 90 - lat_origin_hr

      if lat_origin_hem == 'S':
        lat_origin_hr += 90

      for i in range(lon_origin_hr * size[0], lon_origin_hr * size[0] + size[0]):
        for j in range(lat_origin_hr * size[1] - size[1], lat_origin_hr * size[1]):
          pixels[i, j] = (255, 0, 0, 50)

  image.save(dest_image)

def usage():
  usage = """
  Usage: 
    -h --help
    --dted-level DTED level to calculate coverate for
    --dted-path  Path where the DTED files are located
    --src-image  Image to print dted coverage on
    --dest-image Where to save resulting image
  """
  print usage

if __name__ == "__main__":
  main(sys.argv[1:])

#!/usr/bin/env python

# Copyright (c) 2013 Caleb Morse
# Released under the MIT license
# http://opensource.org/licenses/mit-license.php

import Image
import sys
import os
import fnmatch
import optparse

def main(argv):
  parser = optparse.OptionParser()

  parser.add_option("--dted-level",
                    dest = "dted_level",
                    type = "int",
                    help = "DTED level to calculate coverage for.")

  parser.add_option("--dted-path",
                    dest = "dted_path",
                    default = "DTED",
                    type = "string",
                    help = "Path where the DTED files are located..")

  parser.add_option("--src-image",
                    dest = "src_image",
                    default = "k_earth.bmp",
                    type = "string",
                    help = "Image to print dted coverage on.")

  parser.add_option("--dest-image",
                    dest = "dest_image",
                    default = "k_earth_out.bmp",
                    type = "string",
                    help = "Where to save resulting image.")

  options, remainder = parser.parse_args()

  if options.src_image == options.dest_image:
    print 'Cannot save src_image to dest_image'
    sys.exit(-1)

  if options.dted_level < 0 or options.dted_level > 2:
    print 'Invalid dted level ' + options.dted_level
    sys.exit(-1)

  file_ext = "*.dt" + str(options.dted_level)
  
  image = Image.open(options.src_image)

  size = [image.size[0] / 360, image.size[1] / 180]

  pixels = image.load()

  for root, dirnames, filenames in os.walk(options.dted_path):
    for filename in fnmatch.filter(filenames, file_ext):
      lat_origin_hr = int(filename[1:3])
      lat_origin_hem = filename[0:1].upper()
      lon_origin_hr = int(root[-3:])
      lon_origin_hem = root[-4].upper()

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

  image.save(options.dest_image)

if __name__ == "__main__":
  main(sys.argv[1:])


#!/usr/bin/env python

# Copyright (c) 2013 Caleb Morse
# Released under the MIT license
# http://opensource.org/licenses/mit-license.php

import os, sys
import fnmatch
import optparse
import operator

def main(argv):
  parser = optparse.OptionParser()

  parser.add_option("--input-path",
                    dest = "input_path",
                    default = "input_files/",
                    help = "Folder to get the files from.")

  options, remainder = parser.parse_args()

  cur_onc = ''
  cur_lon = ''

  onc_dict = {}

  for root, dirnames, filenames in os.walk(options.input_path):
    for filename in fnmatch.filter(filenames, '*.dir'):
      src_file = os.path.join(root, filename)

      print src_file

      with open(src_file, 'r') as ifile:
        while 1:
          line = ifile.readline()
          if not line:
            break

          line = line.strip()

          if line[0:3] == "ONC": 
            cur_onc = line

            if not onc_dict.has_key(cur_onc):
              onc_dict[cur_onc] = {}

          elif line[0].upper() == "E" or line[0].upper() == "W":
            cur_lon = int(line[1:])
            if line[0].upper() == "W":
              cur_lon *= -1

            if not onc_dict[cur_onc].has_key(cur_lon):
              onc_dict[cur_onc][cur_lon] = []

          elif line[0].upper() == "N" or line[0].upper() == "S":
            cur_lat = int(line[1:3])
            if line[0].upper() == "S":
              cur_lat *= -1 

            if not cur_lat in onc_dict[cur_onc][cur_lon]:
              onc_dict[cur_onc][cur_lon].append(cur_lat)

          else:
            print 'unknown line', line
            sys.exit(-1)

  with open('onc_test.dir', 'w') as ofile:
    for onc_name, lon_dict in sorted(onc_dict.iteritems()):
      ofile.write(onc_name + '\n')
      for lon, lat_list in sorted(lon_dict.iteritems()):
        ofile.write((' ' * 4) + ("W" if lon < 0 else "E") + str(abs(lon)).zfill(3) + '\n')

        for lat in sorted(lat_list):
          ofile.write((' ' * 9) + ("S" if lat < 0 else "N") + str(abs(lat)).zfill(2) + '.dt0\n')

if __name__ == "__main__":
  main(sys.argv[1:])


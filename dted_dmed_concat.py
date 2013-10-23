#!/usr/bin/env python

# Copyright (c) 2013 Caleb Morse
# Released under the MIT license
# http://opensource.org/licenses/mit-license.php

# Merges group of DTED dmed files together

import os, sys
import fnmatch
import optparse

def main(argv):
  parser = optparse.OptionParser()

  parser.add_option("--input-path",
                    dest = "input_path",
                    default = "input_files/",
                    help = "Folder to get the dmed files from.")

  options, remainder = parser.parse_args()

  cur_onc = ''
  cur_lon = ''

  record_list = []

  bound_lat_low  = 90
  bound_lat_high = -90
  bound_lon_low  = 180
  bound_lon_high = -180

  for root, dirnames, filenames in os.walk(options.input_path):
    for filename in fnmatch.filter(filenames, 'dmed*'):
      src_file = os.path.join(root, filename)

      print 'reading file:', src_file

      with open(src_file, 'rb') as f:
        result = f.read(394)

        cur_bound_lat_low  = fix_lat(int(result[1:3]), result[0])
        cur_bound_lat_high = fix_lat(int(result[4:6]), result[3])
        cur_bound_lon_low  = fix_lon(int(result[7:10]), result[6])
        cur_bound_lon_high = fix_lon(int(result[11:14]), result[10])

        if cur_bound_lon_high == -180 and cur_bound_lon_low > cur_bound_lon_high:
          cur_bound_lon_high = abs(cur_bound_lon_high)

        # Expand bounds as necessary
        if cur_bound_lat_low < bound_lat_low:
          bound_lat_low = cur_bound_lat_low

        if cur_bound_lat_high > bound_lat_high:
          bound_lat_high = cur_bound_lat_high

        if cur_bound_lon_low < bound_lon_low:
          bound_lon_low = cur_bound_lon_low

        if cur_bound_lon_high > bound_lon_high:
          bound_lon_high = cur_bound_lon_high

        while 1:
          result = f.read(394)

          if len(result) < 394:
            if len(result) != 0:
              print 'Bad file length'
              sys.exit(-1)
            else:
              break

          if result[0] not in ["N", "S"] and result[3] not in ["E", "W"]:
            print 'Bad offset'
            sys.exit(1)

          record_list.append(result)

  print 'Bounds', bound_lat_low, bound_lat_high, ' ', bound_lon_low, bound_lon_high

  # Get only unique items from the set
  record_list = list(set(record_list))

  with open('dmed_test', 'wb') as ofile:
    ofile.write(get_lat_hem(bound_lat_low)  + str(abs(bound_lat_low )).zfill(2))
    ofile.write(get_lat_hem(bound_lat_high) + str(abs(bound_lat_high)).zfill(2))
    ofile.write(get_lon_hem(bound_lon_low)  + str(abs(bound_lon_low )).zfill(3))

    # For some reason the dmed files wrap to W180 when they get to E180
    if bound_lon_high == 180:
      bound_lon_high *= -1
    ofile.write(get_lon_hem(bound_lon_high) + str(abs(bound_lon_high)).zfill(3))

    ofile.write(' ' * (394 - 14))

    for item in sorted(record_list, cmp=compare):
      ofile.write(item)

def compare(it1, it2):
  it1_lat = fix_lat(int(it1[1:3]), it1[0]) 
  it2_lat = fix_lat(int(it2[1:3]), it2[0]) 

  it1_lon = fix_lon(int(it1[4:7]), it1[3])
  it2_lon = fix_lon(int(it2[4:7]), it2[3])

  if it1_lat < it2_lat:
    return -1
  elif it1_lat > it2_lat:
    return 1
  else:
    if it1_lon < it2_lon:
      return -1
    elif it1_lon > it2_lon:
      return 1
    else:
      print 'wtf222'
      sys.exit(1)

def fix_lat(lat, lat_hem):
  if lat_hem == 'S':
    lat *= -1

  return lat

def fix_lon(lon, lon_hem):
  if lon_hem == 'W':
    lon *= -1

  return lon

def get_lat_hem(lat):
  return 'S' if lat < 0 else 'N'

def get_lon_hem(lon):
  return 'W' if lon < 0 else 'E'

if __name__ == "__main__":
  main(sys.argv[1:])


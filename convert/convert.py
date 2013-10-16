# Copyright (c) 2013 Caleb Morse
# Released under the MIT license
# http://opensource.org/licenses/mit-license.php

# Converts the DEM (.hgt) file format to DTED level 1 
# See: http://dds.cr.usgs.gov/srtm/version1/Documentation/SRTM_Topo.txt

import numpy
import scipy.misc
import fnmatch
from array import *
import os
import sys
import optparse
import struct

options = ''
base_file_headers = ''

def main(argv):
  global options
  global base_file_headers

  # File to use to construct other files
  file_ext    = 'hgt'


  parser = optparse.OptionParser()

  parser.add_option('--overwrite-dest',
                    action = 'store_true',
                    dest = "overwrite_dest",
                    default = False,
                    help = "Overwrite existing dted files.")

  parser.add_option('--ext',
                    dest = "file_ext",
                    default = 'hgt',
                    help = "Source file extensions to use. Comma delimited.")

  parser.add_option('--dted-base-header',
                    dest = "dted_base_header",
                    default = 'base_dt1_headers.bin')
  parser.add_option('--input-path',
                    dest = "input_path",
                    default = 'input_files/',
                    help = "Folder to get the files from.")
  parser.add_option('--output-path',
                    dest = "output_path",
                    default = 'output_files/',
                    help = "Folder to put the files in.")

  options, remainder = parser.parse_args()
  
  # Split, and prepend '*.' to every extension 
  options.file_ext = ['*.' + ext for ext in options.file_ext.split(',')]

  # Read a copy of this files headers
  with open(options.dted_base_header, 'rb') as ifile:
    base_file_headers = ifile.read(3428)

  for root, dirnames, filenames in os.walk(options.input_path):
    for cur_ext in options.file_ext:
      for filename in fnmatch.filter(filenames, cur_ext):
        src_file = os.path.join(root, filename)
        
        latitude_hem  = filename[:1].upper()
        latitude      = int(filename[1:3])
        longitude_hem = filename[3:4].upper()
        longitude     = int(filename[4:7])

        if(latitude_hem != 'S' and latitude_hem != 'N'):
          print 'Bad_hemisphere: ', latitude_hem
          sys.exit();
        elif(latitude < 0 or latitude > 90):
          print 'Bad latitude: ', latitude
          sys.exit()
        elif(longitude_hem != 'E' and longitude_hem != 'W'):
          print 'Bad_hemisphere: ', longitude_hem
          sys.exit();
        elif(longitude < 0 or longitude > 180):
          print 'Bad longitude: ', longitude
          sys.exit()

        if(latitude_hem == 'S'):
          latitude *= -1

        if(longitude_hem == 'W'):
          longitude *= -1

        with open(src_file, 'rb') as ifile:
          ifile.seek(0, os.SEEK_END)

          # Get file size
          file_size = ifile.tell()
          if(file_size == 1201 * 1201 * 2):
            write_file(src_file, 1, latitude, longitude)

          elif (file_size == 3601 * 3601  * 2):
            write_file(src_file, 1, latitude, longitude)

            write_file(src_file, 2, latitude, longitude)

          else:
            print 'Bad filesize', ifile.tell()
            sys.exit()

def write_file(src_file, dted_level, latitude, longitude):

  dest_file = options.output_path + get_dted_filename(latitude, longitude, dted_level)

  print 'starting', 'Working on file: ', src_file, dest_file

  if not options.overwrite_dest and os.path.isfile(dest_file):
    return

  touch(dest_file)

  with open(src_file, 'rb') as ifile:

    ifile.seek(0, os.SEEK_END)
    # Interval and count is the same in lat and lon directions for src 
    if(ifile.tell() == 1201 * 1201 * 2):
      src_count = 1201
      src_interval = 3

    elif (ifile.tell() == 3601 * 3601  * 2):
      src_count = 3601
      src_interval = 1

    else:
      print 'Bad filesize', ifile.tell()
      sys.exit()
    ifile.seek(0)

    
    dted_lon_interval, dted_lon_count = get_dted_details(latitude, dted_level)
    
    dted_lat_interval = src_interval
    dted_lat_count = src_count
    dted_lon_count = ((src_count * 3) / dted_lon_interval) + 1

    with open(dest_file, 'r+b', 80 + 648 + 2700 + dted_record_size(dted_lat_count) * dted_lon_count) as ofile:
      ofile.write(base_file_headers)

      # Write longitude 
      ofile.seek(4, 0)
      ofile.write(str(abs(longitude)).zfill(3) + '0000' + get_lon_hem(longitude))
      # Write latitude 
      ofile.write(str(abs(latitude)).zfill(3)  + '0000' + get_lat_hem(latitude))

      # Write lat and longitude interval
      ofile.write(str(dted_lon_interval * 10).zfill(4))
      ofile.write(str(dted_lat_interval * 10).zfill(4))

      ofile.seek(47, 0)

      # Write lat and longitude count
      ofile.write(str(dted_lon_count).zfill(4))
      ofile.write(str(dted_lat_count).zfill(4))

      # write mult_acc filed
      ofile.write('0')
      

      ofile.seek(80 + 59)
     
      # Write NIMA series indicator
      ofile.write('DTED' + str(dted_level))

      ofile.write(' ' * 15)        # Blank out unique reference section
      ofile.write(str(1).zfill(2)) # Data edition
      ofile.write('A')             # Match/Merge version
      ofile.write('000000000000')  # Maint date, match/merge date, maint descrip code
      ofile.write('USCNIMA')       # Producer code

      ofile.seek(80 + 149, 0)
      ofile.write('SRTM' + (' ' * 6))


      ofile.seek(80 + 185, 0)
      
      # Write lat_origin and lon_origin
      ofile.write(str(abs(latitude )).zfill(2) + '0000.0' + get_lat_hem(latitude))
      ofile.write(str(abs(longitude)).zfill(3) + '0000.0' + get_lon_hem(longitude))

      # Write lat_sw and lon_sw
      ofile.write(str(abs(latitude )).zfill(2) + '0000' + get_lat_hem(latitude))
      ofile.write(str(abs(longitude)).zfill(3) + '0000' + get_lon_hem(longitude))

      # Write lat_nw and lon_nw
      ofile.write(str(abs(latitude + 1)).zfill(2) + '0000' + get_lat_hem(latitude + 1))
      ofile.write(str(abs(longitude   )).zfill(3) + '0000' + get_lon_hem(longitude))

      # Write lat_ne and lon_ne
      ofile.write(str(abs(latitude  + 1)).zfill(2) + '0000' + get_lat_hem(latitude  + 1))
      ofile.write(str(abs(longitude + 1)).zfill(3) + '0000' + get_lon_hem(longitude + 1))

      # Write lat_se and lon_se
      ofile.write(str(abs(latitude     )).zfill(2) + '0000' + get_lat_hem(latitude))
      ofile.write(str(abs(longitude + 1)).zfill(3) + '0000' + get_lon_hem(longitude + 1))

      ofile.seek(80 + 264 + 9)

      # Write lat and longitude interval
      ofile.write(str(dted_lon_interval * 10).zfill(4))
      ofile.write(str(dted_lat_interval * 10).zfill(4))

      # Write lat and longitude count
      ofile.write(str(dted_lon_count).zfill(4))
      ofile.write(str(dted_lat_count).zfill(4))


      ofile.seek(80 + 648 + 55)  
      ofile.write('00') # Mult_acc flag


      # Read all of the values from the source file into memory
      values = array('H')
      for i in range(0, src_count * src_count):
        values.append(struct.unpack(">H", ifile.read(2))[0])

      # Resize the input array if necessary
      if dted_lon_interval != src_interval or dted_lon_count != src_count:
        values = scipy.misc.imresize(numpy.reshape(values, [src_count, src_count]), [dted_lat_count, dted_lon_count])

      record_size = dted_record_size(dted_lat_count)

      for cur_lon_count in range(0, dted_lon_count):
        ofile.seek(80 + 648 + 2700 + record_size * cur_lon_count)
        ofile.write(struct.pack(">I", cur_lon_count))
        ofile.write(struct.pack(">H", cur_lon_count))
        ofile.write(struct.pack("H", 0))

        checksum = 0xAA
        # Don't need to add lat_count because it is always zero
        checksum += (cur_lon_count & 0xFF) + ((cur_lon_count & 0xFF00) >> 8) + ((cur_lon_count & 0xFF0000) >> 16) + \
                    (cur_lon_count & 0xFF) + ((cur_lon_count & 0xFF00) >> 8)

        # Copy all of the bytes over
        for cur_lat_count in range(0, dted_lat_count):
          data = values[cur_lat_count, cur_lon_count] 

          # Add byte to the checkum
          checksum += (data & 0x00FF) + ((data & 0xFF00) >> 8)

          ofile.write(struct.pack(">H", data))

        # Write checksum
        ofile.write(struct.pack(">I", checksum))

      # Write the sentinels
      for cur_lon_count in range(0, dted_lon_count):
        ofile.seek(80 + 648 + 2700 + record_size * cur_lon_count)
        ofile.write('\xAA')

def get_dted_details(latitude, dted_level):
  if latitude >= 80:
    lon_interval = 6

  elif latitude >= 75:
    lon_interval = 4

  elif latitude >= 70:
    lon_interval = 3

  elif latitude >= 50:
    lon_interval = 2

  else:
    lon_interval = 1

  if dted_level == 0:
    lon_interval *= 30 
    lon_count = 121

  elif dted_level == 1:
    lon_interval *= 3 
    lon_count = 1201

  elif dted_level == 2:
    lon_interval *= 1
    lon_count = 3601

  else:
    print 'Bad dted level'
    sys.exit(-1)

  return lon_interval, lon_count

def get_dted_filename(latitude, longitude, dted_level):
  return get_lon_hem(longitude).lower() + (str(abs(longitude)).zfill(3)) + '/' + \
         get_lat_hem(latitude).lower()  + (str(abs(latitude)).zfill(2)) + '.dt' + str(dted_level)

def dted_record_size(lat_count):
  return 12 + (lat_count * 2)


def touch(path):
  folder = os.path.split(path)[0]
  # Make destination folders
  if not os.path.isdir(folder):
    os.makedirs(folder)

  with open(path, 'a'):
    os.utime(path, None)

def get_lat_hem(lat):
  return 'S' if lat < 0 else 'N'

def get_lon_hem(lon):
  return 'W' if lon < 0 else 'E'

if __name__ == "__main__":
  main(sys.argv[1:])


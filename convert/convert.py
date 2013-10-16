# Copyright (c) 2013 Caleb Morse
# Released under the MIT license
# http://opensource.org/licenses/mit-license.php

import numpy
import scipy
import scipy.misc
import fnmatch
from array import *
import os
import shutil
import sys
import getopt
import struct

base_file_headers = ""
output_path = ""

def main(argv):
  global base_file_headers
  global output_path

  dted_level = 1
  # File to use to construct other files
  dted_base_header = 'base_dt1_headers.bin'
  input_path  = 'input_files'
  output_path = 'output_files/'
  file_ext    = 'hgt'

  try:
    opt, args = getopt.getopt(argv, 'hd:', ['help', 'dted-base-header=', 'input-path=', 'output-path='])
  
    for o, a in opt:
      if o in ("-h", "--help"):
        usage()
        sys.exit()
      elif o in ('--dted-base-header'):
        dted_base_header = str(a)
      elif o in ('--input-path'):
        input_path = str(a)
      elif o in ('--output-path'):
        output_path = str(a)
  
  except getopt.GetoptError, e:
    print e
    usage()
    sys.exit(2)

  with open(dted_base_header, 'rb') as ifile:
    # Read a copy of this files headers
    base_file_headers = ifile.read(3428)

  for root, dirnames, filenames in os.walk(input_path):
    for filename in fnmatch.filter(filenames, '*.' + file_ext):
      src_file = os.path.join(root, filename)
      
      print 'Working on file: ', src_file 

      latitude_hem  = filename[:1].upper()
      latitude      = int(filename[1:3])
      longitude_hem = filename[3:4].upper()
      longitude     = int(filename[4:7])

      if(latitude_hem != 'S' and latitude_hem != 'N'):
        print 'Bad_hemisphere: ', latitude_hem
        sys.exit();
      if(latitude < 0 or latitude > 90):
        print 'Bad latitude: ', latitude
        sys.exit()
      if(longitude_hem != 'E' and longitude_hem != 'W'):
        print 'Bad_hemisphere: ', longitude_hem
        sys.exit();
      if(longitude < 0 or longitude > 180):
        print 'Bad longitude: ', longitude
        sys.exit()

      if(latitude_hem == 'S'):
        latitude *= -1

      if(longitude_hem == 'W'):
        longitude *= -1

      with open(src_file, 'rb') as ifile:
        ifile.seek(0, os.SEEK_END)
        if(ifile.tell() == 1201 * 1201 * 2):
          write_file(src_file, 1, latitude, longitude)
          

        elif (ifile.tell() == 3601 * 3601  * 2):
          write_file(src_file, 1, latitude, longitude)

          write_file(src_file, 2, latitude, longitude)

        else:
          print 'Bad filesize', ifile.tell()
          sys.exit()

def write_file(src_file, dted_level, latitude, longitude):

  with open(src_file, 'rb') as ifile:
    ifile.seek(0, os.SEEK_END)
    if(ifile.tell() == 1201 * 1201 * 2):
      src_lat_count = 1201
      src_lon_count = 1201
      src_lat_interval = 3
      src_lon_interval = 3

    elif (ifile.tell() == 3601 * 3601  * 2):
      src_lat_count = 3601
      src_lon_count = 3601
      src_lat_interval = 1
      src_lon_interval = 1

    else:
      print 'Bad filesize', ifile.tell()
      sys.exit()
    ifile.seek(0)

    if(dted_level == 1):
      if (abs(latitude) >= 80):
        dted_lon_interval = 18
      elif (abs(latitude) >= 75):
        dted_lon_interval = 12
      elif (abs(latitude) >= 70):
        dted_lon_interval = 9
      elif (abs(latitude) >= 50):
        dted_lon_interval = 6
      else:
        dted_lon_interval = 3

      dted_lon_count = 1201

    elif (dted_level == 2):
      if (abs(latitude) >= 80):
        dted_lon_interval = 6
      elif (abs(latitude) >= 75):
        dted_lon_interval = 4
      elif (abs(latitude) >= 70):
        dted_lon_interval = 3
      elif (abs(latitude) >= 50):
        dted_lon_interval = 2
      else:
        dted_lon_interval = 1

      dted_lon_count = 3601

    else:
      print 'Bad dted level'
      sys.exit()
    
    dted_lat_interval = src_lat_interval
    dted_lat_count = src_lat_count
    dted_lat_count = ((src_lon_count * 3) / dted_lon_interval) + 1

    if dted_lon_interval != src_lon_interval:
      print 'different interval', dted_lon_interval, src_lon_interval

    dest_file_path = output_path + get_lon_hem(longitude).lower() + (str(abs(longitude)).zfill(3)) + '/'
    dest_file_name = get_lat_hem(latitude).lower() + (str(abs(latitude)).zfill(2)) + '.dt' + str(dted_level) 

    # Make destination folders
    if not os.path.isdir(dest_file_path):
      os.makedirs(dest_file_path)

    print dest_file_path + dest_file_name

    # Make destination folders
    if not os.path.isdir(dest_file_path):
      os.makedirs(dest_file_path)

    touch(dest_file_path + dest_file_name)

    with open(dest_file_path + dest_file_name, 'r+b') as ofile:
      ofile.write(base_file_headers)

      # Write longitude 
      ofile.seek(4, 0)
      ofile.write(str(abs(longitude)).zfill(3))
      ofile.write('0000')
      ofile.write(get_lon_hem(longitude))
      # Write latitude 
      ofile.write(str(abs(latitude)).zfill(3))
      ofile.write('0000')
      ofile.write(get_lat_hem(latitude))

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

      ofile.seek(80 + 126, 0)
      ofile.write('PRF8902B') # Product specification

      ofile.seek(80 + 149, 0)
      ofile.write('SRTM')
      ofile.write(' ' * 6)


      ofile.seek(80 + 185, 0)
      
      # Write lat_origin
      ofile.write(str(abs(latitude)).zfill(2))
      ofile.write('0000.0')
      ofile.write(get_lat_hem(latitude))
      # Write lon_origin
      ofile.write(str(abs(longitude)).zfill(3))
      ofile.write('0000.0')
      ofile.write(get_lon_hem(longitude))

      # Write lat_sw
      ofile.write(str(abs(latitude)).zfill(2))
      ofile.write('0000')
      ofile.write(get_lat_hem(latitude))
      # Write lon_sw
      ofile.write(str(abs(longitude)).zfill(3))
      ofile.write('0000')
      ofile.write(get_lon_hem(longitude))

      # Write lat_nw
      ofile.write(str(abs(latitude + 1)).zfill(2))
      ofile.write('0000')
      ofile.write(get_lat_hem(latitude + 1))
      # Write lon_nw
      ofile.write(str(abs(longitude)).zfill(3))
      ofile.write('0000')
      ofile.write(get_lon_hem(longitude))

      # Write lat_ne
      ofile.write(str(abs(latitude + 1)).zfill(2))
      ofile.write('0000')
      ofile.write(get_lat_hem(latitude + 1))
      # Write lon_ne
      ofile.write(str(abs(longitude + 1)).zfill(3))
      ofile.write('0000')
      ofile.write(get_lon_hem(longitude + 1))

      # Write lat_se
      ofile.write(str(abs(latitude)).zfill(2))
      ofile.write('0000')
      ofile.write(get_lat_hem(latitude))
      # Write lon_se
      ofile.write(str(abs(longitude + 1)).zfill(3))
      ofile.write('0000')
      ofile.write(get_lon_hem(longitude + 1))

      ofile.seek(80 + 264 + 9)

      # Write lat and longitude interval
      ofile.write(str(dted_lon_interval * 10).zfill(4))
      ofile.write(str(dted_lat_interval * 10).zfill(4))

      # Write lat and longitude count
      ofile.write(str(dted_lon_count).zfill(4))
      ofile.write(str(dted_lat_count).zfill(4))


      ofile.seek(80 + 648 + 55)  
      ofile.write('00') # Mult_acc flag

      # Zero out multi_acc portion of header
      ofile.write(' ' * 2643) 

      record_size = (1 + 3 + 2 + 2 + 4 + (dted_lat_count * 2))


      # How many do we need to average?
      interval_diff = dted_lon_interval / src_lon_interval

      if dted_lon_interval != src_lon_interval or src_lon_count != dted_lon_count or src_lat_count != src_lon_count:
        values = array('H')

        for i in range(0, src_lon_count * src_lat_count):
          values.append(struct.unpack(">H", ifile.read(2))[0])

        values = numpy.reshape(values, [src_lat_count, src_lon_count])

        val2 = scipy.misc.imresize(values, [dted_lat_count, dted_lon_count])

        for cur_lon_count in range(0, dted_lon_count):
          ofile.write(struct.pack(">I", cur_lon_count))

          ofile.seek(80 + 648 + 2700 + record_size * cur_lon_count)
          ofile.write('\xAA')

          ofile.seek(3, 1)
          ofile.write(struct.pack(">H", cur_lon_count))
          ofile.write(struct.pack(">H", 0))

          checksum = 0

          # Calculate checksum for row headers
          ofile.seek(80 + 648 + 2700 + record_size * cur_lon_count)
          for i in range(0, 12 - 4):
            # Add byte to the checkum
            checksum += struct.unpack("B", ofile.read(1))[0]

          # Copy all of the bytes over
          for i in range(0, dted_lat_count):
            data = val2[i, cur_lon_count] 

            # Add byte to the checkum
            checksum += (data & 0x00FF) + ((data & 0xFF00) >> 8)

            ofile.write(struct.pack(">H", data))

          # Write checksum
          ofile.write(struct.pack(">I", checksum))

      else:
        for cur_lon_count in range(0, lon_count):
          ofile.write(struct.pack(">I", cur_lon_count))

          ofile.seek(80 + 648 + 2700 + record_size * cur_lon_count)
          ofile.write('\xAA')

          ofile.seek(3, 1)
          ofile.write(struct.pack(">H", cur_lon_count))
          ofile.write(struct.pack(">H", 0))

          checksum = 0

          # Calculate checksum for row headers
          ofile.seek(80 + 648 + 2700 + record_size * cur_lon_count)
          for i in range(0, 12 - 4):
            # Add byte to the checkum
            checksum += struct.unpack("B", ofile.read(1))[0]

          # Copy all of the bytes over
          for i in range(0, lon_count * 2):
            byte = struct.unpack("B", ifile.read(1))[0]

            # Add byte to the checkum
            checksum += byte

            ofile.write(struct.pack("B", byte))

          # Write checksum
          ofile.write(struct.pack(">I", checksum))

          print 'end', ifile.tell()

def touch(path):
  if os.path.isfile(path):
    os.remove(path)

  with open(path, 'a'):
    os.utime(path, None)

def get_lat_hem(lat):
  return 'S' if lat < 0 else 'N'

def get_lon_hem(lon):
  return 'W' if lon < 0 else 'E'

def usage():
  usage = """
  Usage: 
    -h --help
    --dted-base-header  Base DTED headers to use in the conversion 
    --input-path        Folder to get the files from
    --output-path       Folder to put the files in
  """
  print usage

if __name__ == "__main__":
  main(sys.argv[1:])


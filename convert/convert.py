#!/usr/bin/env python

# Copyright (c) 2013 Caleb Morse
# Released under the MIT license
# http://opensource.org/licenses/mit-license.php

# Converts the DEM (.hgt) file format to DTED level 1 or 2
# See: http://dds.cr.usgs.gov/srtm/version1/Documentation/SRTM_Topo.txt

import numpy, scipy.misc
import sys, os, errno
import fnmatch
import optparse
from array import *
import struct
import subprocess
import StringIO, mmap
import time

sys.path.append('..')

import latlon_tools as latlon

options = ''
base_file_headers = ''

def main(argv):
  global options
  global base_file_headers

  parser = optparse.OptionParser()

  parser.add_option("--overwrite-dest",
                    action = "store_true",
                    dest = "overwrite_dest",
                    default = False,
                    help = "Overwrite existing dted files.")

  parser.add_option("--input-compress",
                    dest = "input_compress",
                    default = "",
                    choices = ["", "lz4", "bz2", "gz"],
                    help = "Input files are compressed")

  parser.add_option("--dted-level",
                    dest = "dted_level",
                    type = "int",
                    help = "DTED level to output.")

  parser.add_option("--ext",
                    dest = "file_ext",
                    default = "hgt",
                    type = "string",
                    help = "Source file extensions to use. Comma delimited.")

  parser.add_option("--dted-base-header",
                    dest = "dted_base_header",
                    default = "base_dt1_headers.bin")
  parser.add_option("--input-path",
                    dest = "input_path",
                    default = "input_files/",
                    help = "Folder to get the files from.")
  parser.add_option("--output-path",
                    dest = "output_path",
                    default = "output_files/",
                    help = "Folder to put the files in.")

  options, remainder = parser.parse_args()

  if options.dted_level < 0 or options.dted_level > 2:
    print 'Invalid dted level ' + str(options.dted_level)
    sys.exit(-1)

  # Split, and prepend '*.' to every extension
  options.file_ext = ['*.' + ext for ext in options.file_ext.split(',')]

  if options.input_compress == 'lz4':
    # Check if the lz4 executable is available
    if not which('lz4'):
      print 'lz4 command line tool must be in path'
      sys.exit(-1)

    options.file_ext = [ext + ".lz4" for ext in options.file_ext]

  elif options.input_compress == 'bz2':
    # Check if the bzcat executable is available
    if not which('bzcat'):
      print 'bzcat command line tool must be in path'
      sys.exit(-1)

    options.file_ext = [ext + ".bz2" for ext in options.file_ext]

  elif options.input_compress == 'gz':
    # Check if the zcat executable is available
    if not which('zcat'):
      print 'zcat command line tool must be in path'
      sys.exit(-1)

    options.file_ext = [ext + ".gz" for ext in options.file_ext]


  # Read a copy of this files headers
  with open(options.dted_base_header, 'rb') as ifile:
    base_file_headers = ifile.read(3428)

  for root, dirnames, filenames in os.walk(options.input_path):
    for cur_ext in options.file_ext:
      for filename in fnmatch.filter(filenames, cur_ext):
        src_file = os.path.join(root, filename)

        latitude_hem  = filename[:1].upper()
        latitude      = latlon.fix_lat(int(filename[1:3]), latitude_hem)
        longitude_hem = filename[3:4].upper()
        longitude     = latlon.fix_lon(int(filename[4:7]), longitude_hem)

        if latitude_hem != 'S' and latitude_hem != 'N':
          print 'Bad_hemisphere: ' + latitude_hem
          sys.exit();
        elif latitude < -90 or latitude > 90:
          print 'Bad latitude: ' + str(latitude)
          sys.exit()
        elif longitude_hem != 'E' and longitude_hem != 'W':
          print 'Bad_hemisphere: ' + longitude_hem
          sys.exit();
        elif longitude < -180 or longitude > 180:
          print 'Bad longitude: ' + str(longitude)
          sys.exit()

        dest_file = options.output_path + get_dted_filename(latitude, longitude, options.dted_level)

        if not options.overwrite_dest and os.path.isfile(dest_file):
          continue

        command = ""
        if options.input_compress == "lz4":
          command = "lz4 -d " + src_file + ""

        elif options.input_compress == "bz2":
          command = "bzcat -d " + src_file + ""

        elif options.input_compress == "gz":
          command = "zcat " + src_file + ""


        if command != '':
          ifile = StringIO.StringIO(subprocess.Popen([command], shell=True, stdout=subprocess.PIPE).communicate()[0])

        else:
          ifile = open(src_file, 'rb')

        print 'files: ', src_file, dest_file

        write_file(src_file, dest_file, ifile, latitude, longitude)

def write_file(src_file, dest_file, ifile, latitude, longitude):
  ifile.seek(0, os.SEEK_END)

  dted_level = options.dted_level

  # Interval and count is the same in lat and lon directions for src
  file_size = ifile.tell()
  if file_size == 1201 * 1201 * 2:
    if dted_level > 1:
      print 'DTED level ' + str(dted_level) + ' is too high for this file type.'
      sys.exit(-1)
    src_count = 1201
    src_interval = 3

  elif file_size == 3601 * 3601  * 2:
    src_count = 3601
    src_interval = 1

  else:
    print 'Bad filesize', ifile.tell()
    sys.exit()
  ifile.seek(0)


  dted_lon_interval, dted_lon_count = get_dted_details(latitude, dted_level)

  dted_lat_interval = src_interval
  dted_lat_count = src_count

  if src_interval == dted_lon_interval:
    dted_lon_count = src_count
  else:
    if dted_level == 0:
      dted_lon_count = ((src_count * 30) / dted_lon_interval) + 1
    elif dted_level == 1:
      dted_lon_count = ((src_count * 3)  / dted_lon_interval) + 1
    else:
      dted_lon_count = ((src_count * 1)  / dted_lon_interval) + 1

  # Check again if the file exists
  if not options.overwrite_dest and os.path.isfile(dest_file):
    return

  touch(dest_file)

  error = False
  with open(dest_file, 'r+b') as ofile:
    with open(dest_file, 'wb') as ofile2:
      ofile2.write(base_file_headers)

    try:
      mm = mmap.mmap(ofile.fileno(), 0)
      mm.resize(get_dted_filesize(dted_lat_count, dted_lon_count))

      # Write longitude
      mm.seek(4, 0)
      mm.write(str(abs(longitude)).zfill(3) + '0000' + latlon.get_lon_hem(longitude))
      # Write latitude
      mm.write(str(abs(latitude)).zfill(3)  + '0000' + latlon.get_lat_hem(latitude))

      # Write lat and longitude interval
      mm.write(str(dted_lon_interval * 10).zfill(4))
      mm.write(str(dted_lat_interval * 10).zfill(4))

      mm.seek(47, 0)

      # Write lat and longitude count
      mm.write(str(dted_lon_count).zfill(4))
      mm.write(str(dted_lat_count).zfill(4))

      # write mult_acc filed
      mm.write('0')


      mm.seek(80 + 59)

      # Write NIMA series indicator
      mm.write('DTED' + str(dted_level))

      mm.write(' ' * 15)        # Blank out unique reference section
      mm.write(str(1).zfill(2)) # Data edition
      mm.write('A')             # Match/Merge version
      mm.write('000000000000')  # Maint date, match/merge date, maint descrip code
      mm.write('USCNIMA')       # Producer code

      mm.seek(80 + 149, 0)
      mm.write('SRTM' + (' ' * 6))


      mm.seek(80 + 185, 0)

      # Write lat_origin and lon_origin
      mm.write(str(abs(latitude )).zfill(2) + '0000.0' + latlon.get_lat_hem(latitude))
      mm.write(str(abs(longitude)).zfill(3) + '0000.0' + latlon.get_lon_hem(longitude))

      # Write lat_sw and lon_sw
      mm.write(str(abs(latitude )).zfill(2) + '0000' + latlon.get_lat_hem(latitude))
      mm.write(str(abs(longitude)).zfill(3) + '0000' + latlon.get_lon_hem(longitude))

      # Write lat_nw and lon_nw
      mm.write(str(abs(latitude + 1)).zfill(2) + '0000' + latlon.get_lat_hem(latitude + 1))
      mm.write(str(abs(longitude   )).zfill(3) + '0000' + latlon.get_lon_hem(longitude))

      # Write lat_ne and lon_ne
      mm.write(str(abs(latitude  + 1)).zfill(2) + '0000' + latlon.get_lat_hem(latitude  + 1))
      mm.write(str(abs(longitude + 1)).zfill(3) + '0000' + latlon.get_lon_hem(longitude + 1))

      # Write lat_se and lon_se
      mm.write(str(abs(latitude     )).zfill(2) + '0000' + latlon.get_lat_hem(latitude))
      mm.write(str(abs(longitude + 1)).zfill(3) + '0000' + latlon.get_lon_hem(longitude + 1))

      mm.seek(80 + 264 + 9)

      # Write lat and longitude interval
      mm.write(str(dted_lon_interval * 10).zfill(4))
      mm.write(str(dted_lat_interval * 10).zfill(4))

      # Write lat and longitude count
      mm.write(str(dted_lon_count).zfill(4))
      mm.write(str(dted_lat_count).zfill(4))


      mm.seek(80 + 648 + 55)
      mm.write('00') # Mult_acc flag


      # Read all of the values from the source file into memory
      values = array('>H')

      values.fromstring(ifile.getvalue())

      # Reshape and flip the array so that it matches the DTED order
      values = numpy.flipud(numpy.reshape(values, [src_count, src_count]))

      # Resize the input array if necessary
      if dted_lon_interval != src_interval or dted_lon_count != src_count:
        values = scipy.misc.imresize(values, [dted_lat_count, dted_lon_count])

      record_size = dted_record_size(dted_lat_count)

      start = time.clock()
      for cur_lon_count in range(0, dted_lon_count):
        mm.seek(dted_headersize + record_size * cur_lon_count)

        # Write data block count, longitude count, and latitude count
        mm.write(struct.pack(">IHH", cur_lon_count, cur_lon_count, 0))

        # Don't need to add lat_count because it is always zero
        # Add first two bits from longitude count twice for data block count and longitude count
        # Only the data block count has a 3rd byte
        checksum = 0xAA + ((cur_lon_count & 0xFF) + ((cur_lon_count & 0xFF00) >> 8)) * 2 + ((cur_lon_count & 0xFF0000) >> 16)

        # Current array of values to work with
        cur_arr = values[:, cur_lon_count]

        # Calculate the checksum
        for cur_val in cur_arr:
          checksum += (cur_val & 0x00FF) + ((cur_val & 0xFF00) >> 8)

        # Copy all of the bytes for this row over
        mm.write(struct.pack(">H" * dted_lat_count, *cur_arr))

        # Write checksum
        mm.write(struct.pack(">I", checksum))

      # Write the sentinels
      for cur_lon_count in range(0, dted_lon_count):
        mm.seek(dted_headersize + record_size * cur_lon_count)
        mm.write('\xAA')

      print 'runtime: ', time.clock() - start
    except ValueError:
      print 'Deleting file, error making memory map'
      error = True

  if error:
    os.remove(dest_file)


def get_dted_details(latitude, dted_level):
  latitude = abs(latitude)

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
  return latlon.get_lon_hem(longitude).lower() + (str(abs(longitude)).zfill(3)) + '/' + \
         latlon.get_lat_hem(latitude).lower()  + (str(abs(latitude)).zfill(2)) + '.dt' + str(dted_level)

def get_dted_filesize(lat_count, lon_count):
  return dted_headersize + dted_record_size(lat_count) * lon_count

dted_headersize = 80 + 648 + 2700

def dted_record_size(lat_count):
  return 12 + (lat_count * 2)

# See: http://stackoverflow.com/a/377028/880928
def which(program):
  def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

  fpath, fname = os.path.split(program)
  if fpath:
    if is_exe(program):
      return program
  else:
    for path in os.environ["PATH"].split(os.pathsep):
      path = path.strip('"')
      exe_file = os.path.join(path, program)
      if is_exe(exe_file):
        return exe_file

  return None

def touch(path):
  folder = os.path.split(path)[0]
  # Make destination folders
  if not os.path.isdir(folder):
    # see: http://stackoverflow.com/a/600612/880928
    try:
      os.makedirs(folder)
    except OSError as exc: # Python >2.5
      if exc.errno == errno.EEXIST and os.path.isdir(folder):
        pass
      else:
        raise

  with open(path, 'a'):
    os.utime(path, None)

if __name__ == "__main__":
  main(sys.argv[1:])


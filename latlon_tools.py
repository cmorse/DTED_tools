#!/usr/bin/env python

# Copyright (c) 2013 Caleb Morse
# Released under the MIT license
# http://opensource.org/licenses/mit-license.php

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


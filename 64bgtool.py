#64bgtool
import struct
import os
from sys import argv as argv
xmax = 640
ymax = 480
alpha = open("bg_alpha.rgba","rb").read()
color = open("bg_color.rgba","rb").read()

def _5to8(c):
    return c << 3

def _8to5(c):
    return (c >> 3) & 0x1F

def _8to1(c):
    return (c >> 7) & 0x1

def packto5551(r, g, b, a):
    return (_8to5(r) << 11 | \
            _8to5(g) <<  6 | \
            _8to5(b) <<  1 | \
            _8to1(a) <<  0)

def clamp255(input):
  return 255 if input > 255 else input

def rgba2drive(rgba_buffer, drive_buffer):
  for x in range(640):
    for y in range(480):
      r, g, b, a = struct.unpack_from("BBBB", rgba_buffer, (x + y * 640)*4)
      _64 = packto5551(r, g, b, a)
      struct.pack_into(">H", drive_buffer, (x + y * 640)*2, _64)
         
def rgba2drive_menu(rgba_buffer, drive_buffer):
  # apply overlay
  swap = bytearray(640 * 480 * 4)
  for x in range(640):
    for y in range(480):
      r , g , b ,  a = struct.unpack_from("BBBB", rgba_buffer, (x + y * 640)*4)
      ra, ga, ba, aa = struct.unpack_from("BBBB", alpha, (x + y * 640)*4)
      rc, gc, bc, ac = struct.unpack_from("BBBB", color, (x + y * 640)*4)
      o = ra / 255
      r = clamp255(int(r * (1-o) + o * rc))
      g = clamp255(int(g * (1-o) + o * rc))
      b = clamp255(int(b * (1-o) + o * rc))
      struct.pack_into("BBBB", swap, (x + y * 640)*4, r, g, b, a)
      
  for x in range(640):
    for y in range(480):
      r, g, b, a = struct.unpack_from("BBBB", swap, (x + y * 640)*4)
      nr = _8to5(r)
      ng = _8to5(g)
      nb = _8to5(b)
      er = r - _5to8(nr)
      eg = g - _5to8(ng)
      eb = b - _5to8(nb)
      # set new pixel
      _64 = packto5551(r, g, b, a)
      struct.pack_into(">H", drive_buffer, (x + y * 640)*2, _64)

      #apply quantization error
      if(x < xmax - 1):
        r, g, b, a = struct.unpack_from("BBBB", swap, ((x+1) + (y+0) * xmax)*4)
        struct.pack_into("BBBB", swap, ((x+1) + (y+0) * xmax)*4, \
          clamp255(int(r + er * 7/16)), clamp255(int(g + eg * 7/16)), clamp255(int(b + eb * 7/16)), a)
          
      if(x > 1 and y < ymax - 1):
        r, g, b, a = struct.unpack_from("BBBB", swap, ((x-1) + (y+1) * xmax)*4)
        struct.pack_into("BBBB", swap, ((x-1) + (y+1) * xmax)*4, \
          clamp255(int(r + er * 3/16)), clamp255(int(g + eg * 3/16)), clamp255(int(b + eb * 3/16)), a)
          
      if(y < ymax - 1):
        r, g, b, a = struct.unpack_from("BBBB", swap, ((x) + (y+1) * xmax)*4)
        struct.pack_into("BBBB", swap, ((x) + (y+1) * xmax)*4, \
          clamp255(int(r + er * 5/16)), clamp255(int(g + eg * 5/16)), clamp255(int(b + eb * 5/16)), a)
          
      if(x < xmax - 1 and y < ymax - 1):
        r, g, b, a = struct.unpack_from("BBBB", swap, ((x+1) + (y+1) * xmax)*4)
        struct.pack_into("BBBB", swap, ((x+1) + (y+1) * xmax)*4, \
          clamp255(int(r + er * 1/16)), clamp255(int(g + eg * 1/16)), clamp255(int(b + eb * 1/16)), a)
      #for each y from top to bottom
      #   for each x from left to right
      #      oldpixel  := pixel[x][y]
      #      newpixel  := find_closest_palette_color(oldpixel)
      #      pixel[x][y]  := newpixel
      #      quant_error  := oldpixel - newpixel
      #      pixel[x+1][y  ] := pixel[x+1][y  ] + quant_error * 7/16
      #      pixel[x-1][y+1] := pixel[x-1][y+1] + quant_error * 3/16
      #      pixel[x  ][y+1] := pixel[x  ][y+1] + quant_error * 5/16
      #      pixel[x+1][y+1] := pixel[x+1][y+1] + quant_error * 1/16

def drive2rgba(drive_buffer, rgba_buffer):
  for i in range(int(len(drive_buffer)/2)):
      px = struct.unpack_from(">H", drive_buffer, i * 2)[0]
      
      r = ((px >> 11) & 0x1F) << 3
      g = ((px >> 6) & 0x1F) << 3
      b = ((px >> 1) & 0x1F) << 3
      a = 0xFF if (px & 0x1) else 0
      
      struct.pack_into("BBBB", rgba_buffer, i*4, r, g, b, a)
            
if len(argv) == 1:
  print("\nusage: %s\n\t[-to64drive source.raw output.bin]\n\t[-torgba source.bin output.raw]" \
    % (argv[0]))
  exit(1)

args = argv[1:]
argc = len(args)
for i in range(argc):
  if(args[i] == "-to64drive" and i+2 <= argc):
    source = open(args[i+1],"rb").read()
    output = bytearray(640 * 480 * 2)
    rgba2drive(source, output)
    open(args[i+2], "wb").write(output)

  if(args[i] == "-to64drivemenu" and i+2 <= argc):
    source = open(args[i+1],"rb").read()
    output = bytearray(640 * 480 * 2)
    rgba2drive_menu(source, output)
    open(args[i+2], "wb").write(output)

  if(args[i] == "-torgba" and i+2 <= argc):
    source = open(args[i+1],"rb").read()
    output = bytearray(640 * 480 * 4)
    drive2rgba(source, output)
    open(args[i+2], "wb").write(output)

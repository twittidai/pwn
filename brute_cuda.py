import pycuda.driver as cuda
import pycuda.compiler as cudac
import pycuda.gpuarray as gpuarray
import pycuda.autoinit

import numpy as np
import struct
import binascii
import base64
import sys
import os
from IPython import embed
import time

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

i = 1
msg = np.array([i >> 64] + [i & 0xffffffff] + [0] * 12 + [24], dtype=np.dtype("uint32"))
#print(msg)

def dev_fits(d):
    return d.endian_little

def solve_pow(prefix, bits):

    # prefix input
    prefix = prefix.ljust(((len(prefix) + 3) >> 2) << 2, b"0")
    pref = np.array([int.from_bytes(prefix[i:i + 4], "big") for i in range(0, len(prefix), 4)], np.uint32)

    # output
    res = np.array([0,0,0], "uint32")

    # load program    
    with open("sha256.cu", "r") as f:
        m = cudac.SourceModule(f.read())
    fun = m.get_function("sha256_crypt_kernel")
    
    mask = (0xffffffff << (32 - bits)) & 0xffffffff    

    t = time.time()
    # draufficken
    rnd = 0
    griddimx = 32*80
    blockdimx = 64
    while True:
        fun(np.uint64(rnd), cuda.In(pref), np.uint64(pref.shape[0]), np.uint32(mask), cuda.InOut(res), block=(blockdimx,1,1), grid=(griddimx,1,1))
        if res[0] != 0:
            break
        rnd += 1

    # print(res_np)
    # print(rnd)
    res = prefix + f"{res[1]:04x}{res[2]:04x}{rnd:08x}".encode()
    t = time.time() - t
    print('Time required is {}'.format(t))
    return res


if __name__ == "__main__":
    if len(sys.argv) == 3:
        print(solve_pow(sys.argv[1].encode(), int(sys.argv[2])).decode())

'''Wrapper for bgpdump_attr.h

Generated with:
ctypesgen-read-only/ctypesgen.py -libbgpdump.so bgpdump_attr.h bgpdump_formats.h bgpdump_lib.h -o parser_head.py

Do not modify this file.
'''

__docformat__ =  'restructuredtext'

# Begin preamble

import ctypes, os, sys
from ctypes import *

_int_types = (c_int16, c_int32)
if hasattr(ctypes, 'c_int64'):
    # Some builds of ctypes apparently do not have c_int64
    # defined; it's a pretty good bet that these builds do not
    # have 64-bit pointers.
    _int_types += (c_int64,)
for t in _int_types:
    if sizeof(t) == sizeof(c_size_t):
        c_ptrdiff_t = t
del t
del _int_types

class c_void(Structure):
    # c_void_p is a buggy return type, converting to int, so
    # POINTER(None) == c_void_p is actually written as
    # POINTER(c_void), so it can be treated as a real pointer.
    _fields_ = [('dummy', c_int)]

def POINTER(obj):
    p = ctypes.POINTER(obj)

    # Convert None to a real NULL pointer to work around bugs
    # in how ctypes handles None on 64-bit platforms
    if not isinstance(p.from_param, classmethod):
        def from_param(cls, x):
            if x is None:
                return cls()
            else:
                return x
        p.from_param = classmethod(from_param)

    return p

class UserString:
    def __init__(self, seq):
        if isinstance(seq, basestring):
            self.data = seq
        elif isinstance(seq, UserString):
            self.data = seq.data[:]
        else:
            self.data = str(seq)
    def __str__(self): return str(self.data)
    def __repr__(self): return repr(self.data)
    def __int__(self): return int(self.data)
    def __long__(self): return long(self.data)
    def __float__(self): return float(self.data)
    def __complex__(self): return complex(self.data)
    def __hash__(self): return hash(self.data)

    def __cmp__(self, string):
        if isinstance(string, UserString):
            return cmp(self.data, string.data)
        else:
            return cmp(self.data, string)
    def __contains__(self, char):
        return char in self.data

    def __len__(self): return len(self.data)
    def __getitem__(self, index): return self.__class__(self.data[index])
    def __getslice__(self, start, end):
        start = max(start, 0); end = max(end, 0)
        return self.__class__(self.data[start:end])

    def __add__(self, other):
        if isinstance(other, UserString):
            return self.__class__(self.data + other.data)
        elif isinstance(other, basestring):
            return self.__class__(self.data + other)
        else:
            return self.__class__(self.data + str(other))
    def __radd__(self, other):
        if isinstance(other, basestring):
            return self.__class__(other + self.data)
        else:
            return self.__class__(str(other) + self.data)
    def __mul__(self, n):
        return self.__class__(self.data*n)
    __rmul__ = __mul__
    def __mod__(self, args):
        return self.__class__(self.data % args)

    # the following methods are defined in alphabetical order:
    def capitalize(self): return self.__class__(self.data.capitalize())
    def center(self, width, *args):
        return self.__class__(self.data.center(width, *args))
    def count(self, sub, start=0, end=sys.maxint):
        return self.data.count(sub, start, end)
    def decode(self, encoding=None, errors=None): # XXX improve this?
        if encoding:
            if errors:
                return self.__class__(self.data.decode(encoding, errors))
            else:
                return self.__class__(self.data.decode(encoding))
        else:
            return self.__class__(self.data.decode())
    def encode(self, encoding=None, errors=None): # XXX improve this?
        if encoding:
            if errors:
                return self.__class__(self.data.encode(encoding, errors))
            else:
                return self.__class__(self.data.encode(encoding))
        else:
            return self.__class__(self.data.encode())
    def endswith(self, suffix, start=0, end=sys.maxint):
        return self.data.endswith(suffix, start, end)
    def expandtabs(self, tabsize=8):
        return self.__class__(self.data.expandtabs(tabsize))
    def find(self, sub, start=0, end=sys.maxint):
        return self.data.find(sub, start, end)
    def index(self, sub, start=0, end=sys.maxint):
        return self.data.index(sub, start, end)
    def isalpha(self): return self.data.isalpha()
    def isalnum(self): return self.data.isalnum()
    def isdecimal(self): return self.data.isdecimal()
    def isdigit(self): return self.data.isdigit()
    def islower(self): return self.data.islower()
    def isnumeric(self): return self.data.isnumeric()
    def isspace(self): return self.data.isspace()
    def istitle(self): return self.data.istitle()
    def isupper(self): return self.data.isupper()
    def join(self, seq): return self.data.join(seq)
    def ljust(self, width, *args):
        return self.__class__(self.data.ljust(width, *args))
    def lower(self): return self.__class__(self.data.lower())
    def lstrip(self, chars=None): return self.__class__(self.data.lstrip(chars))
    def partition(self, sep):
        return self.data.partition(sep)
    def replace(self, old, new, maxsplit=-1):
        return self.__class__(self.data.replace(old, new, maxsplit))
    def rfind(self, sub, start=0, end=sys.maxint):
        return self.data.rfind(sub, start, end)
    def rindex(self, sub, start=0, end=sys.maxint):
        return self.data.rindex(sub, start, end)
    def rjust(self, width, *args):
        return self.__class__(self.data.rjust(width, *args))
    def rpartition(self, sep):
        return self.data.rpartition(sep)
    def rstrip(self, chars=None): return self.__class__(self.data.rstrip(chars))
    def split(self, sep=None, maxsplit=-1):
        return self.data.split(sep, maxsplit)
    def rsplit(self, sep=None, maxsplit=-1):
        return self.data.rsplit(sep, maxsplit)
    def splitlines(self, keepends=0): return self.data.splitlines(keepends)
    def startswith(self, prefix, start=0, end=sys.maxint):
        return self.data.startswith(prefix, start, end)
    def strip(self, chars=None): return self.__class__(self.data.strip(chars))
    def swapcase(self): return self.__class__(self.data.swapcase())
    def title(self): return self.__class__(self.data.title())
    def translate(self, *args):
        return self.__class__(self.data.translate(*args))
    def upper(self): return self.__class__(self.data.upper())
    def zfill(self, width): return self.__class__(self.data.zfill(width))

class MutableString(UserString):
    """mutable string objects

    Python strings are immutable objects.  This has the advantage, that
    strings may be used as dictionary keys.  If this property isn't needed
    and you insist on changing string values in place instead, you may cheat
    and use MutableString.

    But the purpose of this class is an educational one: to prevent
    people from inventing their own mutable string class derived
    from UserString and than forget thereby to remove (override) the
    __hash__ method inherited from UserString.  This would lead to
    errors that would be very hard to track down.

    A faster and better solution is to rewrite your program using lists."""
    def __init__(self, string=""):
        self.data = string
    def __hash__(self):
        raise TypeError("unhashable type (it is mutable)")
    def __setitem__(self, index, sub):
        if index < 0:
            index += len(self.data)
        if index < 0 or index >= len(self.data): raise IndexError
        self.data = self.data[:index] + sub + self.data[index+1:]
    def __delitem__(self, index):
        if index < 0:
            index += len(self.data)
        if index < 0 or index >= len(self.data): raise IndexError
        self.data = self.data[:index] + self.data[index+1:]
    def __setslice__(self, start, end, sub):
        start = max(start, 0); end = max(end, 0)
        if isinstance(sub, UserString):
            self.data = self.data[:start]+sub.data+self.data[end:]
        elif isinstance(sub, basestring):
            self.data = self.data[:start]+sub+self.data[end:]
        else:
            self.data =  self.data[:start]+str(sub)+self.data[end:]
    def __delslice__(self, start, end):
        start = max(start, 0); end = max(end, 0)
        self.data = self.data[:start] + self.data[end:]
    def immutable(self):
        return UserString(self.data)
    def __iadd__(self, other):
        if isinstance(other, UserString):
            self.data += other.data
        elif isinstance(other, basestring):
            self.data += other
        else:
            self.data += str(other)
        return self
    def __imul__(self, n):
        self.data *= n
        return self

class String(MutableString, Union):

    _fields_ = [('raw', POINTER(c_char)),
                ('data', c_char_p)]

    def __init__(self, obj=""):
        if isinstance(obj, (str, unicode, UserString)):
            self.data = str(obj)
        else:
            self.raw = obj

    def __len__(self):
        return self.data and len(self.data) or 0

    def from_param(cls, obj):
        # Convert None or 0
        if obj is None or obj == 0:
            return cls(POINTER(c_char)())

        # Convert from String
        elif isinstance(obj, String):
            return obj

        # Convert from str
        elif isinstance(obj, str):
            return cls(obj)

        # Convert from c_char_p
        elif isinstance(obj, c_char_p):
            return obj

        # Convert from POINTER(c_char)
        elif isinstance(obj, POINTER(c_char)):
            return obj

        # Convert from raw pointer
        elif isinstance(obj, int):
            return cls(cast(obj, POINTER(c_char)))

        # Convert from object
        else:
            return String.from_param(obj._as_parameter_)
    from_param = classmethod(from_param)

def ReturnString(obj, func=None, arguments=None):
    return String.from_param(obj)

# As of ctypes 1.0, ctypes does not support custom error-checking
# functions on callbacks, nor does it support custom datatypes on
# callbacks, so we must ensure that all callbacks return
# primitive datatypes.
#
# Non-primitive return values wrapped with UNCHECKED won't be
# typechecked, and will be converted to c_void_p.
def UNCHECKED(type):
    if (hasattr(type, "_type_") and isinstance(type._type_, str)
        and type._type_ != "P"):
        return type
    else:
        return c_void_p

# ctypes doesn't have direct support for variadic functions, so we have to write
# our own wrapper class
class _variadic_function(object):
    def __init__(self,func,restype,argtypes):
        self.func=func
        self.func.restype=restype
        self.argtypes=argtypes
    def _as_parameter_(self):
        # So we can pass this variadic function as a function pointer
        return self.func
    def __call__(self,*args):
        fixed_args=[]
        i=0
        for argtype in self.argtypes:
            # Typecheck what we can
            fixed_args.append(argtype.from_param(args[i]))
            i+=1
        return self.func(*fixed_args+list(args[i:]))

# End preamble

_libs = {}
_libdirs = []

# Begin loader

# ----------------------------------------------------------------------------
# Copyright (c) 2008 David James
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

import os.path, re, sys, glob
import platform
import ctypes
import ctypes.util

def _environ_path(name):
    if name in os.environ:
        return os.environ[name].split(":")
    else:
        return []

class LibraryLoader(object):
    def __init__(self):
        self.other_dirs=[]

    def load_library(self,libname):
        """Given the name of a library, load it."""
        paths = self.getpaths(libname)

        for path in paths:
            if os.path.exists(path):
                return self.load(path)

        raise ImportError("%s not found." % libname)

    def load(self,path):
        """Given a path to a library, load it."""
        try:
            # Darwin requires dlopen to be called with mode RTLD_GLOBAL instead
            # of the default RTLD_LOCAL.  Without this, you end up with
            # libraries not being loadable, resulting in "Symbol not found"
            # errors
            if sys.platform == 'darwin':
                return ctypes.CDLL(path, ctypes.RTLD_GLOBAL)
            else:
                return ctypes.cdll.LoadLibrary(path)
        except OSError,e:
            raise ImportError(e)

    def getpaths(self,libname):
        """Return a list of paths where the library might be found."""
        if os.path.isabs(libname):
            yield libname
        else:
            # FIXME / TODO return '.' and os.path.dirname(__file__)
            for path in self.getplatformpaths(libname):
                yield path

            path = ctypes.util.find_library(libname)
            if path: yield path

    def getplatformpaths(self, libname):
        return []

# Darwin (Mac OS X)

class DarwinLibraryLoader(LibraryLoader):
    name_formats = ["lib%s.dylib", "lib%s.so", "lib%s.bundle", "%s.dylib",
                "%s.so", "%s.bundle", "%s"]

    def getplatformpaths(self,libname):
        if os.path.pathsep in libname:
            names = [libname]
        else:
            names = [format % libname for format in self.name_formats]

        for dir in self.getdirs(libname):
            for name in names:
                yield os.path.join(dir,name)

    def getdirs(self,libname):
        '''Implements the dylib search as specified in Apple documentation:

        http://developer.apple.com/documentation/DeveloperTools/Conceptual/
            DynamicLibraries/Articles/DynamicLibraryUsageGuidelines.html

        Before commencing the standard search, the method first checks
        the bundle's ``Frameworks`` directory if the application is running
        within a bundle (OS X .app).
        '''

        dyld_fallback_library_path = _environ_path("DYLD_FALLBACK_LIBRARY_PATH")
        if not dyld_fallback_library_path:
            dyld_fallback_library_path = [os.path.expanduser('~/lib'),
                                          '/usr/local/lib', '/usr/lib']

        dirs = []

        if '/' in libname:
            dirs.extend(_environ_path("DYLD_LIBRARY_PATH"))
        else:
            dirs.extend(_environ_path("LD_LIBRARY_PATH"))
            dirs.extend(_environ_path("DYLD_LIBRARY_PATH"))

        dirs.extend(self.other_dirs)
        dirs.append(".")
        dirs.append(os.path.dirname(__file__))

        if hasattr(sys, 'frozen') and sys.frozen == 'macosx_app':
            dirs.append(os.path.join(
                os.environ['RESOURCEPATH'],
                '..',
                'Frameworks'))

        dirs.extend(dyld_fallback_library_path)

        return dirs

# Posix

class PosixLibraryLoader(LibraryLoader):
    _ld_so_cache = None

    def _create_ld_so_cache(self):
        # Recreate search path followed by ld.so.  This is going to be
        # slow to build, and incorrect (ld.so uses ld.so.cache, which may
        # not be up-to-date).  Used only as fallback for distros without
        # /sbin/ldconfig.
        #
        # We assume the DT_RPATH and DT_RUNPATH binary sections are omitted.

        directories = []
        for name in ("LD_LIBRARY_PATH",
                     "SHLIB_PATH", # HPUX
                     "LIBPATH", # OS/2, AIX
                     "LIBRARY_PATH", # BE/OS
                    ):
            if name in os.environ:
                directories.extend(os.environ[name].split(os.pathsep))
        directories.extend(self.other_dirs)
        directories.append(".")
        directories.append(os.path.dirname(__file__))

        try: directories.extend([dir.strip() for dir in open('/etc/ld.so.conf')])
        except IOError: pass

        unix_lib_dirs_list = ['/lib', '/usr/lib', '/lib64', '/usr/lib64']
        if sys.platform.startswith('linux'):
            # Try and support multiarch work in Ubuntu
            # https://wiki.ubuntu.com/MultiarchSpec
            bitage = platform.architecture()[0]
            if bitage.startswith('32'):
                # Assume Intel/AMD x86 compat
                unix_lib_dirs_list += ['/lib/i386-linux-gnu', '/usr/lib/i386-linux-gnu']
            elif bitage.startswith('64'):
                # Assume Intel/AMD x86 compat
                unix_lib_dirs_list += ['/lib/x86_64-linux-gnu', '/usr/lib/x86_64-linux-gnu']
            else:
                # guess...
                unix_lib_dirs_list += glob.glob('/lib/*linux-gnu')
        directories.extend(unix_lib_dirs_list)

        cache = {}
        lib_re = re.compile(r'lib(.*)\.s[ol]')
        ext_re = re.compile(r'\.s[ol]$')
        for dir in directories:
            try:
                for path in glob.glob("%s/*.s[ol]*" % dir):
                    file = os.path.basename(path)

                    # Index by filename
                    if file not in cache:
                        cache[file] = path

                    # Index by library name
                    match = lib_re.match(file)
                    if match:
                        library = match.group(1)
                        if library not in cache:
                            cache[library] = path
            except OSError:
                pass

        self._ld_so_cache = cache

    def getplatformpaths(self, libname):
        if self._ld_so_cache is None:
            self._create_ld_so_cache()

        result = self._ld_so_cache.get(libname)
        if result: yield result

        path = ctypes.util.find_library(libname)
        if path: yield os.path.join("/lib",path)

# Windows

class _WindowsLibrary(object):
    def __init__(self, path):
        self.cdll = ctypes.cdll.LoadLibrary(path)
        self.windll = ctypes.windll.LoadLibrary(path)

    def __getattr__(self, name):
        try: return getattr(self.cdll,name)
        except AttributeError:
            try: return getattr(self.windll,name)
            except AttributeError:
                raise

class WindowsLibraryLoader(LibraryLoader):
    name_formats = ["%s.dll", "lib%s.dll", "%slib.dll"]

    def load_library(self, libname):
        try:
            result = LibraryLoader.load_library(self, libname)
        except ImportError:
            result = None
            if os.path.sep not in libname:
                for name in self.name_formats:
                    try:
                        result = getattr(ctypes.cdll, name % libname)
                        if result:
                            break
                    except WindowsError:
                        result = None
            if result is None:
                try:
                    result = getattr(ctypes.cdll, libname)
                except WindowsError:
                    result = None
            if result is None:
                raise ImportError("%s not found." % libname)
        return result

    def load(self, path):
        return _WindowsLibrary(path)

    def getplatformpaths(self, libname):
        if os.path.sep not in libname:
            for name in self.name_formats:
                dll_in_current_dir = os.path.abspath(name % libname)
                if os.path.exists(dll_in_current_dir):
                    yield dll_in_current_dir
                path = ctypes.util.find_library(name % libname)
                if path:
                    yield path

# Platform switching

# If your value of sys.platform does not appear in this dict, please contact
# the Ctypesgen maintainers.

loaderclass = {
    "darwin":   DarwinLibraryLoader,
    "cygwin":   WindowsLibraryLoader,
    "win32":    WindowsLibraryLoader
}

loader = loaderclass.get(sys.platform, PosixLibraryLoader)()

def add_library_search_dirs(other_dirs):
    loader.other_dirs = other_dirs

load_library = loader.load_library

del loaderclass

# End loader

add_library_search_dirs([])

# Begin libraries

_libs["libbgpdump.so"] = load_library("libbgpdump.so")

# 1 libraries
# End libraries

# No modules

__u_char = c_ubyte # /usr/include/x86_64-linux-gnu/bits/types.h: 31

__time_t = c_long # /usr/include/x86_64-linux-gnu/bits/types.h: 149

__caddr_t = String # /usr/include/x86_64-linux-gnu/bits/types.h: 186

u_char = __u_char # /usr/include/x86_64-linux-gnu/sys/types.h: 34

caddr_t = __caddr_t # /usr/include/x86_64-linux-gnu/sys/types.h: 117

time_t = __time_t # /usr/include/time.h: 76

u_int8_t = c_uint8 # /usr/include/x86_64-linux-gnu/sys/types.h: 174

u_int16_t = c_uint16 # /usr/include/x86_64-linux-gnu/sys/types.h: 175

u_int32_t = c_uint32 # /usr/include/x86_64-linux-gnu/sys/types.h: 176

in_addr_t = c_uint32 # /usr/include/netinet/in.h: 141

# /usr/include/netinet/in.h: 142
class struct_in_addr(Structure):
    pass

struct_in_addr.__slots__ = [
    's_addr',
]
struct_in_addr._fields_ = [
    ('s_addr', in_addr_t),
]

# /usr/include/netinet/in.h: 200
class union_anon_20(Union):
    pass

union_anon_20.__slots__ = [
    '__u6_addr8',
    '__u6_addr16',
    '__u6_addr32',
]
union_anon_20._fields_ = [
    ('__u6_addr8', c_uint8 * 16),
    ('__u6_addr16', c_uint16 * 8),
    ('__u6_addr32', c_uint32 * 4),
]

# /usr/include/netinet/in.h: 198
class struct_in6_addr(Structure):
    pass

struct_in6_addr.__slots__ = [
    '__in6_u',
]
struct_in6_addr._fields_ = [
    ('__in6_u', union_anon_20),
]

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 101
class struct_unknown_attr(Structure):
    pass

struct_unknown_attr.__slots__ = [
    'flag',
    'type',
    'len',
    'raw',
]
struct_unknown_attr._fields_ = [
    ('flag', c_int),
    ('type', c_int),
    ('len', c_int),
    ('raw', POINTER(u_char)),
]

as_t = u_int32_t # /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 109

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 112
class struct_attr(Structure):
    pass

attributes_t = struct_attr # /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 111

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 158
class struct_cluster_list(Structure):
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 170
class struct_aspath(Structure):
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 151
class struct_community(Structure):
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 130
class struct_ecommunity(Structure):
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 164
class struct_transit(Structure):
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 186
class struct_mp_info(Structure):
    pass

struct_attr.__slots__ = [
    'flag',
    'origin',
    'nexthop',
    'med',
    'local_pref',
    'aggregator_as',
    'aggregator_addr',
    'weight',
    'originator_id',
    'cluster',
    'aspath',
    'community',
    'ecommunity',
    'transit',
    'mp_info',
    'len',
    'data',
    'unknown_num',
    'unknown',
    'new_aspath',
    'old_aspath',
    'new_aggregator_as',
    'old_aggregator_as',
    'new_aggregator_addr',
    'old_aggregator_addr',
]
struct_attr._fields_ = [
    ('flag', u_int32_t),
    ('origin', c_int),
    ('nexthop', struct_in_addr),
    ('med', u_int32_t),
    ('local_pref', u_int32_t),
    ('aggregator_as', as_t),
    ('aggregator_addr', struct_in_addr),
    ('weight', u_int32_t),
    ('originator_id', struct_in_addr),
    ('cluster', POINTER(struct_cluster_list)),
    ('aspath', POINTER(struct_aspath)),
    ('community', POINTER(struct_community)),
    ('ecommunity', POINTER(struct_ecommunity)),
    ('transit', POINTER(struct_transit)),
    ('mp_info', POINTER(struct_mp_info)),
    ('len', u_int16_t),
    ('data', caddr_t),
    ('unknown_num', u_int16_t),
    ('unknown', POINTER(struct_unknown_attr)),
    ('new_aspath', POINTER(struct_aspath)),
    ('old_aspath', POINTER(struct_aspath)),
    ('new_aggregator_as', as_t),
    ('old_aggregator_as', as_t),
    ('new_aggregator_addr', struct_in_addr),
    ('old_aggregator_addr', struct_in_addr),
]

struct_community.__slots__ = [
    'size',
    'val',
    'str',
]
struct_community._fields_ = [
    ('size', c_int),
    ('val', POINTER(u_int32_t)),
    ('str', String),
]

struct_cluster_list.__slots__ = [
    'length',
    'list',
]
struct_cluster_list._fields_ = [
    ('length', c_int),
    ('list', POINTER(struct_in_addr)),
]

struct_transit.__slots__ = [
    'length',
    'val',
]
struct_transit._fields_ = [
    ('length', c_int),
    ('val', POINTER(u_char)),
]

struct_aspath.__slots__ = [
    'asn_len',
    'length',
    'count',
    'data',
    'str',
]
struct_aspath._fields_ = [
    ('asn_len', u_int8_t),
    ('length', c_int),
    ('count', c_int),
    ('data', caddr_t),
    ('str', String),
]

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 179
class struct_assegment(Structure):
    pass

struct_assegment.__slots__ = [
    'type',
    'length',
    'data',
]
struct_assegment._fields_ = [
    ('type', u_char),
    ('length', u_char),
    ('data', c_char * 0),
]

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 216
class struct_mp_nlri(Structure):
    pass

struct_mp_info.__slots__ = [
    'withdraw',
    'announce',
]
struct_mp_info._fields_ = [
    ('withdraw', (POINTER(struct_mp_nlri) * (3 + 1)) * (1 + 1)),
    ('announce', (POINTER(struct_mp_nlri) * (3 + 1)) * (1 + 1)),
]

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 200
class union_union_BGPDUMP_IP_ADDRESS(Union):
    pass

union_union_BGPDUMP_IP_ADDRESS.__slots__ = [
    'v4_addr',
    'v6_addr',
]
union_union_BGPDUMP_IP_ADDRESS._fields_ = [
    ('v4_addr', struct_in_addr),
    ('v6_addr', struct_in6_addr),
]

BGPDUMP_IP_ADDRESS = union_union_BGPDUMP_IP_ADDRESS # /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 200

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 210
class struct_prefix(Structure):
    pass

struct_prefix.__slots__ = [
    'address',
    'len',
]
struct_prefix._fields_ = [
    ('address', BGPDUMP_IP_ADDRESS),
    ('len', u_char),
]

struct_mp_nlri.__slots__ = [
    'nexthop_len',
    'nexthop',
    'nexthop_local',
    'prefix_count',
    'nlri',
]
struct_mp_nlri._fields_ = [
    ('nexthop_len', u_char),
    ('nexthop', BGPDUMP_IP_ADDRESS),
    ('nexthop_local', BGPDUMP_IP_ADDRESS),
    ('prefix_count', u_int16_t),
    ('nlri', struct_prefix * 1000),
]

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 100
class struct_struct_BGPDUMP_MRTD_MESSAGE(Structure):
    pass

struct_struct_BGPDUMP_MRTD_MESSAGE.__slots__ = [
    'source_as',
    'source_ip',
    'destination_as',
    'destination_ip',
    'bgp_message',
]
struct_struct_BGPDUMP_MRTD_MESSAGE._fields_ = [
    ('source_as', u_int16_t),
    ('source_ip', struct_in_addr),
    ('destination_as', u_int16_t),
    ('destination_ip', struct_in_addr),
    ('bgp_message', POINTER(u_char)),
]

BGPDUMP_MRTD_MESSAGE = struct_struct_BGPDUMP_MRTD_MESSAGE # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 100

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 112
class struct_struct_BGPDUMP_MRTD_TABLE_DUMP(Structure):
    pass

struct_struct_BGPDUMP_MRTD_TABLE_DUMP.__slots__ = [
    'view',
    'sequence',
    'prefix',
    'mask',
    'status',
    'uptime',
    'peer_ip',
    'peer_as',
    'attr_len',
]
struct_struct_BGPDUMP_MRTD_TABLE_DUMP._fields_ = [
    ('view', u_int16_t),
    ('sequence', u_int16_t),
    ('prefix', BGPDUMP_IP_ADDRESS),
    ('mask', u_char),
    ('status', u_char),
    ('uptime', time_t),
    ('peer_ip', BGPDUMP_IP_ADDRESS),
    ('peer_as', as_t),
    ('attr_len', u_int16_t),
]

BGPDUMP_MRTD_TABLE_DUMP = struct_struct_BGPDUMP_MRTD_TABLE_DUMP # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 112

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 120
class struct_struct_BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE_ENTRY(Structure):
    pass

struct_struct_BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE_ENTRY.__slots__ = [
    'afi',
    'peer_ip',
    'peer_bgp_id',
    'peer_as',
]
struct_struct_BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE_ENTRY._fields_ = [
    ('afi', u_char),
    ('peer_ip', BGPDUMP_IP_ADDRESS),
    ('peer_bgp_id', struct_in_addr),
    ('peer_as', as_t),
]

BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE_ENTRY = struct_struct_BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE_ENTRY # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 120

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 127
class struct_struct_BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE(Structure):
    pass

struct_struct_BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE.__slots__ = [
    'local_bgp_id',
    'view_name',
    'peer_count',
    'entries',
]
struct_struct_BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE._fields_ = [
    ('local_bgp_id', struct_in_addr),
    ('view_name', c_char * 255),
    ('peer_count', c_uint16),
    ('entries', POINTER(BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE_ENTRY)),
]

BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE = struct_struct_BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 127

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 134
class struct_struct_BGPDUMP_TABLE_DUMP_V2_ROUTE_ENTRY(Structure):
    pass

struct_struct_BGPDUMP_TABLE_DUMP_V2_ROUTE_ENTRY.__slots__ = [
    'peer_index',
    'originated_time',
    'peer',
    'attr',
]
struct_struct_BGPDUMP_TABLE_DUMP_V2_ROUTE_ENTRY._fields_ = [
    ('peer_index', c_uint16),
    ('originated_time', c_uint32),
    ('peer', POINTER(BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE_ENTRY)),
    ('attr', POINTER(attributes_t)),
]

BGPDUMP_TABLE_DUMP_V2_ROUTE_ENTRY = struct_struct_BGPDUMP_TABLE_DUMP_V2_ROUTE_ENTRY # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 134

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 144
class struct_struct_BGPDUMP_TABLE_DUMP_V2_PREFIX(Structure):
    pass

struct_struct_BGPDUMP_TABLE_DUMP_V2_PREFIX.__slots__ = [
    'seq',
    'afi',
    'safi',
    'prefix_length',
    'prefix',
    'entry_count',
    'entries',
]
struct_struct_BGPDUMP_TABLE_DUMP_V2_PREFIX._fields_ = [
    ('seq', c_uint32),
    ('afi', c_uint16),
    ('safi', c_uint8),
    ('prefix_length', u_char),
    ('prefix', BGPDUMP_IP_ADDRESS),
    ('entry_count', c_uint16),
    ('entries', POINTER(BGPDUMP_TABLE_DUMP_V2_ROUTE_ENTRY)),
]

BGPDUMP_TABLE_DUMP_V2_PREFIX = struct_struct_BGPDUMP_TABLE_DUMP_V2_PREFIX # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 144

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 158
class struct_struct_BGPDUMP_ZEBRA_STATE_CHANGE(Structure):
    pass

struct_struct_BGPDUMP_ZEBRA_STATE_CHANGE.__slots__ = [
    'source_as',
    'destination_as',
    'interface_index',
    'address_family',
    'source_ip',
    'destination_ip',
    'old_state',
    'new_state',
]
struct_struct_BGPDUMP_ZEBRA_STATE_CHANGE._fields_ = [
    ('source_as', as_t),
    ('destination_as', as_t),
    ('interface_index', u_int16_t),
    ('address_family', u_int16_t),
    ('source_ip', BGPDUMP_IP_ADDRESS),
    ('destination_ip', BGPDUMP_IP_ADDRESS),
    ('old_state', u_int16_t),
    ('new_state', u_int16_t),
]

BGPDUMP_ZEBRA_STATE_CHANGE = struct_struct_BGPDUMP_ZEBRA_STATE_CHANGE # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 158

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 160
class struct_zebra_incomplete(Structure):
    pass

struct_zebra_incomplete.__slots__ = [
    'afi',
    'orig_len',
    'prefix',
]
struct_zebra_incomplete._fields_ = [
    ('afi', u_int16_t),
    ('orig_len', u_int8_t),
    ('prefix', struct_prefix),
]

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 204
class struct_struct_BGPDUMP_ZEBRA_MESSAGE(Structure):
    pass

struct_struct_BGPDUMP_ZEBRA_MESSAGE.__slots__ = [
    'source_as',
    'destination_as',
    'interface_index',
    'address_family',
    'source_ip',
    'destination_ip',
    'size',
    'type',
    'version',
    'my_as',
    'hold_time',
    'bgp_id',
    'opt_len',
    'opt_data',
    'withdraw_count',
    'announce_count',
    'withdraw',
    'announce',
    'cut_bytes',
    'incomplete',
    'error_code',
    'sub_error_code',
    'notify_len',
    'notify_data',
]
struct_struct_BGPDUMP_ZEBRA_MESSAGE._fields_ = [
    ('source_as', as_t),
    ('destination_as', as_t),
    ('interface_index', u_int16_t),
    ('address_family', u_int16_t),
    ('source_ip', BGPDUMP_IP_ADDRESS),
    ('destination_ip', BGPDUMP_IP_ADDRESS),
    ('size', u_int16_t),
    ('type', u_char),
    ('version', u_char),
    ('my_as', as_t),
    ('hold_time', u_int16_t),
    ('bgp_id', struct_in_addr),
    ('opt_len', u_char),
    ('opt_data', POINTER(u_char)),
    ('withdraw_count', u_int16_t),
    ('announce_count', u_int16_t),
    ('withdraw', struct_prefix * 1000),
    ('announce', struct_prefix * 1000),
    ('cut_bytes', u_int16_t),
    ('incomplete', struct_zebra_incomplete),
    ('error_code', u_char),
    ('sub_error_code', u_char),
    ('notify_len', u_int16_t),
    ('notify_data', POINTER(u_char)),
]

BGPDUMP_ZEBRA_MESSAGE = struct_struct_BGPDUMP_ZEBRA_MESSAGE # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 204

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 218
class struct_struct_BGPDUMP_ZEBRA_ENTRY(Structure):
    pass

struct_struct_BGPDUMP_ZEBRA_ENTRY.__slots__ = [
    'view',
    'status',
    'time_last_change',
    'address_family',
    'SAFI',
    'next_hop_len',
    'prefix_length',
    'address_prefix',
    'empty',
    'bgp_atribute',
]
struct_struct_BGPDUMP_ZEBRA_ENTRY._fields_ = [
    ('view', u_int16_t),
    ('status', u_int16_t),
    ('time_last_change', time_t),
    ('address_family', u_int16_t),
    ('SAFI', u_char),
    ('next_hop_len', u_char),
    ('prefix_length', u_char),
    ('address_prefix', POINTER(u_char)),
    ('empty', u_int16_t),
    ('bgp_atribute', POINTER(u_char)),
]

BGPDUMP_ZEBRA_ENTRY = struct_struct_BGPDUMP_ZEBRA_ENTRY # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 218

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 224
class struct_struct_BGPDUMP_ZEBRA_SNAPSHOT(Structure):
    pass

struct_struct_BGPDUMP_ZEBRA_SNAPSHOT.__slots__ = [
    'view',
    'file',
]
struct_struct_BGPDUMP_ZEBRA_SNAPSHOT._fields_ = [
    ('view', u_int16_t),
    ('file', u_int16_t),
]

BGPDUMP_ZEBRA_SNAPSHOT = struct_struct_BGPDUMP_ZEBRA_SNAPSHOT # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 224

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 235
class union_union_BGPDUMP_BODY(Union):
    pass

union_union_BGPDUMP_BODY.__slots__ = [
    'mrtd_message',
    'mrtd_table_dump',
    'mrtd_table_dump_v2_peer_table',
    'mrtd_table_dump_v2_prefix',
    'zebra_state_change',
    'zebra_message',
    'zebra_entry',
    'zebra_snapshot',
]
union_union_BGPDUMP_BODY._fields_ = [
    ('mrtd_message', BGPDUMP_MRTD_MESSAGE),
    ('mrtd_table_dump', BGPDUMP_MRTD_TABLE_DUMP),
    ('mrtd_table_dump_v2_peer_table', BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE),
    ('mrtd_table_dump_v2_prefix', BGPDUMP_TABLE_DUMP_V2_PREFIX),
    ('zebra_state_change', BGPDUMP_ZEBRA_STATE_CHANGE),
    ('zebra_message', BGPDUMP_ZEBRA_MESSAGE),
    ('zebra_entry', BGPDUMP_ZEBRA_ENTRY),
    ('zebra_snapshot', BGPDUMP_ZEBRA_SNAPSHOT),
]

BGPDUMP_BODY = union_union_BGPDUMP_BODY # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 235

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 245
class struct_struct_BGPDUMP_ENTRY(Structure):
    pass

struct_struct_BGPDUMP_ENTRY.__slots__ = [
    'time',
    'type',
    'subtype',
    'length',
    'attr',
    'body',
]
struct_struct_BGPDUMP_ENTRY._fields_ = [
    ('time', time_t),
    ('type', u_int16_t),
    ('subtype', u_int16_t),
    ('length', u_int32_t),
    ('attr', POINTER(attributes_t)),
    ('body', BGPDUMP_BODY),
]

BGPDUMP_ENTRY = struct_struct_BGPDUMP_ENTRY # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 245

# /home/leo/git/hiwi/distrace/parser/bgpdump_lib.h: 43
class struct__CFRFILE(Structure):
    pass

CFRFILE = struct__CFRFILE # /home/leo/git/hiwi/distrace/parser/bgpdump_lib.h: 43

# /home/leo/git/hiwi/distrace/parser/bgpdump_lib.h: 53
class struct_struct_BGPDUMP(Structure):
    pass

struct_struct_BGPDUMP.__slots__ = [
    'f',
    'f_type',
    'eof',
    'filename',
    'parsed',
    'parsed_ok',
]
struct_struct_BGPDUMP._fields_ = [
    ('f', POINTER(CFRFILE)),
    ('f_type', c_int),
    ('eof', c_int),
    ('filename', c_char * 1024),
    ('parsed', c_int),
    ('parsed_ok', c_int),
]

BGPDUMP = struct_struct_BGPDUMP # /home/leo/git/hiwi/distrace/parser/bgpdump_lib.h: 53

# /home/leo/git/hiwi/distrace/parser/bgpdump_lib.h: 57
for _lib in _libs.itervalues():
    if not hasattr(_lib, 'bgpdump_open_dump'):
        continue
    bgpdump_open_dump = _lib.bgpdump_open_dump
    bgpdump_open_dump.argtypes = [String]
    bgpdump_open_dump.restype = POINTER(BGPDUMP)
    break

# /home/leo/git/hiwi/distrace/parser/bgpdump_lib.h: 58
for _lib in _libs.itervalues():
    if not hasattr(_lib, 'bgpdump_close_dump'):
        continue
    bgpdump_close_dump = _lib.bgpdump_close_dump
    bgpdump_close_dump.argtypes = [POINTER(BGPDUMP)]
    bgpdump_close_dump.restype = None
    break

# /home/leo/git/hiwi/distrace/parser/bgpdump_lib.h: 59
for _lib in _libs.itervalues():
    if not hasattr(_lib, 'bgpdump_read_next'):
        continue
    bgpdump_read_next = _lib.bgpdump_read_next
    bgpdump_read_next.argtypes = [POINTER(BGPDUMP)]
    bgpdump_read_next.restype = POINTER(BGPDUMP_ENTRY)
    break

# /home/leo/git/hiwi/distrace/parser/bgpdump_lib.h: 60
for _lib in _libs.itervalues():
    if not hasattr(_lib, 'bgpdump_free_mem'):
        continue
    bgpdump_free_mem = _lib.bgpdump_free_mem
    bgpdump_free_mem.argtypes = [POINTER(BGPDUMP_ENTRY)]
    bgpdump_free_mem.restype = None
    break

# /home/leo/git/hiwi/distrace/parser/bgpdump_lib.h: 62
for _lib in _libs.itervalues():
    if not hasattr(_lib, 'bgpdump_version'):
        continue
    bgpdump_version = _lib.bgpdump_version
    bgpdump_version.argtypes = []
    if sizeof(c_int) == sizeof(c_void_p):
        bgpdump_version.restype = ReturnString
    else:
        bgpdump_version.restype = String
        bgpdump_version.errcheck = ReturnString
    break

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 35
try:
    BGP_ATTR_FLAG_OPTIONAL = 128
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 36
try:
    BGP_ATTR_FLAG_TRANS = 64
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 37
try:
    BGP_ATTR_FLAG_PARTIAL = 32
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 38
try:
    BGP_ATTR_FLAG_EXTLEN = 16
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 41
try:
    BGP_ATTR_ORIGIN = 1
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 42
try:
    BGP_ATTR_AS_PATH = 2
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 43
try:
    BGP_ATTR_NEXT_HOP = 3
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 44
try:
    BGP_ATTR_MULTI_EXIT_DISC = 4
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 45
try:
    BGP_ATTR_LOCAL_PREF = 5
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 46
try:
    BGP_ATTR_ATOMIC_AGGREGATE = 6
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 47
try:
    BGP_ATTR_AGGREGATOR = 7
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 48
try:
    BGP_ATTR_COMMUNITIES = 8
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 49
try:
    BGP_ATTR_ORIGINATOR_ID = 9
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 50
try:
    BGP_ATTR_CLUSTER_LIST = 10
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 51
try:
    BGP_ATTR_DPA = 11
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 52
try:
    BGP_ATTR_ADVERTISER = 12
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 53
try:
    BGP_ATTR_RCID_PATH = 13
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 54
try:
    BGP_ATTR_MP_REACH_NLRI = 14
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 55
try:
    BGP_ATTR_MP_UNREACH_NLRI = 15
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 56
try:
    BGP_ATTR_EXT_COMMUNITIES = 16
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 57
try:
    BGP_ATTR_NEW_AS_PATH = 17
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 58
try:
    BGP_ATTR_NEW_AGGREGATOR = 18
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 61
def ATTR_FLAG_BIT(X):
    return (1 << (X - 1))

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 64
try:
    AS_HEADER_SIZE = 2
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 66
try:
    AS_SET = 1
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 67
try:
    AS_SEQUENCE = 2
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 68
try:
    AS_CONFED_SEQUENCE = 3
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 69
try:
    AS_CONFED_SET = 4
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 71
try:
    AS_SEG_START = 0
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 72
try:
    AS_SEG_END = 1
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 74
try:
    ASPATH_STR_DEFAULT_LEN = 32
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 75
try:
    ASPATH_STR_ERROR = '! Error !'
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 79
try:
    COMMUNITY_NO_EXPORT = 4294967041
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 80
try:
    COMMUNITY_NO_ADVERTISE = 4294967042
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 81
try:
    COMMUNITY_NO_EXPORT_SUBCONFED = 4294967043
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 82
try:
    COMMUNITY_LOCAL_AS = 4294967043
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 84
def com_nthval(X, n):
    return (((X.contents.val).value) + n)

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 92
try:
    AFI_IP = 1
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 93
try:
    BGPDUMP_MAX_AFI = AFI_IP
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 96
try:
    SAFI_UNICAST = 1
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 97
try:
    SAFI_MULTICAST = 2
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 98
try:
    SAFI_UNICAST_MULTICAST = 3
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 99
try:
    BGPDUMP_MAX_SAFI = SAFI_UNICAST_MULTICAST
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 203
try:
    BGPDUMP_ADDRSTRLEN = 46
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 205
try:
    ASN16_LEN = sizeof(u_int16_t)
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 206
try:
    ASN32_LEN = sizeof(u_int32_t)
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 208
try:
    AS_TRAN = 23456
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 215
try:
    MAX_PREFIXES = 1000
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 39
try:
    BGPDUMP_TYPE_MRTD_BGP = 5
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 40
try:
    BGPDUMP_SUBTYPE_MRTD_BGP_NULL = 0
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 41
try:
    BGPDUMP_SUBTYPE_MRTD_BGP_PREFUPDATE = 1
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 42
try:
    BGPDUMP_SUBTYPE_MRTD_BGP_UPDATE = 2
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 43
try:
    BGPDUMP_SUBTYPE_MRTD_BGP_STATE_CHANGE = 3
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 44
try:
    BGPDUMP_SUBTYPE_MRTD_BGP_SYNC = 4
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 45
try:
    BGPDUMP_SUBTYPE_MRTD_BGP_OPEN = 129
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 46
try:
    BGPDUMP_SUBTYPE_MRTD_BGP_NOTIFICATION = 131
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 47
try:
    BGPDUMP_SUBTYPE_MRTD_BGP_KEEPALIVE = 132
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 48
try:
    BGPDUMP_SUBTYPE_MRTD_BGP_ROUT_REFRESH = 133
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 50
try:
    BGPDUMP_TYPE_MRTD_TABLE_DUMP = 12
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 51
try:
    BGPDUMP_SUBTYPE_MRTD_TABLE_DUMP_AFI_IP = 1
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 52
try:
    BGPDUMP_SUBTYPE_MRTD_TABLE_DUMP_AFI_IP6 = 2
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 53
try:
    BGPDUMP_SUBTYPE_MRTD_TABLE_DUMP_AFI_IP_32BIT_AS = 3
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 54
try:
    BGPDUMP_SUBTYPE_MRTD_TABLE_DUMP_AFI_IP6_32BIT_AS = 4
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 56
try:
    BGPDUMP_TYPE_TABLE_DUMP_V2 = 13
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 57
try:
    BGPDUMP_SUBTYPE_TABLE_DUMP_V2_PEER_INDEX_TABLE = 1
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 58
try:
    BGPDUMP_SUBTYPE_TABLE_DUMP_V2_RIB_IPV4_UNICAST = 2
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 59
try:
    BGPDUMP_SUBTYPE_TABLE_DUMP_V2_RIB_IPV4_MULTICAST = 3
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 60
try:
    BGPDUMP_SUBTYPE_TABLE_DUMP_V2_RIB_IPV6_UNICAST = 4
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 61
try:
    BGPDUMP_SUBTYPE_TABLE_DUMP_V2_RIB_IPV6_MULTICAST = 5
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 62
try:
    BGPDUMP_SUBTYPE_TABLE_DUMP_V2_RIB_GENERIC = 6
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 63
try:
    BGPDUMP_PEERTYPE_TABLE_DUMP_V2_AFI_IP = 0
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 64
try:
    BGPDUMP_PEERTYPE_TABLE_DUMP_V2_AFI_IP6 = 1
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 65
try:
    BGPDUMP_PEERTYPE_TABLE_DUMP_V2_AS2 = 0
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 66
try:
    BGPDUMP_PEERTYPE_TABLE_DUMP_V2_AS4 = 2
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 67
try:
    BGPDUMP_TYPE_TABLE_DUMP_V2_MAX_VIEWNAME_LEN = 255
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 70
try:
    BGPDUMP_TYPE_ZEBRA_BGP = 16
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 71
try:
    BGPDUMP_SUBTYPE_ZEBRA_BGP_STATE_CHANGE = 0
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 72
try:
    BGPDUMP_SUBTYPE_ZEBRA_BGP_MESSAGE = 1
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 73
try:
    BGPDUMP_SUBTYPE_ZEBRA_BGP_ENTRY = 2
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 74
try:
    BGPDUMP_SUBTYPE_ZEBRA_BGP_SNAPSHOT = 3
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 75
try:
    BGPDUMP_SUBTYPE_ZEBRA_BGP_MESSAGE_AS4 = 4
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 76
try:
    BGPDUMP_SUBTYPE_ZEBRA_BGP_STATE_CHANGE_AS4 = 5
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 79
try:
    BGP_STATE_IDLE = 1
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 80
try:
    BGP_STATE_CONNECT = 2
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 81
try:
    BGP_STATE_ACTIVE = 3
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 82
try:
    BGP_STATE_OPENSENT = 4
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 83
try:
    BGP_STATE_OPENCONFIRM = 5
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 84
try:
    BGP_STATE_ESTABLISHED = 6
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 87
try:
    BGP_MSG_OPEN = 1
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 88
try:
    BGP_MSG_UPDATE = 2
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 89
try:
    BGP_MSG_NOTIFY = 3
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 90
try:
    BGP_MSG_KEEPALIVE = 4
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 91
try:
    BGP_MSG_ROUTE_REFRESH_01 = 5
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 92
try:
    BGP_MSG_ROUTE_REFRESH = 128
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_lib.h: 38
try:
    BGPDUMP_MAX_FILE_LEN = 1024
except:
    pass

# /home/leo/git/hiwi/distrace/parser/bgpdump_lib.h: 39
try:
    BGPDUMP_MAX_AS_PATH_LEN = 2000
except:
    pass

unknown_attr = struct_unknown_attr # /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 101

attr = struct_attr # /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 112

cluster_list = struct_cluster_list # /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 158

aspath = struct_aspath # /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 170

community = struct_community # /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 151

ecommunity = struct_ecommunity # /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 130

transit = struct_transit # /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 164

mp_info = struct_mp_info # /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 186

assegment = struct_assegment # /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 179

mp_nlri = struct_mp_nlri # /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 216

union_BGPDUMP_IP_ADDRESS = union_union_BGPDUMP_IP_ADDRESS # /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 200

prefix = struct_prefix # /home/leo/git/hiwi/distrace/parser/bgpdump_attr.h: 210

struct_BGPDUMP_MRTD_MESSAGE = struct_struct_BGPDUMP_MRTD_MESSAGE # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 100

struct_BGPDUMP_MRTD_TABLE_DUMP = struct_struct_BGPDUMP_MRTD_TABLE_DUMP # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 112

struct_BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE_ENTRY = struct_struct_BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE_ENTRY # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 120

struct_BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE = struct_struct_BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 127

struct_BGPDUMP_TABLE_DUMP_V2_ROUTE_ENTRY = struct_struct_BGPDUMP_TABLE_DUMP_V2_ROUTE_ENTRY # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 134

struct_BGPDUMP_TABLE_DUMP_V2_PREFIX = struct_struct_BGPDUMP_TABLE_DUMP_V2_PREFIX # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 144

struct_BGPDUMP_ZEBRA_STATE_CHANGE = struct_struct_BGPDUMP_ZEBRA_STATE_CHANGE # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 158

zebra_incomplete = struct_zebra_incomplete # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 160

struct_BGPDUMP_ZEBRA_MESSAGE = struct_struct_BGPDUMP_ZEBRA_MESSAGE # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 204

struct_BGPDUMP_ZEBRA_ENTRY = struct_struct_BGPDUMP_ZEBRA_ENTRY # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 218

struct_BGPDUMP_ZEBRA_SNAPSHOT = struct_struct_BGPDUMP_ZEBRA_SNAPSHOT # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 224

union_BGPDUMP_BODY = union_union_BGPDUMP_BODY # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 235

struct_BGPDUMP_ENTRY = struct_struct_BGPDUMP_ENTRY # /home/leo/git/hiwi/distrace/parser/bgpdump_formats.h: 245

_CFRFILE = struct__CFRFILE # /home/leo/git/hiwi/distrace/parser/bgpdump_lib.h: 43

struct_BGPDUMP = struct_struct_BGPDUMP # /home/leo/git/hiwi/distrace/parser/bgpdump_lib.h: 53

# No inserted files


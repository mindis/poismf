from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import numpy
from sys import platform
import os

## Note: As of the end of 2018, MSVC is still stuck with OpenMP 2.0 (released 2002), which does not support
## parallel for loops with unsigend iterators. If you are using a different compiler, this part can be safely removed
if platform[:3] == "win":
    import re
    fout = open("temp1.txt", "w")
    with open("poismf\\pmf.pyx", "r") as fin:
            for line in fin:
                    fout.write(re.sub("size_t([^\w])", "long\\1", line))
    fout.close()
    fout = open("temp2.txt", "w")
    with open("poismf\\pgd.c", "r") as fin:
            for line in fin:
                    fout.write(re.sub("size_t([^\w])", "long\\1", line))
    fout.close()

    fout = open("poismf\\pmf.pyx", "w")
    with open("temp1.txt", "r") as fin:
            for line in fin:
                    fout.write(line)
    fout.close()
    fout = open("poismf\\pgd.c", "w")
    with open("temp2.txt", "r") as fin:
            for line in fin:
                    fout.write(line)
    fout.close()

## https://stackoverflow.com/questions/52905458/link-cython-wrapped-c-functions-against-blas-from-numpy
err_msg = "Could not locate BLAS library - you'll need to manually modify setup.py to add its path."
try:
    blas_path = numpy.distutils.system_info.get_info('blas')['library_dirs'][0]
except:
    if "library_dirs" in numpy.__config__.blas_mkl_info:
        blas_path = numpy.__config__.blas_mkl_info["library_dirs"][0]
    elif "library_dirs" in numpy.__config__.blas_opt_info:
        blas_path = numpy.__config__.blas_opt_info["library_dirs"][0]
    else:
        raise ValueError(err_msg)


if platform[:3] == "win":
    if os.path.exists(os.path.join(blas_path, "mkl_rt.lib")):
        blas_file = "mkl_rt.lib"
    elif os.path.exists(os.path.join(blas_path, "mkl_rt.dll")):
        blas_file = "mkl_rt.dll"
    else:
        import re
        blas_file = [f for f in os.listdir(blas_path) if bool(re.search("blas", f))]
        if len(blas_file) == 0:
            raise ValueError(err_msg)
        blas_file = blas_file[0]

elif platform[:3] == "dar":
    if os.path.exists(os.path.join(blas_path, "libblas.dylib")):
        blas_file = "libblas.dylib"
    elif os.path.exists(os.path.join(blas_path, "libmkl_rt.dylib")):
        blas_file = "libmkl_rt.dylib"
    else:
        import re
        blas_file = [f for f in os.listdir(blas_path) if bool(re.search("blas", f))]
        if len(blas_file) == 0:
            raise ValueError("Could not locate BLAS library.")
        blas_file = blas_file[0]
else:
    if os.path.exists(os.path.join(blas_path, "libblas.so")):
        blas_file = "libblas.so"
    elif os.path.exists(os.path.join(blas_path, "libmkl_rt.so")):
        blas_file = "libmkl_rt.so"
    else:
        import re
        blas_file = [f for f in os.listdir(blas_path) if bool(re.search("blas", f))]
        if len(blas_file) == 0:
            raise ValueError(err_msg)
        blas_file = blas_file[0]

## https://stackoverflow.com/questions/724664/python-distutils-how-to-get-a-compiler-that-is-going-to-be-used
class build_ext_subclass( build_ext ):
    def build_extensions(self):
        compiler = self.compiler.compiler_type
        if compiler == 'msvc': # visual studio
            for e in self.extensions:
                e.extra_link_args += [os.path.join(blas_path, blas_file)]
                e.extra_compile_args += ['/O2', '/openmp']
        else: # gcc
            for e in self.extensions:
                e.extra_link_args += ["-L"+blas_path, "-l:"+blas_file]
                e.extra_compile_args += ['-O2', '-fopenmp', '-march=native']
                e.extra_link_args += ['-fopenmp']
        build_ext.build_extensions(self)


setup(
    name  = "poismf",
    packages = ["poismf"],
    author = 'David Cortes',
    url = 'https://github.com/david-cortes/poismf',
    cmdclass = {'build_ext': build_ext_subclass},
    ext_modules = [Extension("poismf", sources=["poismf/pmf.pyx"], include_dirs=[numpy.get_include()], extra_link_args=[], extra_compile_args=['-std=c99'])]
    )

{ pkgs }: {
  deps = [
    pkgs.python310
    pkgs.python310Packages.pip
    pkgs.cmake
    pkgs.gcc
    pkgs.libgcc
    pkgs.blas
    pkgs.lapack
    pkgs.libGL
    pkgs.libGLU
    pkgs.glib
    pkgs.pkg-config
  ];
}

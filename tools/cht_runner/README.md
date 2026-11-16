# SCAJ-30007 Windows runner

This build uses the pinned ps2-web-recomp runtime and its software renderer
with an SDL2 window. It is independent of the release launcher's Vulkan build.

Use CMake 3.24+, a Clang-based Windows x64 C++20 toolchain, Python with the
project's Python dependencies, and the SDL2 Windows x64 development package.
Keep the game input, generated code and build output in ignored directories.

From the repository root, with the donor at commit
`1b4808793a12c45125262fd2d5f50a9ec9f7c020`:

```powershell
New-Item -ItemType Directory -Force private/cht-build
python scripts/cht_elf.py '<SCAJ-30007 ISO>' private/cht-build/SCAJ_300.07.elf
& '<eerecomp.exe built from the pinned donor>' private/cht-build/SCAJ_300.07.elf --out private/cht-build/generated
cmake -S tools/cht_runner -B private/cht-build/build -G Ninja -DGT4_DONOR="$PWD/private/references/ps2-web-recomp" -DPS2_GENERATED="$PWD/private/cht-build/generated" -DSDL2_DIR="<SDL2 cmake directory>" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS=-msse4.1
cmake --build private/cht-build/build --target gt4-cht
& private/cht-build/build/gt4-cht.exe private/cht-build/SCAJ_300.07.elf --disc '<SCAJ-30007 ISO>' --window
```

Arrow keys navigate. X is Circle, Z is Cross, and Enter is Start.
Use archive tools compatible with the compiler's Windows object format. For
the Zig 0.15.2 build, CMake detected the system MinGW archive tools. If linking
reports unresolved symbols from both donor archives, index them with
`zig ranlib private/cht-build/build/donor/libps2game.a
private/cht-build/build/donor/libps2runtime.a` and rerun the build.

For an automated smoke test, omit `--window` and use `--frames 2300
--press 600:circle:12 --press 760:right:12 --press 790:circle:12
--press 1400:start:12`. Add `--frames-dir` pointing to an existing directory
to capture frames.

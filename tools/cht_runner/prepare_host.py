"""Prepare the pinned donor's SDL host for the SCAJ-30007 Windows runner."""

import argparse
from pathlib import Path


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"unexpected donor host source at {old!r}")
    return source.replace(old, new, 1)


def prepare(donor, output):
    host = donor / "host"
    output.mkdir(parents=True, exist_ok=True)
    main = (host / "main.cpp").read_text(encoding="utf-8")
    main = replace_once(main, "std::vector<std::string> args{argv[1]};",
                        r'std::vector<std::string> args{"cdrom0:\\SCAJ_300.07;1"};')
    main = replace_once(main, "    std::string load_path;",
                        "    ps2::g_options.pal = false;\n    ps2::g_options.rate_forced = true;\n"
                        "    std::string load_path;")
    window = (host / "window.cpp").read_text(encoding="utf-8")
    window = replace_once(window, "#include <sys/resource.h>\n#include <unistd.h>",
                          "#define WIN32_LEAN_AND_MEAN\n#define NOMINMAX\n"
                          "#include <windows.h>\n#include <psapi.h>")
    start = window.index("double process_cpu_seconds() {")
    end = window.index("void show_speed() {", start)
    window = window[:start] + """double process_cpu_seconds() {
    FILETIME created{}, exited{}, kernel{}, user{};
    if (!GetProcessTimes(GetCurrentProcess(), &created, &exited, &kernel, &user)) return 0;
    const auto ticks = [](const FILETIME &time) {
        return (static_cast<std::uint64_t>(time.dwHighDateTime) << 32) | time.dwLowDateTime;
    };
    return static_cast<double>(ticks(kernel) + ticks(user)) / 1e7;
}

double resident_mb() {
    PROCESS_MEMORY_COUNTERS counters{};
    if (!GetProcessMemoryInfo(GetCurrentProcess(), &counters, sizeof counters)) return 0;
    return static_cast<double>(counters.WorkingSetSize) / (1024.0 * 1024.0);
}

""" + window[end:]
    window = replace_once(window, "bool open_window(bool fullscreen) {",
                          "bool open_window(bool fullscreen) {\n    SDL_SetMainReady();")
    window = window.replace("ps2-web-recomp", "GT4 SCAJ-30007")
    for name, content in {"main.cpp": main, "window.cpp": window,
                          "window.hpp": (host / "window.hpp").read_text(encoding="utf-8")}.items():
        (output / name).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("donor", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    prepare(args.donor, args.output)

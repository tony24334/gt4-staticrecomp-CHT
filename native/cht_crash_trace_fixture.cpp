#include "cht_crash_trace.hpp"
#include "ps2/memory.hpp"
#include <cstdlib>
#include <cstring>
#include <string>
namespace ps2 { std::uint8_t g_ram[kRamSize]; std::uint8_t g_spr[kScratchpadSize]; }
static void require(bool condition, const char *message) {
  if (!condition) { std::fprintf(stderr, "FAIL: %s\n", message); std::exit(1); }
}
int main() {
  using namespace gt4::cht_trace;
  Ring<3> ring;
  for (unsigned i = 0; i < 8; ++i) { Event e; e.argument = i; ring.push(e); }
  require(ring.size() == 3 && ring.total == 8, "ring stays bounded");
  for (unsigned i = 0; i < 3; ++i) require(ring.oldest(i).argument == i + 5 && ring.oldest(i).sequence == i + 5, "ring chronological after wrap");
  std::uint8_t ram[64]{}; std::uint8_t scratch[16]{};
  ram[60] = 0x12; scratch[12] = 0x34;
  Memory memory{ram, sizeof ram, scratch, sizeof scratch}; std::uint32_t value = 0;
  require(read_word(memory, 60, value) && value == 0x12, "last RAM word");
  require(read_word(memory, 0x8000003c, value) && value == 0x12, "RAM alias");
  require(read_word(memory, 0x7000000c, value) && value == 0x34, "scratch word");
  for (auto address : {UINT64_C(61), UINT64_C(0x10000000), UINT64_C(0x7000000d), UINT64_C(0x100000000), UINT64_C(0xfffffff0) + 28})
    require(!read_word(memory, address, value), "reject crossing/wrapped/unmapped/MMIO read");
  ps2::Cpu cpu{}; ps2::ThreadContext saved{};
  reset(); cpu.r[4].w[0] = 0xfffffff0u; entry(cpu);
  interrupt_enter(cpu, 0x1234); target(cpu, 0); interrupt_exit(cpu, 0x1234); restored(cpu, saved);
  cpu.r[1].w[0] = 7; restored(cpu, saved);
  auto *file = std::tmpfile(); require(file != nullptr, "trace capture file"); dump(file); std::rewind(file);
  std::string text; char bytes[1024]; std::size_t count;
  while ((count = std::fread(bytes, 1, sizeof bytes, file))) text.append(bytes, count);
  std::fclose(file);
  require(text.find("object=FFFFFFF0 member=00000000 table=00000000 target=00000000") != std::string::npos, "invalid object recorded without dereference");
  require(text.find("callback-restored") != std::string::npos && text.find("flags=2") != std::string::npos, "restoration mismatch recorded");
  std::puts("PASS: bounded chronological trace, safe memory observation, restore validation");
}

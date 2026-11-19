#include "cht_crash_trace.hpp"
#include "ps2/memory.hpp"
#include <cstring>
#include <cstdlib>
namespace gt4::cht_trace {
namespace {
Ring<512> history;
std::array<std::uint32_t, 32> handlers{};
std::uint32_t nesting{};
bool announced{};
Memory memory() { return {ps2::g_ram, ps2::kRamSize, ps2::g_spr, ps2::kScratchpadSize}; }
Event capture(const ps2::Cpu &cpu, const char *kind) {
  if (!announced) { std::fprintf(stderr, "[cht-trace] enabled v1 capacity=512; observing guest callbacks and 0x00387968\n"); announced = true; }
  Event event; event.kind = kind; event.pc = cpu.pc; event.status = cpu.cop0[12];
  event.nesting = nesting; event.handler = nesting && nesting <= handlers.size() ? handlers[nesting - 1] : 0;
  for (unsigned i = 0; i != 32; ++i) event.registers[i] = cpu.r[i].w[0];
  return event;
}
}
bool read_word(Memory memory, std::uint64_t address, std::uint32_t &value) {
  // Observe only actual backed ranges, never invoke guest accessors or touch MMIO.
  if (address > UINT32_MAX) return false;
  auto physical = static_cast<std::uint32_t>(address);
  if (physical >= 0x80000000u && physical < 0xC0000000u) physical &= 0x1FFFFFFFu;
  else if ((physical >> 28) == 2 || (physical >> 28) == 3) physical &= 0x0FFFFFFFu;
  const std::uint8_t *bytes = nullptr;
  if (memory.ram && memory.ram_size >= 4 && physical <= memory.ram_size - 4) bytes = memory.ram + physical;
  else if (memory.scratch && address >= ps2::kScratchpadBase && memory.scratch_size >= 4 &&
           address - ps2::kScratchpadBase <= memory.scratch_size - 4) bytes = memory.scratch + (address - ps2::kScratchpadBase);
  if (!bytes) return false;
  value = static_cast<std::uint32_t>(bytes[0]) | (static_cast<std::uint32_t>(bytes[1]) << 8) |
          (static_cast<std::uint32_t>(bytes[2]) << 16) | (static_cast<std::uint32_t>(bytes[3]) << 24);
  return true;
}
void entry(const ps2::Cpu &cpu) {
  auto event = capture(cpu, "entry-00387968"); event.object = cpu.r[4].w[0];
  if (read_word(memory(), static_cast<std::uint64_t>(event.object) + 28, event.member)) {
    event.flags |= 1;
    if (read_word(memory(), event.member, event.table)) {
      event.flags |= 2;
      if (read_word(memory(), static_cast<std::uint64_t>(event.table) + 20, event.target)) event.flags |= 4;
    }
  }
  history.push(event);
}
void target(const ps2::Cpu &cpu, std::uint32_t destination) {
  auto event = capture(cpu, "jalr-00387984"); event.argument = destination; history.push(event);
}
void interrupt_enter(const ps2::Cpu &cpu, std::uint32_t address) {
  auto event = capture(cpu, "callback-enter"); event.argument = address; history.push(event);
  if (nesting < handlers.size()) handlers[nesting] = address;
  ++nesting;
}
void interrupt_exit(const ps2::Cpu &cpu, std::uint32_t address) {
  auto event = capture(cpu, "callback-exit"); event.argument = address; history.push(event);
}
void restored(const ps2::Cpu &cpu, const ps2::ThreadContext &saved, std::uint32_t expected_status) {
  auto event = capture(cpu, "callback-restored");
  if (cpu.pc != saved.pc) event.flags |= 1;
  if (std::memcmp(cpu.r, saved.r, sizeof saved.r)) event.flags |= 2;
  if (std::memcmp(&cpu.hi, &saved.hi, sizeof saved.hi) || std::memcmp(&cpu.lo, &saved.lo, sizeof saved.lo) || cpu.sa != saved.sa) event.flags |= 4;
  if (std::memcmp(cpu.f, saved.f, sizeof saved.f) || cpu.facc != saved.facc || cpu.fcr31 != saved.fcr31) event.flags |= 8;
  if (cpu.cop0[12] != expected_status) event.flags |= 16;
  history.push(event);
  if (nesting) --nesting;
}
static void write_dump(std::FILE *output) {
  std::fprintf(output, "[cht-trace] BEGIN v1 total=%llu kept=%zu (pc is dispatcher state; entry/jalr labels identify instructions)\n",
               static_cast<unsigned long long>(history.total), history.size());
  for (std::size_t i = 0; i < history.size(); ++i) {
    const auto &e = history.oldest(i);
    std::fprintf(output, "[cht-trace] #%llu %s pc=%08X arg=%08X handler=%08X nesting=%u flags=%X status=%08X object=%08X member=%08X table=%08X target=%08X\n",
      static_cast<unsigned long long>(e.sequence), e.kind, e.pc, e.argument, e.handler, e.nesting, e.flags, e.status, e.object, e.member, e.table, e.target);
    for (unsigned r = 0; r < 32; r += 8) {
      std::fprintf(output, "[cht-trace] r%02u", r);
      for (unsigned j = 0; j < 8; ++j) std::fprintf(output, " %08X", e.registers[r + j]);
      std::fputc('\n', output);
    }
  }
  std::fprintf(output, "[cht-trace] END entry flags=readable member/table/target bits 1/2/4; restored flags=mismatch PC/GPR/HI-LO-SA/FPU/status bits 1/2/4/8/16\n");
  std::fflush(output);
}
void dump(std::FILE *output) {
  write_dump(output);
  if (const char *path = std::getenv("GT4_CHT_CRASH_TRACE_FILE")) {
    if (*path) {
      if (auto *file = std::fopen(path, "w")) { write_dump(file); std::fclose(file); }
      else std::fprintf(output, "[cht-trace] could not open dedicated trace file\n");
    }
  }
}
void reset() { history = {}; handlers = {}; nesting = 0; announced = false; }
} // namespace gt4::cht_trace

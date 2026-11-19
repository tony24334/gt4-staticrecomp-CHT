#pragma once
#include "ps2/system.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
namespace gt4::cht_trace {
struct Memory {
  const std::uint8_t *ram; std::size_t ram_size;
  const std::uint8_t *scratch; std::size_t scratch_size;
};
bool read_word(Memory memory, std::uint64_t address, std::uint32_t &value);
struct Event {
  std::uint64_t sequence{};
  const char *kind{};
  std::uint32_t pc{}, argument{}, handler{}, nesting{}, flags{}, status{};
  std::array<std::uint32_t, 32> registers{};
  std::uint32_t object{}, member{}, table{}, target{};
};
template <std::size_t Capacity> struct Ring {
  std::array<Event, Capacity> events{};
  std::uint64_t total{};
  void push(Event event) { event.sequence = total; events[total++ % Capacity] = event; }
  std::size_t size() const { return total < Capacity ? static_cast<std::size_t>(total) : Capacity; }
  const Event &oldest(std::size_t offset) const { return events[(total - size() + offset) % Capacity]; }
};
void entry(const ps2::Cpu &cpu);
void target(const ps2::Cpu &cpu, std::uint32_t destination);
void interrupt_enter(const ps2::Cpu &cpu, std::uint32_t address);
void interrupt_exit(const ps2::Cpu &cpu, std::uint32_t address);
void restored(const ps2::Cpu &cpu, const ps2::ThreadContext &saved, std::uint32_t expected_status = 0);
void dump(std::FILE *output);
void reset();
} // namespace gt4::cht_trace

// TASK-174: SCAJ-30007 address table and guest-RAM write rules.
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

#include "game_target.hpp"
#include "race_display.hpp"
#include "race_widescreen.hpp"

namespace {

int failures = 0;

void expect(bool condition, const char *what) {
  if (condition) return;
  std::fprintf(stderr, "cht_hooks: FAILED %s\n", what);
  ++failures;
}

void put32(std::vector<std::uint8_t> &ram, std::uint32_t address, std::uint32_t value) {
  std::memcpy(ram.data() + address, &value, sizeof value);
}

std::uint32_t get32(const std::vector<std::uint8_t> &ram, std::uint32_t address) {
  std::uint32_t value = 0;
  std::memcpy(&value, ram.data() + address, sizeof value);
  return value;
}

void putf(std::vector<std::uint8_t> &ram, std::uint32_t address, float value) {
  std::memcpy(ram.data() + address, &value, sizeof value);
}

void write_record(std::vector<std::uint8_t> &ram, std::uint32_t address, float width, float height) {
  for (std::uint32_t offset = 0; offset < 44u; offset += 4u) put32(ram, address + offset, 0u);
  putf(ram, address + 0xCu, width);
  putf(ram, address + 0x10u, height);
}

void check_widescreen_and_display_holds() {
  using namespace gt4::target;
  std::vector<std::uint8_t> ram(32u << 20, 0u);
  write_record(ram, kChtHooks.widescreen_preset_4_3, 275.0f, 205.0f);
  write_record(ram, kChtHooks.widescreen_preset_wide, 425.0f, 240.0f);
  write_record(ram, kChtHooks.widescreen_preset_4_3_ntsc, 275.0f, 205.0f);
  write_record(ram, kChtHooks.widescreen_preset_wide_ntsc, 425.0f, 240.0f);

  const std::uint32_t owner = 0x00100000u;
  const std::uint32_t option = owner + kChtHooks.widescreen_option_offset;
  put32(ram, kChtHooks.widescreen_owner_pointer, owner);
  put32(ram, option + kChtHooks.video_system_offset, kChtHooks.video_system_ntsc);
  put32(ram, option + kChtHooks.widescreen_flag_offset, 0u);
  write_record(ram, option + kChtHooks.widescreen_record_offset, 275.0f, 205.0f);
  put32(ram, kChtHooks.widescreen_global, 0u);

  gt4::display::WidescreenState wide;
  wide.settle.current = 0x00200000u;
  wide.settle.moves = 1u;
  for (int i = 0; i < 40; ++i) gt4::display::owner_settled(wide.settle, owner);
  expect(gt4::display::force_widescreen_at_vblank(ram.data(), static_cast<std::uint32_t>(ram.size()), wide),
         "16:9 hold writes through CHT addresses");
  expect(get32(ram, option + kChtHooks.widescreen_flag_offset) == 1u, "16:9 flag forced");
  expect(gt4::display::record_is_widescreen(ram.data() + option + kChtHooks.widescreen_record_offset),
         "wide record copied");
  expect(get32(ram, kChtHooks.widescreen_global) == 1u, "published wide word updated");

  const std::uint32_t display = option + kChtHooks.race_display_index_offset;
  put32(ram, display, kChtHooks.race_display_index_1080i);
  gt4::display::Force480pState progressive;
  expect(gt4::display::force_race_480p_at_vblank(ram.data(), static_cast<std::uint32_t>(ram.size()), progressive),
         "480p hold writes through CHT addresses");
  expect(get32(ram, display) == kChtHooks.race_display_index_480p, "1080i race option forced to 480p");
}

void check_frame_skip_table() {
  using namespace gt4::target;
  expect(kChtHooks.frame_update_functor == 0x00100EE0u, "update functor");
  expect(kChtHooks.frame_render_functor == 0x00100F50u, "render functor");
  expect(kChtHooks.frame_idle_functor == 0x00100FC0u, "idle functor");
  expect(kChtHooks.frame_display_page == 0x0060FA84u &&
             kChtHooks.frame_display_page_second == 0x0060FB00u,
         "display page words");
  expect(kChtHooks.frame_race_vtable_first == 0x0066D000u &&
             kChtHooks.frame_race_vtable_last == 0x0067C000u,
         "race class-table range");
  expect(kChtHooks.frame_race_dynamics_offset == 0x70u &&
             kChtHooks.frame_dynamics_clock_offset == 0xF898u &&
             kChtHooks.frame_dynamics_bytes == 0x10000u,
         "race dynamics layout");
  expect(kChtHooks.frame_race_flare_offset == 0xDA0u &&
             kChtHooks.frame_flare_track_count_offset == 0x1848u &&
             kChtHooks.frame_flare_car_count_offset == 0xA34u,
         "flare layout");
  expect(kChtHooks.frame_render_world == 0x003386E0u, "render_world virtual");
}

}  // namespace

int main() {
  expect(gt4::target::active().id == gt4::target::Id::cht, "CHT is active");
  check_widescreen_and_display_holds();
  check_frame_skip_table();
  if (failures != 0) {
    std::fprintf(stderr, "cht_hooks: %d failure(s)\n", failures);
    return 1;
  }
  std::fprintf(stderr, "cht_hooks: all checks passed\n");
  return 0;
}

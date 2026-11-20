// TASK-174: compile game_target.hpp as SCAJ-30007 and expose the fully mapped
// CHT hook table to the common target fixture.
#undef GT4_TARGET_SPEC2
#define GT4_TARGET_CHT 1
#include "game_target.hpp"

bool cht_target_has_all_ported_hooks() {
  using namespace gt4::target;
  const Profile &profile = active();
  if (profile.id != Id::cht || profile.ram_size != 32u << 20)
    return false;
  const HookAddresses &h = profile.hooks;

  if (h.widescreen_owner_pointer != 0x0061A42Cu || h.widescreen_option_offset != 0x38CB0u ||
      h.widescreen_flag_offset != 0x14u || h.widescreen_record_offset != 0x24u ||
      h.widescreen_record_bytes != 44u || h.widescreen_record_width_offset != 0xCu ||
      h.widescreen_record_height_offset != 0x10u || h.video_system_offset != 0x13A0u ||
      h.video_system_ntsc != 1u || h.widescreen_global != 0x0060F9F0u)
    return false;
  if (h.widescreen_preset_4_3 != 0x0061A370u || h.widescreen_preset_wide != 0x0061A3A0u ||
      h.widescreen_preset_4_3_ntsc != 0x0061A3D0u || h.widescreen_preset_wide_ntsc != 0x0061A400u)
    return false;

  if (h.frame_update_functor != 0x00100EE0u || h.frame_render_functor != 0x00100F50u ||
      h.frame_idle_functor != 0x00100FC0u || h.frame_display_page != 0x0060FA84u ||
      h.frame_display_page_second != 0x0060FB00u || h.frame_race_vtable_first != 0x0066D000u ||
      h.frame_race_vtable_last != 0x0067C000u || h.frame_race_dynamics_offset != 0x70u ||
      h.frame_dynamics_clock_offset != 0xF898u || h.frame_dynamics_bytes != 0x10000u ||
      h.frame_race_flare_offset != 0xDA0u || h.frame_flare_track_count_offset != 0x1848u ||
      h.frame_flare_car_count_offset != 0xA34u || h.frame_render_world != 0x003386E0u)
    return false;

  // The other deployed CHT hooks remain present while the two final groups are enabled.
  return h.init_monitor == 0x00382840u && h.race_display_render == 0x003989F0u &&
         h.license_load_demo_inputs == 0x003E3B40u && h.camera_yaw_call_return == 0x0033FDB8u &&
         h.fov_projection_call_return == 0x003744F4u && h.overlay_draw_end_return == 0x003E4F50u;
}

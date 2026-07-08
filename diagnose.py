"""Диагностика: подключение к MOMENTUM 4 и чтение всех настроек (только чтение)."""
import sys

sys.stdout.reconfigure(encoding="utf-8")

from m4 import protocol as P
from m4.client import GaiaClient
from m4.device import Momentum4
from m4.discovery import find_paired_momentum_mac

mac = sys.argv[1] if len(sys.argv) > 1 else find_paired_momentum_mac()
if not mac:
    print("Сопряжённые MOMENTUM 4 не найдены")
    sys.exit(1)
print("MAC:", mac)

c = GaiaClient(mac, on_log=lambda s: print("  " + s))
try:
    ch = c.connect(per_channel_timeout=5.0)
except Exception as e:
    print("CONNECT FAILED:", e)
    sys.exit(1)

print("CONNECTED on channel", ch)
d = Momentum4(c)
print("battery:", d.get_battery())
print("charging:", d.get_charging_status())
print("codec:", d.get_codec())
print("wear:", d.get_physical_state())
print("info:", d.get_info())
print("anc:", d.c.try_request(P.Cmd.GET_ANC))
print("anc modes:", d.get_anc_modes())
print("anc level:", d.get_anc_level())
print("transparency on:", d.get_transparency())
print("transparency level:", d.get_transparency_level())
print("autopause:", d.get_th_autopause())
print("bass boost:", d.get_bass_boost())
print("eq curve:", d.get_eq_curve())
print("eq user gains:", d.get_user_eq())
print("eq freqs:", d.get_eq_band_freqs())
print("sidetone:", d.get_sidetone())
print("touch lock:", d.get_touch_lock())
print("on-head detection:", d.get_on_head_detection())
print("smart pause:", d.get_smart_pause())
print("auto call:", d.get_auto_call())
print("comfort call:", d.get_comfort_call())
print("low latency:", d.get_low_latency())
print("bt compat:", d.get_bt_compat())
print("prompt mode:", d.get_prompt_mode())
print("prompt lang:", d.get_prompt_language())
print("poweroff timer:", d.get_poweroff_timer())
print("MMI map:", {k: hex(v) for k, v in d.get_mmi_map().items()})
print("paired devices:", d.get_paired_devices())
print("own index:", d.get_own_index())
for name, value in d.probe_eq().items():
    print("EQ", name, "->", value)
c.close()
print("DONE")

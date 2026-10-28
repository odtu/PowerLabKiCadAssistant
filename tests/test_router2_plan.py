"""PowerLab router 2's routing plan: each net's role and priority from KiCad's netlist
(patches/kicad-mcp.patch: python/commands/powerlab_router2/plan.py, plan.classify), on a
small made-up board. The plan decides who gets the room when nets compete, so a gate, a
switch node or a crystal taken for a plain signal routes badly.

    "C:\Program Files\KiCad\10.0\bin\python.exe" -m unittest discover -s tests -v
"""
import os
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_mcp_issues import load  # noqa: E402

P = load("python/commands/powerlab_router2/plan.py")
# router.py's name fallback (it imports pcbnew, so not loaded here)
LOW = ("TCK", "TMS", "TDI", "TDO", "JTAG", "SWDIO", "SWCLK", "LED", "BOOT_GPIO", "SCI_", "UART", "DEBUG", "TEST")


def leaf(net):
    return net.rstrip("/").split("/")[-1].upper()

XML = """<export><components>
<comp ref="Q1"><value>X</value><description>N-CH MOSFET 80V</description><libsource lib="Transistor_FET" part="Q_NMOS"/></comp>
<comp ref="Q2"><value>X</value><description>N-CH MOSFET 80V</description><libsource lib="Transistor_FET" part="Q_NMOS"/></comp>
<comp ref="L1"><value>4u7</value><description>Inductor</description><libsource lib="Device" part="L"/></comp>
<comp ref="U1"><value>DRV</value><description>Gate driver</description><libsource lib="X" part="DRV"/></comp>
<comp ref="U2"><value>MCU</value><description>MCU</description><libsource lib="X" part="MCU"/></comp>
<comp ref="Y1"><value>8MHz</value><description>Crystal</description><libsource lib="Device" part="Crystal"/></comp>
<comp ref="R1"><value>1k</value><description>R</description><libsource lib="Device" part="R"/></comp>
<comp ref="D1"><value>Red</value><description>LED SMD</description><libsource lib="Device" part="LED"/></comp>
<comp ref="TP1"><value>TP</value><description>test point</description><libsource lib="Connector" part="TestPoint"/></comp>
<comp ref="C1"><value>100n</value><description>C</description><libsource lib="Device" part="C"/></comp>
<comp ref="U3"><value>OPA</value><description>Operational amplifier</description><libsource lib="Amplifier_Operational" part="OPA"/></comp>
<comp ref="R2"><value>1k</value><description>R</description><libsource lib="Device" part="R"/></comp>
<comp ref="R3"><value>1k</value><description>R</description><libsource lib="Device" part="R"/></comp>
</components><nets>
<net name="Net-(U1-GH)" class="Default"><node ref="U1" pin="1" pinfunction="GH_1" pintype="output"/><node ref="Q1" pin="1" pinfunction="G_1" pintype="input"/></net>
<net name="Net-(Q1-S)" class="Default"><node ref="Q1" pin="2" pinfunction="S_2" pintype="passive"/><node ref="Q2" pin="3" pinfunction="D_3" pintype="passive"/><node ref="L1" pin="1" pinfunction="1_1" pintype="passive"/></net>
<net name="OUT" class="Default"><node ref="L1" pin="2" pinfunction="2_2" pintype="passive"/><node ref="TP1" pin="1" pintype="passive"/></net>
<net name="Net-(U2-PA1)" class="Default"><node ref="U2" pin="5" pinfunction="PA1_5" pintype="bidirectional"/><node ref="U1" pin="2" pinfunction="INH_2" pintype="input"/></net>
<net name="Net-(U2-OSC)" class="Default"><node ref="U2" pin="6" pinfunction="OSC_IN_6" pintype="input"/><node ref="Y1" pin="1" pinfunction="1_1" pintype="passive"/></net>
<net name="Net-(U2-PB2)" class="Default"><node ref="U2" pin="7" pinfunction="PB2_7" pintype="bidirectional"/><node ref="R1" pin="1" pintype="passive"/></net>
<net name="Net-(D1-A)" class="Default"><node ref="R1" pin="2" pintype="passive"/><node ref="D1" pin="1" pinfunction="A_1" pintype="passive"/></net>
<net name="Net-(U2-SWDIO)" class="Default"><node ref="U2" pin="8" pinfunction="SWDIO_8" pintype="bidirectional"/><node ref="TP1" pin="2" pintype="passive"/></net>
<net name="VDD" class="Default"><node ref="U2" pin="9" pinfunction="VDD_9" pintype="power_in"/><node ref="C1" pin="1" pintype="passive"/><node ref="TP1" pin="3" pintype="passive"/></net>
<net name="ISNS" class="Default"><node ref="U1" pin="3" pinfunction="SO_3" pintype="output"/><node ref="U2" pin="10" pinfunction="PA0/ADC1_IN0_10" pintype="input"/></net>
<net name="SIG" class="Default"><node ref="U2" pin="11" pinfunction="PC3_11" pintype="bidirectional"/><node ref="U1" pin="4" pinfunction="NFAULT_4" pintype="output"/></net>
<net name="Net-(U3-+)" class="Default"><node ref="U3" pin="3" pinfunction="+_3" pintype="input"/><node ref="R2" pin="1" pintype="passive"/></net>
<net name="Net-(U3-OUT)" class="Default"><node ref="U3" pin="1" pinfunction="1" pintype="output"/><node ref="R3" pin="1" pintype="passive"/></net>
<net name="/Sense/ISNS_F" class="Default"><node ref="R2" pin="2" pintype="passive"/><node ref="U2" pin="12" pinfunction="PC3_12" pintype="bidirectional"/><node ref="TP1" pin="4" pintype="passive"/></net>
<net name="/Gate Driver/IDRIVE" class="Default"><node ref="U1" pin="5" pinfunction="IDRIVE_5" pintype="input"/><node ref="U2" pin="13" pinfunction="PC4_13" pintype="bidirectional"/></net>
<net name="/MCU/SWCLK" class="Default"><node ref="U2" pin="14" pinfunction="PA14_14" pintype="bidirectional"/><node ref="TP1" pin="5" pintype="passive"/></net>
<net name="/MCU/BOOT0" class="Default"><node ref="U2" pin="15" pinfunction="BOOT0_15" pintype="input"/><node ref="C1" pin="3" pintype="passive"/></net>
</nets></export>"""


class Roles(unittest.TestCase):
    def setUp(self):
        def by_name(net, cls):  # as make_plan's: only asked where the pins say nothing
            n = leaf(net)
            if any(s in n for s in LOW):
                return 0, "debug"
            if "SENSE" in n or "ISNS" in n:
                return 2, "analog"
            if "PWM" in n or "GATE" in n.split("_")[:1]:
                return 3, "pwm"
            return None
        self.p = P.classify(P.parse_netlist(ET.fromstring(XML)), by_name)

    def check(self, net, prio, inner):
        e = self.p[net]
        self.assertEqual((e["priority"], e["inner"]), (prio, inner), f"{net}: {e}")

    def test_gate(self):
        self.check("Net-(U1-GH)", 4, False)  # a power-stage loop

    def test_switch_node(self):
        self.check("Net-(Q1-S)", 4, False)

    def test_inductor_output_is_power_with_its_test_point(self):
        self.check("OUT", 2, False)

    def test_pwm_input(self):
        self.check("Net-(U2-PA1)", 3, True)

    def test_crystal(self):
        self.check("Net-(U2-OSC)", 3, False)

    def test_led_through_resistor(self):
        self.check("Net-(U2-PB2)", 0, True)

    def test_debug(self):
        self.check("Net-(U2-SWDIO)", 0, True)

    def test_rail_with_test_point(self):
        self.check("VDD", 2, False)

    def test_sense(self):
        self.check("ISNS", 2, True)

    def test_opamp_input(self):
        self.check("Net-(U3-+)", 2, True)

    def test_filtered_line_from_an_amplifier(self):
        self.check("/Sense/ISNS_F", 2, True)

    def test_sheet_path_is_not_a_gate(self):
        self.check("/Gate Driver/IDRIVE", 1, True)

    def test_name_says_debug_where_pins_say_nothing(self):
        self.check("/MCU/SWCLK", 0, True)

    def test_boot0_is_a_plain_signal(self):
        self.check("/MCU/BOOT0", 1, True)

    def test_name_never_overrides_pins(self):
        self.check("Net-(U2-PA1)", 3, True)  # a PWM input by its pin, whatever the name

    def test_plain_signal(self):
        self.check("SIG", 1, True)


DUAL = """<export><components>
<comp ref="Q1"><value>X</value><description>Dual N-CH MOSFET</description><libsource lib="Transistor_FET" part="Q_Dual_NMOS"/></comp>
<comp ref="R1"><value>10</value><description>R</description><libsource lib="Device" part="R"/></comp>
</components><nets>
<net name="SRC1" class="Default"><node ref="Q1" pin="1" pinfunction="S_1" pintype="passive"/></net>
<net name="G1" class="Default"><node ref="Q1" pin="2" pinfunction="G_2" pintype="input"/><node ref="R1" pin="1" pintype="passive"/></net>
<net name="DRV1" class="Default"><node ref="R1" pin="2" pintype="passive"/></net>
<net name="SW" class="Default"><node ref="Q1" pin="3" pinfunction="S_3" pintype="passive"/></net>
<net name="G2" class="Default"><node ref="Q1" pin="4" pinfunction="G_4" pintype="input"/></net>
</nets></export>"""


class Loops(unittest.TestCase):
    def test_dual_mosfet_gates_pair_with_their_own_sources(self):
        loops = P.gate_loops(P.parse_netlist(ET.fromstring(DUAL)))
        self.assertIn(["G1", "DRV1", "SRC1"], loops)  # gate path through the resistor, return last
        self.assertIn(["G2", "SW"], loops)


if __name__ == "__main__":
    unittest.main()

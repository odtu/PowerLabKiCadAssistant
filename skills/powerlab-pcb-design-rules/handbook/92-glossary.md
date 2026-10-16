# Glossary

Terms used in the handbook: the English term, its Turkish equivalent and an explanation. Definitions are conceptual; numeric limits and their sources are given in the relevant rule (the prefixes in the column).

| Term (EN) | Turkish term | Explanation | Related |
|---|---|---|---|
| 20H rule | 20H kuralı | Recommendation to pull the power plane back from the GND edge by 20 times the layer spacing (disputed, see STK-008). | STK |
| 3W rule | 3W kuralı | Rule of keeping the spacing between traces at 3 times the trace width (conditional, see HS-011). | HS, EST |
| λ/20 rule | λ/20 kuralı | Rule of keeping via/gap spacing smaller than 1/20 of the wavelength of interest. | GND, RF |
| Acid trap | Acid trap / asit tuzağı | A pocket at an acute-angle copper junction where etchant can collect and over-etch. | DFM, EST |
| Annular ring | Halka (annular ring) | Copper width between the hole edge and the outer edge of the pad. | DFM |
| Antenna keepout / clearance | Anten temiz alanı | Region under and around the antenna that must have no copper on any layer. | RF |
| Antipad | Antipad | Copper-free ring left around a via/pin in a plane layer. | GND, DFM |
| Aspect ratio | Aspect ratio (en-boy oranı) | Ratio of board thickness to hole diameter; limits plating quality. | VIA, DFM |
| Blind / buried via | Kör / gömülü via | A via that connects only some of the layers; costly. | VIA |
| Bootstrap capacitor | Bootstrap kondansatörü | Capacitor that supplies the high-side MOSFET gate driver. | SMPS |
| Bulk capacitor | Bulk kondansatör | Large-value capacitor that meets low-frequency current demands. | PWR |
| Castellated hole | Yarım delik | Plated hole cut in half at the board edge. | DFM |
| Chassis ground | Şasi toprağı | Ground connected to the enclosure/connector shell; may be separate from the circuit GND. | ESD, MEC |
| Common impedance coupling | Ortak empedans | Voltage drop on a shared return path spilling over into another circuit. | GND |
| Controlled impedance | Empedans kontrolü | Tuning the trace geometry, together with the stackup, to a specific characteristic impedance. | HS, STK, RF |
| Copper island / dead copper | Ada (bakır adası) | A piece of pour that is connected to no net and is surrounded by clearance. | GND, DFM |
| Copper pour / zone | Dolgu / döküm | Large copper area connected to a net. | GND, GOR |
| Courtyard | Courtyard | Outer boundary area reserved for a component for assembly. | DFA |
| Crosstalk | Karışma | Unwanted coupling between neighbouring traces. | HS |
| Crystal | Kristal | Piezoelectric part that sets the oscillator frequency. | XTL |
| Decoupling / bypass capacitor | Dekuplaj kondansatörü | Capacitor close to an IC supply pin that supplies high-frequency current locally. | PWR |
| Differential pair | Diferansiyel çift | Two traces in opposite phase; used in interfaces such as USB, Ethernet, HDMI. | HS |
| Exposed / thermal pad | Exposed pad | Large heat/GND pad under QFN and similar packages. | THM, DFA |
| Fiducial | Fiducial | Round copper mark without solder mask that the pick-and-place machine uses to align the board. | DFA |
| Footprint / land pattern | Footprint / land pattern | Arrangement of a component's pads and markings on the board. | DFA |
| Grounded coplanar waveguide | CPWG | RF transmission line with GND beside and below it, tuned to 50 Ω. | RF |
| Guard ring | Guard ring / koruma halkası | Copper ring connected to GND that surrounds a sensitive node. | XTL |
| Hot loop | Sıcak döngü | High-di/dt current loop in a switching power supply (Cin–switches). | SMPS |
| Keepout / rule area | Keepout / kural alanı | Defined area where placing copper, vias or components is forbidden. | RF, MEC |
| Kelvin (4-wire) connection | Kelvin bağlantısı | Taking the measurement traces directly from the measurement point, separate from the current path. | PWR, SMPS |
| Load capacitor | Yük kondansatörü | Capacitors needed for the crystal to oscillate at the correct frequency. | XTL |
| Mounting hole | Montaj deliği | Hole for fixing the board with a screw/standoff. | MEC |
| Mouse bites | Mouse bite | Breakaway tab with closely spaced holes for separating the panel. | MEC, DFM |
| Non-plated / plated through hole | NPTH / PTH | Unplated and plated hole. | DFM |
| Partitioning | Bölümleme | Dividing the circuit into analog/digital/power areas while keeping a single GND plane. | GND, PLC |
| Paste aperture / windowpane | Pasta penceresi | Solder paste opening in the stencil; split into segments on large pads. | THM, DFA |
| Pin-1 indicator | Pin-1 işareti | Silkscreen mark showing pin 1 of an IC/connector. | DFA, SLK |
| Plane | Düzlem | Copper, usually GND or power, that covers most of a layer. | STK, GND |
| Plated over filled via | POFV / dolgulu via | Via filled with epoxy and capped with copper. | VIA, DFA |
| Rated current | Anma akımı | Manufacturer-defined current that a component (connector, fuse, via) can carry continuously. | PWR |
| Ratsnest / airwire | Ratsnest / hava teli | Thin line showing a connection that has not been routed yet. | EST, GOR |
| Reference plane | Referans düzlemi | Plane directly adjacent to a signal layer. | STK, HS |
| Return path | Dönüş yolu | Path by which signal current returns to the source; usually the reference plane directly below. | GND, HS |
| Series termination | Seri sonlandırma | Small resistor at a driver output that reduces reflections. | HS |
| Serpentine / meander | Menderes / serpantin | Meandering trace used to match lengths. | HS |
| Shield can | Kalkan (RF kalkanı) | Metal cover over an RF circuit, and its GND ring. | RF |
| Silkscreen / legend | Serigrafi / silkscreen | White print on the board (labels, markings, logo). | SLK |
| Skew | Skew | Length or delay difference between the traces of a differential pair. | HS |
| Sliver | Sliver | Copper or solder mask strip thin enough to break off. | DFM |
| Snubber | Snubber | RC network that damps switching ringing. | SMPS |
| Solder mask dam / web | Baraj (maske barajı) | Thin strip of solder mask left between two pads. | DFM, VIA |
| Stackup | Stackup | Order, thicknesses and materials of the layers. | STK |
| Starved thermal | Starved thermal | Thermal relief that is not connected well enough because some of its spokes are cut. | DFM |
| Stitching via | Dikiş via'sı | Vias that connect the GND pours on different layers to each other. | GND, RF |
| Stub | Stub | Short open-ended trace/via segment branching off the main signal path. | HS, ESD |
| Switch node (SW) | Switch node | Fast-changing node between the switches and the inductor in a buck/boost. | SMPS |
| Teardrop | Teardrop | Copper that widens the trace–pad junction into a drop shape. | DFM |
| Tenting | Tenting (örtme) | Covering a via with solder mask. | VIA, THM |
| Test point (TP) | Test noktası | Accessible pad reserved for a probe or fixture. | TST |
| Thermal relief / spoke | Spoke / termal rahatlatma | Structure that connects a pad to the pour with thin spokes, making soldering easier. | THM, DFM |
| Thermal via | Termal via | Via made to carry heat to other layers. | THM |
| Tombstoning | Tombstoning | A small passive lifting up on one end during reflow. | DFA |
| TVS diode | TVS | Protection diode that clamps transient overvoltage. | ESD |
| Untented / open via | Açık via | Via not covered by solder mask, with its annular ring and hole exposed. | VIA, DFA |
| V-score | V-kesim | V-shaped groove cut from both sides to separate the panel. | MEC, DFM |
| Via fence | Via fence / via çiti | Row of GND vias along an RF line. | RF |
| Via-in-pad | Via-in-pad | Via placed inside a pad. | VIA, DFA |

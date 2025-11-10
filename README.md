Cacophony
---------

What is this?
-------------

Cacophony is a quasar extension module helping with integration of quasar-made OPC-UA servers into WinCC OA SCADA.

Tutorial:
https://www.youtube.com/watch?v=g2LWOx1BufI

Basic usage mode
----------------

1. Clone it in your quasar project directory
1. From your quasar project directory run:
  `python3 Cacophony/generateStuff.py`
1. All CTL files in `Cacophony/generated` are what is needed to make WinCC OA project profit from that particular quasar OPC-UA server.
1. For a detailed reference, see:
  https://www.youtube.com/watch?v=g2LWOx1BufI

Using Design with meta
------------------------------------

By default, Cacophony uses `Design/Design.xml` (user design only). If you need to include quasar's internal meta-design classes in your generation:

Run with the `--use_design_with_meta` flag:
```
python3 Cacophony/generateStuff.py --use_design_with_meta
```
This will:
- Merge `Design/Design.xml` with `Meta/design/meta-design.xml`
- Create `Design/DesignWithMeta.xml` temporarily in your Design folder
- Use the merged design for code generation
- Automatically delete `DesignWithMeta.xml` after successful generation

Mixed Instantiation Support
---------------------------

Cacophony now parses design-instantiated children of configuration-instantiated objects

**Use case example:**
- A class `AMAC` is instantiated from configuration XML
- `AMAC` has children (e.g., 4 `HVSwitch` objects) instantiated from design

In this scenario, Cacophony will:
- Parse configuration XML to create `AMAC` instances
- Automatically instantiate design-defined children for each `AMAC` instance

Thanks to iTk Strips team (and more specifically to Kees Benkendorfer) for their contribution
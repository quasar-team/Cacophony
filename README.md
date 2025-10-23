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

------------------------------------

By default, Cacophony uses `Design/Design.xml` (user design only). If you need to include quasar's internal meta-design classes in your generation:

1. Run with the `--use_design_with_meta` flag:
   ```
   python3 Cacophony/generateStuff.py --use_design_with_meta
   ```
2. This will:
   - Merge `Design/Design.xml` with `Meta/design/meta-design.xml`
   - Create `Design/DesignWithMeta.xml` temporarily in your Design folder
   - Use the merged design for code generation
   - Automatically delete `DesignWithMeta.xml` after successful generation
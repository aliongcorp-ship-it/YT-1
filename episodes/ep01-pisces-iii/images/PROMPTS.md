# EP01 — plate prompts

All ten plates are generated with the **same base style block**, then one scene block each. That is what keeps the film looking like one hand rather than ten generations. Do not edit the base block per plate.

## Base style block (verbatim, every plate)

> Hand-inked cinematic documentary illustration, charcoal and brush ink on cold-press paper, visible paper grain, dry-brush drag, cross-hatching, slight ink bleed. Limited palette: ink black and deep teal-green, bone-paper cream, warm amber light, one rust-red accent. Cinematic 16:9 wide film still, dramatic single light source, deep shadows, atmospheric ink-wash haze.
>
> [SCENE BLOCK]
>
> At the edge of the frame, small — about one tenth of the frame height — a stickman in a long charcoal coat with a rust-red scarf, holding a small brass lantern with a warm amber glow, standing quietly and watching. He does not interact with the scene.
>
> No text, no letters, no numbers, no watermark, no signature, no border. No realistic faces, no 3D render look, no glossy digital painting.

## Scene blocks

| Plate | Scene block (short form) |
|---|---|
| 01 interior | Interior of a six-foot steel sphere, 1973. Two ink stickmen crewmen sit shoulder to shoulder, knees up; one leans to a porthole, one looks at an amber pressure gauge. Coiled cable, condensation, cross-hatched rivets. One amber lamp. |
| 02 surface-routine | Calm grey Atlantic morning. Small bulbous submersible with two portholes hanging beside a work ship with a lattice crane. Flat ink swell, seabirds as brush marks, deckhands at the rail. Nothing is wrong yet. |
| 03 accident | Just below the surface: the submersible flipped upside down, towline wrenched across an open aft hatch, seawater bursting in white ink sprays. Ship hull looming as black silhouette. Chaotic diagonal composition. |
| 04 descent | The submersible tumbling stern-first into black water, bubbles and a slack frayed line, vertical ink washes darkening downward, mostly negative black space, one small object alone in the middle distance. |
| 05 seabed | Ocean floor at 1,575 ft. The sub lying upside down half-sunk in grey ooze, hatch open, cable tangle, a blade of amber torchlight cutting across the mud. Dense cross-hatching at the frame edges = pressure. |
| 06 rationing | Close interior, near-total darkness. Two crewmen pressed together under a thin blanket, breath fogging, one holding a sandwich, one a can. Tiny emergency lamp from below. Cold, damp, exhausted. Walls pressing in. |
| 07 surface-rescue | Night deck of a rescue ship in heavy swell. Crew under an amber floodlight: radio handset, chart table, two hauling rope, crane and winch behind. Spray as pale ink spatter, rigging in silhouette, distant ship lights. |
| 08 failed-attempt | Two rescue submersibles near the wreck; a manipulator arm outstretched with its rope slipping free and drifting away in a loose curl; spotlight sweeping silt; a coiled line floating uselessly upward. A failed attempt. |
| 09 the-lift | The upside-down sub hauled upward by three converging lines, swinging, dragging an entangled ROV. Bubbles and silt streaming past, strong vertical brush strokes, the surface a pale luminous disc. Upward diagonal, violent motion. |
| 10 surface-hatch | The submersible at the surface in daylight, divers on its back fighting a jammed hatch, one diver's fist raised, spray, the crane wire taut overhead. Exhaustion and relief in equal measure. |

## Model settings that mattered

- **Text is banned in the prompt and replaced in code.** Every letter in the episode (title card, end card, thumbnail, any future labels) is typeset with Pillow. Image models mangle type; this removes the single biggest tell of AI slop.
- **"One rust accent"** is a real constraint: it forces the model to make a compositional decision instead of flooding the frame with colour.
- **"Paper grain / ink bleed / dry brush"** keeps the outputs in one medium. Without it, the model drifts to glossy digital painting by plate 4.
- Wick is always described as *small and watching*. If he is described as heroic or central, models enlarge him, give him a face, and the brand breaks.

## Known drift to watch for

- Plate 06 rendered the crewmen with soft illustrated hair and facial shading — a slightly different register from the pure stickmen in plates 01/02. It reads as an intentional close-up, but for episode 02 the phrase **"round heads, dot eyes, no facial shading"** should be added to the crew description in the scene block.
- Keep an eye on pole/rope counts (the model likes to add a fourth line). The narration says three lines; plates should match.

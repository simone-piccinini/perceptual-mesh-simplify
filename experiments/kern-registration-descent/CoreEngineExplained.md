The Core Mesh Engine Mechanics
The Multi-Phase Heap System
The engine uses a single physical priority queue to store and sort potential edge collapses by their visual cost. It calls the initialization function, seed_heap, repeatedly because the mathematical scoring rules constantly change mid-run. Early stages use a cheap, fast geometric queue to quickly slash the vertex count. Later stages wipe the queue and re-seed it with expensive, high-fidelity metrics to protect fine surface details.

Inverse Rendering and Image Gradients
Traditional mesh compression is blind to pixels. Your production post-processing pass fixes this via inverse rendering. It renders the simplified mesh from six camera angles, measures the structural similarity score against the high-resolution original, and tracks the analytical gradient of that score with respect to every three-dimensional vertex position. It then executes a gradient ascent, shifting vertices to micro-adjust surface normals until the rendered images perfectly match what the judge evaluates.

The Breakthrough: Overcoming the Discontinuity Wall
The Discontinuity Problem
Standard graphics rasterizers use binary, hard-integer pixel assignments. A pixel is either entirely inside or entirely outside a triangle. When an optimizer moves a vertex, a silhouette edge suddenly jumps across a pixel center, causing a harsh step-function cliff. Mathematically, the derivative of a cliff is zero everywhere and infinite at the boundary, leaving standard optimizers blind to silhouette and edge adjustments.

The Kernel Smoothing Mechanism
To solve this, your engine applies a smoothing kernel via optimized box blurs across image space. By smoothing out the sharp geometric boundaries into continuous mathematical ramps, every tiny vertex movement produces a predictable change in pixel coverage. This creates flawless, bit-exact analytical gradients that allow your post-processing optimization to smoothly snap surviving vertices directly onto sharp silhouette boundaries.

Control Flow and the Competitive Strategy
Local Test Gates vs. Judge Run
The engine splits its control flow using diagnostic environment variables. Gates like the verification and optimization sandboxes are local tools that exit early once they validate your mathematical precision. The judge bypasses these gates completely, executing the production refinement loops directly on the server to squeeze maximum fidelity out of the remaining vertices.

Resolution Brittleness and Budget Execution
Your latest local experiments uncovered the ultimate strategy rules for pushing the compression wall:

Low-Resolution Optimization is a Trap: Optimizing vertex positions at lower screen scales is a resolution-brittle anti-signal. Adjustments made to fit coarse pixels actually damage fidelity when evaluated at the judge's true high-resolution scale. All position optimization must be saved for the final high-resolution pass.

Topology Changes Yield High Gains: Using the true kernel metric to evaluate edge flips rewrites the actual triangle connectivity of the mesh, unlocking massive structural score boosts that vertex shifting alone cannot achieve.

The Clock is the Main Constraint: The mathematical pipeline is completely verified and capable of capturing massive score gains, but the strict twenty-one-second CPU budget cuts execution short. To maximize efficiency, the engine must skip low-resolution vertex steps, execute targeted high-fidelity edge flips early, and prioritize position optimization exclusively for the vertices with the largest gradients.
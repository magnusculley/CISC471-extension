L1 makes evaluation order explicit. Program acts as a statement oriented tree.


** Relevant Characteristics**
- Copy, Immediate, Primitive: assign values into destination variables.
- Branch: control-flow split between then and otherwise statement chains.
- Abstract: introduces a named local function with parameters and a body.
- Apply: calls a target with arguments and ends a control path.
- Allocate, Load, Store: explicitlty making a block of memory, reading a block of memory, writing something into memory.
- Halt: returns a final value.


**Difference from L2**
- Nested expressions are lowered into explicit statement sequencing through `then`.
- Let-style expression bindings become direct variable assignments.
- Expression-level function forms are replaced by statement-level Abstract and Apply.

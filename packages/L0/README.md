L0 is the lowest level language. Program is an explicit list of named functions.


**Relevant Characteristics**
- Program: a list of named functions.
- Procedure body: explicit statement chains over named variables.
- Copy, Immediate, Primitive, Branch: low-level value movement and control flow.
- Allocate, Load, Store: explicit memory operations. (I don't think these ever actually change in behavior from L3->L0)
- Address: gets a callable reference to a named function.
- Call and Halt: explicit invocation and return behavior.


Difference from L1
- Abstract-style local function creation is elaborated into explicit named functions.
- Address is introduced to represent function references directly.
- Program structure is simplified from one body term into an explicit function list.
L2 is very close to L3, but without recursive binding. The program is still one expression body that essentially acts like a tree with sub expressions


**Relevant Characteristics**
- Let: local binding values/terms to a name (non-recursive).
- Reference, Abstract, Apply: variable lookup, lambda function creation, and function application over some term(s).
- Immediate: integer literals, ready to be used.
- Primitive: arithmetic over terms using plus, minus, and multiply.
- Branch: expression-level conditional selection using comparisons, like a ternary expression.
- Allocate, Load, Store: explicitlty making a block of memory, reading a block of memory, writing something into memory.
- Begin: starts a sequence of evaluations and returns final value.


**Difference from L3**
- L3 includes LetRec, but L2 does not.
- Because LetRec is removed, recursion must be transformed before lowering into L2.
import pytest
from L3.check import Context, check_program, check_term
from L3.syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Boolean,
    Branch,
    Float,
    Immediate,
    Index,
    Let,
    LetRec,
    Load,
    Primitive,
    Program,
    Reference,
    Store,
    Tuple,
)


def test_check_reference_bound():
    term = Reference(name="x")

    context: Context = {
        "x": None,
    }

    check_term(term, context)


def test_check_reference_free():
    term = Reference(name="x")
    context: Context = {}
    with pytest.raises(ValueError):
        check_term(term, context)


def test_check_let_duplicate_binding():
    term = Let(
        bindings=[
            ("x", Immediate(value=1)),
            ("x", Immediate(value=2)),
        ],
        body=Immediate(value=0),
    )
    context: Context = {}
    with pytest.raises(ValueError):
        check_term(term, context)


# above done in class, below done for coverage


def test_reference_bound():
    check_term(Reference(name="a"), {"a": None})


def test_reference_unbound_raises():
    with pytest.raises(ValueError, match="unknown variable: x"):
        check_term(Reference(name="x"), {})


def test_let_simple_binding():
    term = Let(bindings=[("x", Immediate(value=5))], body=Reference(name="x"))
    check_term(term, {})


def test_let_nested_scopes():
    term = Let(
        bindings=[("x", Immediate(value=1))],
        body=Let(
            bindings=[("y", Reference(name="x"))],
            body=Reference(name="y"),
        ),
    )
    check_term(term, {})


def test_let_unbound_in_binding():
    term = Let(
        bindings=[("x", Reference(name="z"))],
        body=Immediate(value=0),
    )
    with pytest.raises(ValueError, match="unknown variable: z"):
        check_term(term, {})


def test_let_duplicate_binders_error():
    term = Let(
        bindings=[("a", Immediate(value=0)), ("a", Immediate(value=1))],
        body=Immediate(value=0),
    )
    with pytest.raises(ValueError, match="Duplicate binders in Let"):
        check_term(term, {})


def test_letrec_function_binding():
    a = Abstract(parameters=["p"], body=Reference(name="p"))
    term = LetRec(bindings=[("a", a)], body=Apply(target=Reference(name="a"), arguments=[Immediate(value=0)]))
    check_term(term, {})


def test_letrec_duplicate_binders():
    term = LetRec(bindings=[("a", Immediate(value=0)), ("a", Immediate(value=1))], body=Immediate(value=0))
    with pytest.raises(ValueError, match="Duplicate binders in LetRec"):
        check_term(term, {})


def test_letrec_non_function_value():
    term = LetRec(bindings=[("x", Immediate(value=0))], body=Reference(name="x"))
    with pytest.raises(ValueError, match="LetRec binding must be an Abstract"):
        check_term(term, {})


def test_letrec_mutual_recursion():
    a = Abstract(parameters=["x"], body=Apply(target=Reference(name="b"), arguments=[Reference(name="x")]))
    b = Abstract(parameters=["y"], body=Apply(target=Reference(name="a"), arguments=[Reference(name="y")]))
    term = LetRec(bindings=[("a", a), ("b", b)], body=Reference(name="a"))
    check_term(term, {})


def test_abstract_no_parameters():
    check_term(Abstract(parameters=[], body=Immediate(value=0)), {})


def test_abstract_parameter_binding():
    term = Abstract(parameters=["p"], body=Reference(name="p"))
    check_term(term, {})


def test_abstract_duplicate_parameters_raises():
    term = Abstract(parameters=["x", "x"], body=Immediate(value=0))
    with pytest.raises(ValueError, match="Duplicate parameters in Abstract"):
        check_term(term, {})


def test_apply_without_target_bound():
    term = Apply(target=Reference(name="a"), arguments=[Immediate(value=0)])
    with pytest.raises(ValueError, match="unknown variable: a"):
        check_term(term, {})


def test_apply_with_args():
    term = Apply(target=Reference(name="a"), arguments=[Reference(name="b")])
    with pytest.raises(ValueError, match="unknown variable: a"):
        check_term(term, {"b": None})


def test_apply_success():
    term = Apply(target=Reference(name="a"), arguments=[Immediate(value=1)])
    check_term(term, {"a": None})


def test_immediate_trivial():
    check_term(Immediate(value=123), {})


def test_float_trivial():
    check_term(Float(value=3.14), {})


def test_boolean_trivial():
    check_term(Boolean(value=True), {})


def test_tuple_trivial():
    check_term(Tuple(elements=[Immediate(value=1), Immediate(value=2)]), {})


def test_primitive_unbound():
    term = Primitive(operator="+", left=Immediate(value=1), right=Reference(name="a"))
    with pytest.raises(ValueError, match="unknown variable: a"):
        check_term(term, {})


def test_branch_unbound_consequent():
    term = Branch(
        operator="<",
        left=Immediate(value=0),
        right=Immediate(value=1),
        consequent=Reference(name="x"),
        otherwise=Immediate(value=2),
    )
    with pytest.raises(ValueError, match="unknown variable: x"):
        check_term(term, {})


def test_allocate_is_noop():
    check_term(Allocate(count=10), {})


def test_load_and_store_contexts():
    load = Load(base=Reference(name="a"), index=0)
    with pytest.raises(ValueError):
        check_term(load, {})
    check_term(load, {"a": None})

    store = Store(base=Reference(name="a"), index=1, value=Reference(name="b"))
    with pytest.raises(ValueError):
        check_term(store, {"a": None})
    check_term(store, {"a": None, "b": None})


def test_begin_effects_and_value():
    begin = Begin(effects=[Reference(name="e")], value=Reference(name="v"))
    with pytest.raises(ValueError):
        check_term(begin, {})
    check_term(begin, {"e": None, "v": None})


def test_check_program_success_with_params():
    prog = Program(parameters=["a"], body=Reference(name="a"))
    check_program(prog)


def test_check_program_duplicate_params():
    prog = Program(parameters=["a", "a"], body=Immediate(value=0))
    with pytest.raises(ValueError, match="Duplicate parameters in program"):
        check_program(prog)


def test_empty_variants_generate_no_error():
    check_term(Let(bindings=[], body=Immediate(value=0)), {})
    check_term(LetRec(bindings=[], body=Immediate(value=0)), {})
    check_term(Abstract(parameters=[], body=Immediate(value=0)), {})
    check_term(Begin(effects=[], value=Immediate(value=0)), {})


def test_apply_non_function_target_rejected():
    with pytest.raises(ValueError, match="apply target must be a function"):
        check_term(Apply(target=Immediate(value=0), arguments=[]), {})


def test_branch_both_valid():
    term = Branch(
        operator="<",
        left=Immediate(value=0),
        right=Immediate(value=1),
        consequent=Immediate(value=9),
        otherwise=Reference(name="y"),
    )
    with pytest.raises(ValueError, match="unknown variable: y"):
        check_term(term, {})


def test_primitive_rejects_non_numeric_operand():
    term = Primitive(operator="+", left=Boolean(value=True), right=Immediate(value=1))
    with pytest.raises(ValueError, match="Primitive left operand must be numeric"):
        check_term(term, {})


def test_branch_requires_compatible_result_types():
    term = Branch(
        operator="==",
        left=Immediate(value=1),
        right=Immediate(value=1),
        consequent=Immediate(value=0),
        otherwise=Boolean(value=False),
    )
    with pytest.raises(ValueError, match="type mismatch"):
        check_term(term, {})


def test_apply_enforces_known_function_arity():
    term = Let(
        bindings=[("f", Abstract(parameters=["x", "y"], body=Reference(name="x")))],
        body=Apply(target=Reference(name="f"), arguments=[Immediate(value=1)]),
    )
    with pytest.raises(ValueError, match="apply arity mismatch"):
        check_term(term, {})


def test_index_requires_tuple_target():
    term = Index(tuple=Immediate(value=1), index=0)
    with pytest.raises(ValueError, match="Index target must be a tuple"):
        check_term(term, {})


def test_index_out_of_bounds_rejected():
    term = Index(tuple=Tuple(elements=[Immediate(value=1)]), index=2)
    with pytest.raises(ValueError, match="Tuple index out of bounds"):
        check_term(term, {})


def test_branch_less_than_rejects_non_numeric_operands():
    term = Branch(
        operator="<",
        left=Boolean(value=True),
        right=Immediate(value=1),
        consequent=Immediate(value=1),
        otherwise=Immediate(value=0),
    )
    with pytest.raises(ValueError, match="Branch left operand for < must be numeric"):
        check_term(term, {})


def test_branch_tuple_equality_requires_same_length():
    term = Branch(
        operator="==",
        left=Tuple(elements=[Immediate(value=1)]),
        right=Tuple(elements=[Immediate(value=1), Immediate(value=2)]),
        consequent=Immediate(value=1),
        otherwise=Immediate(value=0),
    )
    with pytest.raises(ValueError, match="Tuple equality requires equal lengths"):
        check_term(term, {})


def test_allocate_count_rejects_float():
    with pytest.raises(ValueError, match="Allocate count must be an integer"):
        check_term(Allocate(count=Float(value=1.5)), {})


def test_primitive_success():
    check_term(Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=2)), {})


def test_primitive_unknown_right_operand():
    # _unify(TypeInt, TypeUnknown) hits the right=TypeUnknown branch in _unify
    check_term(Primitive(operator="+", left=Immediate(value=1), right=Reference(name="x")), {"x": None})


def test_primitive_mixed_numeric_types():
    # _unify(TypeFloat, TypeInt) hits the float-promotion branch in _unify
    check_term(Primitive(operator="+", left=Float(value=1.5), right=Immediate(value=1)), {})


def test_allocate_with_unknown_count():
    # _expect_integer with TypeUnknown hits the early return branch
    check_term(Allocate(count=Reference(name="x")), {"x": None})


def test_branch_tuple_equality_same_length():
    # hits the tuple == loop body and return in _check_comparator
    term = Branch(
        operator="==",
        left=Tuple(elements=[Immediate(value=1)]),
        right=Tuple(elements=[Immediate(value=2)]),
        consequent=Immediate(value=1),
        otherwise=Immediate(value=0),
    )
    check_term(term, {})


def test_load_from_memory():
    # hits the TypeMemory path in Load (return base_type.element)
    term = Let(
        bindings=[("a", Allocate(count=1))],
        body=Load(base=Reference(name="a"), index=0),
    )
    check_term(term, {})


def test_load_non_memory_base_raises():
    # hits the "Load base must be memory" raise
    with pytest.raises(ValueError, match="Load base must be memory"):
        check_term(Load(base=Immediate(value=1), index=0), {})


def test_store_to_memory():
    # hits the TypeMemory path in Store (_unify + return TYPE_INT)
    term = Let(
        bindings=[("a", Allocate(count=1))],
        body=Store(base=Reference(name="a"), index=0, value=Immediate(value=42)),
    )
    check_term(term, {})


def test_store_non_memory_base_raises():
    # hits the "Store base must be memory" raise
    with pytest.raises(ValueError, match="Store base must be memory"):
        check_term(Store(base=Immediate(value=1), index=0, value=Immediate(value=0)), {})


def test_index_unknown_tuple():
    # hits the TypeUnknown branch in Index (return TYPE_UNKNOWN)
    check_term(Index(tuple=Reference(name="x"), index=0), {"x": None})


def test_index_in_bounds():
    # hits the successful return path in Index
    check_term(Index(tuple=Tuple(elements=[Immediate(value=1), Immediate(value=2)]), index=1), {})

from L2.constant_folding import constant_folding_program
from L2.constant_propagation import constant_propagation_program
from L2.dead_code_elimination import dead_code_elimination_program, is_pure, is_referenced
from L2.optimize import optimize_program
from L2.syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Branch,
    Immediate,
    Let,
    Load,
    Primitive,
    Program,
    Reference,
    Store,
)


# Propagation

def test_constant_propagation_immediate_and_reference_and_scope():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[
                ("x", Immediate(value=1)),
                ("y", Reference(name="x")),
                ("z", Primitive(operator="+", left=Reference(name="y"), right=Immediate(value=1))),
            ],
            body=Begin(
                effects=[
                    Reference(name="z"),
                    Abstract(
                        parameters=["x"],
                        body=Reference(name="x"),
                    ),
                ],
                value=Reference(name="y"),
            ),
        ),
    )

    actual = constant_propagation_program(program)

    expected = Program(
        parameters=[],
        body=Let(
            bindings=[
                ("x", Immediate(value=1)),
                ("y", Immediate(value=1)),
                ("z", Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=1))),
            ],
            body=Begin(
                effects=[
                    Reference(name="z"),
                    Abstract(
                        parameters=["x"],
                        body=Reference(name="x"),
                    ),
                ],
                value=Immediate(value=1),
            ),
        ),
    )

    assert actual == expected


def test_constant_propagation_other_forms_are_recursed():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[("x", Immediate(value=1))],
            body=Begin(
                effects=[
                    Apply(
                        target=Reference(name="a"),
                        arguments=[Reference(name="x")],
                    ),
                    Store(
                        base=Allocate(count=1),
                        index=0,
                        value=Reference(name="x"),
                    ),
                ],
                value=Branch(
                    operator="==",
                    left=Load(base=Reference(name="x"), index=1),
                    right=Immediate(value=1),
                    consequent=Reference(name="x"),
                    otherwise=Reference(name="x"),
                ),
            ),
        ),
    )

    actual = constant_propagation_program(program)

    expected = Program(
        parameters=[],
        body=Let(
            bindings=[("x", Immediate(value=1))],
            body=Begin(
                effects=[
                    Apply(
                        target=Reference(name="a"),
                        arguments=[Immediate(value=1)],
                    ),
                    Store(
                        base=Allocate(count=1),
                        index=0,
                        value=Immediate(value=1),
                    ),
                ],
                value=Branch(
                    operator="==",
                    left=Load(base=Immediate(value=1), index=1),
                    right=Immediate(value=1),
                    consequent=Immediate(value=1),
                    otherwise=Immediate(value=1),
                ),
            ),
        ),
    )

    assert actual == expected


def test_constant_propagation_reference_passthrough_and_let_scope_pop():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[
                ("x", Immediate(value=1)),
                ("x", Primitive(operator="+", left=Reference(name="x"), right=Immediate(value=1))),
            ],
            body=Reference(name="x"),
        ),
    )

    actual = constant_propagation_program(program)

    expected = Program(
        parameters=[],
        body=Let(
            bindings=[
                ("x", Immediate(value=1)),
                ("x", Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=1))),
            ],
            body=Reference(name="x"),
        ),
    )

    assert actual == expected


def test_constant_propagation_reference_not_in_context_stays_reference():
    program = Program(
        parameters=[],
        body=Reference(name="unknown"),
    )

    actual = constant_propagation_program(program)

    expected = Program(
        parameters=[],
        body=Reference(name="unknown"),
    )

    assert actual == expected


def test_constant_propagation_begin_with_no_effects():
    program = Program(
        parameters=[],
        body=Begin(
            effects=[],
            value=Reference(name="x"),
        ),
    )

    actual = constant_propagation_program(program)

    expected = Program(
        parameters=[],
        body=Begin(
            effects=[],
            value=Reference(name="x"),
        ),
    )

    assert actual == expected


# Folding

def test_constant_folding_primitives_and_branches():
    program = Program(
        parameters=[],
        body=Begin(
            effects=[
                Primitive(operator="+", left=Immediate(value=0), right=Immediate(value=9)),
                Primitive(operator="-", left=Immediate(value=9), right=Immediate(value=0)),
                Primitive(operator="*", left=Immediate(value=0), right=Reference(name="a")),
                Primitive(operator="*", left=Immediate(value=1), right=Reference(name="b")),
                Primitive(operator="*", left=Reference(name="c"), right=Immediate(value=1)),
                Primitive(
                    operator="+",
                    left=Primitive(operator="+", left=Immediate(value=2), right=Reference(name="x")),
                    right=Primitive(operator="+", left=Immediate(value=3), right=Reference(name="y")),
                ),
            ],
            value=Begin(
                effects=[
                    Branch(
                        operator="<",
                        left=Immediate(value=1),
                        right=Immediate(value=2),
                        consequent=Immediate(value=10),
                        otherwise=Immediate(value=20),
                    ),
                    Branch(
                        operator="==",
                        left=Immediate(value=1),
                        right=Immediate(value=2),
                        consequent=Immediate(value=10),
                        otherwise=Immediate(value=20),
                    ),
                ],
                value=Primitive(operator="+", left=Reference(name="x"), right=Immediate(value=0)),
            ),
        ),
    )

    actual = constant_folding_program(program)

    expected = Program(
        parameters=[],
        body=Begin(
            effects=[
                Immediate(value=9),
                Immediate(value=9),
                Immediate(value=0),
                Reference(name="b"),
                Reference(name="c"),
                Primitive(
                    operator="+",
                    left=Primitive(operator="+", left=Reference(name="x"), right=Reference(name="y")),
                    right=Immediate(value=5),
                ),
            ],
            value=Begin(
                effects=[
                    Immediate(value=10),
                    Immediate(value=20),
                ],
                value=Primitive(operator="+", left=Reference(name="x"), right=Immediate(value=0)),
            ),
        ),
    )

    assert actual == expected


def test_constant_folding_other_forms_are_recursed():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[("x", Immediate(value=1))],
            body=Begin(
                effects=[
                    Apply(
                        target=Abstract(
                            parameters=["p"],
                            body=Primitive(operator="+", left=Reference(name="p"), right=Immediate(value=0)),
                        ),
                        arguments=[Primitive(operator="*", left=Immediate(value=1), right=Reference(name="x"))],
                    ),
                    Store(
                        base=Allocate(count=1),
                        index=0,
                        value=Primitive(operator="-", left=Immediate(value=3), right=Immediate(value=1)),
                    ),
                ],
                value=Load(base=Allocate(count=1), index=0),
            ),
        ),
    )

    actual = constant_folding_program(program)

    expected = Program(
        parameters=[],
        body=Let(
            bindings=[("x", Immediate(value=1))],
            body=Begin(
                effects=[
                    Apply(
                        target=Abstract(
                            parameters=["p"],
                            body=Primitive(operator="+", left=Reference(name="p"), right=Immediate(value=0)),
                        ),
                        arguments=[Reference(name="x")],
                    ),
                    Store(
                        base=Allocate(count=1),
                        index=0,
                        value=Immediate(value=2),
                    ),
                ],
                value=Load(base=Allocate(count=1), index=0),
            ),
        ),
    )

    assert actual == expected


def test_constant_folding_plus_immediate_on_right_branch():
    program = Program(
        parameters=[],
        body=Primitive(
            operator="+",
            left=Reference(name="x"),
            right=Immediate(value=3),
        ),
    )

    actual = constant_folding_program(program)

    expected = Program(
        parameters=[],
        body=Primitive(
            operator="+",
            left=Reference(name="x"),
            right=Immediate(value=3),
        ),
    )

    assert actual == expected


def test_constant_folding_subtract_general_case_and_equal_branch_true():
    program = Program(
        parameters=[],
        body=Begin(
            effects=[
                Primitive(
                    operator="-",
                    left=Reference(name="x"),
                    right=Reference(name="y"),
                )
            ],
            value=Branch(
                operator="==",
                left=Immediate(value=4),
                right=Immediate(value=4),
                consequent=Immediate(value=1),
                otherwise=Immediate(value=0),
            ),
        ),
    )

    actual = constant_folding_program(program)

    expected = Program(
        parameters=[],
        body=Begin(
            effects=[
                Primitive(
                    operator="-",
                    left=Reference(name="x"),
                    right=Reference(name="y"),
                )
            ],
            value=Immediate(value=1),
        ),
    )

    assert actual == expected


def test_constant_folding_multiply_general_case_and_non_immediate_branch():
    program = Program(
        parameters=[],
        body=Branch(
            operator="<",
            left=Primitive(operator="*", left=Reference(name="a"), right=Reference(name="b")),
            right=Immediate(value=0),
            consequent=Immediate(value=1),
            otherwise=Immediate(value=2),
        ),
    )

    actual = constant_folding_program(program)

    expected = Program(
        parameters=[],
        body=Branch(
            operator="<",
            left=Primitive(operator="*", left=Reference(name="a"), right=Reference(name="b")),
            right=Immediate(value=0),
            consequent=Immediate(value=1),
            otherwise=Immediate(value=2),
        ),
    )

    assert actual == expected


def test_constant_folding_minus_immediates_and_multiply_by_one_on_right():
    program = Program(
        parameters=[],
        body=Begin(
            effects=[
                Primitive(operator="-", left=Immediate(value=8), right=Immediate(value=3)),
            ],
            value=Primitive(operator="*", left=Reference(name="k"), right=Immediate(value=1)),
        ),
    )

    actual = constant_folding_program(program)

    expected = Program(
        parameters=[],
        body=Begin(
            effects=[
                Immediate(value=5),
            ],
            value=Reference(name="k"),
        ),
    )

    assert actual == expected


def test_constant_folding_branch_less_than_false_and_store_case():
    program = Program(
        parameters=[],
        body=Branch(
            operator="<",
            left=Immediate(value=3),
            right=Immediate(value=1),
            consequent=Store(base=Allocate(count=1), index=0, value=Immediate(value=1)),
            otherwise=Immediate(value=99),
        ),
    )

    actual = constant_folding_program(program)

    expected = Program(
        parameters=[],
        body=Immediate(value=99),
    )

    assert actual == expected


def test_constant_folding_specific_primitive_branches():
    program = Program(
        parameters=[],
        body=Begin(
            effects=[
                Primitive(operator="+", left=Immediate(value=0), right=Reference(name="r")),
                Primitive(operator="-", left=Reference(name="m"), right=Immediate(value=0)),
                Primitive(operator="*", left=Immediate(value=2), right=Immediate(value=3)),
            ],
            value=Primitive(operator="*", left=Reference(name="n"), right=Immediate(value=0)),
        ),
    )

    actual = constant_folding_program(program)

    expected = Program(
        parameters=[],
        body=Begin(
            effects=[
                Reference(name="r"),
                Reference(name="m"),
                Immediate(value=6),
            ],
            value=Immediate(value=0),
        ),
    )

    assert actual == expected


# DCE

def test_dead_code_elimination_removes_unused_pure_initializers_only():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[
                ("unused_pure", Immediate(value=1)),
                (
                    "unused_effectful",
                    Apply(target=Reference(name="a"), arguments=[Immediate(value=1)]),
                ),
                ("used", Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=1))),
            ],
            body=Reference(name="used"),
        ),
    )

    actual = dead_code_elimination_program(program)

    expected = Program(
        parameters=[],
        body=Let(
            bindings=[
                (
                    "unused_effectful",
                    Apply(target=Reference(name="a"), arguments=[Immediate(value=1)]),
                ),
                ("used", Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=1))),
            ],
            body=Reference(name="used"),
        ),
    )

    assert actual == expected


def test_dead_code_elimination_begin_and_misc_nodes():
    program = Program(
        parameters=[],
        body=Begin(
            effects=[
                Immediate(value=1),
                Store(base=Allocate(count=1), index=1, value=Immediate(value=1)),
                Abstract(parameters=["x"], body=Reference(name="x")),
                Load(base=Allocate(count=1), index=1),
            ],
            value=Branch(
                operator="==",
                left=Immediate(value=1),
                right=Immediate(value=1),
                consequent=Reference(name="a"),
                otherwise=Reference(name="b"),
            ),
        ),
    )

    actual = dead_code_elimination_program(program)

    expected = Program(
        parameters=[],
        body=Begin(
            effects=[
                Store(base=Allocate(count=1), index=1, value=Immediate(value=1)),
            ],
            value=Branch(
                operator="==",
                left=Immediate(value=1),
                right=Immediate(value=1),
                consequent=Reference(name="a"),
                otherwise=Reference(name="b"),
            ),
        ),
    )

    assert actual == expected


def test_dead_code_elimination_drop_empty_let():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[("x", Immediate(value=1))],
            body=Immediate(value=0),
        ),
    )

    actual = dead_code_elimination_program(program)

    expected = Program(
        parameters=[],
        body=Immediate(value=0),
    )

    assert actual == expected


def test_dead_code_elimination_keep_binding_used_by_later_binding():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[
                ("x", Immediate(value=1)),
                ("y", Primitive(operator="+", left=Reference(name="x"), right=Immediate(value=1))),
            ],
            body=Reference(name="y"),
        ),
    )

    actual = dead_code_elimination_program(program)

    expected = Program(
        parameters=[],
        body=Let(
            bindings=[
                ("x", Immediate(value=1)),
                ("y", Primitive(operator="+", left=Reference(name="x"), right=Immediate(value=1))),
            ],
            body=Reference(name="y"),
        ),
    )

    assert actual == expected


def test_dead_code_elimination_is_referenced_respects_bound_names():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[
                ("x", Immediate(value=1)),
            ],
            body=Abstract(
                parameters=["x"],
                body=Reference(name="x"),
            ),
        ),
    )

    actual = dead_code_elimination_program(program)

    expected = Program(
        parameters=[],
        body=Abstract(
            parameters=["x"],
            body=Reference(name="x"),
        ),
    )

    assert actual == expected


def test_dead_code_elimination_is_referenced_apply_target_and_begin_effect_hit():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[
                (
                    "a",
                    Abstract(
                        parameters=["n"],
                        body=Reference(name="n"),
                    ),
                ),
                ("x", Immediate(value=1)),
            ],
            body=Begin(
                effects=[
                    Apply(
                        target=Reference(name="a"),
                        arguments=[Reference(name="x")],
                    )
                ],
                value=Immediate(value=0),
            ),
        ),
    )

    actual = dead_code_elimination_program(program)

    expected = Program(
        parameters=[],
        body=Let(
            bindings=[
                (
                    "a",
                    Abstract(
                        parameters=["n"],
                        body=Reference(name="n"),
                    ),
                ),
                ("x", Immediate(value=1)),
            ],
            body=Begin(
                effects=[
                    Apply(
                        target=Reference(name="a"),
                        arguments=[Reference(name="x")],
                    )
                ],
                value=Immediate(value=0),
            ),
        ),
    )

    assert actual == expected


def test_is_pure_cases():
    assert is_pure(Reference(name="x"))
    assert is_pure(Immediate(value=1))
    assert is_pure(Allocate(count=1))
    assert is_pure(Load(base=Reference(name="x"), index=1))
    assert is_pure(Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=1)))
    assert is_pure(
        Branch(
            operator="==",
            left=Immediate(value=1),
            right=Immediate(value=1),
            consequent=Immediate(value=1),
            otherwise=Immediate(value=1),
        )
    )
    assert not is_pure(Apply(target=Reference(name="a"), arguments=[]))
    assert not is_pure(Store(base=Allocate(count=1), index=1, value=Immediate(value=1)))


def test_is_pure_let_and_begin_cases():
    pure_let = Let(
        bindings=[("a", Immediate(value=1))],
        body=Immediate(value=1),
    )
    impure_let = Let(
        bindings=[("a", Apply(target=Reference(name="a"), arguments=[]))],
        body=Immediate(value=1),
    )
    pure_begin = Begin(effects=[], value=Immediate(value=1))
    impure_begin = Begin(
        effects=[Store(base=Allocate(count=1), index=1, value=Immediate(value=1))],
        value=Immediate(value=1),
    )

    assert is_pure(pure_let)
    assert not is_pure(impure_let)
    assert is_pure(pure_begin)
    assert not is_pure(impure_begin)


def test_is_referenced_direct_cases():
    assert is_referenced(Reference(name="x"), "x", set())
    assert not is_referenced(Reference(name="x"), "x", {"x"})
    assert not is_referenced(Immediate(value=1), "x", set())
    assert not is_referenced(Allocate(count=1), "x", set())
    assert is_referenced(Primitive(operator="+", left=Reference(name="x"), right=Immediate(value=1)), "x", set())
    assert is_referenced(Load(base=Reference(name="x"), index=1), "x", set())
    assert is_referenced(Store(base=Reference(name="x"), index=1, value=Immediate(value=1)), "x", set())


def test_is_referenced_let_and_begin_and_apply_false_paths():
    term = Let(
        bindings=[("x", Immediate(value=1))],
        body=Reference(name="x"),
    )
    assert not is_referenced(term, "x", set())

    begin_term = Begin(effects=[Immediate(value=1)], value=Immediate(value=1))
    assert not is_referenced(begin_term, "x", set())

    apply_term = Apply(target=Reference(name="a"), arguments=[Immediate(value=1)])
    assert not is_referenced(apply_term, "x", set())


def test_is_referenced_early_true_and_branch_and_begin_value_true_paths():
    early_true_term = Let(
        bindings=[("a", Reference(name="x"))],
        body=Immediate(value=1),
    )
    assert is_referenced(early_true_term, "x", set())

    branch_term = Branch(
        operator="==",
        left=Immediate(value=1),
        right=Reference(name="x"),
        consequent=Immediate(value=1),
        otherwise=Immediate(value=1),
    )
    assert is_referenced(branch_term, "x", set())

    begin_term = Begin(effects=[Immediate(value=0)], value=Reference(name="x"))
    assert is_referenced(begin_term, "x", set())


def test_dead_code_elimination_begin_with_only_pure_effects_returns_value():
    program = Program(
        parameters=[],
        body=Begin(
            effects=[Immediate(value=1), Allocate(count=1)],
            value=Reference(name="x"),
        ),
    )

    actual = dead_code_elimination_program(program)

    expected = Program(
        parameters=[],
        body=Reference(name="x"),
    )

    assert actual == expected


# Optimize

def test_optimize_program_runs_to_fixed_point_with_reference_constants():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[
                ("x", Immediate(value=1)),
                ("y", Reference(name="x")),
                ("z", Primitive(operator="+", left=Reference(name="y"), right=Immediate(value=1))),
            ],
            body=Reference(name="z"),
        ),
    )

    actual = optimize_program(program)

    expected = Program(
        parameters=[],
        body=Immediate(value=2),
    )

    assert actual == expected

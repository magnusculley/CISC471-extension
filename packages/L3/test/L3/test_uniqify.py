from L3.syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Branch,
    Immediate,
    Let,
    LetRec,
    Load,
    Primitive,
    Program,
    Reference,
    Store,
)
from L3.uniqify import Context, uniqify_program, uniqify_term
from util.sequential_name_generator import SequentialNameGenerator


def test_uniqify_term_reference():
    term = Reference(name="x")

    context: Context = {"x": "y"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh=fresh)

    expected = Reference(name="y")

    assert actual == expected


def test_uniqify_term_reference_unbound_is_unchanged():
    term = Reference(name="x")

    context: Context = {}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh=fresh)

    expected = Reference(name="x")

    assert actual == expected


def test_uniqify_immediate():
    term = Immediate(value=42)

    context: Context = dict[str, str]()
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Immediate(value=42)

    assert actual == expected


def test_uniqify_term_let():
    term = Let(
        bindings=[
            ("x", Immediate(value=1)),
            ("y", Reference(name="x")),
        ],
        body=Apply(
            target=Reference(name="x"),
            arguments=[
                Reference(name="y"),
            ],
        ),
    )

    context: Context = {"x": "y"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Let(
        bindings=[
            ("x0", Immediate(value=1)),
            ("y0", Reference(name="y")),
        ],
        body=Apply(
            target=Reference(name="x0"),
            arguments=[
                Reference(name="y0"),
            ],
        ),
    )

    assert actual == expected


def test_uniqify_term_letrec_mutual_recursion():
    term = LetRec(
        bindings=[
            (
                "f",
                Abstract(
                    parameters=["x"],
                    body=Apply(target=Reference(name="g"), arguments=[Reference(name="x")]),
                ),
            ),
            (
                "g",
                Abstract(
                    parameters=["y"],
                    body=Apply(target=Reference(name="f"), arguments=[Reference(name="y")]),
                ),
            ),
        ],
        body=Reference(name="f"),
    )

    context: Context = {}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = LetRec(
        bindings=[
            (
                "f0",
                Abstract(
                    parameters=["x0"],
                    body=Apply(target=Reference(name="g0"), arguments=[Reference(name="x0")]),
                ),
            ),
            (
                "g0",
                Abstract(
                    parameters=["y0"],
                    body=Apply(target=Reference(name="f0"), arguments=[Reference(name="y0")]),
                ),
            ),
        ],
        body=Reference(name="f0"),
    )

    assert actual == expected


def test_uniqify_term_abstract_shadows_outer_name():
    term = Abstract(
        parameters=["x"],
        body=Primitive(operator="+", left=Reference(name="x"), right=Reference(name="y")),
    )

    context: Context = {"x": "x_outer", "y": "y_outer"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Abstract(
        parameters=["x0"],
        body=Primitive(operator="+", left=Reference(name="x0"), right=Reference(name="y_outer")),
    )

    assert actual == expected


def test_uniqify_term_apply():
    term = Apply(
        target=Reference(name="f"),
        arguments=[Reference(name="x"), Immediate(value=3)],
    )

    context: Context = {"f": "f0", "x": "x0"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Apply(
        target=Reference(name="f0"),
        arguments=[Reference(name="x0"), Immediate(value=3)],
    )

    assert actual == expected


def test_uniqify_term_allocate():
    term = Allocate(count=4)

    context: Context = {}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Allocate(count=4)

    assert actual == expected


def test_uniqify_term_branch_load_store_begin():
    term = Begin(
        effects=[
            Store(base=Reference(name="mem"), index=0, value=Reference(name="x")),
            Load(base=Reference(name="mem"), index=0),
        ],
        value=Branch(
            operator="<",
            left=Reference(name="x"),
            right=Reference(name="y"),
            consequent=Reference(name="x"),
            otherwise=Reference(name="y"),
        ),
    )

    context: Context = {"mem": "mem0", "x": "x0", "y": "y0"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Begin(
        effects=[
            Store(base=Reference(name="mem0"), index=0, value=Reference(name="x0")),
            Load(base=Reference(name="mem0"), index=0),
        ],
        value=Branch(
            operator="<",
            left=Reference(name="x0"),
            right=Reference(name="y0"),
            consequent=Reference(name="x0"),
            otherwise=Reference(name="y0"),
        ),
    )

    assert actual == expected


def test_uniqify_program_parameters_and_body():
    program = Program(
        parameters=["x", "y"],
        body=Let(
            bindings=[("x", Reference(name="y"))],
            body=Primitive(operator="*", left=Reference(name="x"), right=Reference(name="y")),
        ),
    )

    _, actual = uniqify_program(program)

    expected = Program(
        parameters=["x0", "y0"],
        body=Let(
            bindings=[("x1", Reference(name="y0"))],
            body=Primitive(operator="*", left=Reference(name="x1"), right=Reference(name="y0")),
        ),
    )

    assert actual == expected

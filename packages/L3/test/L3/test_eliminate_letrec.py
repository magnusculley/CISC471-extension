from L2 import syntax as L2
from L3 import syntax as L3
from L3.eliminate_letrec import Context, eliminate_letrec_program, eliminate_letrec_term


def test_check_term_let():
    term = L3.Let(
        bindings=[
            ("x", L3.Immediate(value=0)),
        ],
        body=L3.Reference(name="x"),
    )

    context: Context = {}

    expected = L2.Let(
        bindings=[
            ("x", L2.Immediate(value=0)),
        ],
        body=L2.Reference(name="x"),
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected


def test_eliminate_letrec_program():
    program = L3.Program(parameters=[], body=L3.Immediate(value=0))
    result = eliminate_letrec_program(program)
    assert result == L2.Program(parameters=[], body=L2.Immediate(value=0))


## Above implemented in class, below implemented in test file


def test_eliminate_letrec_reference():
    term = L3.LetRec(
        bindings=[("x", L3.Abstract(parameters=["n"], body=L3.Reference(name="n")))],
        body=L3.Reference(name="x"),
    )
    expected = L2.Let(
        bindings=[("x", L2.Allocate(count=2))],
        body=L2.Begin(
            effects=[
                L2.Store(
                    base=L2.Reference(name="x"),
                    index=0,
                    value=L2.Abstract(parameters=["n"], body=L2.Reference(name="n")),
                ),
                L2.Store(
                    base=L2.Reference(name="x"),
                    index=1,
                    value=L2.Reference(name="x"),
                ),
            ],
            value=L2.Reference(name="x"),
        ),
    )
    actual = eliminate_letrec_term(term, context={})
    assert actual == expected


def test_eliminate_letrec_body():
    term = L3.LetRec(
        bindings=[("x", L3.Abstract(parameters=["n"], body=L3.Reference(name="x")))],
        body=L3.Reference(name="x"),
    )

    expected = L2.Let(
        bindings=[("x", L2.Allocate(count=2))],
        body=L2.Begin(
            effects=[
                L2.Store(
                    base=L2.Reference(name="x"),
                    index=0,
                    value=L2.Abstract(parameters=["n"], body=L2.Reference(name="x")),
                ),
                L2.Store(
                    base=L2.Reference(name="x"),
                    index=1,
                    value=L2.Reference(name="x"),
                ),
            ],
            value=L2.Reference(name="x"),
        ),
    )

    actual = eliminate_letrec_term(term, context={})

    assert actual == expected


def test_eliminate_letrec_apply_abstract():
    term = L3.Apply(
        target=L3.Reference(name="f"),
        arguments=[L3.Immediate(value=1)],
    )

    expected = L2.Apply(
        target=L2.Load(base=L2.Reference(name="f"), index=0),
        arguments=[
            L2.Load(base=L2.Reference(name="f"), index=1),
            L2.Immediate(value=1),
        ],
    )

    actual = eliminate_letrec_term(term, context={"f": True})

    assert actual == expected


def test_eliminate_letrec_branch():
    term = L3.Branch(
        operator="==",
        left=L3.Immediate(value=1),
        right=L3.Immediate(value=1),
        consequent=L3.Immediate(value=1),
        otherwise=L3.Immediate(value=1),
    )

    expected = L2.Branch(
        operator="==",
        left=L2.Immediate(value=1),
        right=L2.Immediate(value=1),
        consequent=L2.Immediate(value=1),
        otherwise=L2.Immediate(value=1),
    )

    actual = eliminate_letrec_term(term, context={})

    assert actual == expected


def test_eliminate_letrec_primitive():
    term = L3.Primitive(
        operator="*",
        left=L3.Immediate(value=1),
        right=L3.Immediate(value=1),
    )

    context: Context = {}

    expected = L2.Primitive(
        operator="*",
        left=L2.Immediate(value=1),
        right=L2.Immediate(value=1),
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected


def test_check_term_begin():
    term = L3.Begin(effects=[L3.Immediate(value=0)], value=L3.Immediate(value=0))
    context: Context = {}
    actual = eliminate_letrec_term(term, context)
    assert actual == L2.Begin(effects=[L2.Immediate(value=0)], value=L2.Immediate(value=0))


def test_check_term_load():
    term = L3.Load(base=L3.Reference(name="x"), index=0)
    context: Context = {}
    actual = eliminate_letrec_term(term, context)
    assert actual == L2.Load(base=L2.Reference(name="x"), index=0)


def test_eliminate_letrec_store():
    term = L3.Store(
        base=L3.Allocate(count=1),
        index=0,
        value=L3.Immediate(value=1),
    )

    expected = L2.Store(
        base=L2.Allocate(count=1),
        index=0,
        value=L2.Immediate(value=1),
    )

    actual = eliminate_letrec_term(term, context={})

    assert actual == expected

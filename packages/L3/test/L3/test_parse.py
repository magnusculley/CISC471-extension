from L3.parse import parse_program, parse_term
from L3.syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Boolean,
    Branch,
    Float,
    Immediate,
    Let,
    LetRec,
    Load,
    Primitive,
    Program,
    Reference,
    Store,
    Tuple,
)

# The starter tests for parser already covered 100% branch coverage,
# so I figured I would just explain what each one does


# Let
# Parses (let () x) - a let expression with no bindings that just returns reference x.
def test_parse_let_empty():
    source = "(let () x)"

    expected = Let(
        bindings=[],
        body=Reference(name="x"),
    )

    actual = parse_term(source)

    assert actual == expected


# Parses (let ((x 0)) x) - expects to bind x to 0, then returns x.
def test_parse_let_bindings():
    source = "(let ((x 0)) x)"

    expected = Let(
        bindings=[
            ("x", Immediate(value=0)),
        ],
        body=Reference(name="x"),
    )

    actual = parse_term(source)

    assert actual == expected


# LetRec
# Parses (letrec () x) - letrec with no bindings, returns x.
def test_parse_letrec_empty():
    source = "(letrec () x)"

    expected = LetRec(
        bindings=[],
        body=Reference(name="x"),
    )

    actual = parse_term(source)

    assert actual == expected


# Parses (letrec ((x 0)) x) - binds x to 0 recursively, returns x
def test_parse_letrec_bindings():
    source = "(letrec ((x 0)) x)"

    expected = LetRec(
        bindings=[
            ("x", Immediate(value=0)),
        ],
        body=Reference(name="x"),
    )

    actual = parse_term(source)

    assert actual == expected


# Reference
# Parses x - a standalone variable reference, for use in let and letrec bodies and as arguments to apply
def test_parse_reference():
    source = "x"

    expected = Reference(
        name="x",
    )

    actual = parse_term(source)

    assert actual == expected


# Abstract
# Parses (\ (x) x) - identity function taking parameter x and returning x.
# Python equivalent: lambda x: x
def test_parse_abstract():
    source = "(\\ (x) x)"

    expected = Abstract(
        parameters=["x"],
        body=Reference(name="x"),
    )

    actual = parse_term(source)

    assert actual == expected


# Apply
# Parses (x) - calling x with no arguments.
# Python equivalent: x()
def test_parse_apply_empty():
    source = "(x)"

    expected = Apply(
        target=Reference(name="x"),
        arguments=[],
    )

    actual = parse_term(source)

    assert actual == expected


# Parses (x y z) - calling x with arguments y and z.
# Python equivalent: x(y, z)
def test_parse_apply_arguments():
    source = "(x y z)"

    expected = Apply(
        target=Reference(name="x"),
        arguments=[Reference(name="y"), Reference(name="z")],
    )

    actual = parse_term(source)

    assert actual == expected


# Immediate
# Parses 42 - a literal integer constant
def test_parse_immediate():
    source = "42"

    expected = Immediate(value=42)

    actual = parse_term(source)

    assert actual == expected


# Primitive
# Parses (+ 1 2) - addition operation, 1+2
def test_parse_add():
    source = "(+ 1 2)"

    expected = Primitive(
        operator="+",
        left=Immediate(value=1),
        right=Immediate(value=2),
    )

    actual = parse_term(source)

    assert actual == expected


# Parses (- 3 2) - subtraction operation, 3-2
def test_parse_subtract():
    source = "(- 3 2)"

    expected = Primitive(
        operator="-",
        left=Immediate(value=3),
        right=Immediate(value=2),
    )

    actual = parse_term(source)

    assert actual == expected


# Parses (* 2 3) - multiplication operation, 2*3
def test_parse_multiply():
    source = "(* 2 3)"
    expected = Primitive(
        operator="*",
        left=Immediate(value=2),
        right=Immediate(value=3),
    )
    actual = parse_term(source)
    assert actual == expected


# Branch
# Parses (if (< 1 2) 1 0) - evaluates that the constructed branch is a less-than check, if 1<2 then 1 else 0.
def test_parse_less_than():
    source = "(if (< 1 2) 1 0)"

    expected = Branch(
        operator="<",
        left=Immediate(value=1),
        right=Immediate(value=2),
        consequent=Immediate(value=1),
        otherwise=Immediate(value=0),
    )

    actual = parse_term(source)

    assert actual == expected


# Parses (if (== 1 1) 1 0) - evaluates that the constructed branch is an equality check, if 1==1 then 1 else 0.
def test_parse_equal_to():
    source = "(if (== 1 1) 1 0)"

    expected = Branch(
        operator="==",
        left=Immediate(value=1),
        right=Immediate(value=1),
        consequent=Immediate(value=1),
        otherwise=Immediate(value=0),
    )

    actual = parse_term(source)

    assert actual == expected


# Allocate
# Parses (allocate 0) - allocate memory for 0 elements
def test_parse_allocate():
    source = "(allocate 0)"

    expected = Allocate(
        count=0,
    )

    actual = parse_term(source)

    assert actual == expected


# Load
# Parses (load x 0) - load from memory at base x, index 0.
def test_parse_load():
    source = "(load x 0)"

    expected = Load(
        base=Reference(name="x"),
        index=0,
    )

    actual = parse_term(source)

    assert actual == expected


# Store
# Parses (store x 0 1) - store value 1 to memory at base x, index 0.
def test_parse_store():
    source = "(store x 0 1)"

    expected = Store(
        base=Reference(name="x"),
        index=0,
        value=Immediate(value=1),
    )

    actual = parse_term(source)

    assert actual == expected


# Parses (begin x) - sequence with no effects, just returns x.
def test_parse_begin():
    source = "(begin x)"

    expected = Begin(
        effects=[],
        value=Reference(name="x"),
    )

    actual = parse_term(source)

    assert actual == expected


# Parses (begin x y z) - executes x and y for side effects, returns z.
def test_parse_begin_effects():
    source = "(begin x y z)"

    expected = Begin(
        effects=[
            Reference(name="x"),
            Reference(name="y"),
        ],
        value=Reference(name="z"),
    )

    actual = parse_term(source)

    assert actual == expected


# Program
# Parses (l3 (x) x) a complete L3 program and usually the entry point of the parser
def test_parse_program_identity():
    source = "(l3 (x) x)"

    expected = Program(
        parameters=["x"],
        body=Reference(name="x"),
    )

    actual = parse_program(source)

    assert actual == expected


def test_parse_float():
    source = " 3.14 "

    expected = Float(value=3.14)

    actual = parse_term(source)

    assert actual == expected


def test_parse_boolean():
    source = "true"

    expected = Boolean(value=True)

    actual = parse_term(source)

    assert actual == expected


def test_parse_tuple():
    source = "( 1 2 3 )"

    expected = Tuple(elements=[Immediate(value=1), Immediate(value=2), Immediate(value=3)])

    actual = parse_term(source)

    assert actual == expected


def test_parse_index():
    source = "( 1 2 3 )[1]"

    expected = Index(
        tuple=Tuple(elements=[Immediate(value=1), Immediate(value=2), Immediate(value=3)]),
        index=1,
    )

    actual = parse_term(source)

    assert actual == expected

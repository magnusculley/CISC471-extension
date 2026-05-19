from L0 import syntax as L0
from L1 import syntax as L1
from L1.close import close_program, close_statement, free_identifiers


def test_close_program_lifts_abstract_and_rewrites_apply_with_free_variables():
    program = L1.Program(
        parameters=["x"],
        body=L1.Abstract(
            destination="f",
            parameters=["y"],
            body=L1.Primitive(
                destination="sum",
                operator="+",
                left="x",
                right="y",
                then=L1.Halt(value="sum"),
            ),
            then=L1.Apply(target="f", arguments=["x"]),
        ),
    )

    actual = close_program(program)

    expected = L0.Program(
        procedures=[
            L0.Procedure(
                name="l0",
                parameters=["x"],
                body=L0.Address(
                    destination="f",
                    name="f",
                    then=L0.Call(
                        target="f",
                        arguments=["x", "x"],
                    ),
                ),
            ),
            L0.Procedure(
                name="f",
                parameters=["x", "y"],
                body=L0.Primitive(
                    destination="sum",
                    operator="+",
                    left="x",
                    right="y",
                    then=L0.Halt(value="sum"),
                ),
            ),
        ]
    )

    assert actual == expected


def test_close_statement_copy_tracks_aliases_and_shadowing():
    procedures: list[L0.Procedure] = []

    statement = L1.Copy(
        destination="g",
        source="f",
        then=L1.Copy(
            destination="g",
            source="u",
            then=L1.Immediate(
                destination="k",
                value=1,
                then=L1.Apply(target="g", arguments=["k"]),
            ),
        ),
    )

    actual = close_statement(
        statement,
        context={"f": ("f", ["x"])},
        procedures=procedures,
    )

    expected = L0.Copy(
        destination="g",
        source="f",
        then=L0.Copy(
            destination="g",
            source="u",
            then=L0.Immediate(
                destination="k",
                value=1,
                then=L0.Call(target="g", arguments=["k"]),
            ),
        ),
    )

    assert actual == expected
    assert procedures == []


def test_close_statement_converts_remaining_statement_forms():
    procedures: list[L0.Procedure] = []

    statement = L1.Primitive(
        destination="a",
        operator="+",
        left="x",
        right="y",
        then=L1.Allocate(
            destination="mem",
            count=1,
            then=L1.Store(
                base="mem",
                index=0,
                value="a",
                then=L1.Load(
                    destination="v",
                    base="mem",
                    index=0,
                    then=L1.Branch(
                        operator="<",
                        left="v",
                        right="a",
                        then=L1.Apply(target="p", arguments=["v"]),
                        otherwise=L1.Halt(value="a"),
                    ),
                ),
            ),
        ),
    )

    actual = close_statement(statement, context={}, procedures=procedures)

    expected = L0.Primitive(
        destination="a",
        operator="+",
        left="x",
        right="y",
        then=L0.Allocate(
            destination="mem",
            count=1,
            then=L0.Store(
                base="mem",
                index=0,
                value="a",
                then=L0.Load(
                    destination="v",
                    base="mem",
                    index=0,
                    then=L0.Branch(
                        operator="<",
                        left="v",
                        right="a",
                        then=L0.Call(target="p", arguments=["v"]),
                        otherwise=L0.Halt(value="a"),
                    ),
                ),
            ),
        ),
    )

    assert actual == expected
    assert procedures == []


def test_free_identifiers_collects_ordered_unique_names():
    statement = L1.Copy(
        destination="a",
        source="x",
        then=L1.Abstract(
            destination="f",
            parameters=["p"],
            body=L1.Branch(
                operator="==",
                left="a",
                right="z",
                then=L1.Apply(target="f", arguments=["p", "a"]),
                otherwise=L1.Store(
                    base="m",
                    index=0,
                    value="w",
                    then=L1.Load(
                        destination="tmp",
                        base="m",
                        index=0,
                        then=L1.Halt(value="tmp"),
                    ),
                ),
            ),
            then=L1.Apply(target="f", arguments=["a"]),
        ),
    )

    actual = free_identifiers(statement, set())

    assert actual == ["x", "z", "m", "w"]


def test_free_identifiers_covers_immediate_allocate_primitive_branch_store_paths():
    statement = L1.Immediate(
        destination="tmp0",
        value=0,
        then=L1.Allocate(
            destination="tmp1",
            count=1,
            then=L1.Primitive(
                destination="tmp2",
                operator="+",
                left="l",
                right="r",
                then=L1.Branch(
                    operator="<",
                    left="bl",
                    right="br",
                    then=L1.Apply(target="t", arguments=["a1", "a1"]),
                    otherwise=L1.Store(
                        base="sb",
                        index=0,
                        value="sv",
                        then=L1.Halt(value="hv"),
                    ),
                ),
            ),
        ),
    )

    actual = free_identifiers(statement, {"t", "hv"})

    assert actual == ["l", "r", "bl", "br", "a1", "sb", "sv"]


def test_free_identifiers_skips_bound_names_in_all_conditional_paths():
    statement = L1.Primitive(
        destination="tmp",
        operator="+",
        left="l",
        right="l",
        then=L1.Branch(
            operator="==",
            left="b",
            right="b",
            then=L1.Store(
                base="s",
                index=0,
                value="s",
                then=L1.Halt(value="s"),
            ),
            otherwise=L1.Halt(value="s"),
        ),
    )

    actual = free_identifiers(statement, {"l", "b", "s"})

    assert actual == []


def test_free_identifiers_float_boolean_tuple_index_paths():
    statement = L1.Float(
        destination="f",
        value=1.5,
        then=L1.Boolean(
            destination="b",
            value=True,
            then=L1.Tuple(
                destination="t",
                elements=["x", "x", "y"],
                then=L1.Index(
                    destination="i",
                    tuple="tup",
                    index=0,
                    then=L1.Halt(value="h"),
                ),
            ),
        ),
    )

    actual = free_identifiers(statement, {"h", "y"})

    assert actual == ["x", "tup"]


def test_close_statement_float_boolean_tuple_index_paths():
    procedures: list[L0.Procedure] = []

    statement = L1.Float(
        destination="f",
        value=3.25,
        then=L1.Boolean(
            destination="b",
            value=False,
            then=L1.Tuple(
                destination="t",
                elements=["a", "b"],
                then=L1.Index(
                    destination="i",
                    tuple="t",
                    index=1,
                    then=L1.Apply(target="f", arguments=["i"]),
                ),
            ),
        ),
    )

    actual = close_statement(statement, context={"f": ("f", ["x"])}, procedures=procedures)

    expected = L0.Float(
        destination="f",
        value=3.25,
        then=L0.Boolean(
            destination="b",
            value=False,
            then=L0.Tuple(
                destination="t",
                elements=["a", "b"],
                then=L0.Index(
                    destination="i",
                    tuple="t",
                    index=1,
                    then=L0.Call(target="f", arguments=["i"]),
                ),
            ),
        ),
    )

    assert actual == expected
    assert procedures == []


def test_free_identifiers_index_base_already_bound():
    statement = L1.Index(
        destination="out",
        tuple="tup",
        index=0,
        then=L1.Halt(value="done"),
    )

    actual = free_identifiers(statement, {"tup", "done"})

    assert actual == []

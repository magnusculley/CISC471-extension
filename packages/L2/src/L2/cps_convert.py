# ruff: noqa
from collections.abc import Callable, Sequence
from functools import partial

from L1 import syntax as L1

from L2 import syntax as L2


def cps_convert_term(
    term: L2.Term,
    k: Callable[[L1.Identifier], L1.Statement],
    fresh: Callable[[str], str],
) -> L1.Statement:
    _term = partial(cps_convert_term, fresh=fresh)
    _terms = partial(cps_convert_terms, fresh=fresh)

    match term:
        case L2.Let(bindings=bindings, body=body):
            match bindings:
                case []:
                    return _term(body, k)

                case [(name, value), *rest]:
                    return _term(
                        value,
                        lambda source: L1.Copy(
                            destination=name,
                            source=source,
                            then=_term(L2.Let(bindings=rest, body=body), k),
                        ),
                    )

                case _:  # pragma: no cover
                    raise ValueError(bindings)

        case L2.Reference(name=name):
            return k(name)

        case L2.Abstract(parameters=parameters, body=body):
            destination = fresh("t")
            continuation = fresh("k")

            return L1.Abstract(
                destination=destination,
                parameters=[*parameters, continuation],
                body=_term(
                    body,
                    lambda body_value: L1.Apply(
                        target=continuation,
                        arguments=[body_value],
                    ),
                ),
                then=k(destination),
            )

        case L2.Apply(target=target, arguments=arguments):
            continuation = fresh("k")
            value = fresh("t")
            return _term(
                target,
                lambda target_name: _terms(
                    arguments,
                    lambda argument_names: L1.Abstract(
                        destination=continuation,
                        parameters=[value],
                        body=k(value),
                        then=L1.Apply(
                            target=target_name,
                            arguments=[*argument_names, continuation],
                        ),
                    ),
                ),
            )

        case L2.Immediate(value=value):
            destination = fresh("t")
            return L1.Immediate(
                destination=destination,
                value=value,
                then=k(destination),
            )

        case L2.Primitive(operator=operator, left=left, right=right):
            return _term(
                left,
                lambda left_value: _term(
                    right,
                    lambda right_value: L1.Primitive(
                        destination=(destination := fresh("t")),
                        operator=operator,
                        left=left_value,
                        right=right_value,
                        then=k(destination),
                    ),
                ),
            )

        case L2.Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            join = fresh("j")
            value = fresh("t")

            return L1.Abstract(
                destination=join,
                parameters=[value],
                body=k(value),
                then=_term(
                    left,
                    lambda left_value: _term(
                        right,
                        lambda right_value: L1.Branch(
                            operator=operator,
                            left=left_value,
                            right=right_value,
                            then=_term(
                                consequent,
                                lambda consequent_value: L1.Apply(
                                    target=join,
                                    arguments=[consequent_value],
                                ),
                            ),
                            otherwise=_term(
                                otherwise,
                                lambda otherwise_value: L1.Apply(
                                    target=join,
                                    arguments=[otherwise_value],
                                ),
                            ),
                        ),
                    ),
                ),
            )

        case L2.Allocate(count=count):
            destination = fresh("t")
            return L1.Allocate(
                destination=destination,
                count=count,
                then=k(destination),
            )

        case L2.Load(base=base, index=index):
            return _term(
                base,
                lambda base_value: L1.Load(
                    destination=(destination := fresh("t")),
                    base=base_value,
                    index=index,
                    then=k(destination),
                ),
            )

        case L2.Store(base=base, index=index, value=value):
            return _term(
                base,
                lambda base_value: _term(
                    value,
                    lambda value_name: L1.Store(
                        base=base_value,
                        index=index,
                        value=value_name,
                        then=L1.Immediate(
                            destination=(destination := fresh("t")),
                            value=0,
                            then=k(destination),
                        ),
                    ),
                ),
            )

        case L2.Begin(effects=effects, value=value):  # pragma: no branch
            match effects:
                case []:
                    return _term(value, k)

                case [first, *rest]:
                    return _term(
                        first,
                        lambda _ignored: _term(L2.Begin(effects=rest, value=value), k),
                    )

                case _:  # pragma: no cover
                    raise ValueError(effects)

        case L2.Float(value=value):
            destination = fresh("t")
            return L1.Float(
                destination=destination,
                value=value,
                then=k(destination),
            )

        case L2.Boolean(value=value):
            destination = fresh("t")
            return L1.Boolean(
                destination=destination,
                value=value,
                then=k(destination),
            )

        case L2.Tuple(elements=elements):
            return _terms(
                elements,
                lambda element_values: L1.Tuple(
                    destination=(destination := fresh("t")),
                    elements=element_values,
                    then=k(destination),
                ),
            )

        case L2.Index(tuple=tuple, index=index):
            return _term(
                tuple,
                lambda tuple_value: L1.Index(
                    destination=(destination := fresh("t")),
                    tuple=tuple_value,
                    index=index,
                    then=k(destination),
                ),
            )

        case _:  # pragma: no cover
            raise ValueError(term)


def cps_convert_terms(
    terms: Sequence[L2.Term],
    k: Callable[[Sequence[L1.Identifier]], L1.Statement],
    fresh: Callable[[str], str],
) -> L1.Statement:
    _term = partial(cps_convert_term, fresh=fresh)
    _terms = partial(cps_convert_terms, fresh=fresh)

    match terms:
        case []:
            return k([])

        case [first, *rest]:
            return _term(first, lambda first: _terms(rest, lambda rest: k([first, *rest])))

        case _:  # pragma: no cover
            raise ValueError(terms)


def cps_convert_program(
    program: L2.Program,
    fresh: Callable[[str], str],
) -> L1.Program:
    _term = partial(cps_convert_term, fresh=fresh)

    match program:
        case L2.Program(parameters=parameters, body=body):  # pragma: no branch
            return L1.Program(
                parameters=parameters,
                body=_term(body, lambda value: L1.Halt(value=value)),
            )

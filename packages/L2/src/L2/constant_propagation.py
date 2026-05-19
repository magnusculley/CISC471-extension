from collections.abc import Mapping
from functools import partial

from .syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Boolean,
    Branch,
    Float,
    Identifier,
    Immediate,
    Index,
    Let,
    Load,
    Primitive,
    Program,
    Reference,
    Store,
    Term,
    Tuple,
)

type Constant = Immediate | Reference
type Context = Mapping[Identifier, Constant]


def constant_propagation_term(term: Term, context: Context) -> Term:
    recur = partial(constant_propagation_term, context=context)

    match term:
        case Let(bindings=bindings, body=body):
            propagated_bindings: list[tuple[Identifier, Term]] = []
            scope: dict[Identifier, Constant] = dict(context)

            for name, value in bindings:
                propagated_value = constant_propagation_term(value, scope)
                propagated_bindings.append((name, propagated_value))

                if isinstance(propagated_value, Immediate | Reference):
                    scope[name] = propagated_value
                else:
                    scope.pop(name, None)

            return Let(
                bindings=propagated_bindings,
                body=constant_propagation_term(body, scope),
            )

        case Reference(name=name):
            return context.get(name, term)

        case Abstract(parameters=parameters, body=body):
            inner = dict(context)
            for parameter in parameters:
                inner.pop(parameter, None)

            return Abstract(
                parameters=parameters,
                body=constant_propagation_term(body, inner),
            )

        case Apply(target=target, arguments=arguments):
            return Apply(
                target=recur(target),
                arguments=[recur(argument) for argument in arguments],
            )

        case Immediate():
            return term

        case Primitive(operator=operator, left=left, right=right):
            return Primitive(
                operator=operator,
                left=recur(left),
                right=recur(right),
            )

        case Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            return Branch(
                operator=operator,
                left=recur(left),
                right=recur(right),
                consequent=recur(consequent),
                otherwise=recur(otherwise),
            )

        case Allocate(count=count):
            return Allocate(count=count)

        case Load(base=base, index=index):
            return Load(base=recur(base), index=index)

        case Store(base=base, index=index, value=value):
            return Store(
                base=recur(base),
                index=index,
                value=recur(value),
            )

        case Begin(effects=effects, value=value):  # pragma: no branch
            return Begin(
                effects=[recur(effect) for effect in effects],
                value=recur(value),
            )

        case Float(value=value):
            return term

        case Boolean(value=value):
            return term

        case Tuple(elements=elements):
            return Tuple(elements=[recur(element) for element in elements])

        case Index(tuple=tuple, index=index):
            return Index(tuple=recur(tuple), index=index)


def constant_propagation_program(program: Program) -> Program:
    match program:
        case Program(parameters=parameters, body=body):  # pragma: no branch
            return Program(
                parameters=parameters,
                body=constant_propagation_term(body, context={}),
            )

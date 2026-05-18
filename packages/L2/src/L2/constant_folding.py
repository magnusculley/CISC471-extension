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
    Let,
    Load,
    Primitive,
    Program,
    Reference,
    Store,
    Term,
    Tuple,
)

type Context = Mapping[Identifier, None]


def constant_folding_term(term: Term, context: Context) -> Term:
    recur = partial(constant_folding_term, context=context)

    match term:
        case Let(bindings=bindings, body=body):
            return Let(
                bindings=[(name, recur(value)) for name, value in bindings],
                body=constant_folding_term(body, context={**context, **{name: None for name, _ in bindings}}),
            )

        case Reference(name=name):
            return Reference(name=name)

        case Abstract(parameters=parameters, body=body):
            return Abstract(
                parameters=parameters,
                body=constant_folding_term(body, context={**context, **{parameter: None for parameter in parameters}}),
            )

        case Apply(target=target, arguments=arguments):
            return Apply(
                target=recur(target),
                arguments=[recur(argument) for argument in arguments],
            )

        case Immediate():
            return term

        case Primitive(operator=operator, left=left, right=right):
            match operator:
                case "+":
                    match recur(left), recur(right):
                        case Immediate(value=value1), Immediate(value=value2):
                            return Immediate(value=value1 + value2)
                        case Immediate(value=0), right:
                            return right
                        case (
                            Primitive(left=Immediate(value=value1), right=left),
                            Primitive(left=Immediate(value=value2), right=right),
                        ):
                            return Primitive(
                                operator="+",
                                left=Primitive(operator="+", left=left, right=right),
                                right=Immediate(value=value1 + value2),
                            )

                        case left, Immediate() as right:
                            return Primitive(operator="+", left=left, right=right)
                        case left, right:  # pragma: no branch
                            return Primitive(operator="+", left=left, right=right)
                case "-":
                    match recur(left), recur(right):
                        case Immediate(value=value1), Immediate(value=value2):
                            return Immediate(value=value1 - value2)
                        case left, Immediate(value=0):
                            return left
                        case left, right:  # pragma: no branch
                            return Primitive(operator="-", left=left, right=right)
                case "*":  # pragma: no branch
                    match recur(left), recur(right):
                        case Immediate(value=value1), Immediate(value=value2):
                            return Immediate(value=value1 * value2)
                        case Immediate(value=0), _:
                            return Immediate(value=0)
                        case _, Immediate(value=0):
                            return Immediate(value=0)
                        case Immediate(value=1), right:
                            return right
                        case left, Immediate(value=1):
                            return left
                        case left, right:  # pragma: no branch
                            return Primitive(operator="*", left=left, right=right)
                        # Maybe there is an easier way to do this that covers everything

        case Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            folded_left = recur(left)
            folded_right = recur(right)
            folded_consequent = recur(consequent)
            folded_otherwise = recur(otherwise)

            match folded_left, folded_right:
                case Immediate(value=value1), Immediate(value=value2):
                    if operator == "<":
                        return folded_consequent if value1 < value2 else folded_otherwise

                    return folded_consequent if value1 == value2 else folded_otherwise

                case _, _:  # pragma: no branch
                    return Branch(
                        operator=operator,
                        left=folded_left,
                        right=folded_right,
                        consequent=folded_consequent,
                        otherwise=folded_otherwise,
                    )

        case Allocate(count=count):
            return Allocate(count=count)

        case Load(base=base, index=index):
            return Load(base=recur(base), index=index)

        case Store(base=base, index=index, value=value):
            return Store(base=recur(base), index=index, value=recur(value))

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


def constant_folding_program(program: Program) -> Program:
    match program:
        case Program(parameters=parameters, body=body):  # pragma: no branch
            return Program(
                parameters=parameters,
                body=constant_folding_term(body, context={}),
            )
